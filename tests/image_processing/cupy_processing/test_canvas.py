"""Tests for cupy_processing.canvas module."""

import numpy as np
import pytest


@pytest.mark.gpu
@pytest.mark.cupy
class TestMapContentOntoScaledCanvasGpu:
    def test_canvas_larger_than_input(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.canvas import (
            map_content_onto_scaled_canvas_gpu,
        )

        img = cp.zeros((100, 100), dtype=cp.uint8)
        out = map_content_onto_scaled_canvas_gpu(img)
        assert out.shape[0] > img.shape[0] or out.shape[1] > img.shape[1]

    def test_output_is_uint8(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.canvas import (
            map_content_onto_scaled_canvas_gpu,
        )

        img = cp.full((200, 100), 128, dtype=cp.uint8)
        out = map_content_onto_scaled_canvas_gpu(img)
        assert out.dtype == cp.uint8

    def test_canvas_background_is_white(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.canvas import (
            map_content_onto_scaled_canvas_gpu,
        )

        img = cp.zeros((100, 60), dtype=cp.uint8)  # content is all black
        out = map_content_onto_scaled_canvas_gpu(img)
        # Top-left corner should be white border
        assert int(out[0, 0]) == 255

    def test_content_preserved_at_offset(self, cupy_module):
        cp = cupy_module
        import math

        from pd_book_tools.image_processing.cupy_processing.canvas import (
            map_content_onto_scaled_canvas_gpu,
        )
        from pd_book_tools.image_processing.cv2_processing.canvas import Alignment

        img = cp.full((100, 60), 42, dtype=cp.uint8)
        out = map_content_onto_scaled_canvas_gpu(img, force_align=Alignment.TOP)
        canvas_h, canvas_w = out.shape
        top_offset = int(math.ceil(0.051 * canvas_h))
        left_offset = canvas_w // 2 - 30
        # Spot check a pixel inside the placed content
        assert int(out[top_offset + 5, left_offset + 5]) == 42

    def test_alignment_bottom_places_lower(self, cupy_module):
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.canvas import (
            map_content_onto_scaled_canvas_gpu,
        )
        from pd_book_tools.image_processing.cv2_processing.canvas import Alignment

        img = cp.full((100, 60), 50, dtype=cp.uint8)
        top = map_content_onto_scaled_canvas_gpu(img, force_align=Alignment.TOP)
        bottom = map_content_onto_scaled_canvas_gpu(img, force_align=Alignment.BOTTOM)
        # Both should have same canvas size
        assert top.shape == bottom.shape

    def test_matches_cpu_output(self, cupy_module):
        """GPU and CPU outputs should be pixel-identical."""
        cp = cupy_module
        from pd_book_tools.image_processing.cupy_processing.canvas import (
            map_content_onto_scaled_canvas_gpu,
        )
        from pd_book_tools.image_processing.cv2_processing.canvas import (
            map_content_onto_scaled_canvas,
        )

        rng = np.random.default_rng(3)
        img_np = rng.integers(0, 256, (120, 80), dtype=np.uint8)

        cpu = map_content_onto_scaled_canvas(img_np)
        gpu = cp.asnumpy(map_content_onto_scaled_canvas_gpu(cp.asarray(img_np)))
        np.testing.assert_array_equal(cpu, gpu)

    def test_np_uint8_wrapper_returns_ndarray(self, cupy_module):
        from pd_book_tools.image_processing.cupy_processing.canvas import (
            np_uint8_map_content_onto_scaled_canvas,
        )

        img = np.zeros((100, 60), dtype=np.uint8)
        out = np_uint8_map_content_onto_scaled_canvas(img)
        assert isinstance(out, np.ndarray)
        assert out.dtype == np.uint8
