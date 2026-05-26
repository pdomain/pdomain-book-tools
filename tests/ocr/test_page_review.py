"""Tests for Page.review (optional ReviewMetadata cluster)."""

from __future__ import annotations

from pdomain_book_tools.ocr.page import Page
from pdomain_book_tools.ocr.review import ReviewMetadata


def _minimal_page() -> Page:
    """Build a minimal Page suitable for review-field tests."""
    return Page(width=100, height=100, page_index=0, blocks=[])


def test_page_review_defaults_to_none():
    p = _minimal_page()
    assert p.review is None


def test_page_review_accepts_metadata():
    rm = ReviewMetadata(validated=True, reviewer_note="page ok")
    p = _minimal_page()
    p.review = rm
    assert p.review is rm


def test_page_to_dict_omits_review_key_when_none():
    p = _minimal_page()
    d = p.to_dict()
    assert "review" not in d


def test_page_to_dict_includes_review_when_set():
    rm = ReviewMetadata(validated=True, flagged_for_attention=True)
    p = _minimal_page()
    p.review = rm
    d = p.to_dict()
    assert d["review"] == {
        "validated": True,
        "reviewer_note": None,
        "flagged_for_attention": True,
    }


def test_page_review_roundtrip():
    rm = ReviewMetadata(validated=True, reviewer_note="n", flagged_for_attention=True)
    p = _minimal_page()
    p.review = rm
    p2 = Page.from_dict(p.to_dict())
    assert p2.review == rm
