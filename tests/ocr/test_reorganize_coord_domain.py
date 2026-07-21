"""Dual-domain unit matrix for reorganize band classify and mixed-line Y gap.

Plan A1 / issue reorganize-coord-domain-thresholds: the same synthetic page in
normalized [0, 1] coordinates and in pixel WxH must produce identical role
outcomes. Absolute unit-space thresholds must scale with the coordinate domain.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.geometry.point import Point
from pdomain_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pdomain_book_tools.ocr.reorganize_page_utils import (
    _classify_row_block,
    split_mixed_content_lines,
)
from pdomain_book_tools.ocr.word import Word

if TYPE_CHECKING:
    from collections.abc import Sequence
PAGE_W = 1000
PAGE_H = 2000


def _bbox(
    left: float,
    top: float,
    right: float,
    bottom: float,
    *,
    normalized: bool,
) -> BoundingBox:
    return BoundingBox(
        top_left=Point(left, top, is_normalized=normalized),
        bottom_right=Point(right, bottom, is_normalized=normalized),
        is_normalized=normalized,
    )


def _word(
    text: str,
    left: float,
    top: float,
    right: float,
    bottom: float,
    *,
    normalized: bool,
) -> Word:
    return Word(
        text=text,
        bounding_box=_bbox(left, top, right, bottom, normalized=normalized),
        ocr_confidence=0.9,
    )


def _line(
    words: Sequence[Word],
    *,
    normalized: bool,
) -> Block:
    line = Block(
        items=list(words),
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )
    # Recompute so line bbox matches domain.
    if line.bounding_box is not None:
        assert line.bounding_box.is_normalized is normalized
    return line


def _row_block(lines: Sequence[Block]) -> Block:
    return Block(
        items=list(lines),
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.BLOCK,
    )


def _scale(value: float, *, normalized: bool, axis: str) -> float:
    """Map a unit-space fraction into the target coordinate domain."""
    if normalized:
        return value
    if axis == "x":
        return value * PAGE_W
    return value * PAGE_H


def _header_row(*, normalized: bool) -> Block:
    # Near top of image (y ~ 0.04) and of OCR extent.
    y0 = _scale(0.04, normalized=normalized, axis="y")
    y1 = _scale(0.07, normalized=normalized, axis="y")
    x0 = _scale(0.20, normalized=normalized, axis="x")
    x1 = _scale(0.80, normalized=normalized, axis="x")
    words = [_word("HEADER", x0, y0, x1, y1, normalized=normalized)]
    return _row_block([_line(words, normalized=normalized)])


def _footer_row(*, normalized: bool) -> Block:
    y0 = _scale(0.93, normalized=normalized, axis="y")
    y1 = _scale(0.97, normalized=normalized, axis="y")
    x0 = _scale(0.30, normalized=normalized, axis="x")
    x1 = _scale(0.70, normalized=normalized, axis="x")
    words = [_word("42", x0, y0, x1, y1, normalized=normalized)]
    return _row_block([_line(words, normalized=normalized)])


def _body_row(*, normalized: bool) -> Block:
    y0 = _scale(0.40, normalized=normalized, axis="y")
    y1 = _scale(0.44, normalized=normalized, axis="y")
    x0 = _scale(0.15, normalized=normalized, axis="x")
    x1 = _scale(0.85, normalized=normalized, axis="x")
    words = [_word("body", x0, y0, x1, y1, normalized=normalized)]
    return _row_block([_line(words, normalized=normalized)])


def _sidenote_left_row(*, normalized: bool) -> Block:
    y0 = _scale(0.45, normalized=normalized, axis="y")
    y1 = _scale(0.55, normalized=normalized, axis="y")
    x0 = _scale(0.02, normalized=normalized, axis="x")
    x1 = _scale(0.10, normalized=normalized, axis="x")
    words = [_word("note", x0, y0, x1, y1, normalized=normalized)]
    return _row_block([_line(words, normalized=normalized)])


def _classify(
    block: Block,
    *,
    body_min_x: float,
    body_max_x: float,
    ocr_min_y: float,
    ocr_max_y: float,
    avg_line_h: float,
    median_line_w: float,
) -> str | None:
    return _classify_row_block(
        block,
        PAGE_W,
        PAGE_H,
        body_min_x,
        body_max_x,
        median_line_w,
        ocr_min_y,
        ocr_max_y,
        avg_line_h,
    )


@pytest.mark.parametrize("normalized", [True, False], ids=["normalized", "pixel"])
def test_classify_header_footer_body_roles_match_domain(normalized: bool) -> None:
    """Header near top and footer near bottom must classify correctly in both domains."""
    header = _header_row(normalized=normalized)
    footer = _footer_row(normalized=normalized)
    body = _body_row(normalized=normalized)

    body_min_x = _scale(0.15, normalized=normalized, axis="x")
    body_max_x = _scale(0.85, normalized=normalized, axis="x")
    ocr_min_y = _scale(0.04, normalized=normalized, axis="y")
    ocr_max_y = _scale(0.97, normalized=normalized, axis="y")
    avg_line_h = _scale(0.03, normalized=normalized, axis="y")
    median_line_w = _scale(0.70, normalized=normalized, axis="x")

    assert (
        _classify(
            header,
            body_min_x=body_min_x,
            body_max_x=body_max_x,
            ocr_min_y=ocr_min_y,
            ocr_max_y=ocr_max_y,
            avg_line_h=avg_line_h,
            median_line_w=median_line_w,
        )
        == "page header"
    )
    assert (
        _classify(
            footer,
            body_min_x=body_min_x,
            body_max_x=body_max_x,
            ocr_min_y=ocr_min_y,
            ocr_max_y=ocr_max_y,
            avg_line_h=avg_line_h,
            median_line_w=median_line_w,
        )
        == "page footer"
    )
    assert (
        _classify(
            body,
            body_min_x=body_min_x,
            body_max_x=body_max_x,
            ocr_min_y=ocr_min_y,
            ocr_max_y=ocr_max_y,
            avg_line_h=avg_line_h,
            median_line_w=median_line_w,
        )
        is None
    )


def test_dual_domain_matrix_identical_role_outcomes() -> None:
    """Normalized [0,1] and pixel WxH pages yield the same role labels."""
    cases = (
        ("header", _header_row),
        ("footer", _footer_row),
        ("body", _body_row),
        ("sidenote_left", _sidenote_left_row),
    )
    roles: dict[str, dict[str, str | None]] = {}
    for domain_name, normalized in (("normalized", True), ("pixel", False)):
        body_min_x = _scale(0.15, normalized=normalized, axis="x")
        body_max_x = _scale(0.85, normalized=normalized, axis="x")
        ocr_min_y = _scale(0.04, normalized=normalized, axis="y")
        ocr_max_y = _scale(0.97, normalized=normalized, axis="y")
        avg_line_h = _scale(0.03, normalized=normalized, axis="y")
        median_line_w = _scale(0.70, normalized=normalized, axis="x")
        roles[domain_name] = {}
        for case_name, builder in cases:
            block = builder(normalized=normalized)
            roles[domain_name][case_name] = _classify(
                block,
                body_min_x=body_min_x,
                body_max_x=body_max_x,
                ocr_min_y=ocr_min_y,
                ocr_max_y=ocr_max_y,
                avg_line_h=avg_line_h,
                median_line_w=median_line_w,
            )

    assert roles["normalized"] == roles["pixel"]
    assert roles["normalized"]["header"] == "page header"
    assert roles["normalized"]["footer"] == "page footer"
    assert roles["normalized"]["body"] is None
    assert roles["normalized"]["sidenote_left"] == "sidenote left"


def _mixed_gap_line(y: float, *, height_left: float, height_right: float) -> Block:
    """Line with ≥4 words, large mid gap, height shift, and continuation cue.

    Satisfies ``split_line_by_gap_and_word_height`` guards so mixed-content
    splitting engages; used to exercise preferred-split Y continuity.
    """
    # Left side: taller body words; right side: shorter caption words.
    # Gap mid ~ 550; height ratio > 1.20; left ends with comma for continuation.
    words = [
        _word("Body,", 100, y, 180, y + height_left, normalized=False),
        _word("left", 190, y, 280, y + height_left, normalized=False),
        _word("cap", 700, y, 780, y + height_right, normalized=False),
        _word("right", 790, y, 900, y + height_right, normalized=False),
    ]
    return Block(
        items=words,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )


def test_mixed_content_y_gap_scales_with_pixel_domain() -> None:
    """Preferred-split Y continuity uses domain-scaled gap, not bare 0.08.

    On a pixel page (H=2000), a vertical jump of 100 px is 0.05 of page height
    (< 0.08 * H) and must retain preferred_split continuity so the second line
    still splits. A bare unit-space threshold of 0.08 would reset at 100 > 0.08
    and lose continuity (second line may fail without preferred_split).
    """
    line_a = _mixed_gap_line(500.0, height_left=40.0, height_right=20.0)
    # +100 px — domain-relative small gap (0.05 * H); bare 0.08 would reset.
    line_b = _mixed_gap_line(600.0, height_left=30.0, height_right=28.0)
    # Narrow neighbor so the mixed-content path is eligible for both lines.
    narrow = Block(
        items=[_word("fig", 700, 450, 820, 470, normalized=False)],
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )
    para = Block(
        items=[narrow, line_a, line_b],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
    )
    split_mixed_content_lines([para], PAGE_W, PAGE_H)
    # narrow stays; each mixed line becomes 2 → expect ≥ 1 + 2 + 2 = 5 items
    # when preferred_split continuity is preserved for the second line.
    assert len(para.items) >= 5
