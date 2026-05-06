from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from logging import getLogger
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Any, Collection, Dict, List, Optional, Sequence, Union

from cv2 import COLOR_BGR2RGB, COLOR_GRAY2RGB, COLOR_RGB2BGR, cvtColor, imread
from numpy import array, ndarray

if TYPE_CHECKING:
    from pandas import DataFrame
    from PIL.Image import Image as PILImage

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.doctr_support import get_default_doctr_predictor
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.provenance import OCRModelProvenance, OCRProvenance
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
        self._pages.sort(key=lambda item: item.page_index)

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
            "source_path": str(self.source_path)
            if self.source_path is not None
            else None,
            "pages": [page.to_dict() for page in self.pages] if self.pages else [],
        }

    def to_json_file(self, file_path: Union[str, Path]) -> None:
        """Save OCR results to JSON file"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data) -> "Document":
        """Create Document from dictionary"""
        return cls(
            source_lib=data.get("source_lib", ""),
            source_identifier=data.get("source_identifier", ""),
            source_path=Path(data.get("source_path"))
            if data.get("source_path") and data.get("source_path") != "None"
            else None,
            pages=[Page.from_dict(page) for page in data.get("pages", [])],
        )

    @classmethod
    def from_image_ocr_via_doctr(
        cls,
        image: Union[str, PathLike, ndarray, PILImage],
        source_identifier: str = "",
        predictor=None,
        *,
        auto_rotate: bool = True,
        auto_rotate_threshold: float | None = None,
    ) -> "Document":
        """
        Perform OCR on a single cv2 image using the doctr library.
        :param image: The input image as:
           - A file path (str or PathLike, will use cv2 to load the image)
           - numpy ndarray (usually from cv2, as BGR, RGB, or Grayscale)
           - PIL Image
        :param source_identifier: The source image path or identifier for the OCR results.
        :param predictor: The DocTR OCR predictor to use. If None, it will use the default pre-trained model.
        :param auto_rotate: If True (default), run OCR upright first; if mean
           per-word confidence is below ``auto_rotate_threshold``, also try
           90°/180°/270° and pick whichever produces the highest mean
           confidence. The chosen rotation is recorded on
           ``page.rotation_applied``. Set to False to skip the fallback
           probes and always OCR the image as-is.
        :param auto_rotate_threshold: Mean per-word confidence at which the
           upright pass is considered good enough; ignored when
           ``auto_rotate`` is False. Defaults to
           :data:`pd_book_tools.ocr.rotation.DEFAULT_CONFIDENCE_THRESHOLD`.
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

        def _ocr_one(rgb: ndarray) -> "Document":
            doctr_result = predictor([rgb])
            return cls.from_doctr_result(
                doctr_result=doctr_result,
                source_path=source_path,
                source_identifier=source_identifier,
            )

        if auto_rotate:
            # Lazy import: avoid the small overhead when callers opt out.
            from pd_book_tools.ocr.rotation import (  # noqa: PLC0415
                DEFAULT_CONFIDENCE_THRESHOLD,
                detect_best_rotation,
                rotate_image,
            )

            threshold = (
                DEFAULT_CONFIDENCE_THRESHOLD
                if auto_rotate_threshold is None
                else auto_rotate_threshold
            )
            chosen, ocr_doc, _probes = detect_best_rotation(
                image_rgb,
                ocr_fn=_ocr_one,
                confidence_threshold=threshold,
            )
            # Stash the rotated source image on the page so downstream
            # consumers (layout detector, reorganize_page, labeler UI) all
            # see pixels in the same frame OCR did.
            rotated_source = rotate_image(image_ndarray, chosen)
            ocr_page: Page = ocr_doc.pages[0]
            ocr_page.cv2_numpy_page_image = rotated_source
            ocr_page.rotation_applied = chosen
        else:
            ocr_doc = _ocr_one(image_rgb)
            ocr_page = ocr_doc.pages[0]
            ocr_page.cv2_numpy_page_image = image_ndarray
            # rotation_applied stays at its default 0

        return ocr_doc

    @classmethod
    def from_doctr_result(
        cls,
        doctr_result,
        source_path: Union[str, Path, None] = None,
        source_identifier: str = "",
    ) -> "Document":
        """Create Document from docTR result object"""
        # NOTE (H-12): ``doctr_result.render()`` returns a single ``str`` for
        # the whole document. ``from_doctr_output`` indexes ``original_text``
        # with ``original_text[page_idx]`` to get per-page text — and since
        # ``str`` is a ``Sequence[str]`` in Python, passing the whole-document
        # string would silently yield a single character per page. Split into
        # one rendered string per page instead.
        doctr_output: Dict = doctr_result.export()
        per_page_text: list[str] = [page.render() for page in doctr_result.pages]
        return cls.from_doctr_output(
            doctr_output=doctr_output,
            original_text=per_page_text,
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

        metadata = doctr_output.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        ocr_provenance = cls._build_ocr_provenance(engine="doctr", metadata=metadata)

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
                        # M-16: guard ``geometry`` access to mirror the
                        # block / line / artefact branches above. DocTR
                        # is not formally guaranteed to emit geometry on
                        # every word in every release, and a partial
                        # word should not raise ``KeyError`` and tear
                        # down the whole page — emit ``bounding_box=None``
                        # so the word still flows through (project
                        # invariant: never silently drop OCR content).
                        if word_data.get("geometry"):
                            word_bounding_box = BoundingBox.from_nested_float(
                                word_data["geometry"]
                            )
                        else:
                            word_bounding_box = None
                        word = Word(
                            text=word_data.get("value", ""),
                            bounding_box=word_bounding_box,
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

                # M-14: DocTR's data model is `pages -> blocks -> lines ->
                # words` (no paragraph layer). Tesseract produces
                # `Page -> BLOCK -> PARAGRAPH -> LINE -> Word`. To give
                # consumers a single canonical nesting depth across
                # adapters, wrap DocTR's per-block grouping as
                # `Block(BLOCK) -> Block(PARAGRAPH) -> Block(LINE) -> Word`.
                # The synthetic PARAGRAPH carries the same geometry as its
                # parent BLOCK because DocTR provides only one grouping
                # level — there is exactly one paragraph per block.
                paragraph = Block(
                    items=lines,
                    bounding_box=block_bounding_box,
                    block_category=BlockCategory.PARAGRAPH,
                    child_type=BlockChildType.BLOCKS,
                )
                block = Block(
                    items=[paragraph],
                    bounding_box=block_bounding_box,
                    block_category=BlockCategory.BLOCK,
                    child_type=BlockChildType.BLOCKS,
                )
                blocks.append(block)

                # M-15: DocTR's block export carries both ``"lines"`` (text)
                # and ``"artefacts"`` (non-text regions: stamps, barcodes,
                # QR codes, figures, unclassified blobs). The adapter
                # previously iterated only ``"lines"``, silently discarding
                # every artefact. pd-book-tools' invariant is to never
                # silently drop OCR-derived content, so preserve each
                # artefact as a sibling top-level Block on the page,
                # role-labelled ``"artefact"`` and carrying DocTR's
                # ``type`` / ``confidence`` in additional_block_attributes.
                # ``items`` is empty (artefacts are non-text), so
                # ``page.words`` is unaffected; consumers can filter on the
                # role label to keep, render, or strip them.
                for artefact_data in block_data.get("artefacts", []):
                    if artefact_data.get("geometry"):
                        artefact_bounding_box = BoundingBox.from_nested_float(
                            artefact_data["geometry"]
                        )
                    else:
                        artefact_bounding_box = None
                    artefact_attrs: dict = {}
                    if "type" in artefact_data:
                        artefact_attrs["artefact_type"] = artefact_data["type"]
                    if "confidence" in artefact_data:
                        artefact_attrs["artefact_confidence"] = artefact_data[
                            "confidence"
                        ]
                    artefact_block = Block(
                        items=[],
                        bounding_box=artefact_bounding_box,
                        block_category=BlockCategory.BLOCK,
                        child_type=BlockChildType.WORDS,
                        block_role_labels=["artefact"],
                        additional_block_attributes=artefact_attrs or None,
                    )
                    blocks.append(artefact_block)

            original_ocr_tool_text = None
            if original_text is not None and page_idx < len(original_text):
                original_ocr_tool_text = original_text[page_idx]

            page = Page(
                page_index=page_idx,
                width=width,
                height=height,
                items=blocks,
                original_ocr_tool_text=original_ocr_tool_text,
                ocr_provenance=deepcopy(ocr_provenance),
            )
            result._pages.append(page)

        result._sort_pages()

        return result

    @classmethod
    def _build_ocr_provenance(
        cls, engine: str, metadata: Dict[str, Any]
    ) -> OCRProvenance:
        models = cls._normalize_ocr_models(metadata.get("models"))

        config_fingerprint: str | None = None

        explicit_fingerprint = metadata.get("config_fingerprint")
        if explicit_fingerprint is not None:
            config_fingerprint = str(explicit_fingerprint)
        else:
            source_lib = metadata.get("source_lib")
            model_names = sorted(model.name for model in models if model.name)
            parts: list[str] = []
            if isinstance(source_lib, str) and source_lib:
                parts.append(source_lib)
            parts.extend(model_names)
            if parts:
                config_fingerprint = "|".join(parts)

        return OCRProvenance(
            engine=engine,
            models=models,
            engine_version=str(metadata.get("engine_version", "unknown")),
            config_fingerprint=config_fingerprint,
        )

    @classmethod
    def _normalize_ocr_models(cls, raw_models: Any) -> list[OCRModelProvenance]:
        if not isinstance(raw_models, list):
            return []

        normalized: list[OCRModelProvenance] = []
        for raw_model in raw_models:
            if isinstance(raw_model, str) and raw_model:
                normalized.append(OCRModelProvenance(name=raw_model))
                continue

            if isinstance(raw_model, dict):
                name = raw_model.get("name") or raw_model.get("model")
                if not isinstance(name, str) or not name:
                    continue

                version_value: str | None = None
                version = raw_model.get("version")
                if isinstance(version, (str, int, float)):
                    version_value = str(version)

                weights_id_value: str | None = None
                weights_id = raw_model.get("weights_id")
                if isinstance(weights_id, (str, int, float)):
                    weights_id_value = str(weights_id)

                normalized.append(
                    OCRModelProvenance(
                        name=name,
                        version=version_value,
                        weights_id=weights_id_value,
                    )
                )

        return normalized

    @classmethod
    def _safe_package_version(cls, package_name: str) -> str:
        try:
            return package_version(package_name)
        except PackageNotFoundError:
            return "unknown"
        except Exception:
            return "unknown"

    @classmethod
    def _detect_tesseract_engine_version(cls) -> str:
        try:
            import pytesseract

            detected = pytesseract.get_tesseract_version()
            if detected:
                return str(detected)
        except Exception:
            pass
        return "unknown"

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
    def _tesseract_text(cls, val) -> str:
        """Coerce a Tesseract ``text`` cell to a clean ``str``.

        Tesseract's pandas DataFrame uses ``NaN`` for the ``text`` cell on
        rejected/empty rows. ``str(float('nan'))`` is the literal string
        ``'nan'``, so a naive ``str(word_row.text)`` ingest creates a ghost
        Word with text ``'nan'`` that propagates as real OCR output into
        ground-truth matching and final text. Map NaN / ``None`` to the
        empty string instead of coercing them; everything else is passed
        through ``str``.

        We deliberately do not drop the row — keeping the geometry preserves
        the no-silent-word-drop invariant the reorganize pipeline relies on.
        """
        if val is None:
            return ""
        if hasattr(val, "item"):
            try:
                val = val.item()
            except Exception:
                pass
        if isinstance(val, float) and val != val:  # NaN
            return ""
        return str(val)

    @classmethod
    def _tesseract_confidence(cls, val) -> Optional[float]:
        """Convert a Tesseract ``conf`` cell to ``Optional[float]``.

        Tesseract uses ``conf = -1`` (and emits empty/rejected rows) to mean
        "no confidence available" rather than "very low confidence". Storing
        that sentinel as ``-1.0`` corrupts every downstream confidence
        consumer: rotation detection's per-page mean drops below the
        ``0.6`` threshold and triggers spurious 90/180/270 probes on clean
        pages, ``Block.mean_ocr_confidence`` is dragged toward ``-1``, and
        confidence-based filters keep junk while rejecting good words.

        Treat ``conf <= 0`` and any non-numeric value as ``None`` so the
        sentinel is excluded from aggregation rather than averaged in.
        """
        if val is None:
            return None
        if hasattr(val, "item"):
            val = val.item()
        try:
            f = float(val)
        except (TypeError, ValueError):
            return None
        if f != f:  # NaN
            return None
        if f <= 0:
            return None
        return f

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

        pytesseract_version = cls._safe_package_version("pytesseract")
        tesseract_metadata: Dict[str, Any] = {
            "source_lib": "tesseract",
            "engine_version": cls._detect_tesseract_engine_version(),
            "models": [],
        }
        if pytesseract_version != "unknown":
            tesseract_metadata["config_fingerprint"] = (
                f"tesseract|pytesseract:{pytesseract_version}"
            )

        ocr_provenance = cls._build_ocr_provenance(
            engine="tesseract", metadata=tesseract_metadata
        )

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
            # H-18: Tesseract's block_num / par_num / line_num are NOT
            # guaranteed to be a contiguous 1..N sequence — Tesseract may
            # skip numbers when intermediate regions are empty or dropped.
            # Use the actual values from the DataFrame row (block_row.block_num
            # etc.) rather than the positional ``enumerate`` index, otherwise
            # child rows are filtered against the wrong parent and entire
            # branches of the hierarchy silently disappear.
            for block_row in block_filtered.itertuples():
                left, top, width, height = (
                    cls.safe_float(block_row.left),
                    cls.safe_float(block_row.top),
                    cls.safe_float(block_row.width),
                    cls.safe_float(block_row.height),
                )
                block_bounding_box = BoundingBox.from_ltwh(left, top, width, height)
                block_num_value = block_row.block_num

                paragraphs = []
                paragraph_filter = (
                    (tesseract_output["level"] == 3.0)
                    & (tesseract_output["page_num"] == page_idx + 1)
                    & (tesseract_output["block_num"] == block_num_value)
                )
                paragraph_filtered = tesseract_output.where(paragraph_filter).dropna(
                    how="all"
                )
                for paragraph_row in paragraph_filtered.itertuples():
                    left, top, width, height = (
                        cls.safe_float(paragraph_row.left),
                        cls.safe_float(paragraph_row.top),
                        cls.safe_float(paragraph_row.width),
                        cls.safe_float(paragraph_row.height),
                    )
                    paragraph_bounding_box = BoundingBox.from_ltwh(
                        left, top, width, height
                    )
                    par_num_value = paragraph_row.par_num

                    lines = []
                    line_filter = (
                        (tesseract_output["level"] == 4.0)
                        & (tesseract_output["page_num"] == page_idx + 1)
                        & (tesseract_output["block_num"] == block_num_value)
                        & (tesseract_output["par_num"] == par_num_value)
                    )
                    line_filtered = tesseract_output.where(line_filter).dropna(
                        how="all"
                    )
                    for line_row in line_filtered.itertuples():
                        left, top, width, height = (
                            cls.safe_float(line_row.left),
                            cls.safe_float(line_row.top),
                            cls.safe_float(line_row.width),
                            cls.safe_float(line_row.height),
                        )
                        line_bounding_box = BoundingBox.from_ltwh(
                            left, top, width, height
                        )
                        line_num_value = line_row.line_num

                        words = []
                        word_filter = (
                            (tesseract_output["level"] == 5.0)
                            & (tesseract_output["page_num"] == page_idx + 1)
                            & (tesseract_output["block_num"] == block_num_value)
                            & (tesseract_output["par_num"] == par_num_value)
                            & (tesseract_output["line_num"] == line_num_value)
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
                                text=cls._tesseract_text(word_row.text),
                                bounding_box=word_bounding_box,
                                ocr_confidence=cls._tesseract_confidence(word_row.conf),
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
                ocr_provenance=deepcopy(ocr_provenance),
            )
            result._pages.append(page)

        result._sort_pages()

        if tesseract_string is not None:
            # If a string is provided, we can add it to the first page
            if result.pages:
                result.pages[0].original_ocr_tool_text = tesseract_string

        return result
