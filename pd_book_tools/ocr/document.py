from __future__ import annotations

import json
from dataclasses import dataclass, field
from logging import getLogger
from pathlib import Path
from typing import Collection, Dict, List, Optional, Union

from pandas import DataFrame, to_numeric as pd_to_numeric

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.word import Word

# Configure logging
logger = getLogger(__name__)


@dataclass
class Document:
    """
    Represents single/multiple pages of OCR results from an OCR engine.
    Currently supports doctr and tesseract outputs.
    """

    source_lib: str = ""
    source_path: Optional[Path] = None
    _pages: List[Page] = field(
        default_factory=list,
    )

    def __init__(
        self,
        source_lib: str,
        source_path: Path | str | None,
        pages: Collection ,
    ):
        self.source_lib = source_lib
        if isinstance(source_path, str):
            source_path = Path(source_path)
        self.source_path = source_path
        self.pages = pages

    def _sort_pages(self):
        self._pages.sort(key=lambda item: (item.page_index))

    @property
    def pages(self) -> list[Page]:
        """Returns a copy of the item list in this block"""
        self._sort_pages()
        return self._pages.copy()

    @pages.setter
    def pages(self, value):
        if not isinstance(value, Collection):
            raise TypeError("pages must be a collection")
        for page in value:
            if not hasattr(page, "page_index") or not isinstance(page.page_index, int):
                raise TypeError(
                    "Each item in pages must have a page_index attribute of type int"
                )
        self._pages = list(value)
        self._sort_pages()

    def scale(self, width: int, height: int) -> "Document":
        """Return new document with scaled bounding boxes to absolute pixel coordinates"""
        return Document(
            source_lib=self.source_lib,
            source_path=self.source_path,
            pages=[page.scale(width, height) for page in self.pages],
        )

    def to_dict(self) -> Dict:
        """Convert to a JSON-serializable dictionary"""
        return {
            "source_lib": self.source_lib,
            "source_path": str(self.source_path),
            "pages": [page.to_dict() for page in self.pages] if self.pages else [],
        }

    def to_json_file(self, file_path: Union[str, Path]) -> None:
        """Save OCR results to JSON file"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, dict) -> "Document":
        """Create Document from dictionary"""
        return cls(
            source_lib=dict["source_lib"],
            source_path=Path(dict["source_path"]),
            pages=[Page.from_dict(page) for page in dict["pages"]],
        )

    @classmethod
    def from_doctr_output(
        cls,
        doctr_output: Dict,
        source_path: Union[str, Path, None] = None,
    ) -> "Document":
        """Create Document from docTR output"""
        if isinstance(source_path, str):
            source_path = Path(source_path)

        result = cls(source_lib="doctr", source_path=source_path, pages=[])

        for page_idx, page_data in enumerate(doctr_output.get("pages", [])):
            height, width = page_data.get("dimensions", (0, 0))
            blocks = []
            for block_data in page_data.get("blocks", []):
                if block_data.get("geometry"):
                    block_bounding_box = BoundingBox.from_nested_float(
                        block_data["geometry"]
                    )
                else:
                    block_bounding_box = None

                lines = []
                for line_data in block_data.get("lines", []):
                    if line_data.get("geometry"):
                        line_bounding_box = BoundingBox.from_nested_float(
                            line_data["geometry"]
                        )
                    else:
                        line_bounding_box = None

                    words = []
                    for word_data in line_data.get("words", []):
                        word = Word(
                            text=word_data.get("value", ""),
                            bounding_box=BoundingBox.from_nested_float(
                                word_data["geometry"]
                            ),
                            ocr_confidence=word_data.get("confidence", 0.0),
                        )
                        words.append(word)

                    line = Block(
                        items=words,
                        bounding_box=line_bounding_box,
                        block_category=BlockCategory.LINE,
                        child_type=BlockChildType.WORDS,
                    )

                    lines.append(line)

                block = Block(
                    items=lines,
                    bounding_box=block_bounding_box,
                    block_category=BlockCategory.PARAGRAPH,
                    child_type=BlockChildType.BLOCKS,
                )
                blocks.append(block)

            page = Page(
                page_index=page_idx,
                width=width,
                height=height,
                items=blocks,
            )
            result._pages.append(page)

        result._sort_pages()

        return result

    @classmethod
    def from_json_file(cls, file_path: Union[str, Path]) -> Document:
        """Load OCR from JSON file"""
        d: dict
        with open(file_path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return cls.from_dict(d)

    @classmethod
    def safe_float(cls, val):
        if val is None:
            return 0.0
        if hasattr(val, "item"):
            val = val.item()
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def from_tesseract(
        cls,
        tesseract_output: DataFrame,
        source_path: Union[str, Path, None] = None,
    ) -> "Document":
        """Create Document from PyTesseract output (pandas dataframe)"""
        if isinstance(source_path, str):
            source_path = Path(source_path)

        result = cls(source_lib="tesseract", source_path=source_path, pages=[])

        tesseract_output["left"] = pd_to_numeric(tesseract_output["left"], errors="coerce")
        tesseract_output["top"] = pd_to_numeric(tesseract_output["top"], errors="coerce")
        tesseract_output["width"] = pd_to_numeric(tesseract_output["width"], errors="coerce")
        tesseract_output["height"] = pd_to_numeric(tesseract_output["height"], errors="coerce")

        page_filter = tesseract_output["level"] == 1.0
        page_filtered = tesseract_output.where(page_filter).dropna(how="all")
        for page_idx, page_row in enumerate(page_filtered.itertuples()):

            left, top, width, height = (
                cls.safe_float(page_row.left),
                cls.safe_float(page_row.top),
                cls.safe_float(page_row.width),
                cls.safe_float(page_row.height),
            )
            page_bounding_box = BoundingBox.from_ltwh(left, top, width, height)

            blocks = []
            block_filter = (tesseract_output["level"] == 2.0) & (
                tesseract_output["page_num"] == page_idx + 1
            )
            block_filtered = tesseract_output.where(block_filter).dropna(how="all")
            for block_idx, block_row in enumerate(block_filtered.itertuples()):
                left, top, width, height = (
                    cls.safe_float(block_row.left),
                    cls.safe_float(block_row.top),
                    cls.safe_float(block_row.width),
                    cls.safe_float(block_row.height),
                )
                block_bounding_box = BoundingBox.from_ltwh(left, top, width, height)

                paragraphs = []
                paragraph_filter = (
                    (tesseract_output["level"] == 3.0)
                    & (tesseract_output["page_num"] == page_idx + 1)
                    & (tesseract_output["block_num"] == block_idx + 1)
                )
                paragraph_filtered = tesseract_output.where(paragraph_filter).dropna(
                    how="all"
                )
                for paragraph_idx, paragraph_row in enumerate(
                    paragraph_filtered.itertuples()
                ):
                    left, top, width, height = (
                        cls.safe_float(paragraph_row.left),
                        cls.safe_float(paragraph_row.top),
                        cls.safe_float(paragraph_row.width),
                        cls.safe_float(paragraph_row.height),
                    )
                    paragraph_bounding_box = BoundingBox.from_ltwh(
                        left, top, width, height
                    )

                    lines = []
                    line_filter = (
                        (tesseract_output["level"] == 4.0)
                        & (tesseract_output["page_num"] == page_idx + 1)
                        & (tesseract_output["block_num"] == block_idx + 1)
                        & (tesseract_output["par_num"] == paragraph_idx + 1)
                    )
                    line_filtered = tesseract_output.where(line_filter).dropna(
                        how="all"
                    )
                    for line_idx, line_row in enumerate(line_filtered.itertuples()):
                        left, top, width, height = (
                            cls.safe_float(line_row.left),
                            cls.safe_float(line_row.top),
                            cls.safe_float(line_row.width),
                            cls.safe_float(line_row.height),
                        )
                        line_bounding_box = BoundingBox.from_ltwh(
                            left, top, width, height
                        )

                        words = []
                        word_filter = (
                            (tesseract_output["level"] == 5.0)
                            & (tesseract_output["page_num"] == page_idx + 1)
                            & (tesseract_output["block_num"] == block_idx + 1)
                            & (tesseract_output["par_num"] == paragraph_idx + 1)
                            & (tesseract_output["line_num"] == line_idx + 1)
                        )
                        word_filtered = tesseract_output.where(word_filter).dropna(
                            how="all"
                        )
                        for word_row in word_filtered.itertuples():
                            left, top, width, height = (
                                cls.safe_float(word_row.left),
                                cls.safe_float(word_row.top),
                                cls.safe_float(word_row.width),
                                cls.safe_float(word_row.height),
                            )
                            word_bounding_box = BoundingBox.from_ltwh(
                                left, top, width, height
                            )

                            word = Word(
                                text=str(word_row.text),
                                bounding_box=word_bounding_box,
                                ocr_confidence=cls.safe_float(word_row.conf),
                            )
                            words.append(word)

                        line = Block(
                            items=words,
                            bounding_box=line_bounding_box,
                            child_type=BlockChildType.WORDS,
                            block_category=BlockCategory.LINE,
                        )
                        lines.append(line)

                    paragraph = Block(
                        items=lines,
                        bounding_box=paragraph_bounding_box,
                        child_type=BlockChildType.BLOCKS,
                        block_category=BlockCategory.PARAGRAPH,
                    )
                    paragraphs.append(paragraph)

                block = Block(
                    items=paragraphs,
                    bounding_box=block_bounding_box,
                    child_type=BlockChildType.BLOCKS,
                    block_category=BlockCategory.BLOCK,
                )
                blocks.append(block)

            page = Page(
                page_index=page_idx,
                width=int(page_bounding_box.width),
                height=int(page_bounding_box.height),
                items=blocks,
                bounding_box=page_bounding_box,
            )
            result._pages.append(page)

        result._sort_pages()

        return result
