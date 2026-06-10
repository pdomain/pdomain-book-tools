"""Tests for cv2_processing.denoise module."""

import numpy as np
import pytest

pytest.importorskip("cv2")

from pdomain_book_tools.image_processing.cv2_processing.denoise import denoise_binary

# ---------------------------------------------------------------------------
# Synthetic fixture helpers
# ---------------------------------------------------------------------------


def _synthetic_page_with_speckle() -> np.ndarray:
    """Binary page image (text=0, background=255) with text strokes + speckle.

    Layout (300x200 canvas, all background=255):
    - A thick horizontal text stroke at rows 50-65 (simulates a text line).
    - A vertical stroke at cols 80-90, rows 30-80 (letter stem).
    - A period-sized dot (5x5 px, area=25) at row 150, col 50.
    - Single-pixel speckle scattered in the background (area=1).
    - A 2x2 cluster speckle (area=4) at row 180, col 180.
    """
    img = np.full((300, 200), 255, dtype=np.uint8)
    # Horizontal text line (background strip)
    img[50:65, 20:180] = 0
    # Vertical letter stem
    img[30:80, 80:90] = 0
    # Period-sized dot (5x5 = 25 px^2 — must survive default denoise)
    img[150:155, 50:55] = 0
    # Salt-and-pepper speckle (single pixels — must be removed)
    speckle_coords = [
        (10, 10),
        (20, 150),
        (90, 170),
        (200, 30),
        (250, 100),
        (5, 5),
        (280, 190),
        (100, 100),
        (60, 10),
        (60, 195),
    ]
    for r, c in speckle_coords:
        img[r, c] = 0
    # 2x2 cluster speckle (area=4 — must be removed at default min_component_area=6)
    img[180:182, 180:182] = 0
    return img


# ---------------------------------------------------------------------------
# Core behaviour
# ---------------------------------------------------------------------------


class TestDenoiseBinarySpeckleRemoval:
    def test_single_pixel_speckle_removed(self):
        """Single-pixel background specks (area=1) must be erased."""
        img = _synthetic_page_with_speckle()
        out = denoise_binary(img)
        assert out[10, 10] == 255, "Single-pixel speckle must be removed"
        assert out[20, 150] == 255

    def test_cluster_speckle_below_threshold_removed(self):
        """2x2 cluster (area=4) below default min_component_area=6 must be removed."""
        img = _synthetic_page_with_speckle()
        out = denoise_binary(img)
        assert (out[180:182, 180:182] == 255).all(), (
            "2x2 speckle cluster must be removed"
        )

    def test_text_stroke_preserved(self):
        """Thick text strokes must survive denoising."""
        img = _synthetic_page_with_speckle()
        out = denoise_binary(img)
        # Centre of the horizontal stroke must remain text (0)
        assert out[57, 100] == 0, "Text stroke centre must be preserved"

    def test_period_sized_dot_preserved_at_default_settings(self):
        """A 5x5 period dot (area=25) must survive at the default min_component_area=6."""
        img = _synthetic_page_with_speckle()
        out = denoise_binary(img)
        # Centre of the period dot
        assert out[152, 52] == 0, "Period-sized dot (25 px) must be preserved"

    def test_diacritic_sized_dot_preserved_at_default_settings(self):
        """A 3x3 dot (area=9 >= 6) must also be preserved by default."""
        img = np.full((100, 100), 255, dtype=np.uint8)
        img[40:43, 40:43] = 0  # 3x3 dot, area=9
        out = denoise_binary(img)
        assert (out[40:43, 40:43] == 0).all(), (
            "3x3 diacritic dot (9 px) must be preserved"
        )


# ---------------------------------------------------------------------------
# Idempotence
# ---------------------------------------------------------------------------


class TestDenoiseBinaryIdempotence:
    def test_applying_twice_equals_once(self):
        """denoise_binary(denoise_binary(x)) == denoise_binary(x)."""
        img = _synthetic_page_with_speckle()
        once = denoise_binary(img)
        twice = denoise_binary(once)
        np.testing.assert_array_equal(
            once, twice, err_msg="denoise_binary must be idempotent"
        )


