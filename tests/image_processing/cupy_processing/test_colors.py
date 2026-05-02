"""Tests for cupy_processing.colors module."""

import numpy as np
import pytest


@pytest.mark.gpu
@pytest.mark.cupy
class TestBgrToGrayGpu:
    def test_output_shape_and_dtype(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.colors import (
            bgr_to_gray_gpu,
        )

        img = cp.zeros((10, 10, 3), dtype=cp.uint8)
        out = bgr_to_gray_gpu(img)
        assert out.shape == (10, 10)
        assert out.dtype == cp.uint8

    def test_white_stays_white(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.colors import (
            bgr_to_gray_gpu,
        )

        img = cp.full((5, 5, 3), 255, dtype=cp.uint8)
        out = bgr_to_gray_gpu(img)
        assert int(out[0, 0]) == 255

    def test_black_stays_black(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.colors import (
            bgr_to_gray_gpu,
        )

        img = cp.zeros((5, 5, 3), dtype=cp.uint8)
        out = bgr_to_gray_gpu(img)
        assert int(out[0, 0]) == 0

    def test_matches_cv2_reference(self, cupy_module):
        """GPU output must match cv2.COLOR_BGR2GRAY within ±1 LSB rounding."""
        cp = cupy_module
        pytest.importorskip("cv2")
        import cv2

        from pd_book_tools.image_processing.cupy_processing.colors import (
            bgr_to_gray_gpu,
        )

        rng = np.random.default_rng(11)
        img_np = rng.integers(0, 256, (50, 50, 3), dtype=np.uint8)
        cpu = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY).astype(np.int16)
        gpu = cp.asnumpy(bgr_to_gray_gpu(cp.asarray(img_np))).astype(np.int16)
        assert np.max(np.abs(cpu - gpu)) <= 1

    def test_np_wrapper_returns_numpy(self, cupy_module):
        from pd_book_tools.image_processing.cupy_processing.colors import (
            np_uint8_bgr_to_gray,
        )

        img = np.zeros((10, 10, 3), dtype=np.uint8)
        out = np_uint8_bgr_to_gray(img)
        assert isinstance(out, np.ndarray)
        assert out.ndim == 2
        assert out.dtype == np.uint8


@pytest.mark.gpu
@pytest.mark.cupy
class TestGrayToBgrGpu:
    def test_output_shape_and_dtype(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.colors import (
            gray_to_bgr_gpu,
        )

        img = cp.zeros((10, 10), dtype=cp.uint8)
        out = gray_to_bgr_gpu(img)
        assert out.shape == (10, 10, 3)
        assert out.dtype == cp.uint8

    def test_channels_are_equal(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.colors import (
            gray_to_bgr_gpu,
        )

        rng = cp.random.default_rng(0)
        img = rng.integers(0, 256, (20, 20), dtype=cp.uint8)
        out = gray_to_bgr_gpu(img)
        assert cp.array_equal(out[:, :, 0], img)
        assert cp.array_equal(out[:, :, 1], img)
        assert cp.array_equal(out[:, :, 2], img)

    def test_np_wrapper_returns_numpy(self, cupy_module):
        from pd_book_tools.image_processing.cupy_processing.colors import (
            np_uint8_gray_to_bgr,
        )

        img = np.full((5, 5), 128, dtype=np.uint8)
        out = np_uint8_gray_to_bgr(img)
        assert isinstance(out, np.ndarray)
        assert out.shape == (5, 5, 3)


@pytest.mark.gpu
@pytest.mark.cupy
class TestBgrToRgbGpu:
    def test_channel_order_reversed(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.colors import bgr_to_rgb_gpu

        img = cp.zeros((5, 5, 3), dtype=cp.uint8)
        img[:, :, 0] = 10  # B
        img[:, :, 1] = 20  # G
        img[:, :, 2] = 30  # R
        out = bgr_to_rgb_gpu(img)
        assert int(out[0, 0, 0]) == 30  # was R, now first channel
        assert int(out[0, 0, 1]) == 20  # G unchanged
        assert int(out[0, 0, 2]) == 10  # was B, now last channel

    def test_round_trip_is_identity(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.colors import (
            bgr_to_rgb_gpu,
            rgb_to_bgr_gpu,
        )

        rng = cp.random.default_rng(5)
        img = rng.integers(0, 256, (20, 20, 3), dtype=cp.uint8)
        assert cp.array_equal(rgb_to_bgr_gpu(bgr_to_rgb_gpu(img)), img)

    def test_matches_cv2_reference(self, cupy_module):
        cp = cupy_module
        pytest.importorskip("cv2")
        import cv2

        from pd_book_tools.image_processing.cupy_processing.colors import bgr_to_rgb_gpu

        rng = np.random.default_rng(7)
        img_np = rng.integers(0, 256, (20, 20, 3), dtype=np.uint8)
        cpu = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
        gpu = cp.asnumpy(bgr_to_rgb_gpu(cp.asarray(img_np)))
        np.testing.assert_array_equal(cpu, gpu)

    def test_np_wrapper_returns_numpy(self, cupy_module):
        from pd_book_tools.image_processing.cupy_processing.colors import (
            np_uint8_bgr_to_rgb,
        )

        img = np.zeros((5, 5, 3), dtype=np.uint8)
        out = np_uint8_bgr_to_rgb(img)
        assert isinstance(out, np.ndarray)
        assert out.shape == img.shape
