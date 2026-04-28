"""Tests for cv2_processing.contours module."""

import numpy as np
import pytest

pytest.importorskip("cv2")

from pd_book_tools.image_processing.cv2_processing.contours import (  # noqa: E402
    find_and_draw_contours,
    remove_small_contours,
)


def _binary_image_with_blobs() -> np.ndarray:
    """Create a 100x100 binary image with a couple of blobs."""
    img = np.zeros((100, 100), dtype=np.uint8)
    # Big blob
    img[30:70, 30:70] = 255
    # Tiny blob (small contour)
    img[5:9, 5:9] = 255
    return img


class TestFindAndDrawContours:
    def test_finds_contours_and_returns_visualization(self):
        img = _binary_image_with_blobs()
        out_img, contours = find_and_draw_contours(img.copy())
        assert out_img is not None
        # Should detect at least 2 contours
        assert len(contours) >= 2
        # Output is a 3-channel BGR image with the contours drawn
        assert out_img.ndim == 3
        assert out_img.shape[2] == 3

    def test_no_contours_returns_original(self):
        # An all-zero image has no contours
        img = np.zeros((50, 50), dtype=np.uint8)
        out_img, contours = find_and_draw_contours(img.copy())
        assert len(contours) == 0
        # Image should be returned as-is (still grayscale)
        assert out_img.shape == img.shape


class TestRemoveSmallContours:
    def test_no_contours_returns_image_unchanged(self):
        img = np.zeros((50, 50), dtype=np.uint8)
        out_img, vis = remove_small_contours(img.copy(), [])
        np.testing.assert_array_equal(out_img, img)
        # Visualization should be a 3-channel BGR
        assert vis.shape == (50, 50, 3)

    def test_removes_tiny_contour(self):
        from cv2 import (
            CHAIN_APPROX_SIMPLE,
            RETR_EXTERNAL,
            findContours,
        )

        img = _binary_image_with_blobs()
        contours, _ = findContours(img.copy(), RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)
        # Initial image has tiny blob at [5:9, 5:9]
        assert (img[5:9, 5:9] == 255).all()
        cleaned, _ = remove_small_contours(img.copy(), contours)
        # Tiny blob should now be zeroed out
        assert (cleaned[5:9, 5:9] == 0).all()
        # Big blob should remain
        assert (cleaned[30:70, 30:70] == 255).all()
