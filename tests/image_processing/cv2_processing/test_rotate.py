"""Tests for cv2_processing.rotate module."""

import numpy as np
import pytest

pytest.importorskip("cv2")

from pd_book_tools.image_processing.cv2_processing.rotate import (
    rotate_image,  # noqa: E402
)


class TestRotateImage:
    def test_zero_angle_keeps_dimensions(self):
        img = np.full((20, 30), 200, dtype=np.uint8)
        out = rotate_image(img, angle=0)
        assert out.shape == img.shape
        # 0-degree rotation should return the same content
        np.testing.assert_array_equal(out, img)

    def test_90_degree_rotation_swaps_dimensions(self):
        img = np.zeros((20, 30, 3), dtype=np.uint8)
        out = rotate_image(img, angle=90)
        # 90-degree rotation should swap height and width
        assert out.shape == (30, 20, 3)

    def test_45_degree_rotation_grows_canvas(self):
        img = np.zeros((20, 20), dtype=np.uint8)
        out = rotate_image(img, angle=45)
        # Diagonal rotation increases bounding box
        assert out.shape[0] > 20
        assert out.shape[1] > 20

    def test_border_value_color(self):
        img = np.zeros((20, 20, 3), dtype=np.uint8)
        out = rotate_image(img, angle=30, borderValue=(255.0, 0.0, 0.0))
        # The corners of the new bounding box should be filled with the border color
        assert (out[0, 0] == [255, 0, 0]).all()
