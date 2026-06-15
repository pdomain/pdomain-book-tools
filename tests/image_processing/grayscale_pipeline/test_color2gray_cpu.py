"""Tests for CPU Color2Gray port (parity with cupy_color_to_gray)."""

from __future__ import annotations

import numpy as np
import pytest

from pdomain_book_tools.image_processing.grayscale_pipeline.color2gray_cpu import (
    color2gray_cpu,
)


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


def _img() -> np.ndarray:
    return np.random.default_rng(3).integers(0, 256, (24, 24, 3), dtype=np.uint8)


def test_returns_uint8_2d() -> None:
    out = color2gray_cpu(_img(), radius=8, samples=4, iterations=4, seed=0)
    assert out.shape == (24, 24)
    assert out.dtype == np.uint8


def test_deterministic_with_seed() -> None:
    img = _img()
    a = color2gray_cpu(img, radius=8, samples=4, iterations=4, seed=0)
    b = color2gray_cpu(img, radius=8, samples=4, iterations=4, seed=0)
    assert np.array_equal(a, b)


def test_differs_from_bt601_luma() -> None:
    import cv2

    img = _img()
    assert np.any(
        color2gray_cpu(img, radius=8, samples=4, iterations=4, seed=0)
        != cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    )


@pytest.mark.skipif(not _has_cupy(), reason="cupy not available")
def test_parity_with_gpu_within_tolerance() -> None:
    from pdomain_book_tools.image_processing.cupy_processing.color_to_gray import (
        np_uint8_color_to_gray,
    )

    img = _img()
    cpu = color2gray_cpu(img, radius=8, samples=64, iterations=64, seed=0).astype(
        np.int16
    )
    gpu = np_uint8_color_to_gray(img, radius=8, samples=64, iterations=64).astype(
        np.int16
    )
    mean_abs_diff = float(np.abs(cpu - gpu).mean())
    assert mean_abs_diff < 12.0, (
        f"mean abs diff {mean_abs_diff:.2f} exceeds tolerance 12.0"
    )
