"""Tests for BoundingBox geometry properties: vertical_midpoint, horizontal_midpoint, y_range."""

import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point


@pytest.fixture
def pixel_box():
    """Pixel-coordinate bounding box (2,3) -> (8,10)."""
    return BoundingBox(top_left=Point(2, 3), bottom_right=Point(8, 10))


@pytest.fixture
def normalized_box():
    """Normalized bounding box (0.1, 0.2) -> (0.5, 0.8)."""
    return BoundingBox(
        top_left=Point(0.1, 0.2, is_normalized=True),
        bottom_right=Point(0.5, 0.8, is_normalized=True),
    )


class TestVerticalMidpoint:
    def test_pixel_box(self, pixel_box):
        assert pixel_box.vertical_midpoint == pytest.approx(6.5)  # (3+10)/2

    def test_normalized_box(self, normalized_box):
        assert normalized_box.vertical_midpoint == pytest.approx(0.5)  # (0.2+0.8)/2

    def test_zero_height(self):
        bbox = BoundingBox.from_ltrb(0, 5, 10, 5)
        assert bbox.vertical_midpoint == pytest.approx(5.0)


class TestHorizontalMidpoint:
    def test_pixel_box(self, pixel_box):
        assert pixel_box.horizontal_midpoint == pytest.approx(5.0)  # (2+8)/2

    def test_normalized_box(self, normalized_box):
        assert normalized_box.horizontal_midpoint == pytest.approx(0.3)  # (0.1+0.5)/2

    def test_zero_width(self):
        bbox = BoundingBox.from_ltrb(7, 0, 7, 10)
        assert bbox.horizontal_midpoint == pytest.approx(7.0)


class TestYRange:
    def test_pixel_box(self, pixel_box):
        assert pixel_box.y_range == (3, 10)

    def test_normalized_box(self, normalized_box):
        yr = normalized_box.y_range
        assert yr[0] == pytest.approx(0.2)
        assert yr[1] == pytest.approx(0.8)

    def test_returns_tuple(self, pixel_box):
        assert isinstance(pixel_box.y_range, tuple)
        assert len(pixel_box.y_range) == 2
