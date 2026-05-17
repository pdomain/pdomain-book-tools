from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.label_normalization import (
    normalize_character_components,
    normalize_text_style_labels,
)
from pd_book_tools.schemas._helpers import (
    NUMBER_SCHEMA,
    STR_LIST_SCHEMA,
)


@dataclass
class Character:
    """Represents a single OCR character with its own bounding box and labels."""

    text: str
    bounding_box: BoundingBox
    ocr_confidence: float | None = None
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
    def from_dict(cls, data: dict) -> Character:
        """Create Character from dictionary."""
        word_components = list(data.get("word_components", []))
        if data.get("is_footnote_marker"):
            word_components.append("footnote marker")

        bb_raw = data["bounding_box"]
        bounding_box = (
            bb_raw if isinstance(bb_raw, BoundingBox) else BoundingBox.from_dict(bb_raw)
        )
        return Character(
            text=data["text"],
            bounding_box=bounding_box,
            ocr_confidence=data.get("ocr_confidence"),
            text_style_labels=data.get("text_style_labels", []),
            word_components=word_components,
        )

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        # Local import to avoid a circular: BoundingBox imports Point,
        # Character imports BoundingBox. Module-level is fine here since
        # this module is loaded after both.
        bb_schema = handler.generate_schema(BoundingBox)
        return core_schema.no_info_after_validator_function(
            function=cls.from_dict,
            schema=core_schema.typed_dict_schema(
                {
                    "type": core_schema.typed_dict_field(
                        core_schema.literal_schema(["Character"]),
                        required=False,
                    ),
                    "text": core_schema.typed_dict_field(
                        core_schema.str_schema(),
                    ),
                    "bounding_box": core_schema.typed_dict_field(bb_schema),
                    "ocr_confidence": core_schema.typed_dict_field(
                        core_schema.nullable_schema(NUMBER_SCHEMA),
                        required=False,
                    ),
                    "text_style_labels": core_schema.typed_dict_field(
                        STR_LIST_SCHEMA,
                        required=False,
                    ),
                    "word_components": core_schema.typed_dict_field(
                        STR_LIST_SCHEMA,
                        required=False,
                    ),
                }
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls.to_dict,
            ),
        )
