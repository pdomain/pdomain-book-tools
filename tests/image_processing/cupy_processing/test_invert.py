"""Tests for cupy_processing.invert module."""

import pytest


@pytest.fixture
def cupy_invert(cupy_module):
    """Import the cupy invert module only when cupy is available."""
    from pd_book_tools.image_processing.cupy_processing import invert as invert_mod

    return invert_mod, cupy_module


class TestCupyInvertImage:
    def test_invert_uint8(self, cupy_invert):
        invert_mod, cp = cupy_invert
        img = cp.asarray([[0, 1, 127, 254, 255]], dtype=cp.uint8)
        out = invert_mod.invert_image(img)
        expected = cp.asarray([[255, 254, 128, 1, 0]], dtype=cp.uint8)
        assert bool((out == expected).all())

    def test_double_invert_returns_original(self, cupy_invert):
        invert_mod, cp = cupy_invert
        img = cp.random.randint(0, 256, (8, 8), dtype=cp.uint8)
        out = invert_mod.invert_image(invert_mod.invert_image(img))
        assert bool((out == img).all())
