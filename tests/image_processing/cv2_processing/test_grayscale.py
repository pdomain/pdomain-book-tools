"""Tests for cv2_processing.grayscale.to_grayscale."""

import numpy as np
import pytest

pytest.importorskip("cv2")

from pdomain_book_tools.image_processing.cv2_processing.grayscale import to_grayscale

# ---------------------------------------------------------------------------
# Synthetic fixture helpers
# ---------------------------------------------------------------------------


def _bgr_ramp(h: int = 32, w: int = 32) -> np.ndarray:
    """Small synthetic BGR uint8 image with distinct R/G/B channel values.

    B increases left-to-right, G increases top-to-bottom, R is constant at
    100 — enough spatial variation to exercise both standard and perceptual
    conversion paths and make gamma / sampler effects measurable.
    """
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:, :, 0] = np.linspace(20, 200, w, dtype=np.uint8)[np.newaxis, :]  # B
    img[:, :, 1] = np.linspace(30, 220, h, dtype=np.uint8)[:, np.newaxis]  # G
    img[:, :, 2] = 100  # R constant
    return img


def _uniform_bgr(value: int = 128) -> np.ndarray:
    return np.full((16, 16, 3), value, dtype=np.uint8)


# ---------------------------------------------------------------------------
# Core contract tests
# ---------------------------------------------------------------------------


def test_output_shape_and_dtype():
    img = _bgr_ramp()
    result = to_grayscale(img)
    assert result.ndim == 2
    assert result.shape == img.shape[:2]
    assert result.dtype == np.uint8


def test_standard_vs_perceptual_differ():
    img = _bgr_ramp()
    std = to_grayscale(img, mode="standard", output_range=(0, 255))
    perc = to_grayscale(img, mode="perceptual", output_range=(0, 255))
    # BT.601 vs BT.709 in linear light: must produce measurably different arrays.
    assert not np.array_equal(std, perc), (
        "standard and perceptual must differ on the same input"
    )


def test_gamma_changes_output():
    img = _bgr_ramp()
    g10 = to_grayscale(img, mode="perceptual", gamma=1.0, output_range=(0, 255))
    g22 = to_grayscale(img, mode="perceptual", gamma=2.2, output_range=(0, 255))
    assert not np.array_equal(g10, g22), (
        "gamma=1.0 and gamma=2.2 must produce different outputs"
    )


def test_sampler_radius_changes_output():
    img = _bgr_ramp()
    r0 = to_grayscale(img, mode="perceptual", sampler_radius=0, output_range=(0, 255))
    r5 = to_grayscale(img, mode="perceptual", sampler_radius=5, output_range=(0, 255))
    assert not np.array_equal(r0, r5), (
        "sampler_radius=0 and sampler_radius=5 must differ"
    )


def test_output_range_respected():
    img = _bgr_ramp()
    min_out, max_out = 20, 200
    result = to_grayscale(img, output_range=(min_out, max_out))
    assert int(result.min()) >= min_out
    assert int(result.max()) <= max_out


def test_output_range_changes_output():
    img = _bgr_ramp()
    narrow = to_grayscale(img, output_range=(50, 100))
    wide = to_grayscale(img, output_range=(0, 255))
    assert not np.array_equal(narrow, wide), (
        "different output_range must produce different arrays"
    )


def test_output_range_bounds_are_tight():
    """The minimum output value equals min_out and maximum equals max_out."""
    img = _bgr_ramp()
    min_out, max_out = 12, 248
    result = to_grayscale(img, output_range=(min_out, max_out))
    assert int(result.min()) == min_out
    assert int(result.max()) == max_out


def test_already_grayscale_input_passthrough():
    """A 2-D HxW input skips channel conversion; output_range is still applied."""
    gray = np.linspace(0, 255, 32 * 32, dtype=np.uint8).reshape(32, 32)
    result = to_grayscale(gray, output_range=(10, 240))
    assert result.ndim == 2
    assert result.shape == gray.shape
    assert int(result.min()) == 10
    assert int(result.max()) == 240


def test_uniform_image_does_not_crash():
    img = _uniform_bgr(128)
    result = to_grayscale(img)
    assert result.shape == img.shape[:2]
    assert result.dtype == np.uint8


