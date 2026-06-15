"""Parity tests for GPU color-to-grayscale converter ops.

Each test guards itself with ``_has_cupy()`` and verifies that the GPU wrapper
returns output within a defined tolerance of the CPU reference implementation.

Tolerances (mean absolute difference on uint8 outputs):
- luma_gpu:         <= 1.0  (weighted sum, no non-linear ops)
- lab_l_gpu:        <= 3.0  (delegates to CPU ops_cpu.lab_l; exact match expected)
- best_channel_gpu: exact   (selects a channel, no arithmetic)
- flatten_gpu:      <= 3.0  (Gaussian kernel slight numerical variation GPU vs CPU)
- clahe_gpu:        <= 3.0  (delegates to CPU ops_cpu.clahe; exact match expected)
"""

from __future__ import annotations

import numpy as np
import pytest


def _has_cupy() -> bool:
    try:
        from pdomain_book_tools.image_processing.cupy_processing._cupy_compat import (
            require_cupy,
        )

        require_cupy()
    except ImportError:
        return False
    else:
        return True


def _img_color() -> np.ndarray:
    """Small BGR uint8 test image (seeded for reproducibility)."""
    return np.random.default_rng(5).integers(0, 256, (16, 16, 3), dtype=np.uint8)


def _img_large() -> np.ndarray:
    """Larger BGR uint8 test image for flatten tests."""
    return np.random.default_rng(42).integers(0, 256, (64, 64, 3), dtype=np.uint8)


def _gray() -> np.ndarray:
    """Grayscale uint8 test image for clahe."""
    return np.random.default_rng(11).integers(110, 140, size=(64, 64), dtype=np.uint8)


# ---------------------------------------------------------------------------
# luma_gpu
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _has_cupy(), reason="cupy not available")
def test_gpu_luma_bt601_matches_cpu() -> None:
    from pdomain_book_tools.image_processing.grayscale_pipeline import ops_cpu, ops_gpu

    img = _img_color()
    cpu = ops_cpu.luma(img, bt709=False).astype(np.int16)
    gpu = ops_gpu.luma_gpu(img, bt709=False).astype(np.int16)
    diff = float(np.abs(cpu - gpu).mean())
    assert diff <= 1.0, f"luma bt601 mean-abs diff {diff:.4f} > 1.0"


@pytest.mark.skipif(not _has_cupy(), reason="cupy not available")
def test_gpu_luma_bt709_matches_cpu() -> None:
    from pdomain_book_tools.image_processing.grayscale_pipeline import ops_cpu, ops_gpu

    img = _img_color()
    cpu = ops_cpu.luma(img, bt709=True).astype(np.int16)
    gpu = ops_gpu.luma_gpu(img, bt709=True).astype(np.int16)
    diff = float(np.abs(cpu - gpu).mean())
    assert diff <= 1.0, f"luma bt709 mean-abs diff {diff:.4f} > 1.0"


@pytest.mark.skipif(not _has_cupy(), reason="cupy not available")
def test_gpu_luma_output_shape_dtype() -> None:
    from pdomain_book_tools.image_processing.grayscale_pipeline import ops_gpu

    img = _img_color()
    out = ops_gpu.luma_gpu(img)
    assert out.shape == (16, 16)
    assert out.dtype == np.uint8


# ---------------------------------------------------------------------------
# lab_l_gpu
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _has_cupy(), reason="cupy not available")
def test_gpu_lab_l_matches_cpu() -> None:
    from pdomain_book_tools.image_processing.grayscale_pipeline import ops_cpu, ops_gpu

    img = _img_color()
    cpu = ops_cpu.lab_l(img).astype(np.int16)
    gpu = ops_gpu.lab_l_gpu(img).astype(np.int16)
    diff = float(np.abs(cpu - gpu).mean())
    assert diff <= 3.0, f"lab_l mean-abs diff {diff:.4f} > 3.0"


