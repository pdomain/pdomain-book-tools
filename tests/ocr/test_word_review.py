"""Tests for Word.review (optional ReviewMetadata cluster)."""

from __future__ import annotations

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.review import ReviewMetadata
from pd_book_tools.ocr.word import Word


def _bbox():
    # Use whatever shape BoundingBox accepts in this codebase — keep tests
    # consistent with existing Word fixtures.
    return BoundingBox.from_dict(
        {
            "top_left": {"x": 0, "y": 0},
            "bottom_right": {"x": 10, "y": 10},
        }
    )


def test_word_review_defaults_to_none():
    w = Word(text="hello", bounding_box=_bbox())
    assert w.review is None


def test_word_review_accepts_metadata():
    rm = ReviewMetadata(validated=True, reviewer_note="ok")
    w = Word(text="hello", bounding_box=_bbox(), review=rm)
    assert w.review is rm


def test_word_to_dict_omits_review_key_when_none():
    w = Word(text="hello", bounding_box=_bbox())
    d = w.to_dict()
    assert "review" not in d


def test_word_to_dict_includes_review_when_set():
    rm = ReviewMetadata(validated=True, reviewer_note="ok", flagged_for_attention=True)
    w = Word(text="hello", bounding_box=_bbox(), review=rm)
    d = w.to_dict()
    assert d["review"] == {
        "validated": True,
        "reviewer_note": "ok",
        "flagged_for_attention": True,
    }


def test_word_from_dict_without_review_key():
    base = {
        "type": "Word",
        "text": "hello",
        "bounding_box": _bbox().to_dict(),
    }
    w = Word.from_dict(base)
    assert w.review is None


def test_word_from_dict_with_review_key():
    base = {
        "type": "Word",
        "text": "hello",
        "bounding_box": _bbox().to_dict(),
        "review": {
            "validated": True,
            "reviewer_note": "n",
            "flagged_for_attention": False,
        },
    }
    w = Word.from_dict(base)
    assert w.review == ReviewMetadata(
        validated=True,
        reviewer_note="n",
        flagged_for_attention=False,
    )


def test_word_review_roundtrip():
    rm = ReviewMetadata(validated=True, reviewer_note="hi")
    w = Word(text="hello", bounding_box=_bbox(), review=rm)
    w2 = Word.from_dict(w.to_dict())
    assert w2.review == rm
