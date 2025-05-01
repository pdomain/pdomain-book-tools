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
