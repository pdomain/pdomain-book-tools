"""Tests for cupy_processing.rescale module."""

import numpy as np
import pytest


@pytest.mark.gpu
@pytest.mark.cupy
class TestRescaleImageGpu:
    def test_portrait_short_side_becomes_target(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.rescale import (
            rescale_image_gpu,
        )

        img = cp.zeros((400, 200), dtype=cp.uint8)
        out = rescale_image_gpu(img, target_short_side=100)
        assert out.shape[1] == 100  # width is short side
        assert out.shape[0] == 200  # height scales by 0.5

    def test_landscape_short_side_becomes_target(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.rescale import (
            rescale_image_gpu,
        )

        img = cp.zeros((200, 400), dtype=cp.uint8)
        out = rescale_image_gpu(img, target_short_side=100)
        assert out.shape[0] == 100  # height is short side
        assert out.shape[1] == 200

    def test_output_is_uint8(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.rescale import (
            rescale_image_gpu,
        )

        img = cp.full((300, 200), 128, dtype=cp.uint8)
        out = rescale_image_gpu(img, target_short_side=100)
        assert out.dtype == cp.uint8

    def test_color_image_preserves_channels(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.rescale import (
            rescale_image_gpu,
        )

        img = cp.zeros((300, 200, 3), dtype=cp.uint8)
        out = rescale_image_gpu(img, target_short_side=100)
        assert out.ndim == 3
        assert out.shape[2] == 3

    def test_matches_cpu_output_shape(self, cupy_module):
        """GPU output shape must exactly match CPU reference."""
        cp = cupy_module
        pytest.importorskip("cv2")
        from pd_book_tools.image_processing.cupy_processing.rescale import (
            rescale_image_gpu,
        )
        from pd_book_tools.image_processing.cv2_processing.rescale import rescale_image

        img_np = np.zeros((400, 200), dtype=np.uint8)
        cpu_out = rescale_image(img_np, target_short_side=100)
        gpu_out = rescale_image_gpu(cp.asarray(img_np), target_short_side=100)

        assert cpu_out.shape == tuple(gpu_out.shape)

    def test_np_uint8_rescale_image_wrapper(self, cupy_module):
        from pd_book_tools.image_processing.cupy_processing.rescale import (
            np_uint8_rescale_image,
        )

        img = np.zeros((400, 200), dtype=np.uint8)
        out = np_uint8_rescale_image(img, target_short_side=100)
        assert isinstance(out, np.ndarray)
        assert out.shape[1] == 100
        assert out.dtype == np.uint8
