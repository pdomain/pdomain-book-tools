"""Tests for cupy_processing.whitespace module."""

import numpy as np
import pytest


@pytest.mark.gpu
@pytest.mark.cupy
class TestAddWhitespacePixelsGpu:
    def test_output_shape_increases_correctly(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.whitespace import (
            add_whitespace_pixels_gpu,
        )

        img = cp.zeros((100, 80), dtype=cp.uint8)
        out = add_whitespace_pixels_gpu(
            img, left_px=5, right_px=10, top_px=3, bottom_px=7
        )
        assert out.shape == (100 + 3 + 7, 80 + 5 + 10)

    def test_border_is_white(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.whitespace import (
            add_whitespace_pixels_gpu,
        )

        img = cp.zeros((50, 50), dtype=cp.uint8)
        out = add_whitespace_pixels_gpu(
            img, left_px=5, right_px=5, top_px=5, bottom_px=5
        )
        assert int(out[0, 0]) == 255  # top-left border pixel
        assert int(out[-1, -1]) == 255  # bottom-right border pixel

    def test_original_content_preserved(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.whitespace import (
            add_whitespace_pixels_gpu,
        )

        img = cp.full((10, 10), 128, dtype=cp.uint8)
        out = add_whitespace_pixels_gpu(
            img, left_px=3, right_px=0, top_px=2, bottom_px=0
        )
        # Content starts at row 2, col 3
        assert int(out[2, 3]) == 128
        assert int(out[2, 0]) == 255  # border

    def test_color_image_supported(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.whitespace import (
            add_whitespace_pixels_gpu,
        )

        img = cp.zeros((20, 20, 3), dtype=cp.uint8)
        out = add_whitespace_pixels_gpu(
            img, left_px=2, right_px=2, top_px=2, bottom_px=2
        )
        assert out.shape == (24, 24, 3)
        assert int(out[0, 0, 0]) == 255

    def test_matches_cpu_reference(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.whitespace import (
            add_whitespace_pixels_gpu,
        )
        from pd_book_tools.image_processing.cv2_processing.whitespace import (
            add_whitespace_pixels,
        )

        rng = np.random.default_rng(7)
        img_np = rng.integers(0, 256, (50, 40), dtype=np.uint8)
        cpu = add_whitespace_pixels(img_np, 5, 10, 3, 7)
        gpu = cp.asnumpy(add_whitespace_pixels_gpu(cp.asarray(img_np), 5, 10, 3, 7))
        np.testing.assert_array_equal(cpu, gpu)

    def test_zero_padding_is_noop(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.whitespace import (
            add_whitespace_pixels_gpu,
        )

        img = cp.full((30, 30), 99, dtype=cp.uint8)
        out = add_whitespace_pixels_gpu(img, 0, 0, 0, 0)
        assert cp.array_equal(out, img)


@pytest.mark.gpu
@pytest.mark.cupy
class TestAddWhitespacePercentageGpu:
    def test_percentage_converts_to_pixels(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.whitespace import (
            add_whitespace_percentage_gpu,
        )

        img = cp.zeros((100, 100), dtype=cp.uint8)
        out = add_whitespace_percentage_gpu(
            img, left_pct=0.1, right_pct=0.1, top_pct=0.05, bottom_pct=0.05
        )
        assert out.shape == (110, 120)


@pytest.mark.gpu
@pytest.mark.cupy
class TestNpUint8AddWhitespacePixels:
    def test_returns_numpy_array(self, cupy_module):
        from pd_book_tools.image_processing.cupy_processing.whitespace import (
            np_uint8_add_whitespace_pixels,
        )

        img = np.zeros((50, 50), dtype=np.uint8)
        out = np_uint8_add_whitespace_pixels(img, 5, 5, 5, 5)
        assert isinstance(out, np.ndarray)
        assert out.shape == (60, 60)
        assert out.dtype == np.uint8
