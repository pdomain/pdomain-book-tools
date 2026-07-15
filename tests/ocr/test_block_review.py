"""Tests for Block.review (optional ReviewMetadata cluster).

Block covers both block-scope and line-scope review semantics, since
'Line' in the pdomain-book-tools model is a Block with block_category=LINE."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pdomain_book_tools.ocr.review import ReviewMetadata

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pdomain_book_tools.ocr.word import Word


def _bbox() -> BoundingBox:
    return BoundingBox.from_dict(
        {
            "top_left": {"x": 0, "y": 0, "is_normalized": False},
            "bottom_right": {"x": 100, "y": 50, "is_normalized": False},
            "is_normalized": False,
        }
    )


def _line_block(words: Sequence[Word] | None = None) -> Block:
    return Block(
        items=list(words or []),
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
        bounding_box=_bbox(),
    )


def test_block_review_defaults_to_none() -> None:
    b = _line_block()
    assert b.review is None


def test_block_review_accepts_metadata() -> None:
    rm = ReviewMetadata(validated=True)
    b = _line_block()
    b.review = rm
    assert b.review is rm


def test_block_to_dict_omits_review_key_when_none() -> None:
    b = _line_block()
    d = b.to_dict()
    assert "review" not in d


def test_block_to_dict_includes_review_when_set() -> None:
    rm = ReviewMetadata(validated=True, reviewer_note="line ok")
    b = _line_block()
    b.review = rm
    d = b.to_dict()
    assert d["review"] == {
        "validated": True,
        "reviewer_note": "line ok",
        "flagged_for_attention": False,
    }


def test_block_from_dict_without_review_key() -> None:
    b = _line_block()
    base = b.to_dict()
    assert "review" not in base
    b2 = Block.from_dict(base)
    assert b2.review is None


def test_block_review_roundtrip() -> None:
    rm = ReviewMetadata(validated=True, reviewer_note="n")
    b = _line_block()
    b.review = rm
    b2 = Block.from_dict(b.to_dict())
    assert b2.review == rm
