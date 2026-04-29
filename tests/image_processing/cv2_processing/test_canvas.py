"""Tests for cv2_processing.canvas module."""

import numpy as np
import pytest

from pd_book_tools.image_processing.cv2_processing.canvas import (
    Alignment,
    map_content_onto_scaled_canvas,
)


def _make_image(h: int, w: int, fill: int = 0) -> np.ndarray:
    return np.full((h, w), fill, dtype=np.uint8)


class TestAlignmentEnum:
    def test_alignment_values(self):
        assert Alignment.TOP.value == "top"
        assert Alignment.CENTER.value == "center"
        assert Alignment.BOTTOM.value == "bottom"
        assert Alignment.DEFAULT.value == "default"


class TestMapContentOntoScaledCanvas:
    def test_default_alignment_taller_than_target_ratio(self):
        # Image taller than wide: ratio (h/w) >= height_width_ratio path
        img = _make_image(330, 100)
        out = map_content_onto_scaled_canvas(img)

        # canvas should be at least as large as the source
        assert out.shape[0] >= img.shape[0]
        assert out.shape[1] >= img.shape[1]
        # canvas should be white (255) wherever image was not placed
        assert out.dtype == np.uint8
        # The corners should be the canvas fill (255)
        assert out[0, 0] == 255
        assert out[0, -1] == 255
        assert out[-1, 0] == 255
        assert out[-1, -1] == 255

    def test_default_alignment_wider_than_target_ratio(self):
        # Image wide enough that current ratio < target ratio
        img = _make_image(50, 200)
        out = map_content_onto_scaled_canvas(img)

        assert out.shape[0] >= img.shape[0]
        assert out.shape[1] >= img.shape[1]

    @pytest.mark.parametrize(
        "alignment",
        [Alignment.TOP, Alignment.CENTER, Alignment.BOTTOM, Alignment.DEFAULT],
    )
    def test_alignment_options(self, alignment):
        img = _make_image(165, 100)
        out = map_content_onto_scaled_canvas(img, force_align=alignment)
        assert out.shape[0] >= img.shape[0]
        assert out.shape[1] >= img.shape[1]

    def test_image_content_preserved(self):
        # Use a non-trivial fill to verify the image is placed onto the canvas
        img = _make_image(165, 100, fill=42)
        out = map_content_onto_scaled_canvas(
            img, force_align=Alignment.CENTER, whitespace_add=0.05
        )
        # The image's pixel value should appear somewhere in the canvas
        assert (out == 42).any()
        # And a lot of the canvas should still be the white background
        assert (out == 255).any()

    def test_custom_height_width_ratio(self):
        img = _make_image(100, 100)
        out = map_content_onto_scaled_canvas(
            img, height_width_ratio=2.0, whitespace_add=0.0
        )
        assert out.shape[0] >= img.shape[0]
        assert out.shape[1] >= img.shape[1]
