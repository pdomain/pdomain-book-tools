"""Tests for Character.__get_pydantic_core_schema__ — wire-shape JSON Schema."""

from __future__ import annotations

from pydantic import TypeAdapter

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.geometry.point import Point
from pdomain_book_tools.ocr.character import Character


def _bbox() -> BoundingBox:
    return BoundingBox(
        top_left=Point(0, 0, is_normalized=False),
        bottom_right=Point(5, 5, is_normalized=False),
    )


def test_character_type_adapter_does_not_raise():
    adapter = TypeAdapter(Character)
    assert adapter is not None


def test_character_json_schema_shape():
    schema = TypeAdapter(Character).json_schema()
    assert schema["type"] == "object"
    props = schema["properties"]
    assert set(props.keys()) == {
        "type",
        "text",
        "bounding_box",
        "ocr_confidence",
        "text_style_labels",
        "word_components",
    }
    assert props["type"]["const"] == "Character"
    assert props["text"]["type"] == "string"
    assert "anyOf" in props["ocr_confidence"] or "null" in str(props["ocr_confidence"])
    assert props["text_style_labels"]["type"] == "array"
    assert props["word_components"]["type"] == "array"


def test_character_validate_from_dict_roundtrip():
    adapter = TypeAdapter(Character)
    c = Character(text="a", bounding_box=_bbox(), ocr_confidence=0.9)
    d = c.to_dict()
    validated = adapter.validate_python(d)
    assert isinstance(validated, Character)
    assert validated == c
    dumped = adapter.dump_python(validated)
    assert dumped == d
