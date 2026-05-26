"""Tests for GlyphAnnotations, LigatureKind, and LigatureMark.

Spec: pdomain-book-tools/docs/specs/05-glyph-annotations.md
Issue: pdomain/pdomain-book-tools#41
Plan: pdomain/pdomain-book-tools#163
"""

from __future__ import annotations

import pytest

from pdomain_book_tools.ocr.glyph_annotations import (
    GlyphAnnotations,
    LigatureKind,
    LigatureMark,
)

# ---------------------------------------------------------------------------
# LigatureKind enum — UPPERCASE values (Phase 1, plan #163)
# ---------------------------------------------------------------------------


def test_ligature_kind_values_are_uppercase_strings():
    """LigatureKind values are now UPPERCASE per plan #163 (Phase 1)."""
    assert LigatureKind.FI == "FI"
    assert LigatureKind.FL == "FL"
    assert LigatureKind.FF == "FF"
    assert LigatureKind.FFI == "FFI"
    assert LigatureKind.FFL == "FFL"
    assert LigatureKind.CT == "CT"
    assert LigatureKind.ST == "ST"
    # Renamed from LONG_S_T to LONG_ST with uppercase value
    assert LigatureKind.LONG_ST == "LONG_ST"
    assert LigatureKind.LONG_S_S == "LONG_S_S"
    assert LigatureKind.LONG_S_I == "LONG_S_I"
    assert LigatureKind.SP == "SP"
    assert LigatureKind.QU == "QU"
    # New members from SPA spec 20 §3
    assert LigatureKind.OE == "OE"
    assert LigatureKind.AE == "AE"


def test_ligature_kind_long_s_t_member_renamed_to_long_st():
    """LONG_S_T was renamed to LONG_ST (plan #163 decision 2)."""
    assert hasattr(LigatureKind, "LONG_ST")
    # Old name should no longer exist
    assert not hasattr(LigatureKind, "LONG_S_T")


def test_ligature_kind_new_members_oe_ae():
    """OE and AE are new members added per SPA spec 20 §3 (plan #163 decision 4)."""
    assert LigatureKind.OE == "OE"
    assert LigatureKind.AE == "AE"


def test_ligature_kind_is_str_subtype():
    assert isinstance(LigatureKind.FI, str)


def test_ligature_kind_from_uppercase_string():
    """Direct construction from uppercase value works."""
    assert LigatureKind("CT") is LigatureKind.CT
    assert LigatureKind("LONG_ST") is LigatureKind.LONG_ST
    assert LigatureKind("OE") is LigatureKind.OE
    assert LigatureKind("AE") is LigatureKind.AE


def test_ligature_kind_unknown_raises():
    with pytest.raises(ValueError):
        LigatureKind("unknown_value")


def test_ligature_kind_member_count():
    """All 14 expected members are present (12 original renamed/uppercased + 2 new)."""
    member_names = {m.name for m in LigatureKind}
    expected = {
        "FI",
        "FL",
        "FF",
        "FFI",
        "FFL",
        "CT",
        "ST",
        "LONG_ST",
        "LONG_S_S",
        "LONG_S_I",
        "SP",
        "QU",
        "OE",
        "AE",
    }
    assert member_names == expected


# ---------------------------------------------------------------------------
# LigatureMark — to_dict emits UPPERCASE values
# ---------------------------------------------------------------------------


def test_ligature_mark_with_span():
    mark = LigatureMark(kind=LigatureKind.FI, char_span=(2, 4))
    assert mark.kind is LigatureKind.FI
    assert mark.char_span == (2, 4)


def test_ligature_mark_without_span():
    mark = LigatureMark(kind=LigatureKind.CT)
    assert mark.char_span is None


def test_ligature_mark_to_dict_emits_uppercase_kind():
    """to_dict always emits uppercase kind value (plan #163 Phase 1 step 6)."""
    mark = LigatureMark(kind=LigatureKind.CT, char_span=(2, 4))
    d = mark.to_dict()
    assert d == {"kind": "CT", "char_span": [2, 4]}


def test_ligature_mark_to_dict_without_span_emits_uppercase():
    mark = LigatureMark(kind=LigatureKind.ST)
    d = mark.to_dict()
    assert d == {"kind": "ST", "char_span": None}


def test_ligature_mark_to_dict_long_st_emits_new_value():
    """LONG_ST renamed member emits 'LONG_ST' not 'long_s_t'."""
    mark = LigatureMark(kind=LigatureKind.LONG_ST, char_span=(0, 2))
    d = mark.to_dict()
    assert d["kind"] == "LONG_ST"


