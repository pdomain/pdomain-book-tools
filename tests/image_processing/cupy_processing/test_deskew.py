"""Tests for cupy_processing.deskew module."""

import math

import numpy as np
import pytest


@pytest.mark.gpu
@pytest.mark.cupy
class TestRotateGpu:
    def test_zero_angle_returns_original(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.deskew import _rotate_gpu

        img = cp.ones((50, 60), dtype=cp.uint8) * 128
        result = _rotate_gpu(img, 0.0)
        assert cp.array_equal(result, img)

    def test_canvas_expands_for_45_degrees(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.deskew import _rotate_gpu

        img = cp.ones((100, 100), dtype=cp.uint8) * 200
        rotated = _rotate_gpu(img, 45.0)
        expected_side = int(
            100 * math.cos(math.radians(45)) + 100 * math.sin(math.radians(45))
        )
        assert rotated.shape[0] >= expected_side - 1
        assert rotated.shape[1] >= expected_side - 1

    def test_cw_and_ccw_produce_same_canvas_size(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.deskew import _rotate_gpu

        img = cp.ones((80, 120), dtype=cp.uint8) * 100
        cw = _rotate_gpu(img, 10.0)
        ccw = _rotate_gpu(img, -10.0)
        assert cw.shape == ccw.shape

    def test_output_is_cupy_ndarray(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.deskew import _rotate_gpu

        img = cp.zeros((50, 50), dtype=cp.uint8)
        result = _rotate_gpu(img, 5.0)
        assert isinstance(result, cp.ndarray)


@pytest.mark.gpu
@pytest.mark.cupy
class TestAutoDeskewGpu:
    def test_blank_image_returns_3tuple(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.deskew import (
            auto_deskew_gpu,
        )

        img = cp.zeros((100, 100), dtype=cp.uint8)
        result = auto_deskew_gpu(img)
        assert isinstance(result, tuple) and len(result) == 3
        out, top, bottom = result
        assert isinstance(out, cp.ndarray)

    def test_zero_pct_returns_unchanged_image(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.deskew import (
            auto_deskew_gpu,
        )

        img = cp.zeros((100, 100), dtype=cp.uint8)
        out, top, bottom = auto_deskew_gpu(img, pct=0.0)
        assert cp.array_equal(out, img)

    def test_straight_block_output_is_ndarray(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.deskew import (
            auto_deskew_gpu,
        )

        img = cp.zeros((200, 200), dtype=cp.uint8)
        img[40:160, 40:160] = 255
        out, top, bottom = auto_deskew_gpu(img)
        assert isinstance(out, cp.ndarray)
        assert isinstance(top, cp.ndarray)
        assert isinstance(bottom, cp.ndarray)

    def test_skewed_block_clockwise_produces_output(self, cupy_module):
        """Image with CW skew: bottom-left column > top-left column."""
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.deskew import (
            auto_deskew_gpu,
        )

        img_np = np.zeros((200, 200), dtype=np.uint8)
        for row, start_col in zip(range(40, 160), range(40, 160)):
            img_np[row, start_col : start_col + 40] = 255
        img = cp.asarray(img_np)
        out, top, bottom = auto_deskew_gpu(img)
        assert isinstance(out, cp.ndarray)

    def test_skewed_block_ccw_produces_output(self, cupy_module):
        """Image with CCW skew: bottom-left column < top-left column."""
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.deskew import (
            auto_deskew_gpu,
        )

        img_np = np.zeros((200, 200), dtype=np.uint8)
        for row, start_col in zip(range(40, 160), range(160, 40, -1)):
            if start_col + 30 <= 200:
                img_np[row, start_col : start_col + 30] = 255
        img = cp.asarray(img_np)
        out, top, bottom = auto_deskew_gpu(img)
        assert isinstance(out, cp.ndarray)

    def test_matches_cpu_output_shape(self, cupy_module):
        """GPU deskew output shape should be within 5 pixels of CPU result."""
        cp = cupy_module
        pytest.importorskip("cv2")
        from pd_book_tools.image_processing.cupy_processing.deskew import (
            auto_deskew_gpu,
        )
        from pd_book_tools.image_processing.cv2_processing.perspective_adjustment import (
            auto_deskew,
        )

        img_np = np.zeros((200, 200), dtype=np.uint8)
        img_np[40:160, 40:160] = 255

        cpu_result = auto_deskew(img_np)
        cpu_out = cpu_result[0] if isinstance(cpu_result, tuple) else cpu_result

        gpu_out = cp.asnumpy(auto_deskew_gpu(cp.asarray(img_np))[0])

        assert abs(cpu_out.shape[0] - gpu_out.shape[0]) <= 5
        assert abs(cpu_out.shape[1] - gpu_out.shape[1]) <= 5

    def test_np_uint8_auto_deskew_wrapper_returns_ndarray(self, cupy_module):
        from pd_book_tools.image_processing.cupy_processing.deskew import (
            np_uint8_auto_deskew,
        )

        img = np.zeros((200, 200), dtype=np.uint8)
        img[40:160, 40:160] = 255
        result = np_uint8_auto_deskew(img)
        assert isinstance(result, np.ndarray)
        assert result.ndim == 2
