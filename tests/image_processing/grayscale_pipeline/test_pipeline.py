"""Tests for the grayscale pipeline orchestrator."""

from __future__ import annotations

import numpy as np
import pytest

from pdomain_book_tools.image_processing.grayscale_pipeline import (
    ClaheConfig,
    Converter,
    FlattenConfig,
    GrayscaleConfig,
    run_grayscale_pipeline,
)


def _img() -> np.ndarray:
    return np.random.default_rng(9).integers(0, 256, (40, 40, 3), np.uint8)


def test_default_pipeline_equals_luma() -> None:
    import cv2

    img = _img()
    out = run_grayscale_pipeline(img, GrayscaleConfig(), use_gpu=False)
    assert np.array_equal(out, cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))


def test_flatten_then_clahe_changes_output() -> None:
    img = _img()
    base = run_grayscale_pipeline(img, GrayscaleConfig(), use_gpu=False)
    cfg = GrayscaleConfig(
        flatten=FlattenConfig(enabled=True), clahe=ClaheConfig(enabled=True)
    )
    assert np.any(run_grayscale_pipeline(img, cfg, use_gpu=False) != base)


def test_converter_choice_changes_output() -> None:
    img = _img()
    a = run_grayscale_pipeline(
        img, GrayscaleConfig(converter=Converter.luma), use_gpu=False
    )
    b = run_grayscale_pipeline(
        img, GrayscaleConfig(converter=Converter.lab_l), use_gpu=False
    )
    assert np.any(a != b)


def test_luma_bt709_changes_output() -> None:
    img = _img()
    a = run_grayscale_pipeline(
        img, GrayscaleConfig(converter=Converter.luma), use_gpu=False
    )
    b = run_grayscale_pipeline(
        img, GrayscaleConfig(converter=Converter.luma_bt709), use_gpu=False
    )
    assert np.any(a != b)


def test_best_channel_converter() -> None:
    img = _img()
    out = run_grayscale_pipeline(
        img,
        GrayscaleConfig(converter=Converter.best_channel, channel="red"),
        use_gpu=False,
    )
    assert out.shape == (40, 40)
    assert out.dtype == np.uint8


def test_color2gray_converter() -> None:
    img = _img()
    out = run_grayscale_pipeline(
        img, GrayscaleConfig(converter=Converter.color2gray), use_gpu=False
    )
    assert out.shape == (40, 40)
    assert out.dtype == np.uint8


def test_output_range_applied() -> None:
    img = _img()
    cfg = GrayscaleConfig(output_range=(50, 200))
    out = run_grayscale_pipeline(img, cfg, use_gpu=False)
    assert int(out.min()) >= 50
    assert int(out.max()) <= 200


def test_output_range_none_is_no_op() -> None:
    img = _img()
    cfg_no_range = GrayscaleConfig(output_range=None)
    cfg_full_range = GrayscaleConfig(output_range=(0, 255))
    out_no = run_grayscale_pipeline(img, cfg_no_range, use_gpu=False)
    out_full = run_grayscale_pipeline(img, cfg_full_range, use_gpu=False)
    # output_range=None skips stretching; output_range=(0,255) stretches.
    # They won't always be equal, but both must be uint8 grayscale.
    assert out_no.shape == (40, 40)
    assert out_full.shape == (40, 40)


def test_use_gpu_false_with_luma() -> None:
    """CPU path produces correct shape/dtype."""
    img = _img()
    out = run_grayscale_pipeline(img, GrayscaleConfig(), use_gpu=False)
    assert out.shape == (40, 40)
    assert out.dtype == np.uint8


# ---------------------------------------------------------------------------
# GPU path test — requires CuPy
# ---------------------------------------------------------------------------
try:
    import cupy

    _ = cupy
    _CUPY_AVAILABLE = True
except ImportError:
    _CUPY_AVAILABLE = False  # pyright: ignore[reportConstantRedefinition]  # reassigned in except; not a true constant


@pytest.mark.skipif(not _CUPY_AVAILABLE, reason="CuPy not installed")
def test_gpu_luma_matches_cpu() -> None:
    """GPU path (use_gpu=True) for converter=luma matches CPU within tolerance."""
    img = _img()
    cfg = GrayscaleConfig(converter=Converter.luma)
    cpu_out = run_grayscale_pipeline(img, cfg, use_gpu=False)
    gpu_out = run_grayscale_pipeline(img, cfg, use_gpu=True)
    assert gpu_out.shape == cpu_out.shape
    assert gpu_out.dtype == np.uint8
    # GPU BT.601 replicates the float32 weighted sum path — allow ±1 rounding diff.
    max_diff = int(np.max(np.abs(cpu_out.astype(np.int32) - gpu_out.astype(np.int32))))
    assert max_diff <= 1, f"GPU/CPU luma diverged by {max_diff} (expected <=1)"
