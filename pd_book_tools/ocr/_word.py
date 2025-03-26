from dataclasses import dataclass
from typing import Optional

from ..geometry import BoundingBox


@dataclass
class Word:
    """Represents a single word (uninterrupted sequence of characters) detected by OCR"""

    _text: str
    bounding_box: BoundingBox
    ocr_confidence: float
    word_labels: Optional[list[str]] = None

    def __init__(
        self,
        text: str,
        bounding_box: BoundingBox,
        ocr_confidence: float,
        word_labels: Optional[list[str]] = None,
    ):
        self.text = text  # Use the setter for validation or processing
        self.bounding_box = bounding_box
        self.ocr_confidence = ocr_confidence
        self.word_labels = word_labels

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary"""
        return {
            "type": "Word",
            "text": self.text,
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None,
            "ocr_confidence": self.ocr_confidence,
            "word_labels": self.word_labels,
        }

    def from_dict(dict) -> "Word":
        """Create OCRWord from dictionary"""
        return Word(
            text=dict["text"],
            bounding_box=BoundingBox.from_dict(dict["bounding_box"]),
            ocr_confidence=dict["ocr_confidence"],
            word_labels=dict.get("word_labels", []),
        )