def test_ligature_mark_to_dict_new_members():
    """OE and AE new members serialize correctly."""
    assert LigatureMark(kind=LigatureKind.OE).to_dict()["kind"] == "OE"
    assert LigatureMark(kind=LigatureKind.AE).to_dict()["kind"] == "AE"


def test_ligature_mark_from_dict_uppercase_kind():
    """from_dict accepts new uppercase values."""
    mark = LigatureMark.from_dict({"kind": "FI", "char_span": [0, 2]})
    assert mark.kind is LigatureKind.FI
    assert mark.char_span == (0, 2)


def test_ligature_mark_from_dict_without_span():
    mark = LigatureMark.from_dict({"kind": "CT"})
    assert mark.kind is LigatureKind.CT
    assert mark.char_span is None


def test_ligature_mark_from_dict_unknown_kind_raises():
    with pytest.raises(ValueError):
        LigatureMark.from_dict({"kind": "bogus"})


def test_ligature_mark_roundtrip():
    mark = LigatureMark(kind=LigatureKind.LONG_ST, char_span=(0, 2))
    assert LigatureMark.from_dict(mark.to_dict()) == mark


def test_ligature_mark_roundtrip_no_span():
    mark = LigatureMark(kind=LigatureKind.QU, char_span=None)
    assert LigatureMark.from_dict(mark.to_dict()) == mark


# ---------------------------------------------------------------------------
# Phase 2 — Migration shim: legacy lowercase values still deserialize
# ---------------------------------------------------------------------------


def test_ligature_kind_legacy_migration_roundtrip():
    """Old lowercase kind values from pre-#163 snapshots still deserialize.

    This is the migration shim (plan #163 Phase 2). Old JSON had 'fi', 'ct', etc.
    After migration, from_dict must accept them and map to the new uppercase members.
    """
    # All original lowercase values must still deserialize
    assert LigatureMark.from_dict({"kind": "fi"}).kind is LigatureKind.FI
    assert LigatureMark.from_dict({"kind": "fl"}).kind is LigatureKind.FL
    assert LigatureMark.from_dict({"kind": "ff"}).kind is LigatureKind.FF
    assert LigatureMark.from_dict({"kind": "ffi"}).kind is LigatureKind.FFI
    assert LigatureMark.from_dict({"kind": "ffl"}).kind is LigatureKind.FFL
    assert LigatureMark.from_dict({"kind": "ct"}).kind is LigatureKind.CT
    assert LigatureMark.from_dict({"kind": "st"}).kind is LigatureKind.ST
    assert LigatureMark.from_dict({"kind": "long_s_s"}).kind is LigatureKind.LONG_S_S
    assert LigatureMark.from_dict({"kind": "long_s_i"}).kind is LigatureKind.LONG_S_I
    assert LigatureMark.from_dict({"kind": "sp"}).kind is LigatureKind.SP
    assert LigatureMark.from_dict({"kind": "qu"}).kind is LigatureKind.QU


def test_ligature_kind_legacy_long_s_t_name_migrates_to_long_st():
    """Old 'long_s_t' value (old name) maps to LigatureKind.LONG_ST."""
    mark = LigatureMark.from_dict({"kind": "long_s_t"})
    assert mark.kind is LigatureKind.LONG_ST


def test_ligature_kind_legacy_long_s_t_uppercase_old_name_migrates():
    """Old 'LONG_S_T' uppercase enum value (old name) maps to LigatureKind.LONG_ST."""
    mark = LigatureMark.from_dict({"kind": "LONG_S_T"})
    assert mark.kind is LigatureKind.LONG_ST


def test_legacy_value_roundtrip_after_migration():
    """Loading a legacy lowercase dict and re-serializing emits new uppercase value."""
    old_dict = {"kind": "ct", "char_span": [2, 4]}
    mark = LigatureMark.from_dict(old_dict)
    assert mark.kind is LigatureKind.CT
    new_dict = mark.to_dict()
    assert new_dict == {"kind": "CT", "char_span": [2, 4]}


def test_legacy_long_s_t_roundtrip():
    """Loading legacy 'long_s_t' value, re-serializing emits 'LONG_ST'."""
    old_dict = {"kind": "long_s_t", "char_span": [0, 2]}
    mark = LigatureMark.from_dict(old_dict)
    assert mark.kind is LigatureKind.LONG_ST
    new_dict = mark.to_dict()
    assert new_dict == {"kind": "LONG_ST", "char_span": [0, 2]}


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
    assert d == {
        "ligatures": [],
        "long_s_positions": [],
        "swash": False,
        "source": "human",
    }


