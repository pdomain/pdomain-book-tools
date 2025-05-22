from dataclasses import dataclass, field
from logging import getLogger
from typing import Optional

from numpy import ndarray
from thefuzz.fuzz import ratio as fuzz_ratio

from ..geometry import BoundingBox

# Configure logging
logger = getLogger(__name__)


@dataclass
class Word:
    """Represents a single word (uninterrupted sequence of characters) detected by OCR"""

    _text: str
    bounding_box: BoundingBox
    ocr_confidence: float
    word_labels: list[str] = field(default_factory=list)

    _ground_truth_text: Optional[str] = None
    ground_truth_bounding_box: Optional[BoundingBox] = None
    ground_truth_match_keys: dict = field(default_factory=dict)

    def __init__(
        self,
        text: str,
        bounding_box: BoundingBox,
        ocr_confidence: float,
        word_labels: Optional[list[str]] = None,
        ground_truth_text: Optional[str] = None,
        ground_truth_bounding_box: Optional[BoundingBox] = None,
        ground_truth_match_keys: Optional[dict] = None,
    ):
        self.text = text  # Use the setter for validation or processing
        self.bounding_box = bounding_box
        self.ocr_confidence = ocr_confidence
        if word_labels:
            self.word_labels = word_labels
        else:
            self.word_labels = []
        self.ground_truth_text = ground_truth_text
        self.ground_truth_bounding_box = ground_truth_bounding_box
        if ground_truth_match_keys:
            self.ground_truth_match_keys = ground_truth_match_keys
        else:
            self.ground_truth_match_keys = {}

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value

    @property
    def ground_truth_text(self) -> str:
        return self._ground_truth_text

    @ground_truth_text.setter
    def ground_truth_text(self, value: str) -> None:
        self._ground_truth_text = value

    @property
    def ground_truth_exact_match(self) -> bool:
        """Check if the word matches the ground truth text exactly"""
        if self.ground_truth_text:
            return self.text == self.ground_truth_text
        return False

    def scale(self, width, height):
        """
        Return new word with scaled bounding box
        to absolute pixel coordinates
        """
        return Word(
            text=self.text,
            bounding_box=self.bounding_box.scale(width, height),
            ocr_confidence=self.ocr_confidence,
            word_labels=self.word_labels,
        )

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

    def from_dict(dict) -> "Word":
        """Create OCRWord from dictionary"""
        return Word(
            text=dict["text"],
            bounding_box=BoundingBox.from_dict(dict["bounding_box"]),
            ocr_confidence=dict["ocr_confidence"],
            word_labels=dict.get("word_labels", []),
            ground_truth_text=dict.get("ground_truth_text"),
            ground_truth_bounding_box=(
                BoundingBox.from_dict(dict["ground_truth_bounding_box"])
                if dict.get("ground_truth_bounding_box")
                else None
            ),
            ground_truth_match_keys=dict.get("ground_truth_match_keys", {}),
        )

    def refine_bounding_box(self, image: ndarray):
        self.bounding_box = self.bounding_box.refine(image)

    def split(self, bbox_split_offset: float, character_split_index: int):
        """Split a word into two words at the given indices"""
        logger.debug(
            f"Splitting word '{self.text}' at bbox_split_offset {bbox_split_offset} and character_split_index {character_split_index}"
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
            ground_truth_text=right_ground_truth_text,
            ground_truth_match_keys={
                "split": True,
            },
        )
        logger.debug(f"Left word: {left_word.text}, Right word: {right_word.text}")
        return left_word, right_word

    def merge(self, word_to_merge: "Word"):
        """Merge this word with another word"""
        if not isinstance(word_to_merge, Word):
            raise TypeError("word_to_merge must be an instance of Word")

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

        self.ocr_confidence = (self.ocr_confidence + word_to_merge.ocr_confidence) / 2
        self.word_labels.extend(word_to_merge.word_labels)

        self.ground_truth_match_keys.update(word_to_merge.ground_truth_match_keys)
        self.ground_truth_match_keys.update(self.ground_truth_match_keys)
        self.word_labels.extend(word_to_merge.word_labels)
        self.word_labels = list(set(self.word_labels))
        # Remove duplicates
        self.word_labels = list(dict.fromkeys(self.word_labels))
