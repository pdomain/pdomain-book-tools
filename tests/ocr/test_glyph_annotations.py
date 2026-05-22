"""Tests for GlyphAnnotations, LigatureKind, and LigatureMark.

Spec: pd-book-tools/docs/specs/05-glyph-annotations.md
Issue: ConcaveTrillion/pd-book-tools#41
"""

from __future__ import annotations

import pytest

from pd_book_tools.ocr.glyph_annotations import (
    GlyphAnnotations,
    LigatureKind,
    LigatureMark,
)

# ---------------------------------------------------------------------------
# LigatureKind enum
# ---------------------------------------------------------------------------


def test_ligature_kind_values_are_strings():
    """LigatureKind is a str-valued Enum so JSON serialization yields bare strings."""
    assert LigatureKind.FI == "fi"
    assert LigatureKind.FL == "fl"
    assert LigatureKind.FF == "ff"
    assert LigatureKind.FFI == "ffi"
    assert LigatureKind.FFL == "ffl"
    assert LigatureKind.CT == "ct"
    assert LigatureKind.ST == "st"
    assert LigatureKind.LONG_S_T == "long_s_t"
    assert LigatureKind.LONG_S_S == "long_s_s"
    assert LigatureKind.LONG_S_I == "long_s_i"
    assert LigatureKind.SP == "sp"
    assert LigatureKind.QU == "qu"


def test_ligature_kind_is_str_subtype():
    assert isinstance(LigatureKind.FI, str)


def test_ligature_kind_from_string():
    assert LigatureKind("ct") is LigatureKind.CT


def test_ligature_kind_unknown_raises():
    with pytest.raises(ValueError):
        LigatureKind("unknown_value")


# ---------------------------------------------------------------------------
# LigatureMark
# ---------------------------------------------------------------------------


def test_ligature_mark_with_span():
    mark = LigatureMark(kind=LigatureKind.FI, char_span=(2, 4))
    assert mark.kind is LigatureKind.FI
    assert mark.char_span == (2, 4)


def test_ligature_mark_without_span():
    mark = LigatureMark(kind=LigatureKind.CT)
    assert mark.char_span is None


def test_ligature_mark_to_dict_with_span():
    mark = LigatureMark(kind=LigatureKind.CT, char_span=(2, 4))
    d = mark.to_dict()
    assert d == {"kind": "ct", "char_span": [2, 4]}


def test_ligature_mark_to_dict_without_span():
    mark = LigatureMark(kind=LigatureKind.ST)
    d = mark.to_dict()
    assert d == {"kind": "st", "char_span": None}


def test_ligature_mark_from_dict_with_span():
    mark = LigatureMark.from_dict({"kind": "fi", "char_span": [0, 2]})
    assert mark.kind is LigatureKind.FI
    assert mark.char_span == (0, 2)


def test_ligature_mark_from_dict_without_span():
    mark = LigatureMark.from_dict({"kind": "ct"})
    assert mark.kind is LigatureKind.CT
    assert mark.char_span is None


def test_ligature_mark_from_dict_unknown_kind_raises():
    with pytest.raises(ValueError):
        LigatureMark.from_dict({"kind": "bogus"})


def test_ligature_mark_roundtrip():
    mark = LigatureMark(kind=LigatureKind.LONG_S_T, char_span=(0, 2))
    assert LigatureMark.from_dict(mark.to_dict()) == mark


def test_ligature_mark_roundtrip_no_span():
    mark = LigatureMark(kind=LigatureKind.QU, char_span=None)
    assert LigatureMark.from_dict(mark.to_dict()) == mark


# ---------------------------------------------------------------------------
# GlyphAnnotations defaults and construction
# ---------------------------------------------------------------------------


def test_glyph_annotations_defaults():
    ga = GlyphAnnotations()
    assert ga.ligatures == []
    assert ga.long_s_positions == []
    assert ga.swash is False


def test_glyph_annotations_explicit():
    mark = LigatureMark(kind=LigatureKind.FI, char_span=(0, 2))
    ga = GlyphAnnotations(ligatures=[mark], long_s_positions=[3], swash=True)
    assert ga.ligatures == [mark]
    assert ga.long_s_positions == [3]
    assert ga.swash is True


def test_glyph_annotations_equality_empty():
    assert GlyphAnnotations() == GlyphAnnotations()


# ---------------------------------------------------------------------------
# GlyphAnnotations serialization
# ---------------------------------------------------------------------------


