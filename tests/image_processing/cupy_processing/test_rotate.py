"""Tests for cupy_processing.rotate module."""

import math

import numpy as np
import pytest


@pytest.mark.gpu
@pytest.mark.cupy
class TestRotateImageGpu:
    def test_zero_angle_returns_original(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.rotate import (
            rotate_image_gpu,
        )

        img = cp.ones((50, 60), dtype=cp.uint8) * 128
        result = rotate_image_gpu(img, 0.0)
        assert cp.array_equal(result, img)

    def test_canvas_expands_for_45_degrees(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.rotate import (
            rotate_image_gpu,
        )

        img = cp.ones((100, 100), dtype=cp.uint8) * 200
        rotated = rotate_image_gpu(img, 45.0)
        expected_side = int(
            100 * math.cos(math.radians(45)) + 100 * math.sin(math.radians(45))
        )
        assert rotated.shape[0] >= expected_side - 1
        assert rotated.shape[1] >= expected_side - 1

    def test_cw_and_ccw_produce_same_canvas_size(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.rotate import (
            rotate_image_gpu,
        )

        img = cp.ones((80, 120), dtype=cp.uint8) * 100
        cw = rotate_image_gpu(img, 10.0)
        ccw = rotate_image_gpu(img, -10.0)
        assert cw.shape == ccw.shape

    def test_output_dtype_preserved(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.rotate import (
            rotate_image_gpu,
        )

        img = cp.zeros((50, 50), dtype=cp.uint8)
        result = rotate_image_gpu(img, 5.0)
        assert result.dtype == cp.uint8

    def test_color_image_shape(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.rotate import (
            rotate_image_gpu,
        )

        img = cp.ones((60, 80, 3), dtype=cp.uint8) * 128
        result = rotate_image_gpu(img, 15.0)
        assert result.ndim == 3
        assert result.shape[2] == 3

    def test_border_fill_cval(self, cupy_module):
        """Corners of a rotated image should fill with cval."""
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.rotate import (
            rotate_image_gpu,
        )

        img = cp.full((50, 50), 200, dtype=cp.uint8)
        result = rotate_image_gpu(img, 45.0, cval=0)
        # After 45° rotation the corner pixels must be 0 (border fill)
        assert int(result[0, 0]) == 0

    def test_matches_cv2_shape(self, cupy_module):
        """Output shape should match cv2.warpAffine for the same angle."""
        cp = cupy_module
        pytest.importorskip("cv2")
        import cv2

        from pd_book_tools.image_processing.cupy_processing.rotate import (
            rotate_image_gpu,
        )

        img_np = np.zeros((200, 150), dtype=np.uint8)
        angle = 12.0
        h, w = img_np.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), -angle, 1.0)
        abs_cos, abs_sin = abs(M[0, 0]), abs(M[0, 1])
        new_w = int(h * abs_sin + w * abs_cos)
        new_h = int(h * abs_cos + w * abs_sin)

        result = cp.asnumpy(rotate_image_gpu(cp.asarray(img_np), angle))
        assert abs(result.shape[0] - new_h) <= 1
        assert abs(result.shape[1] - new_w) <= 1

    def test_np_wrapper_returns_numpy(self, cupy_module):
        from pd_book_tools.image_processing.cupy_processing.rotate import (
            np_uint8_rotate_image,
        )

        img = np.ones((40, 40), dtype=np.uint8) * 100
        out = np_uint8_rotate_image(img, 5.0)
        assert isinstance(out, np.ndarray)
        assert out.dtype == np.uint8
