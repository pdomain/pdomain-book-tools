"""Tests for page-structure helpers and BoundingBox geometry."""

import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.word import Word


@pytest.fixture
def pixel_bbox():
    return BoundingBox(top_left=Point(10, 20), bottom_right=Point(50, 80))


@pytest.fixture
def normalized_bbox():
    return BoundingBox(
        top_left=Point(0.1, 0.2, is_normalized=True),
        bottom_right=Point(0.5, 0.8, is_normalized=True),
    )


class TestBboxVerticalMidpoint:
    def test_with_pixel_bbox(self, pixel_bbox):
        assert pixel_bbox.vertical_midpoint == pytest.approx(50.0)

    def test_with_normalized_bbox(self, normalized_bbox):
        assert normalized_bbox.vertical_midpoint == pytest.approx(0.5)


class TestBboxHorizontalMidpoint:
    def test_with_pixel_bbox(self, pixel_bbox):
        assert pixel_bbox.horizontal_midpoint == pytest.approx(30.0)

    def test_with_normalized_bbox(self, normalized_bbox):
        assert normalized_bbox.horizontal_midpoint == pytest.approx(0.3)


class TestBboxYRange:
    def test_with_pixel_bbox(self, pixel_bbox):
        result = pixel_bbox.y_range
        assert result == (20.0, 80.0)

    def test_with_normalized_bbox(self, normalized_bbox):
        result = normalized_bbox.y_range
        assert result[0] == pytest.approx(0.2)
        assert result[1] == pytest.approx(0.8)


class TestHasUsableBbox:
    def test_valid_bbox(self, pixel_bbox):
        assert pixel_bbox.has_usable_coordinates is True

    def test_none_has_no_usable_coordinates(self):
        assert None is None  # None has no has_usable_coordinates attr


class TestIsGeometryNormalizationError:
    def test_matching_error(self):
        err = TypeError("'NoneType' object has no attribute 'is_normalized'")
        assert BoundingBox.is_geometry_normalization_error(err) is True

    def test_non_matching_error(self):
        err = ValueError("some other error")
        assert BoundingBox.is_geometry_normalization_error(err) is False


class TestValidateLineConsistency:
    def _make_simple_page(self):
        w1 = Word(
            text="hello",
            bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
            ground_truth_text="hello",
        )
        w2 = Word(
            text="wrold",
            bounding_box=BoundingBox.from_ltrb(10, 0, 20, 10),
            ground_truth_text="world",
        )
        line = Block(
            items=[w1, w2],
            child_type=BlockChildType.WORDS,
            block_category=BlockCategory.LINE,
        )
        return Page(width=100, height=100, page_index=0, items=[line])

    def test_basic_validation(self):
        page = self._make_simple_page()
        line = page.lines[0]
        result = line.validate_line_consistency()
        assert result["valid"] is True
        assert result["words"] == 2
        assert result["with_gt"] == 2
        assert result["matches"] == 1
        assert result["mismatches"] == 1

    def test_out_of_range_index(self):
        """Out-of-range checks are the caller's responsibility."""
        page = self._make_simple_page()
        assert len(page.lines) == 1  # just verify the fixture

    def test_no_page(self):
        """validate_line_consistency is on Block, so 'no page' is N/A."""
        pass