def test_perceptual_mode_is_perceptually_encoded_not_darkened():
    """Perceptual mode with typical gamma must NOT globally darken the image.

    The pipeline linearises channels (decode: ** gamma), weights by BT.709,
    then re-encodes (** (1/gamma)).  With gamma > 1 the round-trip is
    identity for uniform luminance, so the perceptual output mean must be
    within a reasonable band of the standard output mean — not consistently
    and significantly darker.

    This locks in that `gamma` is a tone-mixing control, not a global darkener.
    Concretely: perceptual mean must be >= standard mean * 0.85 (i.e. no more
    than 15% darker overall), which standard mode passes trivially and a broken
    linear-light-only pipeline at gamma=2.2 would fail (mean drops ~30%).
    """
    img = _bgr_ramp()
    std = to_grayscale(img, mode="standard", sampler_radius=0, output_range=(0, 255))
    perc = to_grayscale(
        img, mode="perceptual", gamma=1.1, sampler_radius=0, output_range=(0, 255)
    )
    std_mean = float(std.mean())
    perc_mean = float(perc.mean())
    # Re-encoded perceptual output must not be crushed dark relative to standard.
    assert perc_mean >= std_mean * 0.85, (
        f"perceptual mean {perc_mean:.1f} is more than 15% below "
        f"standard mean {std_mean:.1f} — re-encode step may be missing"
    )


def test_standard_mode_ignores_gamma_and_sampler():
    """standard mode must return identical results regardless of perceptual params."""
    img = _bgr_ramp()
    r1 = to_grayscale(
        img, mode="standard", gamma=1.0, sampler_radius=0, output_range=(0, 255)
    )
    r2 = to_grayscale(
        img, mode="standard", gamma=2.2, sampler_radius=10, output_range=(0, 255)
    )
    assert np.array_equal(r1, r2), (
        "standard mode must not vary with gamma/sampler_radius"
    )


# ---------------------------------------------------------------------------
# Validation / error tests
# ---------------------------------------------------------------------------


def test_raises_on_float_input():
    img = np.zeros((8, 8, 3), dtype=np.float32)
    with pytest.raises(ValueError, match="uint8"):
        to_grayscale(img)  # type: ignore[arg-type]


def test_raises_on_wrong_channel_count():
    img = np.zeros((8, 8, 4), dtype=np.uint8)
    with pytest.raises(ValueError, match="3 channels"):
        to_grayscale(img)


def test_raises_on_invalid_output_range_equal():
    img = _bgr_ramp()
    with pytest.raises(ValueError, match="min must be < max"):
        to_grayscale(img, output_range=(100, 100))


def test_raises_on_invalid_output_range_reversed():
    img = _bgr_ramp()
    with pytest.raises(ValueError, match="min must be < max"):
        to_grayscale(img, output_range=(200, 50))


def test_raises_on_out_of_255_range():
    img = _bgr_ramp()
    with pytest.raises(ValueError, match=r"\[0, 255\]"):
        to_grayscale(img, output_range=(-1, 200))


def test_raises_on_negative_gamma():
    img = _bgr_ramp()
    with pytest.raises(ValueError, match="gamma must be > 0"):
        to_grayscale(img, gamma=-1.0)


def test_raises_on_zero_gamma():
    img = _bgr_ramp()
    with pytest.raises(ValueError, match="gamma must be > 0"):
        to_grayscale(img, gamma=0.0)


def test_raises_on_invalid_mode():
    img = _bgr_ramp()
    with pytest.raises(ValueError, match="mode must be"):
        to_grayscale(img, mode="unknown")  # type: ignore[arg-type]


def test_raises_on_negative_sampler_radius():
    img = _bgr_ramp()
    with pytest.raises(ValueError, match="sampler_radius must be >= 0"):
        to_grayscale(img, sampler_radius=-1)


def test_raises_on_4d_input():
    img = np.zeros((2, 8, 8, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="2-D or 3-D"):
        to_grayscale(img)


# ---------------------------------------------------------------------------
# Public re-export tests
# ---------------------------------------------------------------------------


def test_importable_from_cv2_processing():
    from pdomain_book_tools.image_processing.cv2_processing import to_grayscale as tg

    assert callable(tg)
