from copy import deepcopy
from dataclasses import dataclass, field
from logging import getLogger
from typing import ClassVar, Dict, Optional

import cv2
import numpy as np
from numpy import ndarray
from thefuzz.fuzz import ratio as fuzz_ratio

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point
from pd_book_tools.ocr.character import Character
from pd_book_tools.ocr.label_normalization import (
    ALLOWED_COMPONENTS,
    ALLOWED_TEXT_STYLE_LABEL_SCOPES,
    ALLOWED_TEXT_STYLE_LABELS,
    normalize_text_style_label,
    normalize_text_style_label_scope,
    normalize_text_style_label_scopes,
    normalize_text_style_labels,
    normalize_word_component,
    normalize_word_components,
)

# Configure logging
logger = getLogger(__name__)


@dataclass
class Word:
    """Represents a single word (uninterrupted sequence of characters) detected by OCR"""

    ALLOWED_TEXT_STYLE_LABELS: ClassVar[frozenset[str]] = ALLOWED_TEXT_STYLE_LABELS

    ALLOWED_TEXT_STYLE_LABEL_SCOPES: ClassVar[frozenset[str]] = (
        ALLOWED_TEXT_STYLE_LABEL_SCOPES
    )

    ALLOWED_WORD_COMPONENTS: ClassVar[frozenset[str]] = ALLOWED_COMPONENTS

    STYLE_LABEL_BY_ATTR: ClassVar[dict[str, str]] = {
        "italic": "italics",
        "is_italic": "italics",
        "small_caps": "small caps",
        "is_small_caps": "small caps",
        "blackletter": "blackletter",
        "is_blackletter": "blackletter",
    }

    WORD_COMPONENT_BY_ATTR: ClassVar[dict[str, str]] = {
        "left_footnote": "footnote marker",
        "is_left_footnote": "footnote marker",
        "right_footnote": "footnote marker",
        "is_right_footnote": "footnote marker",
        "footnote": "footnote marker",
        "is_footnote": "footnote marker",
    }

    _text: str
    bounding_box: BoundingBox
    ocr_confidence: float | None
    word_labels: list[str] = field(default_factory=list)
    text_style_labels: list[str] = field(default_factory=list)
    text_style_label_scopes: dict[str, str] = field(default_factory=dict)
    word_components: list[str] = field(default_factory=list)

    _ground_truth_text: Optional[str] = None
    ground_truth_bounding_box: Optional[BoundingBox] = None
    ground_truth_match_keys: dict = field(default_factory=dict)
    baseline: dict[str, float | str] | None = None

    def __init__(
        self,
        text: str,
        bounding_box: BoundingBox,
        ocr_confidence: Optional[float] = None,
        word_labels: Optional[list[str]] = None,
        text_style_labels: Optional[list[str]] = None,
        text_style_label_scopes: Optional[dict[str, str]] = None,
        word_components: Optional[list[str]] = None,
        baseline: Optional[dict[str, float | str]] = None,
        ground_truth_text: Optional[str] = None,
        ground_truth_bounding_box: Optional[BoundingBox] = None,
        ground_truth_match_keys: Optional[dict] = None,
    ):
        self.text = text  # Use the setter for validation or processing
        self.bounding_box = bounding_box
        self.ocr_confidence = ocr_confidence
        if word_labels:
            self.word_labels = list(word_labels)
        else:
            self.word_labels = []
        self.text_style_labels = self._normalize_text_style_labels(text_style_labels)
        self.text_style_label_scopes = self._normalize_text_style_label_scopes(
            self.text_style_labels,
            text_style_label_scopes,
        )
        self.word_components = self._normalize_word_components(word_components)
        self.baseline = baseline.copy() if baseline else None
        self.ground_truth_text = ground_truth_text or ""
        self.ground_truth_bounding_box = ground_truth_bounding_box
        if ground_truth_match_keys:
            self.ground_truth_match_keys = ground_truth_match_keys
        else:
            self.ground_truth_match_keys = {}

    @classmethod
    def _normalize_text_style_label(cls, label: str) -> str:
        return normalize_text_style_label(label)

    @classmethod
    def _normalize_text_style_labels(cls, labels: Optional[list[str]]) -> list[str]:
        return normalize_text_style_labels(labels)

    @classmethod
    def _normalize_text_style_label_scopes(
        cls,
        labels: list[str],
        scopes: Optional[dict[str, str]],
    ) -> dict[str, str]:
        return normalize_text_style_label_scopes(labels, scopes)

    @classmethod
    def _normalize_word_component(cls, component: str) -> str:
        return normalize_word_component(component)

    @classmethod
    def _normalize_word_components(cls, components: Optional[list[str]]) -> list[str]:
        return normalize_word_components(components)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value

    @property
    def ground_truth_text(self) -> str:
        return self._ground_truth_text or ""

    @ground_truth_text.setter
    def ground_truth_text(self, value: str) -> None:
        self._ground_truth_text = value

    def copy_ocr_to_ground_truth(self) -> bool:
        """Copy OCR text into ground truth text. Returns True if text was present."""
        if not self.text:
            return False
        self.ground_truth_text = self.text
        return True

    def copy_ground_truth_to_ocr(self) -> bool:
        """Copy ground truth text into OCR text. Returns True if GT was present."""
        if not self.ground_truth_text:
            return False
        self.text = self.ground_truth_text
        return True

    def clear_ground_truth(self) -> bool:
        """Clear ground truth text. Returns True if there was GT text to clear."""
        if not self.ground_truth_text:
            return False
        self.ground_truth_text = ""
        return True

    @property
    def ground_truth_exact_match(self) -> bool:
        """Check if the word matches the ground truth text exactly"""
        if self.ground_truth_text:
            return self.text == self.ground_truth_text
        return False

    @property
    def is_empty(self) -> bool:
        """Return True when this word has no text."""
        return not self.text

    # ------------------------------------------------------------------
    # Style and component attribute methods
    # ------------------------------------------------------------------

    def read_style_attribute(
        self,
        primary_name: str,
        aliases: tuple[str, ...] = (),
    ) -> bool:
        """Read a legacy boolean word attribute from modern Word structures."""
        style_label = self._resolve_style_label(primary_name, aliases)
        if style_label is not None:
            return style_label in self._normalized_style_labels()

        component_label = self._resolve_word_component(primary_name, aliases)
        if component_label is not None:
            return component_label in self._normalized_components()

        return False

    def update_style_attributes(
        self,
        *,
        italic: bool,
        small_caps: bool,
        blackletter: bool,
        left_footnote: bool,
        right_footnote: bool,
    ) -> bool:
        """Update text styles and word components."""
        desired_flags = {
            "italic": bool(italic),
            "small_caps": bool(small_caps),
            "blackletter": bool(blackletter),
            "left_footnote": bool(left_footnote),
            "right_footnote": bool(right_footnote),
        }
        current_flags = {
            name: self.read_style_attribute(name) for name in desired_flags
        }
        if current_flags == desired_flags:
            return True

        style_labels = self._normalized_style_labels()
        style_scopes = self._normalized_style_scopes()
        word_components = self._normalized_components()

        style_labels_set = set(style_labels)
        component_set = set(word_components)

        for attr_name in ("italic", "small_caps", "blackletter"):
            style_label = self._resolve_style_label(attr_name, ())
            if style_label is None:
                continue
            if desired_flags[attr_name]:
                style_labels_set.add(style_label)
                style_scopes.setdefault(style_label, "whole")
            else:
                style_labels_set.discard(style_label)
                style_scopes.pop(style_label, None)

        footnote_component = self._resolve_word_component("left_footnote", ())
        if footnote_component is not None:
            if desired_flags["left_footnote"] or desired_flags["right_footnote"]:
                component_set.add(footnote_component)
            else:
                component_set.discard(footnote_component)

        normalized_style_labels = self._ordered_values(style_labels, style_labels_set)
        normalized_components = self._ordered_values(word_components, component_set)

        if not normalized_style_labels:
            normalized_style_labels = ["regular"]
        elif "regular" in normalized_style_labels and len(normalized_style_labels) > 1:
            normalized_style_labels = [
                label for label in normalized_style_labels if label != "regular"
            ]

        normalized_style_scopes = {
            label: normalize_text_style_label_scope(style_scopes.get(label, "whole"))
            for label in normalized_style_labels
        }

        self.text_style_labels = normalized_style_labels
        self.text_style_label_scopes = normalized_style_scopes
        self.word_components = normalized_components
        return True

    def apply_style_scope(
        self,
        style: str,
        scope: str,
    ) -> bool:
        """Apply a scope to an existing or implied text style label."""
        normalized_style = normalize_text_style_label(style)
        normalized_scope = normalize_text_style_label_scope(scope)

        style_labels = self._normalized_style_labels()
        style_scopes = self._normalized_style_scopes()
        style_set = set(style_labels)
        style_set.add(normalized_style)
        style_set.discard("regular")

        ordered_labels = self._ordered_values(style_labels, style_set)
        if normalized_style not in ordered_labels:
            ordered_labels.append(normalized_style)

        style_scopes[normalized_style] = normalized_scope
        self.text_style_labels = ordered_labels or [normalized_style]
        self.text_style_label_scopes = {
            label: normalize_text_style_label_scope(style_scopes.get(label, "whole"))
            for label in self.text_style_labels
        }
        return True

    def apply_component(
        self,
        component: str,
        *,
        enabled: bool,
    ) -> bool:
        """Add or remove a normalized word component label."""
        normalized_component = normalize_word_component(component)
        word_components = self._normalized_components()
        component_set = set(word_components)
        if enabled:
            component_set.add(normalized_component)
        else:
            component_set.discard(normalized_component)
        self.word_components = self._ordered_values(word_components, component_set)
        return True

    def remove_style_label(self, style: str) -> bool:
        """Remove a text style label while preserving other style metadata."""
        normalized_style = normalize_text_style_label(style)
        style_labels = self._normalized_style_labels()
        style_scopes = self._normalized_style_scopes()

        style_set = set(style_labels)
        style_set.discard(normalized_style)
        style_scopes.pop(normalized_style, None)

        ordered_labels = self._ordered_values(style_labels, style_set)
        if not ordered_labels:
            ordered_labels = ["regular"]

        self.text_style_labels = ordered_labels
        self.text_style_label_scopes = {
            label: normalize_text_style_label_scope(style_scopes.get(label, "whole"))
            for label in ordered_labels
        }
        return True

    def clear_all_scopes(self) -> bool:
        """Remove all scope assignments from text style labels.

        Returns True if at least one scope was removed, False otherwise.
        """
        style_labels = self._normalized_style_labels()
        candidate_styles = [label for label in style_labels if label != "regular"]
        if not candidate_styles:
            return False

        scopes = self._normalized_style_scopes()
        changed = False
        for style_label in candidate_styles:
            if style_label in scopes:
                scopes.pop(style_label)
                changed = True

        if changed:
            self.text_style_label_scopes = scopes
        return changed

    def _normalized_style_labels(self) -> list[str]:
        """Return normalized text style labels list."""
        labels = list(self.text_style_labels or [])
        normalized = []
        for label in labels:
            try:
                normalized.append(normalize_text_style_label(str(label)))
            except ValueError:
                logger.debug("Ignoring invalid text style label %r", label)
        if not normalized:
            return ["regular"]
        return list(dict.fromkeys(normalized))

    def _normalized_style_scopes(self) -> dict[str, str]:
        """Return normalized text style label scopes dict."""
        scopes = dict(self.text_style_label_scopes or {})
        normalized: dict[str, str] = {}
        for label, scope in scopes.items():
            try:
                normalized_label = normalize_text_style_label(str(label))
                normalized[normalized_label] = normalize_text_style_label_scope(scope)
            except ValueError:
                logger.debug(
                    "Ignoring invalid text style scope entry %r=%r", label, scope
                )
        return normalized

    def _normalized_components(self) -> list[str]:
        """Return normalized word components list."""
        components = list(self.word_components or [])
        normalized = []
        for component in components:
            try:
                normalized.append(normalize_word_component(str(component)))
            except ValueError:
                logger.debug("Ignoring invalid word component %r", component)
        return normalized

    @classmethod
    def _resolve_style_label(
        cls,
        primary_name: str,
        aliases: tuple[str, ...],
    ) -> str | None:
        """Resolve a legacy attribute name to a style label."""
        style_label = cls.STYLE_LABEL_BY_ATTR.get(primary_name)
        if style_label is not None:
            return style_label
        for alias in aliases:
            style_label = cls.STYLE_LABEL_BY_ATTR.get(alias)
            if style_label is not None:
                return style_label
        return None

    @classmethod
    def _resolve_word_component(
        cls,
        primary_name: str,
        aliases: tuple[str, ...],
    ) -> str | None:
        """Resolve a legacy attribute name to a word component label."""
        component_label = cls.WORD_COMPONENT_BY_ATTR.get(primary_name)
        if component_label is not None:
            return component_label
        for alias in aliases:
            component_label = cls.WORD_COMPONENT_BY_ATTR.get(alias)
            if component_label is not None:
                return component_label
        return None

    @staticmethod
    def _ordered_values(original: list[str], values: set[str]) -> list[str]:
        """Return values in their original order, with new values sorted at end."""
        ordered = [value for value in original if value in values]
        ordered.extend(sorted(value for value in values if value not in set(ordered)))
        return ordered

    # ------------------------------------------------------------------
    # Bounding box refinement and expansion
    # ------------------------------------------------------------------

    @property
    def bbox_signature(self) -> tuple[float, float, float, float, bool] | None:
        """Return a stable bbox signature for convergence checks."""
        bbox = self.bounding_box
        if bbox is None:
            return None
        return (
            round(bbox.minX, 6),
            round(bbox.minY, 6),
            round(bbox.maxX, 6),
            round(bbox.maxY, 6),
            bbox.is_normalized,
        )

    def refine_bbox(self, page_image: ndarray | None) -> bool:
        """Refine this word's bounding box using the page image.

        Tries BoundingBox.refine first, falls back to crop_bottom.
        Returns True if refinement succeeded.
        """
        bbox = self.bounding_box
        if bbox is None:
            return False

        if page_image is not None:
            try:
                refined_bbox = bbox.refine(
                    page_image,
                    padding_px=1,
                    expand_beyond_original=False,
                )
                if refined_bbox is not None:
                    self.bounding_box = refined_bbox
                    return True
            except Exception:
                logger.debug(
                    "Bounding-box refine failed during word refine; falling back",
                    exc_info=True,
                )

        if page_image is not None:
            try:
                self.crop_bottom(page_image)
                return True
            except Exception:
                logger.debug(
                    "crop_bottom failed during word refine",
                    exc_info=True,
                )

        return False

    def expand_bbox(
        self,
        padding_px: float,
        page_width: float,
        page_height: float,
    ) -> bool:
        """Expand this word's bbox by uniform pixel padding, clamped to page bounds.

        Returns True if the bbox was successfully expanded.
        """
        bbox = self.bounding_box
        if bbox is None:
            return False

        if bbox.is_normalized:
            if page_width <= 0.0 or page_height <= 0.0:
                return False
            x1 = bbox.minX * page_width
            y1 = bbox.minY * page_height
            x2 = bbox.maxX * page_width
            y2 = bbox.maxY * page_height
        else:
            x1 = bbox.minX
            y1 = bbox.minY
            x2 = bbox.maxX
            y2 = bbox.maxY

        nx1 = max(0.0, x1 - padding_px)
        ny1 = max(0.0, y1 - padding_px)
        nx2 = x2 + padding_px
        ny2 = y2 + padding_px
        if page_width > 0.0:
            nx2 = min(nx2, page_width)
        if page_height > 0.0:
            ny2 = min(ny2, page_height)

        if nx2 <= nx1 or ny2 <= ny1:
            return False

        if bbox.is_normalized:
            new_bbox = BoundingBox(
                Point(nx1 / page_width, ny1 / page_height),
                Point(nx2 / page_width, ny2 / page_height),
                is_normalized=True,
            )
        else:
            new_bbox = BoundingBox(
                Point(nx1, ny1),
                Point(nx2, ny2),
                is_normalized=False,
            )

        self.bounding_box = new_bbox
        return True

    def expand_then_refine_bbox(self, page_image: ndarray | None) -> bool:
        """Iteratively expand and refine this word's bbox until it stabilizes.

        Returns True if any refinement occurred.
        """
        refined = False

        previous_signature = self.bbox_signature
        seen_signatures: set[tuple[float, float, float, float, bool] | None] = {
            previous_signature
        }
        for _ in range(8):
            bbox = self.bounding_box
            if bbox is not None and page_image is not None:
                try:
                    refined_bbox = bbox.refine(
                        page_image,
                        padding_px=0,
                        expand_beyond_original=True,
                    )
                    if refined_bbox is not None:
                        self.bounding_box = refined_bbox
                        refined = True
                        break
                except Exception:
                    logger.debug(
                        "Bounding-box refine (expand_beyond_original=True) failed; falling back",
                        exc_info=True,
                    )

            if page_image is not None:
                try:
                    self.crop_bottom(page_image)
                    refined = True
                except Exception:
                    logger.debug(
                        "crop_bottom failed during expand-then-refine",
                        exc_info=True,
                    )

            current_signature = self.bbox_signature
            if current_signature == previous_signature:
                break
            if current_signature in seen_signatures:
                break

            seen_signatures.add(current_signature)
            previous_signature = current_signature

        return refined

    @property
    def ground_truth_text_only_ocr(self) -> str:
        """Ground truth text limited to words that actually have OCR text.

        For alignment tasks we sometimes need the subset of ground truth tokens
        that correspond to OCR-emitted tokens (ignoring inserted GT-only tokens).
        A Word with empty OCR "text" is treated as non-existent for this view.
        """
        if not self.text:
            return ""
        return self.ground_truth_text or ""

    def scale(self, width, height):
        """Return a deep-copied Word with pixel-space bounding box.

        Behavior:
            * If the current bounding box is already pixel-space (non-normalized),
                returns a deep copy (no coordinate change) and logs an info message.
            * If normalized, scales to pixel coordinates (width/height) and returns
                a deep copy whose bounding box is the scaled (pixel) one while all
                other metadata is duplicated.
        """
        if not self.bounding_box.is_normalized:
            logger.info(
                "Word.scale() called on pixel-space bounding box; returning unchanged deep copy"
            )
            return Word.from_dict(deepcopy(self.to_dict()))
        scaled_bbox = self.bounding_box.scale(width, height)
        data = deepcopy(self.to_dict())
        data["bounding_box"] = scaled_bbox.to_dict()
        return Word.from_dict(data)

    def fuzz_score_against(self, ground_truth_text):
        """Scores a string as "matching" against a ground truth string

        TODO: Perhaps add loose scoring for curly quotes against straight quotes,
        and em-dashes against hyphens to count these as "closer" to gt

        Args:
            ground_truth_text (_type_): 'correct' text
        """
        return fuzz_ratio(self.text, ground_truth_text)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary"""
        return {
            "type": "Word",
            "text": self.text,
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None,
            "ocr_confidence": self.ocr_confidence,
            "word_labels": self.word_labels,
            "text_style_labels": self.text_style_labels,
            "text_style_label_scopes": self.text_style_label_scopes,
            "word_components": self.word_components,
            "baseline": self.baseline,
            "ground_truth_text": (
                self.ground_truth_text if self.ground_truth_text else None
            ),
            "ground_truth_bounding_box": (
                self.ground_truth_bounding_box.to_dict()
                if self.ground_truth_bounding_box
                else None
            ),
            "ground_truth_match_keys": self.ground_truth_match_keys,
        }

    @classmethod
    def from_dict(cls, dict: Dict) -> "Word":
        """Create OCRWord from dictionary"""
        return Word(
            text=dict["text"],
            bounding_box=BoundingBox.from_dict(dict["bounding_box"]),
            ocr_confidence=dict["ocr_confidence"],
            word_labels=dict.get("word_labels", []),
            text_style_labels=dict.get("text_style_labels", []),
            text_style_label_scopes=dict.get("text_style_label_scopes"),
            word_components=dict.get("word_components", []),
            baseline=dict.get("baseline"),
            ground_truth_text=dict.get("ground_truth_text"),
            ground_truth_bounding_box=(
                BoundingBox.from_dict(dict["ground_truth_bounding_box"])
                if dict.get("ground_truth_bounding_box")
                else None
            ),
            ground_truth_match_keys=dict.get("ground_truth_match_keys", {}),
        )

    def refine_bounding_box(self, image: ndarray | None, padding_px: int = 0):
        if image is None:
            logger.warning("Image is None, skipping bounding box refinement")
            return
        logger.debug(
            f"Refining bounding box for word '{self.text}' with padding {padding_px} pixels"
        )
        """Refine the bounding box of the word based on the image content"""
        self.bounding_box = self.bounding_box.refine(image, padding_px=padding_px)

    def split(self, bbox_split_offset: float, character_split_index: int):
        """Split a word into two words at the given indices"""
        logger.debug(
            f"Splitting word '{self.text}' at bbox_split_offset {bbox_split_offset} and character_split_index {character_split_index}"
        )
        # Validation: if ground truth bbox exists ensure same coordinate category
        if self.ground_truth_bounding_box and (
            self.ground_truth_bounding_box.is_normalized
            != self.bounding_box.is_normalized
        ):
            raise ValueError(
                "Cannot split Word: bounding_box and ground_truth_bounding_box use different coordinate systems"
            )
        if bbox_split_offset < 0 or character_split_index < 0:
            raise ValueError(
                "bbox_split_index and character_split_index must be non-negative"
            )

        if character_split_index >= len(self.text):
            raise IndexError("character_split_index is out of range for text")

        # Split the bounding box
        left_bbox, right_bbox = self.bounding_box.split_x_offset(bbox_split_offset)
        logger.debug(
            f"Left bounding box: {left_bbox}, Right bounding box: {right_bbox}"
        )

        # Split the text
        left_text, right_text = (
            self.text[:character_split_index],
            self.text[character_split_index:],
        )
        logger.debug(f"Left text: {left_text}, Right text: {right_text}")

        left_ground_truth_text = (
            self.ground_truth_text[:character_split_index]
            if self.ground_truth_text
            else None
        )
        right_ground_truth_text = (
            self.ground_truth_text[character_split_index:]
            if self.ground_truth_text
            else None
        )
        logger.debug(
            f"Left ground truth text: {left_ground_truth_text}, Right ground truth text: {right_ground_truth_text}"
        )

        left_word = Word(
            text=left_text,
            bounding_box=left_bbox,
            ocr_confidence=None,
            word_labels=self.word_labels,
            text_style_labels=self.text_style_labels,
            text_style_label_scopes=self.text_style_label_scopes,
            word_components=self.word_components,
            ground_truth_text=left_ground_truth_text,
            ground_truth_match_keys={
                "split": True,
            },
        )
        right_word = Word(
            text=right_text,
            bounding_box=right_bbox,
            ocr_confidence=None,
            word_labels=self.word_labels,
            text_style_labels=self.text_style_labels,
            text_style_label_scopes=self.text_style_label_scopes,
            word_components=self.word_components,
            ground_truth_text=right_ground_truth_text,
            ground_truth_match_keys={
                "split": True,
            },
        )
        logger.debug(f"Left word: {left_word.text}, Right word: {right_word.text}")
        return left_word, right_word

    def split_into_characters_from_whitespace(
        self, image: ndarray | None, min_ink_pixels_per_column: int = 1
    ) -> list[Character]:
        """Split word into Character objects using vertical whitespace gaps.

        The word ROI is extracted from the image, converted to grayscale if needed,
        then segmented into runs of non-whitespace columns. If the number of runs
        doesn't match text length, a uniform fallback split is used.
        """
        if image is None:
            raise ValueError("Image is None, cannot split word into characters")
        if not self.text:
            return []

        img_h, img_w = image.shape[:2]
        pixel_bbox = (
            self.bounding_box.scale(img_w, img_h)
            if self.bounding_box.is_normalized
            else self.bounding_box
        )

        min_x = max(0, int(np.floor(pixel_bbox.minX)))
        min_y = max(0, int(np.floor(pixel_bbox.minY)))
        max_x = min(img_w, int(np.ceil(pixel_bbox.maxX)))
        max_y = min(img_h, int(np.ceil(pixel_bbox.maxY)))
        if min_x >= max_x or min_y >= max_y:
            raise ValueError("Word bounding box is out of image bounds")

        roi = image[min_y:max_y, min_x:max_x]
        if roi.ndim == 3:
            gray = roi.mean(axis=2)
        else:
            gray = roi

        min_ink = max(1, int(min_ink_pixels_per_column))
        dark_as_ink = gray < 128
        light_as_ink = ~dark_as_ink

        def _runs_from_mask(mask: ndarray) -> list[tuple[int, int]]:
            columns = np.sum(mask, axis=0) >= min_ink
            mask_runs: list[tuple[int, int]] = []
            run_start: int | None = None
            for idx, has_ink in enumerate(columns):
                if has_ink and run_start is None:
                    run_start = idx
                elif not has_ink and run_start is not None:
                    mask_runs.append((run_start, idx))
                    run_start = None
            if run_start is not None:
                mask_runs.append((run_start, len(columns)))
            return mask_runs

        dark_runs = _runs_from_mask(dark_as_ink)
        light_runs = _runs_from_mask(light_as_ink)
        if abs(len(dark_runs) - len(self.text)) <= abs(
            len(light_runs) - len(self.text)
        ):
            runs = dark_runs
            chosen_mask = dark_as_ink
        else:
            runs = light_runs
            chosen_mask = light_as_ink

        # Best-effort fallback: morphology + distance transform can recover
        # character gaps when sparse noise bridges whitespace columns.
        if len(runs) != len(self.text):
            _, otsu_binary = cv2.threshold(
                gray.astype(np.uint8),
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU,
            )

            def _morph_runs_from_foreground(
                foreground: ndarray,
            ) -> tuple[list[tuple[int, int]], ndarray]:
                kernel = np.ones((2, 2), np.uint8)
                opened = cv2.morphologyEx(foreground, cv2.MORPH_OPEN, kernel)
                closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
                dist = cv2.distanceTransform(closed, cv2.DIST_L2, 3)
                if float(dist.max()) > 0:
                    sure_fg = dist >= (0.2 * float(dist.max()))
                else:
                    sure_fg = closed > 0
                return _runs_from_mask(sure_fg), sure_fg

            morph_runs_a, morph_mask_a = _morph_runs_from_foreground(otsu_binary)
            morph_runs_b, morph_mask_b = _morph_runs_from_foreground(
                cv2.bitwise_not(otsu_binary)
            )
            if abs(len(morph_runs_a) - len(self.text)) <= abs(
                len(morph_runs_b) - len(self.text)
            ):
                morph_runs = morph_runs_a
                morph_mask = morph_mask_a
            else:
                morph_runs = morph_runs_b
                morph_mask = morph_mask_b

            if abs(len(morph_runs) - len(self.text)) < abs(len(runs) - len(self.text)):
                runs = morph_runs
                chosen_mask = morph_mask

        if len(runs) != len(self.text):
            logger.debug(
                "Whitespace segmentation run count (%s) differs from text length (%s); using uniform fallback",
                len(runs),
                len(self.text),
            )
            roi_width = max_x - min_x
            per_char = roi_width / len(self.text)
            runs = []
            for i in range(len(self.text)):
                left = int(round(i * per_char))
                right = int(round((i + 1) * per_char))
                runs.append((left, right))
            # Keep using last selected mask for vertical bounds when possible.

        # For character splits we intentionally propagate every word-level style label
        # to every character, including labels scoped as "part". This is a conservative
        # placeholder until a human reviewer or a character-level OCR model resolves
        # the exact character subset for partial styles.
        character_style_labels = [
            label
            for label in self.text_style_labels
            if self.text_style_label_scopes.get(label, "whole") in {"whole", "part"}
        ]
        character_word_components = list(self.word_components)

        characters: list[Character] = []
        for idx, ch in enumerate(self.text):
            left, right = runs[idx]

            run_mask = chosen_mask[:, left:right]
            row_has_ink = np.any(run_mask, axis=1) if run_mask.size else np.array([])
            if row_has_ink.size and np.any(row_has_ink):
                row_indices = np.where(row_has_ink)[0]
                top_rel = int(row_indices[0])
                bottom_rel = int(row_indices[-1]) + 1
            else:
                top_rel = 0
                bottom_rel = max_y - min_y

            char_bbox = BoundingBox.from_ltrb(
                min_x + left,
                min_y + top_rel,
                min_x + right,
                min_y + bottom_rel,
            )
            characters.append(
                Character(
                    text=ch,
                    bounding_box=char_bbox,
                    ocr_confidence=self.ocr_confidence,
                    text_style_labels=list(character_style_labels),
                    word_components=list(character_word_components),
                )
            )

        # Baseline/topline heuristic: label characters displaced vertically.
        if len(characters) >= 2:
            tops = np.array([c.bounding_box.minY for c in characters], dtype=float)
            bottoms = np.array([c.bounding_box.maxY for c in characters], dtype=float)
            heights = np.array(
                [max(c.bounding_box.height, 1.0) for c in characters], dtype=float
            )

            # Descenders (e.g., p/g/j/q/Q) naturally dip below baseline,
            # so reduce their influence in baseline estimation.
            descender_chars = {"p", "g", "j", "q", "Q"}
            weights = np.array(
                [0.35 if c.text in descender_chars else 1.0 for c in characters],
                dtype=float,
            )
            median_top = float(np.average(tops, weights=weights))
            median_bottom = float(np.average(bottoms, weights=weights))
            median_height = float(np.average(heights, weights=weights))
            top_delta = 0.2 * median_height
            bottom_delta = 0.1 * median_height

            for c in characters:
                is_super = c.bounding_box.minY <= (
                    median_top - top_delta
                ) and c.bounding_box.maxY <= (median_bottom - bottom_delta)
                is_sub = c.bounding_box.minY >= (
                    median_top + top_delta
                ) and c.bounding_box.maxY >= (median_bottom + bottom_delta)
                if is_super and "superscript" not in c.word_components:
                    c.word_components.append("superscript")
                if is_sub and "subscript" not in c.word_components:
                    c.word_components.append("subscript")
        return characters

    def estimate_baseline_from_image(
        self, image: ndarray | None
    ) -> dict[str, float | str] | None:
        """Estimate a horizontal baseline for this word in pixel coordinates."""
        if image is None or not self.text:
            self.baseline = None
            return None

        characters = self.split_into_characters_from_whitespace(image)
        if not characters:
            self.baseline = None
            return None

        descender_chars = {"p", "g", "j", "q", "Q"}
        bottoms = np.array([c.bounding_box.maxY for c in characters], dtype=float)
        heights = np.array(
            [max(c.bounding_box.height, 1.0) for c in characters], dtype=float
        )
        weights = np.array(
            [0.35 if c.text in descender_chars else 1.0 for c in characters],
            dtype=float,
        )

        baseline_y = float(np.average(bottoms, weights=weights))
        height_ref = float(np.average(heights, weights=weights))
        residual = bottoms - baseline_y
        weighted_var = float(np.average(residual * residual, weights=weights))
        weighted_std = float(np.sqrt(weighted_var))
        confidence = max(0.0, 1.0 - (weighted_std / max(1.0, height_ref)))

        self.baseline = {
            "type": "horizontal",
            "y": baseline_y,
            "confidence": confidence,
            "coordinate_space": "pixel",
        }
        return self.baseline

    def merge(self, word_to_merge: "Word"):
        """Merge this word with another word"""
        if not isinstance(word_to_merge, Word):
            raise TypeError("word_to_merge must be an instance of Word")

        # Coordinate system consistency checks
        if self.bounding_box.is_normalized != word_to_merge.bounding_box.is_normalized:
            raise ValueError(
                "Cannot merge Words: bounding boxes use different coordinate systems (pixel vs normalized)"
            )
        if self.ground_truth_bounding_box and word_to_merge.ground_truth_bounding_box:
            if (
                self.ground_truth_bounding_box.is_normalized
                != word_to_merge.ground_truth_bounding_box.is_normalized
            ):
                raise ValueError(
                    "Cannot merge Words: ground truth bounding boxes use different coordinate systems"
                )
        # Also ensure if only one word has ground truth bbox it matches its own main bbox category
        for w in (self, word_to_merge):
            if w.ground_truth_bounding_box and (
                w.ground_truth_bounding_box.is_normalized
                != w.bounding_box.is_normalized
            ):
                raise ValueError(
                    "Cannot merge Words: a word has mismatched coordinate systems between its bounding box and ground truth bounding box"
                )

        word_order_left_to_right = True
        if self.bounding_box.top_left.x > word_to_merge.bounding_box.top_left.x:
            word_order_left_to_right = False

        self.bounding_box = BoundingBox.union(
            [self.bounding_box, word_to_merge.bounding_box]
        )

        if word_order_left_to_right:
            self.text = (self.text or "") + (word_to_merge.text or "")
            self.ground_truth_text = (self.ground_truth_text or "") + (
                word_to_merge.ground_truth_text or ""
            )
        else:
            self.text = (word_to_merge.text or "") + self.text
            self.ground_truth_text = (word_to_merge.ground_truth_text or "") + (
                self.ground_truth_text or ""
            )

        if self.ocr_confidence is not None and word_to_merge.ocr_confidence is not None:
            self.ocr_confidence = (
                self.ocr_confidence + word_to_merge.ocr_confidence
            ) / 2
        elif self.ocr_confidence is None and word_to_merge.ocr_confidence is not None:
            self.ocr_confidence = word_to_merge.ocr_confidence
        elif self.ocr_confidence is not None and word_to_merge.ocr_confidence is None:
            self.ocr_confidence = self.ocr_confidence
        else:
            self.ocr_confidence = None
        # Merge labels & ground truth keys
        self.word_labels.extend(word_to_merge.word_labels)
        self.text_style_labels.extend(word_to_merge.text_style_labels)
        self.word_components.extend(word_to_merge.word_components)
        self.ground_truth_match_keys.update(word_to_merge.ground_truth_match_keys)
        # Deduplicate labels while preserving first occurrence order
        self.word_labels = list(dict.fromkeys(self.word_labels))
        self.text_style_labels = list(dict.fromkeys(self.text_style_labels))
        self.word_components = list(dict.fromkeys(self.word_components))

        merged_scopes = self._normalize_text_style_label_scopes(
            self.text_style_labels,
            self.text_style_label_scopes,
        )
        incoming_scopes = self._normalize_text_style_label_scopes(
            word_to_merge.text_style_labels,
            word_to_merge.text_style_label_scopes,
        )
        for label in self.text_style_labels:
            current = merged_scopes.get(label, "whole")
            incoming = incoming_scopes.get(label, "whole")
            merged_scopes[label] = "part" if "part" in (current, incoming) else "whole"
        self.text_style_label_scopes = merged_scopes

    def crop_bottom(self, img_ndarray):
        """Crop the bottom of the word using bounding box crop_bottom method"""
        if not self.bounding_box:
            logger.warning("Bounding box is None, cannot crop bottom")
            raise ValueError("Bounding box is None, cannot crop bottom")

        if img_ndarray is None:
            logger.warning("Image ndarray is None, cannot crop bottom")
            raise ValueError("Image ndarray is None, cannot crop bottom")

        cropped_bbox = self.bounding_box.crop_bottom(img_ndarray)
        if cropped_bbox is None:
            logger.warning("Cropped bounding box is None, cannot crop bottom")
        self.bounding_box = cropped_bbox

    def crop_top(self, img_ndarray):
        """Crop the top of the word using bounding box crop_top method"""
        if not self.bounding_box:
            logger.warning("Bounding box is None, cannot crop top")
            raise ValueError("Bounding box is None, cannot crop top")

        if img_ndarray is None:
            logger.warning("Image ndarray is None, cannot crop top")
            raise ValueError("Image ndarray is None, cannot crop top")

        cropped_bbox = self.bounding_box.crop_top(img_ndarray)
        if cropped_bbox is None:
            logger.warning("Cropped bounding box is None, cannot crop top")
        self.bounding_box = cropped_bbox
