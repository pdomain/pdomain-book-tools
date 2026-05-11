"""Tests for cupy_processing.color_to_gray module."""

import numpy as np
import pytest


@pytest.fixture
def cupy_color_to_gray(cupy_module):
    from pd_book_tools.image_processing.cupy_processing import color_to_gray as mod

    return mod, cupy_module


class TestCupyColorToGray:
    def test_uniform_color_converts(self, cupy_color_to_gray):
        mod, cp = cupy_color_to_gray
        img = cp.full((20, 20, 3), 0.5, dtype=cp.float32)
        out = mod.cupy_color_to_gray(
            img, radius=5, samples=2, iterations=2, batch_size=10
        )
        assert out.shape == (20, 20)
        assert out.dtype == cp.float32

    def test_uniform_color_with_shadows(self, cupy_color_to_gray):
        mod, cp = cupy_color_to_gray
        img = cp.full((20, 20, 3), 0.7, dtype=cp.float32)
        out = mod.cupy_color_to_gray(
            img,
            radius=5,
            samples=2,
            iterations=2,
            enhance_shadows=True,
            batch_size=10,
        )
        assert out.shape == (20, 20)

    def test_rejects_2d_grayscale_input(self, cupy_color_to_gray):
        """M-18 regression: a 2-D grayscale input must be rejected at the
        public boundary with a clear ValueError naming the actual issue,
        rather than a confusing `ValueError: not enough values to unpack`
        from `height, width, _ = img.shape` deep inside the helper."""
        mod, cp = cupy_color_to_gray
        img = cp.full((20, 20), 0.5, dtype=cp.float32)
        with pytest.raises(ValueError, match=r"2-D grayscale|3-channel|ndim"):
            mod.cupy_color_to_gray(
                img, radius=5, samples=2, iterations=2, batch_size=10
            )

    def test_accepts_4channel_rgba_dropping_alpha(self, cupy_color_to_gray):
        """M-18 regression: a 4-channel RGBA input is accepted (matching
        cv2's COLOR_BGRA2GRAY semantics, which ignore alpha rather than
        alpha-blending). Output must equal the result of running the
        same call on the BGR-only slice — i.e. the alpha channel content
        must not affect the gray output."""
        mod, cp = cupy_color_to_gray
        # Use a deterministic RNG so both calls operate on identical data.
        cp.random.seed(0)
        rgb = cp.random.uniform(0, 1, (20, 20, 3)).astype(cp.float32)
        # Construct a 4-channel image whose alpha channel carries arbitrary
        # values that should be ignored.
        alpha = cp.random.uniform(0, 1, (20, 20, 1)).astype(cp.float32)
        rgba = cp.concatenate([rgb, alpha], axis=2)

        cp.random.seed(42)
        out_rgba = mod.cupy_color_to_gray(
            rgba, radius=5, samples=2, iterations=2, batch_size=10
        )
        cp.random.seed(42)
        out_rgb = mod.cupy_color_to_gray(
            rgb, radius=5, samples=2, iterations=2, batch_size=10
        )
        assert out_rgba.shape == (20, 20)
        assert cp.allclose(out_rgba, out_rgb)

    def test_rejects_single_channel_3d_input(self, cupy_color_to_gray):
        """M-18 regression: a (H, W, 1) input is invalid (insufficient
        channels) and must raise rather than silently produce garbage."""
        mod, cp = cupy_color_to_gray
        img = cp.full((20, 20, 1), 0.5, dtype=cp.float32)
        with pytest.raises(ValueError, match=r"3 channels|channel"):
            mod.cupy_color_to_gray(
                img, radius=5, samples=2, iterations=2, batch_size=10
            )


class TestNpUint8FloatColorToGray:
    def test_returns_uint8_grayscale(self, cupy_color_to_gray):
        mod, _ = cupy_color_to_gray
        img = np.full((20, 20, 3), 128, dtype=np.uint8)
        out = mod.np_uint8_color_to_gray(
            img, radius=5, samples=2, iterations=2, batch_size=10
        )
        assert out.dtype == np.uint8
        assert out.shape == (20, 20)

    def test_rejects_float32_input(self):
        """M-17 regression: float32 [0, 1] input must not silently be divided
        by 255 (which would collapse it to [0, 0.004] and produce a near-black
        result). The function's name documents a uint8 contract; non-uint8
        input must raise rather than silently mis-handle."""
        # Lazy import: this test does not need cupy/CUDA — the dtype check
        # runs before any cp.asarray call. Skip only if numpy is missing.
        from pd_book_tools.image_processing.cupy_processing import (
            color_to_gray as mod,
        )

        img = np.full((20, 20, 3), 0.5, dtype=np.float32)
        with pytest.raises(TypeError, match="uint8"):
            mod.np_uint8_color_to_gray(
                img, radius=5, samples=2, iterations=2, batch_size=10
            )

    def test_rejects_float64_input(self):
        """M-17 regression: float64 input is also rejected (same silent-collapse
        risk as float32)."""
        from pd_book_tools.image_processing.cupy_processing import (
            color_to_gray as mod,
        )

        img = np.full((20, 20, 3), 0.5, dtype=np.float64)
        with pytest.raises(TypeError, match="uint8"):
            mod.np_uint8_color_to_gray(
                img, radius=5, samples=2, iterations=2, batch_size=10
            )
