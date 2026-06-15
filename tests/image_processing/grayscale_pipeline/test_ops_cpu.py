"""Tests for CPU color-to-grayscale converter ops."""

import numpy as np

from pdomain_book_tools.image_processing.grayscale_pipeline import ops_cpu


def _img() -> np.ndarray:
    rng = np.random.default_rng(7)
    return rng.integers(0, 256, size=(32, 48, 3), dtype=np.uint8)  # BGR


def test_luma_bt601_shape_dtype() -> None:
    out = ops_cpu.luma(_img(), bt709=False)
    assert out.shape == (32, 48)
    assert out.dtype == np.uint8


def test_bt601_differs_from_bt709() -> None:
    img = _img()
    assert np.any(ops_cpu.luma(img, bt709=False) != ops_cpu.luma(img, bt709=True))


def test_lab_l_differs_from_luma() -> None:
    img = _img()
    assert np.any(ops_cpu.lab_l(img) != ops_cpu.luma(img, bt709=False))


def test_best_channel_green_returns_green() -> None:
    img = np.zeros((4, 4, 3), np.uint8)
    img[..., 1] = 200  # BGR green = index 1
    assert np.all(ops_cpu.best_channel(img, "green") == 200)


def test_best_channel_auto_picks_highest_variance() -> None:
    img = np.zeros((8, 8, 3), np.uint8)
    img[..., 0] = 100  # blue flat
    img[:, ::2, 2] = 255  # red high variance
    assert np.array_equal(ops_cpu.best_channel(img, "auto"), img[..., 2])
