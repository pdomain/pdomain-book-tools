"""Tests for cv2_processing.threshold module."""

import numpy as np
import pytest

pytest.importorskip("cv2")

from pdomain_book_tools.image_processing.cv2_processing.threshold import (
    adaptive_binary_thresh,
    binarize,
    binary_thresh,
    niblack_binary_thresh,
    otsu_binary_thresh,
    sauvola_binary_thresh,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _gradient_with_text_fixture() -> np.ndarray:
    """100x100 image: smooth brightness gradient + 4 dark 10x10 'text' patches.

    The gradient alone would confuse global Otsu (the boundary is near the
    gradient midpoint, not at the dark patches); local methods should recover
    the dark patches as 0 pixels regardless.
    """
    h, w = 100, 100
    # Horizontal gradient 80..220 — bright background, no perfect bimodal split
    gradient = np.tile(np.linspace(80, 220, w, dtype=np.float32), (h, 1)).astype(
        np.uint8
    )
    # Four 10x10 dark text patches (value=10)
    for r, col in [(10, 10), (30, 60), (60, 15), (75, 70)]:
        gradient[r : r + 10, col : col + 10] = 10
    return gradient


# ---------------------------------------------------------------------------
# binary_thresh
# ---------------------------------------------------------------------------


class TestBinaryThresh:
    def test_default_level(self):
        img = np.array([[0, 100, 127, 128, 200, 255]], dtype=np.uint8)
        out = binary_thresh(img)
        # Default level=127: values <=127 -> 0, > 127 -> 255
        assert out.shape == img.shape
        assert out[0, 0] == 0
        assert out[0, 1] == 0
        assert out[0, 2] == 0
        assert out[0, 3] == 255
        assert out[0, 4] == 255
        assert out[0, 5] == 255

    def test_custom_level(self):
        img = np.array([[0, 50, 100, 150, 200, 255]], dtype=np.uint8)
        out = binary_thresh(img, level=200)
        assert out[0, 0] == 0
        assert out[0, 4] == 0
        assert out[0, 5] == 255


# ---------------------------------------------------------------------------
# otsu_binary_thresh
# ---------------------------------------------------------------------------


class TestOtsuBinaryThresh:
    def test_bimodal_image(self):
        # Create a bimodal image - clearly two clusters
        img = np.zeros((20, 20), dtype=np.uint8)
        img[:10, :] = 30
        img[10:, :] = 220
        out = otsu_binary_thresh(img)
        # Otsu should split into 0 and 255 along that boundary
        assert out.dtype == np.uint8
        # All values should be either 0 or 255
        unique = np.unique(out)
        assert set(unique.tolist()).issubset({0, 255})
        # The dark and light regions should map to 0 and 255 respectively
        assert (out[:10, :] == 0).all()
        assert (out[10:, :] == 255).all()


# ---------------------------------------------------------------------------
# adaptive_binary_thresh
# ---------------------------------------------------------------------------


class TestAdaptiveBinaryThresh:
    def test_returns_uint8_binary(self):
        img = _gradient_with_text_fixture()
        out = adaptive_binary_thresh(img)
        assert out.dtype == np.uint8
        assert out.shape == img.shape
        assert set(np.unique(out).tolist()).issubset({0, 255})

    def test_gaussian_mode(self):
        img = _gradient_with_text_fixture()
        out = adaptive_binary_thresh(img, mode="gaussian")
        assert out.dtype == np.uint8
        assert set(np.unique(out).tolist()).issubset({0, 255})

    def test_mean_mode(self):
        img = _gradient_with_text_fixture()
        out = adaptive_binary_thresh(img, mode="mean")
        assert out.dtype == np.uint8
        assert set(np.unique(out).tolist()).issubset({0, 255})

    def test_unknown_mode_raises_value_error(self):
        img = np.zeros((10, 10), dtype=np.uint8)
        with pytest.raises(ValueError, match="Unknown adaptive mode"):
            adaptive_binary_thresh(img, mode="bogus")

    def test_recovers_dark_text_patches(self):
        """Adaptive method should classify dark text pixels as 0."""
        img = _gradient_with_text_fixture()
        out = adaptive_binary_thresh(img, block_size=31, c=10)
        # The four dark text patches (value=10) should be majority 0 (text)
        # Centre pixels of each patch (far from borders) should be 0
        for r, col in [(15, 15), (35, 65), (65, 20), (80, 75)]:
            assert out[r, col] == 0, f"Expected 0 at ({r},{col}), got {out[r, col]}"


# ---------------------------------------------------------------------------
# sauvola_binary_thresh
# ---------------------------------------------------------------------------


class TestSauvolaBinaryThresh:
    def test_returns_uint8_binary(self):
        img = _gradient_with_text_fixture()
        out = sauvola_binary_thresh(img)
        assert out.dtype == np.uint8
        assert out.shape == img.shape
        assert set(np.unique(out).tolist()).issubset({0, 255})

    def test_recovers_dark_text_where_otsu_struggles(self):
        """Sauvola should classify dark text pixels as 0 on a gradient image
        where global Otsu misclassifies parts of the gradient as text."""
        img = _gradient_with_text_fixture()
        otsu_out = otsu_binary_thresh(img)
        sauvola_out = sauvola_binary_thresh(img)

        # Sauvola should find dark patches — centre pixels must be 0
        for r, col in [(15, 15), (35, 65), (65, 20), (80, 75)]:
            assert sauvola_out[r, col] == 0, (
                f"Sauvola: expected 0 at ({r},{col}), got {sauvola_out[r, col]}"
            )

        # Sauvola and Otsu should both classify the brightest background pixels as 255
        assert otsu_out[50, 99] == 255
        assert sauvola_out[50, 99] == 255

    def test_custom_params(self):
        img = _gradient_with_text_fixture()
        out = sauvola_binary_thresh(img, window_size=15, k=0.1, r=64)
        assert out.dtype == np.uint8
        assert set(np.unique(out).tolist()).issubset({0, 255})


# ---------------------------------------------------------------------------
# niblack_binary_thresh
# ---------------------------------------------------------------------------


class TestNiblackBinaryThresh:
    def test_returns_uint8_binary(self):
        img = _gradient_with_text_fixture()
        out = niblack_binary_thresh(img)
        assert out.dtype == np.uint8
        assert out.shape == img.shape
        assert set(np.unique(out).tolist()).issubset({0, 255})

    def test_recovers_dark_text_where_otsu_struggles(self):
        """Niblack should classify dark text pixels as 0 on a gradient image."""
        img = _gradient_with_text_fixture()
        niblack_out = niblack_binary_thresh(img)

        # Niblack should find dark patches — centre pixels must be 0
        for r, col in [(15, 15), (35, 65), (65, 20), (80, 75)]:
            assert niblack_out[r, col] == 0, (
                f"Niblack: expected 0 at ({r},{col}), got {niblack_out[r, col]}"
            )

    def test_custom_params(self):
        img = _gradient_with_text_fixture()
        out = niblack_binary_thresh(img, window_size=15, k=-0.1)
        assert out.dtype == np.uint8
        assert set(np.unique(out).tolist()).issubset({0, 255})


# ---------------------------------------------------------------------------
# binarize dispatcher
# ---------------------------------------------------------------------------


class TestBinarize:
    def test_default_method_is_otsu(self):
        img = np.zeros((20, 20), dtype=np.uint8)
        img[:10, :] = 30
        img[10:, :] = 220
        out = binarize(img)
        expected = otsu_binary_thresh(img)
        assert np.array_equal(out, expected)

    def test_explicit_otsu_matches_helper(self):
        img = np.zeros((20, 20), dtype=np.uint8)
        img[:10, :] = 30
        img[10:, :] = 220
        assert np.array_equal(binarize(img, method="otsu"), otsu_binary_thresh(img))

    def test_adaptive_method_dispatches(self):
        img = _gradient_with_text_fixture()
        out = binarize(img, method="adaptive")
        expected = adaptive_binary_thresh(img)
        assert np.array_equal(out, expected)

    def test_sauvola_method_dispatches(self):
        img = _gradient_with_text_fixture()
        out = binarize(img, method="sauvola")
        expected = sauvola_binary_thresh(img)
        assert np.array_equal(out, expected)

    def test_niblack_method_dispatches(self):
        img = _gradient_with_text_fixture()
        out = binarize(img, method="niblack")
        expected = niblack_binary_thresh(img)
        assert np.array_equal(out, expected)

    def test_adaptive_params_forwarded(self):
        img = _gradient_with_text_fixture()
        out = binarize(img, method="adaptive", block_size=21, c=5)
        expected = adaptive_binary_thresh(img, block_size=21, c=5)
        assert np.array_equal(out, expected)

    def test_sauvola_params_forwarded(self):
        img = _gradient_with_text_fixture()
        out = binarize(img, method="sauvola", window_size=15, k=0.15)
        expected = sauvola_binary_thresh(img, window_size=15, k=0.15)
        assert np.array_equal(out, expected)

    def test_niblack_params_forwarded(self):
        img = _gradient_with_text_fixture()
        out = binarize(img, method="niblack", window_size=15, k=-0.15)
        expected = niblack_binary_thresh(img, window_size=15, k=-0.15)
        assert np.array_equal(out, expected)

    def test_unknown_method_raises_value_error(self):
        img = np.zeros((4, 4), dtype=np.uint8)
        with pytest.raises(ValueError):
            binarize(img, method="bogus")
