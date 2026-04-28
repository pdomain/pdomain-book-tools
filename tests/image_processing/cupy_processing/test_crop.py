"""Tests for cupy_processing.crop module."""

import pytest


@pytest.fixture
def cupy_crop(cupy_module):
    from pd_book_tools.image_processing.cupy_processing import crop as crop_mod

    return crop_mod, cupy_module


class TestCupyCropToRectangle:
    def test_basic_crop(self, cupy_crop):
        crop_mod, cp = cupy_crop
        img = cp.arange(100, dtype=cp.uint8).reshape(10, 10)
        cropped = crop_mod.crop_to_rectangle(img, 2, 8, 1, 5)
        assert tuple(cropped.shape) == (4, 6)

    def test_invalid_returns_original(self, cupy_crop):
        crop_mod, cp = cupy_crop
        img = cp.zeros((10, 10), dtype=cp.uint8)
        out = crop_mod.crop_to_rectangle(img, 8, 3, 2, 5)
        assert out is img

    def test_clamps_to_bounds(self, cupy_crop):
        crop_mod, cp = cupy_crop
        img = cp.zeros((10, 10), dtype=cp.uint8)
        cropped = crop_mod.crop_to_rectangle(img, -5, 20, -3, 15)
        # Should produce a valid crop
        assert cropped.shape[0] > 0
        assert cropped.shape[1] > 0


class TestCupyCropEdges:
    def test_crop_each_edge(self, cupy_crop):
        crop_mod, cp = cupy_crop
        img = cp.arange(100, dtype=cp.uint8).reshape(10, 10)
        out = crop_mod.crop_edges(img, top=1, bottom=2, left=3, right=4)
        assert tuple(out.shape) == (7, 3)

    def test_no_crop_returns_same_shape(self, cupy_crop):
        crop_mod, cp = cupy_crop
        img = cp.zeros((6, 6), dtype=cp.uint8)
        out = crop_mod.crop_edges(img)
        assert tuple(out.shape) == (6, 6)

    def test_excessive_crop_raises(self, cupy_crop):
        crop_mod, cp = cupy_crop
        img = cp.zeros((10, 10), dtype=cp.uint8)
        with pytest.raises(ValueError, match="exceed"):
            crop_mod.crop_edges(img, top=6, bottom=5)
