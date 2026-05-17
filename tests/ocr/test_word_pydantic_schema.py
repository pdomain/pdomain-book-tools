"""Tests for Word.__get_pydantic_core_schema__ — wire-shape JSON Schema."""

from __future__ import annotations

from pydantic import TypeAdapter

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point
from pd_book_tools.ocr.review import ReviewMetadata
from pd_book_tools.ocr.word import Word


def _bbox() -> BoundingBox:
    return BoundingBox(
        top_left=Point(0, 0, is_normalized=False),
        bottom_right=Point(10, 10, is_normalized=False),
    )


def test_word_type_adapter_does_not_raise():
    adapter = TypeAdapter(Word)
    assert adapter is not None


def test_word_json_schema_shape():
    schema = TypeAdapter(Word).json_schema()
    assert schema["type"] == "object"
    props = schema["properties"]
    # Wire-shape keys (NOT dataclass field names): ``text`` and
    # ``ground_truth_text`` (no leading underscore).
    expected_keys = {
        "type",
        "text",
        "bounding_box",
        "ocr_confidence",
        "word_labels",
        "text_style_labels",
        "text_style_label_scopes",
        "word_components",
        "baseline",
        "ground_truth_text",
        "ground_truth_bounding_box",
        "ground_truth_match_keys",
        "review",
    }
    assert set(props.keys()) == expected_keys
    assert "_text" not in props
    assert "_ground_truth_text" not in props


def test_word_validate_from_dict_roundtrip_minimal():
    adapter = TypeAdapter(Word)
    w = Word(text="hello", bounding_box=_bbox())
    d = w.to_dict()
    validated = adapter.validate_python(d)
    assert isinstance(validated, Word)
    assert validated.text == "hello"
    assert validated.bounding_box == w.bounding_box
    dumped = adapter.dump_python(validated)
    assert dumped == d


def test_word_validate_from_dict_roundtrip_full():
    adapter = TypeAdapter(Word)
    w = Word(
        text="hello",
        bounding_box=_bbox(),
        ocr_confidence=0.95,
        word_labels=["test-label"],
        text_style_labels=["italics"],
        text_style_label_scopes={"italics": "whole"},
        word_components=["footnote marker"],
        baseline={"m": 0.0, "b": 5.0, "source": "ocr"},
        ground_truth_text="hello",
        ground_truth_bounding_box=_bbox(),
        ground_truth_match_keys={"matched_text": "hello"},
        review=ReviewMetadata(validated=True, reviewer_note="ok"),
    )
    d = w.to_dict()
    validated = adapter.validate_python(d)
    assert isinstance(validated, Word)
    assert validated == w
    dumped = adapter.dump_python(validated)
    assert dumped == d
