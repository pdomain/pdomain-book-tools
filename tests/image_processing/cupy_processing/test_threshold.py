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


class TestBinaryThreshGpu:
    def test_pixels_above_level_become_255(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        # level=127: pixels strictly > 127 become 255; 127 itself stays 0
        img = cp.array([[0, 100, 127, 128, 255]], dtype=cp.uint8)
        out = thresh_mod.binary_thresh_gpu(img, level=127)
        expected = cp.array([[0, 0, 0, 255, 255]], dtype=cp.uint8)
        assert cp.array_equal(out, expected)

    def test_output_dtype_is_uint8(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        img = cp.zeros((10, 10), dtype=cp.uint8)
        out = thresh_mod.binary_thresh_gpu(img)
        assert out.dtype == cp.uint8

    def test_matches_cv2_reference(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        pytest.importorskip("cv2")
        import cv2
        import numpy as np

        rng = np.random.default_rng(99)
        img_np = rng.integers(0, 256, (50, 50), dtype=np.uint8)
        _, cpu = cv2.threshold(img_np, 127, 255, cv2.THRESH_BINARY)
        gpu = cp.asnumpy(thresh_mod.binary_thresh_gpu(cp.asarray(img_np), level=127))
        np.testing.assert_array_equal(cpu, gpu)


class TestNpUint8BinaryThresh:
    def test_returns_uint8_numpy(self, cupy_threshold):
        thresh_mod, _ = cupy_threshold
        import numpy as np

        img = np.array([[0, 100, 200]], dtype=np.uint8)
        out = thresh_mod.np_uint8_binary_thresh(img, level=127)
        assert isinstance(out, np.ndarray)
        assert out.dtype == np.uint8
        assert out[0, 0] == 0
        assert out[0, 2] == 255


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
