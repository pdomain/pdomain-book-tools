"""Tests for cv2_processing.whitespace module."""

import numpy as np

from pd_book_tools.image_processing.cv2_processing.whitespace import (
    add_whitespace_percentage,
    add_whitespace_pixels,
)


class TestAddWhitespacePixels:
    def test_pads_grayscale_image(self):
        img = np.zeros((10, 20), dtype=np.uint8)
        out = add_whitespace_pixels(img, left_px=2, right_px=3, top_px=4, bottom_px=5)
        # New shape: (10+4+5, 20+2+3) = (19, 25)
        assert out.shape == (19, 25)
        # Original image area should still be 0
        assert (out[4:14, 2:22] == 0).all()
        # Surrounding padding should be 255
        assert (out[:4, :] == 255).all()
        assert (out[14:, :] == 255).all()
        assert (out[:, :2] == 255).all()
        assert (out[:, 22:] == 255).all()

    def test_pads_color_image(self):
        img = np.zeros((5, 5, 3), dtype=np.uint8)
        out = add_whitespace_pixels(img, left_px=1, right_px=1, top_px=1, bottom_px=1)
        assert out.shape == (7, 7, 3)
        # Border pixels should be white
        assert (out[0, 0] == [255, 255, 255]).all()
        # Center pixel should be 0
        assert (out[3, 3] == [0, 0, 0]).all()

    def test_zero_padding_returns_same_size(self):
        img = np.zeros((6, 6), dtype=np.uint8)
        out = add_whitespace_pixels(img, 0, 0, 0, 0)
        assert out.shape == img.shape
        np.testing.assert_array_equal(out, img)


class TestAddWhitespacePercentage:
    def test_pct_padding_grayscale(self):
        img = np.zeros((100, 200), dtype=np.uint8)
        out = add_whitespace_percentage(
            img, left_pct=0.1, right_pct=0.1, top_pct=0.05, bottom_pct=0.05
        )
        # Expected: (100 + 5 + 5, 200 + 20 + 20) = (110, 240)
        assert out.shape == (110, 240)

    def test_pct_zero_no_change(self):
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        out = add_whitespace_percentage(img)
        assert out.shape == img.shape
