"""Tests for cv2_processing.split module."""

import numpy as np
import pytest

from pd_book_tools.image_processing.cv2_processing.split import (
    split_x_columns,
    split_y_rows,
)


class TestSplitXColumns:
    def test_basic_split(self):
        img = np.arange(100, dtype=np.uint8).reshape(10, 10)
        left, right = split_x_columns(img, 4)
        assert left.shape == (10, 4)
        assert right.shape == (10, 6)
        np.testing.assert_array_equal(left, img[:, :4])
        np.testing.assert_array_equal(right, img[:, 4:])

    def test_split_at_zero(self):
        img = np.zeros((5, 8), dtype=np.uint8)
        left, right = split_x_columns(img, 0)
        assert left.shape == (5, 0)
        assert right.shape == (5, 8)

    def test_split_at_width(self):
        img = np.zeros((5, 8), dtype=np.uint8)
        left, right = split_x_columns(img, 8)
        assert left.shape == (5, 8)
        assert right.shape == (5, 0)

    def test_out_of_bounds_negative(self):
        img = np.zeros((5, 8), dtype=np.uint8)
        with pytest.raises(ValueError, match="out of bounds"):
            split_x_columns(img, -1)

    def test_out_of_bounds_too_large(self):
        img = np.zeros((5, 8), dtype=np.uint8)
        with pytest.raises(ValueError, match="out of bounds"):
            split_x_columns(img, 9)


class TestSplitYRows:
    def test_basic_split(self):
        img = np.arange(100, dtype=np.uint8).reshape(10, 10)
        top, bottom = split_y_rows(img, 3)
        assert top.shape == (3, 10)
        assert bottom.shape == (7, 10)
        np.testing.assert_array_equal(top, img[:3, :])
        np.testing.assert_array_equal(bottom, img[3:, :])

    def test_out_of_bounds(self):
        img = np.zeros((6, 6), dtype=np.uint8)
        with pytest.raises(ValueError, match="out of bounds"):
            split_y_rows(img, -2)
        with pytest.raises(ValueError, match="out of bounds"):
            split_y_rows(img, 100)