def test_glyph_annotations_to_dict_empty():
    ga = GlyphAnnotations()
    d = ga.to_dict()
    assert d == {"ligatures": [], "long_s_positions": [], "swash": False}


def test_glyph_annotations_to_dict_full():
    mark = LigatureMark(kind=LigatureKind.CT, char_span=(2, 4))
    ga = GlyphAnnotations(ligatures=[mark], long_s_positions=[0], swash=True)
    d = ga.to_dict()
    assert d == {
        "ligatures": [{"kind": "ct", "char_span": [2, 4]}],
        "long_s_positions": [0],
        "swash": True,
    }


def test_glyph_annotations_from_dict_empty():
    ga = GlyphAnnotations.from_dict(
        {"ligatures": [], "long_s_positions": [], "swash": False}
    )
    assert ga == GlyphAnnotations()


def test_glyph_annotations_from_dict_missing_keys_use_defaults():
    ga = GlyphAnnotations.from_dict({})
    assert ga == GlyphAnnotations()


def test_glyph_annotations_from_dict_full():
    d = {
        "ligatures": [{"kind": "long_s_t", "char_span": [0, 2]}],
        "long_s_positions": [0],
        "swash": False,
    }
    ga = GlyphAnnotations.from_dict(d)
    assert len(ga.ligatures) == 1
    assert ga.ligatures[0].kind is LigatureKind.LONG_S_T
    assert ga.ligatures[0].char_span == (0, 2)
    assert ga.long_s_positions == [0]
    assert ga.swash is False


def test_glyph_annotations_roundtrip_full():
    mark = LigatureMark(kind=LigatureKind.FFI, char_span=(1, 4))
    ga = GlyphAnnotations(ligatures=[mark], long_s_positions=[2], swash=True)
    assert GlyphAnnotations.from_dict(ga.to_dict()) == ga


def test_glyph_annotations_roundtrip_empty():
    ga = GlyphAnnotations()
    assert GlyphAnnotations.from_dict(ga.to_dict()) == ga


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _make_word(text: str, gt: str | None = None):
    """Helper: build a minimal Word-like object."""
    from pd_book_tools.geometry.bounding_box import BoundingBox
    from pd_book_tools.geometry.point import Point
    from pd_book_tools.ocr.word import Word

    bb = BoundingBox(top_left=Point(0, 0), bottom_right=Point(10, 10))
    word = Word(text=text, bounding_box=bb)
    word._ground_truth_text = gt if gt is not None else text
    return word


def test_validate_passes_clean_word():
    ga = GlyphAnnotations(
        ligatures=[LigatureMark(kind=LigatureKind.FI, char_span=(0, 2))],
        long_s_positions=[],
    )
    word = _make_word("find", "find")
    ga.validate(word)  # must not raise


def test_validate_gt_contains_ligature_codepoint_raises():
    """GT containing U+FB01 (fi ligature) must fail pre-validation."""
    ga = GlyphAnnotations()
    word = _make_word("fi", "ﬁnd")  # U+FB01 in GT
    with pytest.raises(ValueError, match="GT text contains banned codepoint"):
        ga.validate(word)


def test_validate_gt_contains_long_s_raises():
    """GT containing U+017F (long-s) must fail pre-validation."""
    ga = GlyphAnnotations()
    long_s_hall = "\u017fhall"  # U+017F + "hall"
    word = _make_word("shall", long_s_hall)
    with pytest.raises(ValueError, match="GT text contains banned codepoint"):
        ga.validate(word)


def test_validate_ligature_span_out_of_bounds_raises():
    ga = GlyphAnnotations(
        ligatures=[LigatureMark(kind=LigatureKind.FI, char_span=(0, 10))]
    )
    word = _make_word("fi", "fi")
    with pytest.raises(ValueError, match="char_span"):
        ga.validate(word)


def test_validate_ligature_span_empty_raises():
    """start == end is disallowed; None should be used for unknown location."""
    ga = GlyphAnnotations(
        ligatures=[LigatureMark(kind=LigatureKind.CT, char_span=(2, 2))]
    )
    word = _make_word("act", "act")
    with pytest.raises(ValueError, match="char_span"):
        ga.validate(word)


def test_validate_ligature_span_start_gt_end_raises():
    ga = GlyphAnnotations(
        ligatures=[LigatureMark(kind=LigatureKind.ST, char_span=(3, 1))]
    )
    word = _make_word("stand", "stand")
    with pytest.raises(ValueError, match="char_span"):
        ga.validate(word)