@pytest.mark.skipif(not _has_cupy(), reason="cupy not available")
def test_gpu_lab_l_output_shape_dtype() -> None:
    from pdomain_book_tools.image_processing.grayscale_pipeline import ops_gpu

    img = _img_color()
    out = ops_gpu.lab_l_gpu(img)
    assert out.shape == (16, 16)
    assert out.dtype == np.uint8


# ---------------------------------------------------------------------------
# best_channel_gpu
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _has_cupy(), reason="cupy not available")
def test_gpu_best_channel_named_matches_cpu() -> None:
    from pdomain_book_tools.image_processing.grayscale_pipeline import ops_cpu, ops_gpu

    img = _img_color()
    for ch in ("blue", "green", "red"):
        cpu = ops_cpu.best_channel(img, ch)
        gpu = ops_gpu.best_channel_gpu(img, ch)
        assert np.array_equal(cpu, gpu), f"best_channel '{ch}' mismatch"


@pytest.mark.skipif(not _has_cupy(), reason="cupy not available")
def test_gpu_best_channel_auto_matches_cpu() -> None:
    from pdomain_book_tools.image_processing.grayscale_pipeline import ops_cpu, ops_gpu

    img = _img_color()
    cpu = ops_cpu.best_channel(img, "auto")
    gpu = ops_gpu.best_channel_gpu(img, "auto")
    assert np.array_equal(cpu, gpu), "best_channel 'auto' mismatch"


@pytest.mark.skipif(not _has_cupy(), reason="cupy not available")
def test_gpu_best_channel_output_shape_dtype() -> None:
    from pdomain_book_tools.image_processing.grayscale_pipeline import ops_gpu

    img = _img_color()
    out = ops_gpu.best_channel_gpu(img, "green")
    assert out.shape == (16, 16)
    assert out.dtype == np.uint8


# ---------------------------------------------------------------------------
# flatten_gpu
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _has_cupy(), reason="cupy not available")
def test_gpu_flatten_matches_cpu() -> None:
    from pdomain_book_tools.image_processing.grayscale_pipeline import ops_cpu, ops_gpu

    img = _img_large()
    cpu = ops_cpu.flatten(img, radius=24, strength=1.0).astype(np.int16)
    gpu = ops_gpu.flatten_gpu(img, radius=24, strength=1.0).astype(np.int16)
    diff = float(np.abs(cpu - gpu).mean())
    assert diff <= 3.0, f"flatten mean-abs diff {diff:.4f} > 3.0"


@pytest.mark.skipif(not _has_cupy(), reason="cupy not available")
def test_gpu_flatten_output_shape_dtype() -> None:
    from pdomain_book_tools.image_processing.grayscale_pipeline import ops_gpu

    img = _img_large()
    out = ops_gpu.flatten_gpu(img, radius=24, strength=1.0)
    assert out.shape == img.shape
    assert out.dtype == np.uint8


# ---------------------------------------------------------------------------
# clahe_gpu
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _has_cupy(), reason="cupy not available")
def test_gpu_clahe_matches_cpu() -> None:
    from pdomain_book_tools.image_processing.grayscale_pipeline import ops_cpu, ops_gpu

    gray = _gray()
    cpu = ops_cpu.clahe(gray, clip_limit=2.0, tile_grid=8).astype(np.int16)
    gpu = ops_gpu.clahe_gpu(gray, clip_limit=2.0, tile_grid=8).astype(np.int16)
    diff = float(np.abs(cpu - gpu).mean())
    assert diff <= 3.0, f"clahe mean-abs diff {diff:.4f} > 3.0"


@pytest.mark.skipif(not _has_cupy(), reason="cupy not available")
def test_gpu_clahe_output_shape_dtype() -> None:
    from pdomain_book_tools.image_processing.grayscale_pipeline import ops_gpu

    gray = _gray()
    out = ops_gpu.clahe_gpu(gray)
    assert out.shape == gray.shape
    assert out.dtype == np.uint8
