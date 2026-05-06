"""Tests for the region-adjacency helpers in ``pd_book_tools.layout.geometry``."""

import pytest

from pd_book_tools.layout.geometry import (
    caption_for_figure,
    contains,
    horizontal_overlap_ratio,
    iou,
    region_reading_order,
)
from pd_book_tools.layout.types import LayoutRegion, RegionType


def R(L, T, R_, B, type_=RegionType.text):
    return LayoutRegion(type=type_, L=L, R=R_, T=T, B=B, confidence=0.9)


class TestIoU:
    def test_zero_when_disjoint(self):
        assert iou(R(0, 0, 10, 10), R(20, 20, 30, 30)) == 0.0

    def test_full_overlap(self):
        a = R(10, 10, 30, 30)
        assert iou(a, a) == pytest.approx(1.0)

    def test_partial(self):
        a = R(0, 0, 10, 10)
        b = R(5, 5, 15, 15)
        # intersection 5x5=25; union = 100+100-25 = 175
        assert iou(a, b) == pytest.approx(25 / 175)

    def test_identical_zero_area_returns_zero_by_convention(self):
        """L-05: two identical zero-area regions return 0.0, not 1.0.

        Mathematically IoU of identical sets is 1.0 even with zero measure,
        but this module treats IoU as a "meaningful spatial overlap" signal.
        Two coincident point/line regions carry no coverage to overlap on,
        so the convention is 0.0. Documented in the function docstring.
        Locking this so a future "fix" doesn't accidentally flip the
        contract and break dedupe passes that rely on it.
        """
        # Two coincident zero-width vertical line regions
        z = R(10, 5, 10, 25)
        assert z.area == 0
        assert iou(z, z) == 0.0

        # Two coincident point regions
        p = R(7, 7, 7, 7)
        assert p.area == 0
        assert iou(p, p) == 0.0

        # And the docstring claim about mismatched zero-area inputs:
        # disjoint zero-area regions also return 0.0
        z2 = R(50, 50, 50, 70)
        assert iou(z, z2) == 0.0


class TestContains:
    def test_inside(self):
        outer = R(0, 0, 100, 100)
        inner = R(10, 10, 90, 90)
        assert contains(outer, inner)

    def test_outside_one_edge(self):
        outer = R(0, 0, 100, 100)
        inner = R(10, 10, 110, 90)
        assert not contains(outer, inner)
        assert contains(outer, inner, tol=10)


class TestHorizontalOverlap:
    def test_same_columns(self):
        a = R(100, 0, 300, 200)
        b = R(100, 250, 300, 290)
        assert horizontal_overlap_ratio(a, b) == 1.0

    def test_no_overlap(self):
        a = R(0, 0, 100, 200)
        b = R(200, 0, 300, 200)
        assert horizontal_overlap_ratio(a, b) == 0.0

    def test_partial(self):
        a = R(0, 0, 100, 200)  # width 100
        b = R(50, 0, 200, 200)  # width 150, intersection width 50
        assert horizontal_overlap_ratio(a, b) == pytest.approx(50 / 100)


class TestCaptionForFigure:
    def test_caption_just_below(self):
        figure = R(100, 100, 500, 500, type_=RegionType.figure)
        caption = R(100, 520, 500, 560, type_=RegionType.caption)
        assert caption_for_figure(figure, [figure, caption]) is caption

    def test_caption_too_far(self):
        figure = R(100, 100, 500, 500, type_=RegionType.figure)
        caption = R(100, 700, 500, 740, type_=RegionType.caption)
        assert caption_for_figure(figure, [figure, caption]) is None

    def test_horizontal_misalignment_skipped(self):
        figure = R(100, 100, 500, 500, type_=RegionType.figure)
        caption = R(700, 520, 900, 560, type_=RegionType.caption)
        assert caption_for_figure(figure, [figure, caption]) is None

    def test_explicit_caption_preferred_over_text(self):
        figure = R(100, 100, 500, 500, type_=RegionType.figure)
        text = R(100, 520, 500, 560, type_=RegionType.text)
        caption = R(100, 540, 500, 580, type_=RegionType.caption)
        chosen = caption_for_figure(figure, [figure, text, caption])
        assert chosen is caption

    def test_caption_above_ignored_by_default(self):
        """L-06: default behaviour is below-only — caption above is missed.

        Locks the back-compat contract; opt-in via above=True is tested below.
        """
        figure = R(100, 200, 500, 600, type_=RegionType.figure)
        caption_above = R(100, 150, 500, 190, type_=RegionType.caption)
        assert caption_for_figure(figure, [figure, caption_above]) is None

    def test_caption_above_found_when_above_true(self):
        """L-06: with above=True, captions just above the figure are found."""
        figure = R(100, 200, 500, 600, type_=RegionType.figure)
        caption_above = R(100, 150, 500, 190, type_=RegionType.caption)
        result = caption_for_figure(figure, [figure, caption_above], above=True)
        assert result is caption_above

    def test_caption_above_too_far_when_above_true(self):
        """L-06: max_gap_px applies symmetrically to above-search."""
        figure = R(100, 300, 500, 600, type_=RegionType.figure)
        caption_above = R(100, 50, 500, 100, type_=RegionType.caption)
        # gap = 300 - 100 = 200, default max_gap_px=80
        assert caption_for_figure(figure, [figure, caption_above], above=True) is None

    def test_caption_below_preferred_over_caption_above(self):
        """L-06: when both sides have a caption, the closer one wins."""
        figure = R(100, 200, 500, 600, type_=RegionType.figure)
        caption_above = R(100, 150, 500, 190, type_=RegionType.caption)  # gap 10
        caption_below = R(100, 620, 500, 660, type_=RegionType.caption)  # gap 20
        result = caption_for_figure(
            figure, [figure, caption_above, caption_below], above=True
        )
        assert result is caption_above


class TestReadingOrder:
    def test_top_then_left(self):
        a = R(100, 0, 200, 50)
        b = R(0, 0, 80, 50)
        c = R(0, 100, 200, 200)
        assert region_reading_order([c, a, b]) == [b, a, c]
