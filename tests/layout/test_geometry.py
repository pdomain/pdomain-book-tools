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


class TestReadingOrder:
    def test_top_then_left(self):
        a = R(100, 0, 200, 50)
        b = R(0, 0, 80, 50)
        c = R(0, 100, 200, 200)
        assert region_reading_order([c, a, b]) == [b, a, c]
