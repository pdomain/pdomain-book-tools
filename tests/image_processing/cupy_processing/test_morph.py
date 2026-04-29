"""Tests for cupy_processing.morph module."""

import pytest


@pytest.fixture
def cupy_morph(cupy_module):
    from pd_book_tools.image_processing.cupy_processing import morph as morph_mod

    return morph_mod, cupy_module


class TestCupyMorph:
    def test_dilate_expands_single_pixel(self, cupy_morph):
        morph_mod, cp = cupy_morph
        img = cp.zeros((5, 5), dtype=cp.uint8)
        img[2, 2] = 1
        kernel = cp.ones((3, 3), dtype=cp.uint8)
        out = morph_mod.dilate(img, kernel)
        # Dilation with a 3x3 kernel expands the single 1 to a 3x3 square
        assert int(out.sum()) >= 9

    def test_erode_removes_lone_pixel(self, cupy_morph):
        morph_mod, cp = cupy_morph
        img = cp.zeros((5, 5), dtype=cp.uint8)
        img[2, 2] = 1
        kernel = cp.ones((3, 3), dtype=cp.uint8)
        out = morph_mod.erode(img, kernel)
        # Erosion of a single pixel with a 3x3 kernel removes it
        assert int(out.sum()) == 0

    def test_morph_fill_preserves_blob(self, cupy_morph):
        morph_mod, cp = cupy_morph
        img = cp.zeros((10, 10), dtype=cp.uint8)
        img[3:7, 3:7] = 1
        out = morph_mod.morph_fill(img, shape=(3, 3))
        assert tuple(out.shape) == (10, 10)
