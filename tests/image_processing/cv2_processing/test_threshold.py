"""Tests for cv2_processing.threshold module."""

import numpy as np
import pytest

pytest.importorskip("cv2")

from pd_book_tools.image_processing.cv2_processing.threshold import (  # noqa: E402
    binary_thresh,
    otsu_binary_thresh,
)


class TestBinaryThresh:
    def test_default_level(self):
        img = np.array([[0, 100, 127, 128, 200, 255]], dtype=np.uint8)
        out = binary_thresh(img)
        # Default level=127: values <=127 -> 0, > 127 -> 255
        assert out.shape == img.shape
        assert out[0, 0] == 0
        assert out[0, 1] == 0
        assert out[0, 2] == 0
        assert out[0, 3] == 255
        assert out[0, 4] == 255
        assert out[0, 5] == 255

    def test_custom_level(self):
        img = np.array([[0, 50, 100, 150, 200, 255]], dtype=np.uint8)
        out = binary_thresh(img, level=200)
        assert out[0, 0] == 0
        assert out[0, 4] == 0
        assert out[0, 5] == 255


class TestOtsuBinaryThresh:
    def test_bimodal_image(self):
        # Create a bimodal image - clearly two clusters
        img = np.zeros((20, 20), dtype=np.uint8)
        img[:10, :] = 30
        img[10:, :] = 220
        out = otsu_binary_thresh(img)
        # Otsu should split into 0 and 255 along that boundary
        assert out.dtype == np.uint8
        # All values should be either 0 or 255
        unique = np.unique(out)
        assert set(unique.tolist()).issubset({0, 255})
        # The dark and light regions should map to 0 and 255 respectively
        assert (out[:10, :] == 0).all()
        assert (out[10:, :] == 255).all()
