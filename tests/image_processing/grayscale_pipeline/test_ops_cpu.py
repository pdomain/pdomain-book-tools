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


def test_flatten_reduces_low_frequency_gradient() -> None:
    # synthetic uneven illumination: a bright ramp across a mid-gray page
    h, w = 64, 64
    ramp = np.tile(np.linspace(60, 200, w, dtype=np.float32), (h, 1))
    img = np.stack([ramp, ramp, ramp], axis=-1).astype(np.uint8)
    flat = ops_cpu.flatten(img, radius=24, strength=1.0)
    # after flattening, the column-mean spread should shrink markedly
    before = float(img[..., 1].mean(axis=0).std())
    after = float(flat[..., 1].mean(axis=0).std())
    assert after < before * 0.5


def test_clahe_increases_local_contrast_on_faded() -> None:
    faded = np.random.default_rng(1).integers(110, 140, size=(64, 64), dtype=np.uint8)
    out = ops_cpu.clahe(faded, clip_limit=3.0, tile_grid=8)
    assert float(out.std()) > float(faded.std())


def test_output_range_stretches() -> None:
    g = np.full((8, 8), 128, np.uint8)
    g[0, 0] = 100
    g[0, 1] = 150
    out = ops_cpu.apply_output_range(g, (0, 255))
    assert out.min() == 0
    assert out.max() == 255
