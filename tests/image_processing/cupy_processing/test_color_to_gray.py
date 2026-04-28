"""Tests for cupy_processing.colorToGray module."""

import numpy as np
import pytest


@pytest.fixture
def cupy_color_to_gray(cupy_module):
    from pd_book_tools.image_processing.cupy_processing import colorToGray as mod

    return mod, cupy_module


class TestCupyColorToGray:
    def test_uniform_color_converts(self, cupy_color_to_gray):
        mod, cp = cupy_color_to_gray
        img = cp.full((20, 20, 3), 0.5, dtype=cp.float32)
        out = mod.cupy_colorToGray(
            img, radius=5, samples=2, iterations=2, batch_size=10
        )
        assert out.shape == (20, 20)
        assert out.dtype == cp.float32

    def test_uniform_color_with_shadows(self, cupy_color_to_gray):
        mod, cp = cupy_color_to_gray
        img = cp.full((20, 20, 3), 0.7, dtype=cp.float32)
        out = mod.cupy_colorToGray(
            img,
            radius=5,
            samples=2,
            iterations=2,
            enhance_shadows=True,
            batch_size=10,
        )
        assert out.shape == (20, 20)


class TestNpUint8FloatColorToGray:
    def test_returns_uint8_grayscale(self, cupy_color_to_gray):
        mod, _ = cupy_color_to_gray
        img = np.full((20, 20, 3), 128, dtype=np.uint8)
        out = mod.np_uint8_float_colorToGray(
            img, radius=5, samples=2, iterations=2, batch_size=10
        )
        assert out.dtype == np.uint8
        assert out.shape == (20, 20)
