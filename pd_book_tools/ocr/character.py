from dataclasses import dataclass, field
from typing import Dict, Optional

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.label_normalization import (
    normalize_character_components,
    normalize_text_style_labels,
)


@dataclass
class Character:
    """Represents a single OCR character with its own bounding box and labels."""

    text: str
    bounding_box: BoundingBox
    ocr_confidence: Optional[float] = None
    text_style_labels: list[str] = field(default_factory=list)
    word_components: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.text_style_labels = normalize_text_style_labels(self.text_style_labels)
        self.word_components = normalize_character_components(self.word_components)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "type": "Character",
            "text": self.text,
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None,
            "ocr_confidence": self.ocr_confidence,
            "text_style_labels": self.text_style_labels,
            "word_components": self.word_components,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Character":
        """Create Character from dictionary."""
        word_components = list(data.get("word_components", []))
        if data.get("is_footnote_marker"):
            word_components.append("footnote marker")

        return Character(
            text=data["text"],
            bounding_box=BoundingBox.from_dict(data["bounding_box"]),
            ocr_confidence=data.get("ocr_confidence"),
            text_style_labels=data.get("text_style_labels", []),
            word_components=word_components,
        )
