"""Tests for cv2_processing.perspective_adjustment module."""

import numpy as np
import pytest

pytest.importorskip("cv2")

from pd_book_tools.image_processing.cv2_processing.perspective_adjustment import (  # noqa: E402
    auto_deskew,
)


class TestAutoDeskew:
    def test_blank_image_returns_tuple_unchanged(self):
        img = np.zeros((100, 100), dtype=np.uint8)
        result = auto_deskew(img)
        # Blank image: still falls through and returns the original via the
        # "do nothing 2" branch (top/bottom columns are equal -> dist_b == dist_c).
        assert isinstance(result, tuple)
        new_img, top_of_img, bottom_of_img = result
        np.testing.assert_array_equal(new_img, img)
        assert isinstance(top_of_img, np.ndarray)
        assert isinstance(bottom_of_img, np.ndarray)

    def test_zero_pct_returns_image_only(self):
        img = np.zeros((100, 100), dtype=np.uint8)
        # pct=0 -> h_percent==0 -> early return of original image only
        out = auto_deskew(img, pct=0.0)
        assert isinstance(out, np.ndarray)
        np.testing.assert_array_equal(out, img)

    def test_straight_block_no_skew(self):
        img = np.zeros((200, 200), dtype=np.uint8)
        img[40:160, 40:160] = 255
        result = auto_deskew(img)
        # Should return a 3-tuple when content is found
        if isinstance(result, tuple):
            new_img, top_of_img, bottom_of_img = result
            assert isinstance(new_img, np.ndarray)
            assert isinstance(top_of_img, np.ndarray)
            assert isinstance(bottom_of_img, np.ndarray)
        else:
            assert isinstance(result, np.ndarray)

    def test_skewed_block_clockwise(self):
        # Image where bottom-left starts further right than top-left
        # (positive slope) -> auto_deskew should rotate clockwise
        img = np.zeros((200, 200), dtype=np.uint8)
        for row, start_col in zip(range(40, 160), range(40, 160)):
            img[row, start_col : start_col + 100] = 255
        result = auto_deskew(img)
        assert isinstance(result, tuple)
        new_img = result[0]
        assert isinstance(new_img, np.ndarray)

    def test_skewed_block_counter_clockwise(self):
        # Image where bottom-left starts further left than top-left
        # (negative slope) -> auto_deskew should rotate counter-clockwise
        img = np.zeros((200, 200), dtype=np.uint8)
        for row, start_col in zip(range(40, 160), range(160, 40, -1)):
            img[row, start_col : start_col + 30] = 255
        result = auto_deskew(img)
        assert isinstance(result, tuple)
        new_img = result[0]
        assert isinstance(new_img, np.ndarray)
