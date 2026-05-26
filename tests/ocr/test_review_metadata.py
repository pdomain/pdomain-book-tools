"""Tests for the ReviewMetadata dataclass on pdomain_book_tools.ocr.review."""

from __future__ import annotations

from pdomain_book_tools.ocr.review import ReviewMetadata


def test_review_metadata_defaults():
    rm = ReviewMetadata()
    assert rm.validated is False
    assert rm.reviewer_note is None
    assert rm.flagged_for_attention is False


def test_review_metadata_explicit_values():
    rm = ReviewMetadata(
        validated=True,
        reviewer_note="checked against original",
        flagged_for_attention=False,
    )
    assert rm.validated is True
    assert rm.reviewer_note == "checked against original"
    assert rm.flagged_for_attention is False


def test_review_metadata_to_dict_full():
    rm = ReviewMetadata(
        validated=True,
        reviewer_note="ok",
        flagged_for_attention=True,
    )
    assert rm.to_dict() == {
        "validated": True,
        "reviewer_note": "ok",
        "flagged_for_attention": True,
    }


def test_review_metadata_to_dict_defaults_omit_none_note():
    rm = ReviewMetadata()
    d = rm.to_dict()
    # validated and flagged_for_attention always present (bools);
    # reviewer_note is included as None so consumers can disambiguate
    # "absent field" vs "explicit null" — the rule: to_dict is the wire shape,
    # absent fields handled at the parent (Word/Block/Page) level by
    # omitting `review` entirely when None.
    assert d == {
        "validated": False,
        "reviewer_note": None,
        "flagged_for_attention": False,
    }


def test_review_metadata_from_dict_full():
    rm = ReviewMetadata.from_dict(
        {
            "validated": True,
            "reviewer_note": "n",
            "flagged_for_attention": True,
        }
    )
    assert rm == ReviewMetadata(
        validated=True,
        reviewer_note="n",
        flagged_for_attention=True,
    )


def test_review_metadata_from_dict_missing_keys_use_defaults():
    rm = ReviewMetadata.from_dict({"validated": True})
    assert rm == ReviewMetadata(
        validated=True,
        reviewer_note=None,
        flagged_for_attention=False,
    )


def test_review_metadata_roundtrip():
    rm = ReviewMetadata(validated=True, reviewer_note="hi", flagged_for_attention=True)
    assert ReviewMetadata.from_dict(rm.to_dict()) == rm
