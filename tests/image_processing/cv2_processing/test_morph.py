"""Tests for cv2_processing.morph module."""

import numpy as np
import pytest

pytest.importorskip("cv2")

from pd_book_tools.image_processing.cv2_processing.morph import morph_fill  # noqa: E402


class TestMorphFill:
    def test_morph_fills_small_holes(self):
        img = np.full((20, 20), 255, dtype=np.uint8)
        # Punch a tiny hole
        img[10, 10] = 0
        out = morph_fill(img, shape=(3, 3))
        # After CLOSE with 3x3 kernel, hole should be filled
        assert out[10, 10] == 255
        assert out.shape == img.shape

    def test_returns_ndarray(self):
        img = np.zeros((10, 10), dtype=np.uint8)
        out = morph_fill(img)
        assert out.shape == img.shape
