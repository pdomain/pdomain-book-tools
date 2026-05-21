from __future__ import annotations

import json
import math
from collections.abc import Collection, Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from cv2 import COLOR_BGR2RGB, COLOR_GRAY2RGB, COLOR_RGB2BGR, cvtColor, imread
from numpy import array, ndarray

if TYPE_CHECKING:
    from os import PathLike

    from pandas import DataFrame
    from PIL.Image import Image as PILImage

import contextlib

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
    source_path: Path | None = None
    _pages: list[Page] = field(
        default_factory=list,
    )

    def __init__(
        self,
        source_lib: str,
        source_path: Path | str | None,
        pages: Collection[Page],
        source_identifier: str = "",
    ) -> None:
        self.source_lib = source_lib
        if isinstance(source_path, str):
            source_path = Path(source_path)
        self.source_path = source_path
        self.pages = pages
        self.source_identifier = source_identifier

    def _sort_pages(self) -> None:
        self._pages.sort(key=lambda item: item.page_index)

    @property
    def pages(self) -> list[Page]:
        """Returns a copy of the item list in this block."""
        self._sort_pages()
        return self._pages.copy()

    @pages.setter
    def pages(self, value: Collection[Page]) -> None:
        if not isinstance(value, Collection):
            raise TypeError("pages must be a collection")
        for page in value:
            if not hasattr(page, "page_index") or not isinstance(page.page_index, int):
                raise TypeError(
                    "Each item in pages must have a page_index attribute of type int"
                )
        self._pages = list(value)  # pyright: ignore[reportAttributeAccessIssue]  # dataclass field; setter assigns outside __init__
        self._sort_pages()

    def scale(self, width: int, height: int) -> Document:
        """Return new document with scaled bounding boxes to absolute pixel coordinates."""
        return Document(
            source_lib=self.source_lib,
            source_path=self.source_path,
            pages=[page.scale(width, height) for page in self.pages],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a JSON-serializable dictionary."""
        return {
            "source_lib": self.source_lib,
            "source_identifier": self.source_identifier,
            "source_path": str(self.source_path)
            if self.source_path is not None
            else None,
            "pages": [page.to_dict() for page in self.pages] if self.pages else [],
        }

    def to_json_file(self, file_path: str | Path) -> None:
        """Save OCR results to JSON file."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data) -> Document:
        """Create Document from dictionary."""
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
        image: str | PathLike[str] | ndarray | PILImage,
        source_identifier: str = "",
        predictor=None,
        *,
        auto_rotate: bool = True,
        auto_rotate_threshold: float | None = None,
    ) -> Document:
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
                _loaded = imread(str(image))
                source_path = Path(str(image))
                if _loaded is None:
                    raise ValueError(f"Could not load image from path: {image}")
                image_ndarray = _loaded
            except Exception as e:
                raise ValueError(
                    f"Failed to load image from path '{image}': {e}"
                ) from e

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

        def _ocr_one(rgb: ndarray) -> Document:
            doctr_result = predictor([rgb])
            return cls.from_doctr_result(
                doctr_result=doctr_result,
                source_path=source_path,
                source_identifier=source_identifier,
            )

        if auto_rotate:
            # Lazy import: avoid the small overhead when callers opt out.
            from pd_book_tools.ocr.rotation import (
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
        source_path: str | Path | None = None,
        source_identifier: str = "",
    ) -> Document:
        """Create Document from docTR result object."""
        # NOTE (H-12): ``doctr_result.render()`` returns a single ``str`` for
        # the whole document. ``from_doctr_output`` indexes ``original_text``
        # with ``original_text[page_idx]`` to get per-page text — and since
        # ``str`` is a ``Sequence[str]`` in Python, passing the whole-document
        # string would silently yield a single character per page. Split into
        # one rendered string per page instead.
        doctr_output: dict[str, Any] = doctr_result.export()
        per_page_text: list[str] = [page.render() for page in doctr_result.pages]
        return cls.from_doctr_output(
            doctr_output=doctr_output,
            original_text=per_page_text,
            source_path=source_path,
            source_identifier=source_identifier,
        )

    @staticmethod
    def _doctr_bbox(geometry: Any) -> BoundingBox | None:
        """Return a ``BoundingBox`` from a DocTR geometry tuple, or ``None``.

        DocTR emits geometry as a nested float tuple; absent/falsy geometry
        means "not provided" (M-16), and the caller must preserve the
        record without raising — pd-book-tools' invariant is to never
        silently drop OCR-derived content.
        """
        if not geometry:
            return None
        return BoundingBox.from_nested_float(geometry)

    @classmethod
    def _word_from_doctr(cls, word_data: dict[str, Any]) -> Word:
        """Build a ``Word`` from a DocTR word dict.

        Geometry is guarded (M-16) and ``confidence`` is forwarded as-is so
        a missing key remains ``None`` ("unknown") rather than ``0.0``
        ("certain error") — see L-19.
        """
        return Word(
            text=word_data.get("value", ""),
            bounding_box=cast(
                "BoundingBox", cls._doctr_bbox(word_data.get("geometry"))
            ),  # pyright: ignore[reportArgumentType]  # DocTR may return None bbox; Word checks it defensively
            ocr_confidence=word_data.get("confidence"),
        )

    @classmethod
    def _line_from_doctr(cls, line_data: dict[str, Any]) -> Block:
        """Build a ``Block(LINE)`` of ``Word`` children from a DocTR line dict."""
        words = [cls._word_from_doctr(w) for w in line_data.get("words", [])]
        return Block(
            items=words,
            bounding_box=cls._doctr_bbox(line_data.get("geometry")),
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )

    @classmethod
    def _artefact_from_doctr(cls, artefact_data: dict[str, Any]) -> Block:
        """Build a role-labelled artefact ``Block`` from a DocTR artefact dict.

        DocTR's block export carries non-text regions (stamps, barcodes, QR
        codes, figures, unclassified blobs) under ``"artefacts"`` alongside
        ``"lines"``. They have no words but we preserve them as sibling
        page-level Blocks tagged ``role="artefact"`` (M-15) so consumers
        can keep, render, or strip them on intent.
        """
        attrs: dict[str, Any] = {}
        if "type" in artefact_data:
            attrs["artefact_type"] = artefact_data["type"]
        if "confidence" in artefact_data:
            attrs["artefact_confidence"] = artefact_data["confidence"]
        return Block(
            items=[],
            bounding_box=cls._doctr_bbox(artefact_data.get("geometry")),
            block_category=BlockCategory.BLOCK,
            child_type=BlockChildType.WORDS,
            block_role_labels=["artefact"],
            additional_block_attributes=attrs or None,
        )

    @classmethod
    def _block_from_doctr(cls, block_data: dict[str, Any]) -> list[Block]:
        """Expand a DocTR block dict into one canonical Block plus artefact siblings.

        DocTR's data model is ``pages -> blocks -> lines -> words`` (no
        paragraph layer). Tesseract produces ``Page -> BLOCK -> PARAGRAPH
        -> LINE -> Word``. To give consumers a single canonical nesting
        depth across adapters, this wraps DocTR's per-block grouping as
        ``Block(BLOCK) -> Block(PARAGRAPH) -> Block(LINE) -> Word`` (M-14).
        Artefacts are returned as sibling page-level blocks (M-15).
        """
        block_bbox = cls._doctr_bbox(block_data.get("geometry"))
        lines = [cls._line_from_doctr(ln) for ln in block_data.get("lines", [])]
        # The synthetic PARAGRAPH carries the same geometry as its parent
        # BLOCK because DocTR provides only one grouping level — there is
        # exactly one paragraph per block.
        paragraph = Block(
            items=lines,
            bounding_box=block_bbox,
            block_category=BlockCategory.PARAGRAPH,
            child_type=BlockChildType.BLOCKS,
        )
        canonical_block = Block(
            items=[paragraph],
            bounding_box=block_bbox,
            block_category=BlockCategory.BLOCK,
            child_type=BlockChildType.BLOCKS,
        )
        result: list[Block] = [
            canonical_block,
            *[cls._artefact_from_doctr(a) for a in block_data.get("artefacts", [])],
        ]
        return result

    @classmethod
    def _page_from_doctr(
        cls,
        page_data: dict[str, Any],
        page_idx: int,
        ocr_provenance: OCRProvenance,
        original_text: Sequence[str] | None,
    ) -> Page:
        """Build a single ``Page`` from a DocTR page dict."""
        height, width = page_data.get("dimensions", (0, 0))
        blocks: list[Block] = []
        for block_data in page_data.get("blocks", []):
            blocks.extend(cls._block_from_doctr(block_data))

        original_ocr_tool_text = None
        if original_text is not None and page_idx < len(original_text):
            original_ocr_tool_text = original_text[page_idx]

        return Page(
            page_index=page_idx,
            width=width,
            height=height,
            blocks=blocks,
            original_ocr_tool_text=original_ocr_tool_text,
            ocr_provenance=deepcopy(ocr_provenance),
        )

    @classmethod
    def from_doctr_output(
        cls,
        doctr_output: dict[str, Any],
        original_text: Sequence[str] | None = None,
        source_path: str | Path | None = None,
        source_identifier: str = "",
    ) -> Document:
        """Create Document from docTR dictionary."""
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
            result._pages.append(
                cls._page_from_doctr(
                    page_data=page_data,
                    page_idx=page_idx,
                    ocr_provenance=ocr_provenance,
                    original_text=original_text,
                )
            )

        result._sort_pages()

        return result

    @classmethod
    def _build_ocr_provenance(
        cls, engine: str, metadata: dict[str, Any]
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
            models=tuple(models),
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
        except Exception:  # pytesseract version detection may fail for various reasons
            logger.debug("Could not detect tesseract version", exc_info=True)
        return "unknown"

    @classmethod
    def from_json_file(cls, file_path: str | Path) -> Document:
        """Load OCR from JSON file."""
        d: dict[str, Any]
        with open(file_path, encoding="utf-8") as f:
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
            with contextlib.suppress(Exception):
                val = val.item()
        if isinstance(val, float) and math.isnan(val):
            return ""
        return str(val)

    @classmethod
    def _tesseract_confidence(cls, val) -> float | None:
        """Convert a Tesseract ``conf`` cell to ``float | None``.

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
        if math.isnan(f):
            return None
        if f <= 0:
            return None
        return f

    @classmethod
    def _tesseract_filter_level(
        cls, df: DataFrame, *, level: float, **eq: Any
    ) -> DataFrame:
        """Return DataFrame rows matching ``level`` and any extra equality filters.

        Tesseract emits a flat row-per-region DataFrame keyed by
        ``level`` (1=page, 2=block, 3=paragraph, 4=line, 5=word) plus
        ``page_num`` / ``block_num`` / ``par_num`` / ``line_num``. This
        helper keeps the per-level adapter functions free of boolean-mask
        gymnastics and mirrors the ``where(...).dropna(how="all")``
        pattern used previously.
        """
        mask = df["level"] == level
        for col, value in eq.items():
            mask = mask & (df[col] == value)
        return df.where(mask).dropna(how="all")

    @classmethod
    def _tesseract_bbox(cls, row: Any) -> BoundingBox:
        """Build a ``BoundingBox`` from a Tesseract row's L/T/W/H columns."""
        return BoundingBox.from_ltwh(
            cls.safe_float(row.left),
            cls.safe_float(row.top),
            cls.safe_float(row.width),
            cls.safe_float(row.height),
        )

    @classmethod
    def _word_from_tesseract(cls, word_row: Any) -> Word:
        """Build a ``Word`` from a Tesseract level-5 row.

        ``_tesseract_text`` and ``_tesseract_confidence`` handle the NaN /
        ``conf=-1`` sentinels Tesseract uses for rejected rows so the
        word survives without poisoning downstream confidence aggregates.
        """
        return Word(
            text=cls._tesseract_text(word_row.text),
            bounding_box=cls._tesseract_bbox(word_row),
            ocr_confidence=cls._tesseract_confidence(word_row.conf),
        )

    @classmethod
    def _line_from_tesseract(
        cls,
        line_row: Any,
        df: DataFrame,
        page_num: int,
        block_num: Any,
        par_num: Any,
    ) -> Block:
        """Build a ``Block(LINE)`` of ``Word`` children from a Tesseract level-4 row.

        ``page_num`` / ``block_num`` / ``par_num`` are forwarded for the
        level-5 word filter — H-18: Tesseract numbers can be
        non-contiguous, so we must use the row's actual ids, not a
        positional enumerate index, or whole hierarchy branches vanish.
        """
        word_rows = cls._tesseract_filter_level(
            df,
            level=5.0,
            page_num=page_num,
            block_num=block_num,
            par_num=par_num,
            line_num=line_row.line_num,
        )
        words = [cls._word_from_tesseract(w) for w in word_rows.itertuples()]
        return Block(
            items=words,
            bounding_box=cls._tesseract_bbox(line_row),
            child_type=BlockChildType.WORDS,
            block_category=BlockCategory.LINE,
        )

    @classmethod
    def _paragraph_from_tesseract(
        cls,
        paragraph_row: Any,
        df: DataFrame,
        page_num: int,
        block_num: Any,
    ) -> Block:
        """Build a ``Block(PARAGRAPH)`` of ``Block(LINE)`` children."""
        line_rows = cls._tesseract_filter_level(
            df,
            level=4.0,
            page_num=page_num,
            block_num=block_num,
            par_num=paragraph_row.par_num,
        )
        lines = [
            cls._line_from_tesseract(
                line_row=line_row,
                df=df,
                page_num=page_num,
                block_num=block_num,
                par_num=paragraph_row.par_num,
            )
            for line_row in line_rows.itertuples()
        ]
        return Block(
            items=lines,
            bounding_box=cls._tesseract_bbox(paragraph_row),
            child_type=BlockChildType.BLOCKS,
            block_category=BlockCategory.PARAGRAPH,
        )

    @classmethod
    def _block_from_tesseract(
        cls,
        block_row: Any,
        df: DataFrame,
        page_num: int,
    ) -> Block:
        """Build a ``Block(BLOCK)`` of ``Block(PARAGRAPH)`` children."""
        paragraph_rows = cls._tesseract_filter_level(
            df,
            level=3.0,
            page_num=page_num,
            block_num=block_row.block_num,
        )
        paragraphs = [
            cls._paragraph_from_tesseract(
                paragraph_row=paragraph_row,
                df=df,
                page_num=page_num,
                block_num=block_row.block_num,
            )
            for paragraph_row in paragraph_rows.itertuples()
        ]
        return Block(
            items=paragraphs,
            bounding_box=cls._tesseract_bbox(block_row),
            child_type=BlockChildType.BLOCKS,
            block_category=BlockCategory.BLOCK,
        )

    @classmethod
    def _page_from_tesseract(
        cls,
        page_row: Any,
        df: DataFrame,
        page_idx: int,
        ocr_provenance: OCRProvenance,
    ) -> Page:
        """Build a single ``Page`` from a Tesseract level-1 row.

        ``page_num`` in Tesseract's DataFrame is 1-indexed, while
        ``page_idx`` is 0-indexed for downstream ``Document._pages``.
        """
        page_bbox = cls._tesseract_bbox(page_row)
        page_num = page_idx + 1
        block_rows = cls._tesseract_filter_level(df, level=2.0, page_num=page_num)
        blocks = [
            cls._block_from_tesseract(block_row=br, df=df, page_num=page_num)
            for br in block_rows.itertuples()
        ]
        return Page(
            page_index=page_idx,
            width=int(page_bbox.width),
            height=int(page_bbox.height),
            blocks=blocks,
            bounding_box=page_bbox,
            ocr_provenance=deepcopy(ocr_provenance),
        )

    @classmethod
    def from_tesseract(
        cls,
        tesseract_output: DataFrame,
        tesseract_string: str | None = None,
        source_path: str | Path | None = None,
        lang: str = "eng",
        tesseract_config: str | None = None,
    ) -> Document:
        try:
            from pandas import to_numeric as pd_to_numeric
        except ImportError as err:
            raise ImportError(
                "pandas library is required for from_tesseract function. Please install pandas."
            ) from err

        """Create Document from PyTesseract output (pandas dataframe)"""
        if isinstance(source_path, str):
            source_path = Path(source_path)

        result = cls(source_lib="tesseract", source_path=source_path, pages=[])

        pytesseract_version = cls._safe_package_version("pytesseract")
        # L-18: record the actual Tesseract language pack as a model entry.
        # Pre-fix ``models`` was hardcoded to ``[]`` so two runs with
        # different language packs produced byte-identical provenance and
        # consumers could not tell which model produced which output.
        tesseract_models: list[dict[str, Any]] = []
        if lang:
            tesseract_models.append({"name": str(lang)})
        tesseract_metadata: dict[str, Any] = {
            "source_lib": "tesseract",
            "engine_version": cls._detect_tesseract_engine_version(),
            "models": tesseract_models,
        }
        fingerprint_parts = ["tesseract"]
        if pytesseract_version != "unknown":
            fingerprint_parts.append(f"pytesseract:{pytesseract_version}")
        if tesseract_config:
            # Include a fingerprint of the Tesseract config so the same
            # binary + lang invoked with different ``--oem`` / ``--dpi`` /
            # ``-c`` flags yields distinguishable provenance.
            fingerprint_parts.append(f"config:{tesseract_config}")
        if len(fingerprint_parts) > 1:
            tesseract_metadata["config_fingerprint"] = "|".join(fingerprint_parts)

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

        page_filtered = cls._tesseract_filter_level(tesseract_output, level=1.0)
        for page_idx, page_row in enumerate(page_filtered.itertuples()):
            result._pages.append(
                cls._page_from_tesseract(
                    page_row=page_row,
                    df=tesseract_output,
                    page_idx=page_idx,
                    ocr_provenance=ocr_provenance,
                )
            )

        result._sort_pages()

        if tesseract_string is not None and result.pages:
            # If a string is provided, we can add it to the first page
            result.pages[0].original_ocr_tool_text = tesseract_string

        return result
