"""Tests for Block.review (optional ReviewMetadata cluster).

Block covers both block-scope and line-scope review semantics, since
'Line' in the pd-book-tools model is a Block with block_category=LINE."""

from __future__ import annotations

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.review import ReviewMetadata


def _bbox():
    return BoundingBox.from_dict(
        {
            "top_left": {"x": 0, "y": 0},
            "bottom_right": {"x": 100, "y": 50},
        }
    )


def _line_block(words=None) -> Block:
    return Block(
        items=list(words or []),
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
        bounding_box=_bbox(),
    )


def test_block_review_defaults_to_none():
    b = _line_block()
    assert b.review is None


def test_block_review_accepts_metadata():
    rm = ReviewMetadata(validated=True)
    b = _line_block()
    b.review = rm
    assert b.review is rm


def test_block_to_dict_omits_review_key_when_none():
    b = _line_block()
    d = b.to_dict()
    assert "review" not in d


def test_block_to_dict_includes_review_when_set():
    rm = ReviewMetadata(validated=True, reviewer_note="line ok")
    b = _line_block()
    b.review = rm
    d = b.to_dict()
    assert d["review"] == {
        "validated": True,
        "reviewer_note": "line ok",
        "flagged_for_attention": False,
    }


def test_block_from_dict_without_review_key():
    b = _line_block()
    base = b.to_dict()
    assert "review" not in base
    b2 = Block.from_dict(base)
    assert b2.review is None


def test_block_review_roundtrip():
    rm = ReviewMetadata(validated=True, reviewer_note="n")
    b = _line_block()
    b.review = rm
    b2 = Block.from_dict(b.to_dict())
    assert b2.review == rm
