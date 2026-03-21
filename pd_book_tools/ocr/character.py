from dataclasses import dataclass, field
from typing import Dict, Optional

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.label_normalization import (
    normalize_text_style_labels,
    normalize_word_components,
)


@dataclass
class Character:
    """Represents a single OCR character with its own bounding box and labels."""

    text: str
    bounding_box: BoundingBox
    ocr_confidence: Optional[float] = None
    text_style_labels: list[str] = field(default_factory=list)
    word_components: list[str] = field(default_factory=list)
    is_superscript: bool = False
    is_subscript: bool = False

    def __post_init__(self) -> None:
        self.text_style_labels = normalize_text_style_labels(self.text_style_labels)
        self.word_components = normalize_word_components(self.word_components)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "type": "Character",
            "text": self.text,
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None,
            "ocr_confidence": self.ocr_confidence,
            "text_style_labels": self.text_style_labels,
            "word_components": self.word_components,
            "is_superscript": self.is_superscript,
            "is_subscript": self.is_subscript,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Character":
        """Create Character from dictionary."""
        return Character(
            text=data["text"],
            bounding_box=BoundingBox.from_dict(data["bounding_box"]),
            ocr_confidence=data.get("ocr_confidence"),
            text_style_labels=data.get("text_style_labels", []),
            word_components=data.get("word_components", []),
            is_superscript=data.get("is_superscript", False),
            is_subscript=data.get("is_subscript", False),
        )
