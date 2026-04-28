"""Tests for cv2_processing.colors module."""

import numpy as np
import pytest

pytest.importorskip("cv2")

from pd_book_tools.image_processing.cv2_processing.colors import (  # noqa: E402
    cv2_convert_to_grayscale,
)


class TestCv2ConvertToGrayscale:
    def test_color_to_gray(self):
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        img[:, :] = [50, 100, 150]  # BGR
        out = cv2_convert_to_grayscale(img)
        assert out.ndim == 2
        assert out.shape == (10, 10)
        # All pixels should map to a single grayscale value
        assert np.unique(out).size == 1

    def test_white_to_gray(self):
        img = np.full((5, 5, 3), 255, dtype=np.uint8)
        out = cv2_convert_to_grayscale(img)
        assert (out == 255).all()
