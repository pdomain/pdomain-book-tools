from __future__ import annotations

import json
from dataclasses import dataclass, field
from logging import getLogger
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Collection, Dict, List, Optional, Sequence, Union

from cv2 import COLOR_BGR2RGB, COLOR_GRAY2RGB, COLOR_RGB2BGR, cvtColor, imread
from numpy import array, ndarray

if TYPE_CHECKING:
    from pandas import DataFrame
    from PIL.Image import Image as PILImage

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.doctr_support import get_default_doctr_predictor
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
    source_identifier: str = ""
    source_path: Optional[Path] = None
    _pages: List[Page] = field(
        default_factory=list,
    )

    def __init__(
        self,
        source_lib: str,
        source_path: Path | str | None,
        pages: Collection,
        source_identifier: str = "",
    ):
        self.source_lib = source_lib
        if isinstance(source_path, str):
            source_path = Path(source_path)
        self.source_path = source_path
        self.pages = pages
        self.source_identifier = source_identifier

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
            "source_identifier": self.source_identifier,
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
            source_lib=dict.get("source_lib", ""),
            source_identifier=dict.get("source_identifier", ""),
            source_path=Path(dict.get("source_path"))
            if dict.get("source_path")
            else None,
            pages=[Page.from_dict(page) for page in dict.get("pages", [])],
        )

    @classmethod
    def from_image_ocr_via_doctr(
        cls,
        image: Union[str, PathLike, ndarray, PILImage],
        source_identifier: str = "",
        predictor=None,
    ) -> "Document":
        """
        Perform OCR on a single cv2 image using the doctr library.
        :param image: The input image as:
           - A file path (str or PathLike, will use cv2 to load the image)
           - numpy ndarray (usually from cv2, as BGR, RGB, or Grayscale)
           - PIL Image
        :param image_path_override: The source image path or identifier for the OCR results.
        :param predictor: The DocTR OCR predictor to use. If None, it will use the default pre-trained model.
        :return: Document containing the OCR results.
        """
        if predictor is None:
            predictor = get_default_doctr_predictor()

        has_PIL = False
        try:
            from PIL.Image import Image as PILImage

            has_PIL = True
        except ImportError:
            has_PIL = False
            PILImage = None

        source_path = None

        image_ndarray: ndarray

        # Handle different input types
        if isinstance(image, ndarray):
            # Already a numpy array (cv2 format)
            image_ndarray = image
        elif has_PIL and PILImage is not None and isinstance(image, PILImage):
            # Convert PIL Image to numpy array
            # PIL Images are typically in RGB format
            image_ndarray = array(image)
            # Convert from RGB to BGR for cv2 compatibility if it's a color image
            if len(image_ndarray.shape) == 3 and image_ndarray.shape[2] == 3:
                image_ndarray = cvtColor(image_ndarray, COLOR_RGB2BGR)
        else:
            # Handle path-like objects (str, Path, or any PathLike)
            try:
                image_ndarray = imread(str(image))
                source_path = Path(str(image))
                if image_ndarray is None:
                    raise ValueError(f"Could not load image from path: {image}")
            except Exception as e:
                raise ValueError(f"Failed to load image from path '{image}': {e}")

        # Convert to RGB format for doctr processing
        if len(image_ndarray.shape) == 2:
            # Grayscale image - convert to RGB
            image_rgb = cvtColor(image_ndarray, COLOR_GRAY2RGB)
        elif len(image_ndarray.shape) == 3 and image_ndarray.shape[2] == 3:
            # Color image (BGR) - convert to RGB
            image_rgb = cvtColor(image_ndarray, COLOR_BGR2RGB)
        elif len(image_ndarray.shape) == 3 and image_ndarray.shape[2] == 1:
            # Single channel image with shape (H, W, 1) - squeeze and convert to RGB
            image_gray = image_ndarray.squeeze()
            image_rgb = cvtColor(image_gray, COLOR_GRAY2RGB)
        else:
            # Already in RGB or unsupported format - use as is
            image_rgb = image_ndarray

        image_list = [image_rgb]

        doctr_result = predictor(image_list)
        ocr_doc: Document = cls.from_doctr_result(
            doctr_result=doctr_result,
            source_path=source_path,
            source_identifier=source_identifier,
        )

        # Always 1 page per OCR in this case
        ocr_page: Page = ocr_doc.pages[0]
        ocr_page.cv2_numpy_page_image = image_ndarray

        return ocr_doc

    @classmethod
    def from_doctr_result(
        cls,
        doctr_result,
        source_path: Union[str, Path, None] = None,
        source_identifier: str = "",
    ) -> "Document":
        """Create Document from docTR result object"""
        doctr_text = doctr_result.render()
        doctr_output: Dict = doctr_result.export()
        return cls.from_doctr_output(
            doctr_output=doctr_output,
            original_text=doctr_text,
            source_path=source_path,
            source_identifier=source_identifier,
        )

    @classmethod
    def from_doctr_output(
        cls,
        doctr_output: Dict,
        original_text: Optional[Sequence[str]] = None,
        source_path: Union[str, Path, None] = None,
        source_identifier: str = "",
    ) -> "Document":
        """Create Document from docTR dictionary"""
        if isinstance(source_path, str):
            source_path = Path(source_path)

        result = cls(
            source_lib="doctr",
            source_path=source_path,
            source_identifier=source_identifier,
            pages=[],
        )

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

            original_ocr_tool_text = None
            if original_text is not None and page_idx < len(original_text):
                original_ocr_tool_text = original_text[page_idx]

            page = Page(
                page_index=page_idx,
                width=width,
                height=height,
                items=blocks,
                original_ocr_tool_text=original_ocr_tool_text,
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
        tesseract_output: "DataFrame",
        tesseract_string: Optional[str] = None,
        source_path: Union[str, Path, None] = None,
    ) -> "Document":
        try:
            from pandas import to_numeric as pd_to_numeric
        except ImportError:
            raise ImportError(
                "pandas library is required for from_tesseract function. Please install pandas."
            )

        """Create Document from PyTesseract output (pandas dataframe)"""
        if isinstance(source_path, str):
            source_path = Path(source_path)

        result = cls(source_lib="tesseract", source_path=source_path, pages=[])

        tesseract_output["left"] = pd_to_numeric(
            tesseract_output["left"], errors="coerce"
        )
        tesseract_output["top"] = pd_to_numeric(
            tesseract_output["top"], errors="coerce"
        )
        tesseract_output["width"] = pd_to_numeric(
            tesseract_output["width"], errors="coerce"
        )
        tesseract_output["height"] = pd_to_numeric(
            tesseract_output["height"], errors="coerce"
        )

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

        if tesseract_string is not None:
            # If a string is provided, we can add it to the first page
            if result.pages:
                result.pages[0].original_ocr_tool_text = tesseract_string

        return result
