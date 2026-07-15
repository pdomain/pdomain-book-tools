"""Tests for cv2_processing.crop module."""

import numpy as np
import pytest

from pdomain_book_tools.image_processing.cv2_processing.crop import (
    crop_edges,
    crop_to_rectangle,
)


class TestCropToRectangle:
    def test_basic_crop(self):
        img = np.arange(100, dtype=np.uint8).reshape(10, 10)
        cropped = crop_to_rectangle(img, minX=2, maxX=8, minY=1, maxY=5)
        assert cropped.shape == (4, 6)
        np.testing.assert_array_equal(cropped, img[1:5, 2:8])

    def test_clamps_to_bounds(self):
        img = np.zeros((10, 10), dtype=np.uint8)
        cropped = crop_to_rectangle(img, minX=-5, maxX=20, minY=-3, maxY=15)
        # Should produce a valid crop (clamped to image dimensions)
        assert cropped.shape[0] > 0
        assert cropped.shape[1] > 0
        assert cropped.shape[0] <= 10
        assert cropped.shape[1] <= 10

    def test_invalid_crop_returns_original(self):
        img = np.zeros((10, 10), dtype=np.uint8)
        # minX >= maxX -> invalid; should return original image
        out = crop_to_rectangle(img, minX=8, maxX=3, minY=2, maxY=5)
        assert out is img

    def test_invalid_y_returns_original(self):
        img = np.zeros((10, 10), dtype=np.uint8)
        out = crop_to_rectangle(img, minX=0, maxX=5, minY=8, maxY=3)
        assert out is img

    def test_entirely_right_of_image_returns_original(self):
        """#169: box entirely beyond right edge must return original, not a 1-px strip."""
        img = np.zeros((10, 10), dtype=np.uint8)
        # minX=15 > width=10, so no overlap
        out = crop_to_rectangle(img, minX=15, maxX=20, minY=2, maxY=5)
        assert out is img

    def test_entirely_below_image_returns_original(self):
        """#169: box entirely beyond bottom edge must return original, not a 1-px strip."""
        img = np.zeros((10, 10), dtype=np.uint8)
        # minY=15 > height=10, so no overlap
        out = crop_to_rectangle(img, minX=2, maxX=5, minY=15, maxY=20)
        assert out is img

    def test_color_image(self):
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        cropped = crop_to_rectangle(img, minX=1, maxX=4, minY=2, maxY=6)
        assert cropped.shape == (4, 3, 3)


class TestCropEdges:
    def test_default_no_crop(self):
        img = np.arange(100, dtype=np.uint8).reshape(10, 10)
        out = crop_edges(img)
        np.testing.assert_array_equal(out, img)

    def test_crop_each_edge(self):
        img = np.arange(100, dtype=np.uint8).reshape(10, 10)
        out = crop_edges(img, top=1, bottom=2, left=3, right=4)
        # Resulting shape should be (10-1-2, 10-3-4) = (7, 3)
        assert out.shape == (7, 3)
        np.testing.assert_array_equal(out, img[1:8, 3:6])

    def test_color_image(self):
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        out = crop_edges(img, top=2, bottom=2, left=2, right=2)
        assert out.shape == (6, 6, 3)

    def test_raises_on_excessive_crop(self):
        img = np.zeros((10, 10), dtype=np.uint8)
        with pytest.raises(ValueError, match="exceed"):
            crop_edges(img, top=6, bottom=5)
        with pytest.raises(ValueError, match="exceed"):
            crop_edges(img, left=6, right=5)

    @pytest.mark.parametrize("edge", ["top", "bottom", "left", "right"])
    def test_raises_on_negative_edge(self, edge: str):
        img = np.zeros((10, 10), dtype=np.uint8)
        with pytest.raises(ValueError, match="non-negative"):
            crop_edges(img, **{edge: -1})