def test_glyph_annotations_to_dict_full():
    """to_dict emits uppercase kind values."""
    mark = LigatureMark(kind=LigatureKind.CT, char_span=(2, 4))
    ga = GlyphAnnotations(ligatures=[mark], long_s_positions=[0], swash=True)
    d = ga.to_dict()
    assert d == {
        "ligatures": [{"kind": "CT", "char_span": [2, 4]}],
        "long_s_positions": [0],
        "swash": True,
        "source": "human",
    }


# ---------------------------------------------------------------------------
# GlyphAnnotations.source provenance field (spec 20-glyph-annotations.md S3,
# ADR D-044 -- object-level provenance)
# ---------------------------------------------------------------------------


def test_glyph_annotations_source_default_is_human():
    assert GlyphAnnotations().source == "human"


@pytest.mark.parametrize("src", ["human", "predicted", "human_confirmed"])
def test_glyph_annotations_source_accepts_valid_values(src):
    ga = GlyphAnnotations(source=src)
    assert ga.source == src
    assert ga.to_dict()["source"] == src


def test_glyph_annotations_source_invalid_value_raises():
    with pytest.raises(ValueError):
        GlyphAnnotations(source="robot")


def test_glyph_annotations_from_dict_missing_source_defaults_to_human():
    ga = GlyphAnnotations.from_dict(
        {"ligatures": [], "long_s_positions": [], "swash": False}
    )
    assert ga.source == "human"


def test_glyph_annotations_from_dict_reads_source():
    ga = GlyphAnnotations.from_dict(
        {
            "ligatures": [],
            "long_s_positions": [],
            "swash": False,
            "source": "predicted",
        }
    )
    assert ga.source == "predicted"


def test_glyph_annotations_from_dict_unknown_source_raises():
    with pytest.raises(ValueError):
        GlyphAnnotations.from_dict(
            {
                "ligatures": [],
                "long_s_positions": [],
                "swash": False,
                "source": "bogus",
            }
        )


def test_glyph_annotations_source_roundtrip():
    ga = GlyphAnnotations(source="human_confirmed", swash=True)
    assert GlyphAnnotations.from_dict(ga.to_dict()) == ga


def test_glyph_annotations_from_dict_empty():
    ga = GlyphAnnotations.from_dict(
        {"ligatures": [], "long_s_positions": [], "swash": False}
    )
    assert ga == GlyphAnnotations()


def test_glyph_annotations_from_dict_missing_keys_use_defaults():
    ga = GlyphAnnotations.from_dict({})
    assert ga == GlyphAnnotations()


def test_glyph_annotations_from_dict_full():
    """from_dict with legacy lowercase kind values still works via migration shim."""
    d = {
        "ligatures": [{"kind": "long_s_t", "char_span": [0, 2]}],
        "long_s_positions": [0],
        "swash": False,
    }
    ga = GlyphAnnotations.from_dict(d)
    assert len(ga.ligatures) == 1
    # Legacy 'long_s_t' maps to LONG_ST (renamed member)
    assert ga.ligatures[0].kind is LigatureKind.LONG_ST
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
    from pdomain_book_tools.geometry.bounding_box import BoundingBox
    from pdomain_book_tools.geometry.point import Point
    from pdomain_book_tools.ocr.word import Word

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
    """Word.to_dict now emits uppercase kind values."""
    word = _make_word("stand", "stand")
    ga = GlyphAnnotations(
        ligatures=[LigatureMark(kind=LigatureKind.ST, char_span=(0, 2))]
    )
    word.glyph_annotations = ga
    d = word.to_dict()
    assert "glyph_annotations" in d
    assert d["glyph_annotations"]["ligatures"][0]["kind"] == "ST"


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
        "source": "human",
    }


def test_word_from_dict_roundtrip_without_glyph_annotations():
    """Old-style dicts (no glyph_annotations key) load with glyph_annotations=None."""
    from pdomain_book_tools.ocr.word import Word

    word = _make_word("stand")
    d = word.to_dict()
    assert "glyph_annotations" not in d
    word2 = Word.from_dict(d)
    assert word2.glyph_annotations is None


def test_word_from_dict_roundtrip_with_glyph_annotations():
    from pdomain_book_tools.ocr.word import Word

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
    from pdomain_book_tools.ocr.word import Word

    word = _make_word("stand")
    word.glyph_annotations = GlyphAnnotations()
    d = word.to_dict()
    word2 = Word.from_dict(d)
    assert word2.glyph_annotations == GlyphAnnotations()
    assert word2.glyph_annotations is not None
