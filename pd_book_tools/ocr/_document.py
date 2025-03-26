import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Collection, Dict, Optional, Union

from pandas import DataFrame
from sortedcontainers import SortedList

from ..geometry import BoundingBox
from ._block import Block, BlockChildType, BlockCategory
from ._page import Page
from ._word import Word


@dataclass
class Document:
    """
    Represents single/multiple pages of OCR results from an OCR engine.
    Currently supports doctr and tesseract outputs.
    """

    source_lib: str = ""
    source_path: Optional[Path] = None
    _pages: SortedList[Page] = field(
        default_factory=lambda: SortedList(key=lambda page: page.page_index)
    )

    def __init__(
        self,
        source_lib: str,
        source_path: Path,
        pages: Collection,
    ):
        self.source_lib = source_lib
        self.source_path = source_path
        self.pages = pages

    @property
    def pages(self) -> SortedList:
        return self._pages

    @pages.setter
    def pages(self, value):
        if isinstance(value, SortedList):
            self._pages = value
            return
        if not isinstance(value, Collection):
            raise TypeError("pages must be a collection")
        for page in value:
            if not hasattr(page, "page_index") or not isinstance(page.page_index, int):
                raise TypeError(
                    "Each item in pages must have a page_index attribute of type int"
                )
        self._pages = SortedList(value, key=lambda page: page.page_index)

    def to_dict(self) -> Dict:
        """Convert to a JSON-serializable dictionary"""
        return {
            "source_lib": self.source_lib,
            "source_path": str(self.source_path),
            "pages": [page.to_dict() for page in self.pages] if self.pages else [],
        }

    def from_dict(dict) -> "Document":
        """Create OCRDocument from dictionary"""
        return Document(
            source_lib=dict["source_lib"],
            source_path=Path(dict["source_path"]),
            pages=SortedList(
                [Page.from_dict(page) for page in dict["pages"]],
                key=lambda page: page.page_index,
            ),
        )

    def save_json(self, file_path: Union[str, Path]) -> None:
        """Save OCR results to JSON file"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def from_doctr_output(
        cls,
        doctr_output: Dict,
        source_path: Union[str, Path],
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

                lines = []
                for line_data in block_data.get("lines", []):
                    if line_data.get("geometry"):
                        line_bounding_box = BoundingBox.from_nested_float(
                            line_data["geometry"]
                        )

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
                    block_category=BlockCategory.BLOCK,
                    child_type=BlockChildType.BLOCKS,
                )
                blocks.append(block)

            page = Page(
                page_index=page_idx,
                width=width,
                height=height,
                items=blocks,
            )
            result.pages.add(page)

        return result

    @classmethod
    def from_tesseract(
        cls,
        tesseract_output: DataFrame,
        source_path: Union[str, Path],
    ) -> "Document":
        """Create Document from PyTesseract output (pandas dataframe)"""
        if isinstance(source_path, str):
            source_path = Path(source_path)

        result = cls(source_lib="tesseract", source_path=source_path, pages=[])

        page_filter = tesseract_output["level"] == 1.0
        page_filtered = tesseract_output.where(page_filter).dropna(how="all")
        for page_idx, page_row in enumerate(page_filtered.itertuples()):
            left, top, width, height = (
                page_row.left,
                page_row.top,
                page_row.width,
                page_row.height,
            )
            page_bounding_box = BoundingBox.from_ltwh(left, top, width, height)

            blocks = []
            block_filter = (tesseract_output["level"] == 2.0) & (
                tesseract_output["page_num"] == page_idx + 1
            )
            block_filtered = tesseract_output.where(block_filter).dropna(how="all")
            for block_idx, block_row in enumerate(block_filtered.itertuples()):
                left, top, width, height = (
                    block_row.left,
                    block_row.top,
                    block_row.width,
                    block_row.height,
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
                        paragraph_row.left,
                        paragraph_row.top,
                        paragraph_row.width,
                        paragraph_row.height,
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
                            line_row.left,
                            line_row.top,
                            line_row.width,
                            line_row.height,
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
                                word_row.left,
                                word_row.top,
                                word_row.width,
                                word_row.height,
                            )
                            word_bounding_box = BoundingBox.from_ltwh(
                                left, top, width, height
                            )

                            word = Word(
                                text=word_row.text,
                                bounding_box=word_bounding_box,
                                ocr_confidence=word_row.conf,
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
                width=page_bounding_box.width,
                height=page_bounding_box.height,
                items=blocks,
                bounding_box=page_bounding_box,
            )
            result.pages.add(page)
        return result
