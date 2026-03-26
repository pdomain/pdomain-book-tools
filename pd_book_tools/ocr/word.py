from copy import deepcopy
from dataclasses import dataclass, field
from logging import getLogger
from typing import ClassVar, Dict, Optional

import cv2
import numpy as np
from numpy import ndarray
from thefuzz.fuzz import ratio as fuzz_ratio

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.character import Character
from pd_book_tools.ocr.label_normalization import (
    ALLOWED_COMPONENTS,
    ALLOWED_TEXT_STYLE_LABEL_SCOPES,
    ALLOWED_TEXT_STYLE_LABELS,
    normalize_text_style_label,
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

    @property
    def ground_truth_exact_match(self) -> bool:
        """Check if the word matches the ground truth text exactly"""
        if self.ground_truth_text:
            return self.text == self.ground_truth_text
        return False

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
