"""Tests for Word.__get_pydantic_core_schema__ — wire-shape JSON Schema."""

from __future__ import annotations

from pydantic import TypeAdapter

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point
from pd_book_tools.ocr.glyph_annotations import (
    GlyphAnnotations,
    LigatureKind,
    LigatureMark,
)
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
        "glyph_annotations",
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


# ---------------------------------------------------------------------------
# Issue #180: glyph_annotations dropped by pydantic round-trip
# ---------------------------------------------------------------------------


def _ga_with_ligature() -> GlyphAnnotations:
    """Return a non-empty GlyphAnnotations with one ligature mark."""
    return GlyphAnnotations(
        ligatures=[LigatureMark(kind=LigatureKind.FI, char_span=(0, 2))],
        long_s_positions=[],
        swash=False,
        source="human",
    )


def test_word_pydantic_roundtrip_preserves_glyph_annotations():
    """TypeAdapter(Word).validate_python must NOT drop glyph_annotations (closes #180)."""
    adapter = TypeAdapter(Word)
    w = Word(
        text="fi",
        bounding_box=_bbox(),
        glyph_annotations=_ga_with_ligature(),
    )
    d = w.to_dict()
    # to_dict must include glyph_annotations
    assert "glyph_annotations" in d, "to_dict() did not serialize glyph_annotations"

    validated = adapter.validate_python(d)
    assert isinstance(validated, Word)
    assert validated.glyph_annotations is not None, (
        "pydantic validate_python dropped glyph_annotations (issue #180)"
    )
    assert validated.glyph_annotations == w.glyph_annotations


def test_word_pydantic_roundtrip_preserves_empty_glyph_annotations():
    """Empty GlyphAnnotations (reviewed-no-glyphs) must also survive round-trip."""
    adapter = TypeAdapter(Word)
    w = Word(
        text="hello",
        bounding_box=_bbox(),
        glyph_annotations=GlyphAnnotations(),  # reviewed; no glyphs
    )
    d = w.to_dict()
    validated = adapter.validate_python(d)
    assert validated.glyph_annotations is not None, (
        "pydantic validate_python dropped empty GlyphAnnotations"
    )
    assert validated.glyph_annotations == w.glyph_annotations


def test_word_pydantic_roundtrip_none_glyph_annotations_stays_none():
    """None glyph_annotations (unreviewed) must remain None after round-trip."""
    adapter = TypeAdapter(Word)
    w = Word(text="hello", bounding_box=_bbox(), glyph_annotations=None)
    d = w.to_dict()
    validated = adapter.validate_python(d)
    assert validated.glyph_annotations is None
