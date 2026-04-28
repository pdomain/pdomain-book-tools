"""Tests for cupy_processing.threshold module."""

import numpy as np
import pytest


@pytest.fixture
def cupy_threshold(cupy_module):
    from pd_book_tools.image_processing.cupy_processing import threshold as thresh_mod

    return thresh_mod, cupy_module


class TestOtsuBinaryThresh:
    def test_bimodal_image(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        img = cp.zeros((20, 20), dtype=cp.float32)
        img[:10, :] = 0.1
        img[10:, :] = 0.9
        out = thresh_mod.otsu_binary_thresh(img)
        # Output is binary float (0.0 or 1.0)
        assert out.dtype == cp.float32
        assert tuple(out.shape) == (20, 20)
        # Values should be split 0/1
        flattened = out.get().ravel()
        assert set(np.unique(flattened).tolist()).issubset({0.0, 1.0})

    def test_color_image_handled(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        img = cp.zeros((10, 10, 3), dtype=cp.float32)
        img[:, :, 0] = 0.1
        img[:, :, 1] = 0.5
        img[:, :, 2] = 0.9
        out = thresh_mod.otsu_binary_thresh(img)
        assert out.ndim == 2
        assert tuple(out.shape) == (10, 10)


class TestNpUint8FloatBinaryThresh:
    def test_returns_uint8(self, cupy_threshold):
        thresh_mod, _ = cupy_threshold
        img = np.zeros((20, 20), dtype=np.uint8)
        img[:10, :] = 30
        img[10:, :] = 220
        out = thresh_mod.np_uint8_float_binary_thresh(img)
        assert out.dtype == np.uint8
        assert out.shape == img.shape
        # Values should be either 0 or 255
        assert set(np.unique(out).tolist()).issubset({0, 255})