# ---------------------------------------------------------------------------
# Dtype and shape preservation
# ---------------------------------------------------------------------------


class TestDenoiseBinaryArrayProperties:
    def test_dtype_preserved(self):
        img = _synthetic_page_with_speckle()
        out = denoise_binary(img)
        assert out.dtype == np.uint8

    def test_shape_preserved(self):
        img = _synthetic_page_with_speckle()
        out = denoise_binary(img)
        assert out.shape == img.shape

    def test_output_is_binary(self):
        """Output values must only be 0 or 255."""
        img = _synthetic_page_with_speckle()
        out = denoise_binary(img)
        assert set(np.unique(out).tolist()).issubset({0, 255})


# ---------------------------------------------------------------------------
# Input immutability
# ---------------------------------------------------------------------------


class TestDenoiseBinaryInputUnmodified:
    def test_input_not_mutated(self):
        """denoise_binary must never modify the caller's array in-place."""
        img = _synthetic_page_with_speckle()
        original = img.copy()
        _out = denoise_binary(img)
        np.testing.assert_array_equal(
            img, original, err_msg="Input array must not be mutated"
        )


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestDenoiseBinaryEdgeCases:
    def test_all_white_image_unchanged(self):
        """A blank white page (no ink) should come back as all-255."""
        img = np.full((50, 50), 255, dtype=np.uint8)
        out = denoise_binary(img)
        assert (out == 255).all()

    def test_all_black_image_unchanged(self):
        """A fully-inked page should survive (one huge component)."""
        img = np.zeros((50, 50), dtype=np.uint8)
        out = denoise_binary(img)
        assert (out == 0).all()

    def test_custom_min_component_area_removes_period(self):
        """Setting min_component_area=30 must remove a 5x5 dot (area=25)."""
        img = np.full((100, 100), 255, dtype=np.uint8)
        img[40:45, 40:45] = 0  # 5x5 dot, area=25
        out = denoise_binary(img, min_component_area=30)
        assert (out[40:45, 40:45] == 255).all(), (
            "5x5 dot must be removed when threshold=30"
        )

    def test_custom_min_component_area_preserves_period(self):
        """Setting min_component_area=3 must preserve a 5x5 dot (area=25)."""
        img = np.full((100, 100), 255, dtype=np.uint8)
        img[40:45, 40:45] = 0  # 5x5 dot, area=25
        out = denoise_binary(img, min_component_area=3)
        assert (out[40:45, 40:45] == 0).all(), "5x5 dot must be kept when threshold=3"

    def test_median_kernel_reduces_speckle(self):
        """With median_kernel_size=3, single-pixel speckle must also be removed."""
        img = np.full((100, 100), 255, dtype=np.uint8)
        img[50, 50] = 0  # single speckle pixel
        out = denoise_binary(img, median_kernel_size=3)
        assert out[50, 50] == 255, (
            "Single-pixel speckle must be removed with median pre-pass"
        )

    def test_invalid_ndim_raises(self):
        """3-D arrays must raise ValueError."""
        img_3d = np.zeros((10, 10, 3), dtype=np.uint8)
        with pytest.raises(ValueError, match="2-D"):
            denoise_binary(img_3d)  # type: ignore[arg-type]

    def test_invalid_dtype_raises(self):
        """Non-uint8 arrays must raise ValueError."""
        img_float = np.zeros((10, 10), dtype=np.float32)
        with pytest.raises(ValueError, match="uint8"):
            denoise_binary(img_float)  # type: ignore[arg-type]

    def test_invalid_even_median_kernel_raises(self):
        """Even kernel sizes must raise ValueError."""
        img = np.zeros((10, 10), dtype=np.uint8)
        with pytest.raises(ValueError, match="odd"):
            denoise_binary(img, median_kernel_size=4)

    def test_invalid_negative_median_kernel_raises(self):
        """Negative kernel sizes must raise ValueError."""
        img = np.zeros((10, 10), dtype=np.uint8)
        with pytest.raises(ValueError, match="odd"):
            denoise_binary(img, median_kernel_size=-1)