def test_validate_ligature_span_none_passes():
    """span=None means 'unknown location'; validation must accept it."""
    ga = GlyphAnnotations(
        ligatures=[LigatureMark(kind=LigatureKind.CT, char_span=None)]
    )
    word = _make_word("act", "act")
    ga.validate(word)  # must not raise


def test_validate_long_s_position_oob_raises():
    ga = GlyphAnnotations(long_s_positions=[99])
    word = _make_word("shall", "shall")
    with pytest.raises(ValueError, match="long_s_positions"):
        ga.validate(word)


def test_validate_long_s_position_wrong_char_raises():
    """Index pointing at a non-s character is a caller bug."""
    ga = GlyphAnnotations(long_s_positions=[1])
    word = _make_word("shall", "shall")
    with pytest.raises(ValueError, match="long_s_positions"):
        ga.validate(word)


def test_validate_long_s_position_correct_s_passes():
    ga = GlyphAnnotations(long_s_positions=[0])
    word = _make_word("shall", "shall")
    ga.validate(word)  # index 0 = 's', must not raise


def test_validate_long_s_position_uppercase_s_passes():
    """Upper-case S is also a valid normalized form."""
    ga = GlyphAnnotations(long_s_positions=[0])
    word = _make_word("Shall", "Shall")
    ga.validate(word)  # index 0 = 'S', must not raise


# ---------------------------------------------------------------------------
# Word integration: glyph_annotations field
# ---------------------------------------------------------------------------


def test_word_glyph_annotations_defaults_none():
    """A freshly constructed Word should have glyph_annotations = None."""
    word = _make_word("stand")
    assert word.glyph_annotations is None


def test_word_glyph_annotations_assignment():
    word = _make_word("stand")
    ga = GlyphAnnotations(
        ligatures=[LigatureMark(kind=LigatureKind.ST, char_span=(0, 2))]
    )
    word.glyph_annotations = ga
    assert word.glyph_annotations is ga


def test_word_to_dict_omits_glyph_annotations_when_none():
    word = _make_word("stand")
    assert word.glyph_annotations is None
    d = word.to_dict()
    assert "glyph_annotations" not in d


def test_word_to_dict_includes_glyph_annotations_when_set():
    word = _make_word("stand", "stand")
    ga = GlyphAnnotations(
        ligatures=[LigatureMark(kind=LigatureKind.ST, char_span=(0, 2))]
    )
    word.glyph_annotations = ga
    d = word.to_dict()
    assert "glyph_annotations" in d
    assert d["glyph_annotations"]["ligatures"][0]["kind"] == "st"


def test_word_to_dict_includes_empty_glyph_annotations():
    """Empty GlyphAnnotations() != None — emit-when-non-None policy."""
    word = _make_word("stand")
    word.glyph_annotations = GlyphAnnotations()
    d = word.to_dict()
    assert "glyph_annotations" in d
    assert d["glyph_annotations"] == {
        "ligatures": [],
        "long_s_positions": [],
        "swash": False,
    }


def test_word_from_dict_roundtrip_without_glyph_annotations():
    """Old-style dicts (no glyph_annotations key) load with glyph_annotations=None."""
    from pd_book_tools.ocr.word import Word

    word = _make_word("stand")
    d = word.to_dict()
    assert "glyph_annotations" not in d
    word2 = Word.from_dict(d)
    assert word2.glyph_annotations is None


def test_word_from_dict_roundtrip_with_glyph_annotations():
    from pd_book_tools.ocr.word import Word

    word = _make_word("stand", "stand")
    ga = GlyphAnnotations(
        ligatures=[LigatureMark(kind=LigatureKind.ST, char_span=(0, 2))],
        long_s_positions=[],
        swash=False,
    )
    word.glyph_annotations = ga
    d = word.to_dict()
    word2 = Word.from_dict(d)
    assert word2.glyph_annotations == ga


def test_word_from_dict_roundtrip_with_empty_glyph_annotations():
    """Empty-but-set GlyphAnnotations() round-trips correctly (not collapsed to None)."""
    from pd_book_tools.ocr.word import Word

    word = _make_word("stand")
    word.glyph_annotations = GlyphAnnotations()
    d = word.to_dict()
    word2 = Word.from_dict(d)
    assert word2.glyph_annotations == GlyphAnnotations()
    assert word2.glyph_annotations is not None
