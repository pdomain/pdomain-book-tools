"""Tests for Page.page_kind (typed, validated page-kind field)."""

from __future__ import annotations

import pytest
from pdomain_book_contracts.annotation import PageKind

from pdomain_book_tools.ocr.page import Page


def _minimal_page() -> Page:
    """Build a minimal Page suitable for page_kind-field tests."""
    return Page(width=100, height=100, page_index=0, blocks=[])


def test_page_kind_defaults_to_none():
    p = _minimal_page()
    assert p.page_kind is None


def test_page_kind_accepts_a_page_kind_member():
    p = _minimal_page()
    p.page_kind = PageKind.CHAPTER_OPENING
    assert p.page_kind is PageKind.CHAPTER_OPENING


def test_page_to_dict_omits_page_kind_key_when_none():
    p = _minimal_page()
    d = p.to_dict()
    assert "page_kind" not in d


def test_page_to_dict_includes_page_kind_when_set():
    p = _minimal_page()
    p.page_kind = PageKind.TITLE_PAGE
    d = p.to_dict()
    assert d["page_kind"] == "title page"


def test_page_kind_roundtrip():
    p = _minimal_page()
    p.page_kind = PageKind.INDEX
    p2 = Page.from_dict(p.to_dict())
    assert p2.page_kind is PageKind.INDEX


def test_a_stored_page_without_page_kind_still_loads():
    """A page written before this field existed must keep loading."""
    p = _minimal_page()
    d = p.to_dict()
    assert "page_kind" not in d
    p2 = Page.from_dict(d)
    assert p2.page_kind is None


def test_an_invalid_stored_page_kind_raises():
    p = _minimal_page()
    d = p.to_dict()
    d["page_kind"] = "not-a-real-kind"
    with pytest.raises(ValueError, match="not-a-real-kind"):
        Page.from_dict(d)


def test_page_kind_survives_scale():
    p = _minimal_page()
    p.page_kind = PageKind.BODY
    scaled = p.scale(200, 200)
    assert scaled.page_kind is PageKind.BODY
