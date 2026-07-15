"""Configurable grayscale conversion for book-scan page images.

Input convention: BGR channel order (as produced by ``cv2.imread`` and the
rest of this library).  Callers working with RGB arrays must convert first
(e.g. ``img[:, :, ::-1]`` or ``cv2.cvtColor(img, cv2.COLOR_RGB2BGR)``).
Already-grayscale (HxW) inputs are accepted and pass through the
``output_range`` step unchanged.

Channel weights used in perceptual mode follow the ITU-R BT.709 primaries
(sRGB / web standard) in BGR order: B=0.0722, G=0.7152, R=0.2126.  The
conversion proceeds in linear light (sRGB gamma removed via the ``gamma``
parameter) so that the weighted sum approximates true luminance rather than
a gamma-compressed approximation.

The optional ``sampler_radius`` in perceptual mode applies a small
locally-adaptive contrast enhancement: the pixel luminance is pulled
towards the local neighbourhood mean by a small fraction (10%), which
sharpens local ink/paper transitions on scanner images while remaining
visually natural.
"""

from __future__ import annotations

import logging
from typing import Literal, cast

import cv2
import numpy as np
import numpy.typing as npt

logger = logging.getLogger(__name__)

ImageArray = npt.NDArray[np.uint8]

# ITU-R BT.709 luminance weights in BGR order.
_BT709_BGR = (0.0722, 0.7152, 0.2126)


def to_grayscale(
    img: npt.NDArray[np.uint8],
    *,
    mode: Literal["perceptual", "standard"] = "perceptual",
    sampler_radius: int = 3,
    gamma: float = 1.1,
    output_range: tuple[int, int] = (12, 248),
) -> ImageArray:
    """Convert a BGR (or already-grayscale) uint8 image to a grayscale uint8 image.

    Input must be dtype uint8.  For 3-channel inputs the channel order must be
    BGR (the cv2 convention used throughout this library).  A 2-D HxW input is
    treated as an already-grayscale image; only ``output_range`` is applied.

    Args:
        img: uint8 array, either HxWx3 (BGR) or HxW (grayscale).
        mode: Conversion algorithm.

            - ``"standard"`` -- fast luma via ``cv2.COLOR_BGR2GRAY``
              (BT.601 weights: 0.299R, 0.587G, 0.114B in cv2 BGR order).
              ``sampler_radius`` and ``gamma`` are ignored in this mode.
            - ``"perceptual"`` -- gamma-aware luminance (BT.709 primaries in
              linear light) plus an optional local-contrast nudge controlled
              by ``sampler_radius``.

        sampler_radius: Local neighbourhood radius (pixels) for the
            perceptual contrast step.  Larger values smooth local adaptation
            over a wider area.  ``0`` disables the local step entirely.
            Negative values are rejected.  Ignored in ``"standard"`` mode.
        gamma: Tone-mixing control for the perceptual pipeline.  The
            linearisation step divides stored values by 255, raises to the
            power ``gamma`` (removing display gamma), applies BT.709 channel
            weights to form a linear-light luminance, then **re-encodes back
            to perceptual/display space** via ``luminance ** (1.0 / gamma)``
            before mapping to the output range.  Higher ``gamma`` values pull
            midtones *brighter* (more output headroom for midtones), not
            darker.  ``1.0`` is a no-op (identity round-trip).  Typical
            values are 1.0-2.2.  Ignored in ``"standard"`` mode.
        output_range: ``(min_out, max_out)`` window for the final 8-bit
            output.  The grayscale result is linearly mapped so that the
            darkest pixel lands at ``min_out`` and the brightest at
            ``max_out``.  Raises if ``min_out >= max_out`` or if either
            value is outside [0, 255].

    Returns:
        HxW uint8 array with values in ``[output_range[0], output_range[1]]``.

    Raises:
        ValueError: On invalid ``img`` shape/dtype, out-of-range
            ``output_range``, or invalid ``sampler_radius`` / ``gamma``.
    """
    _validate_inputs(img, mode, sampler_radius, gamma, output_range)

    if img.ndim == 2:
        gray_f32 = img.astype(np.float32)
    elif mode == "standard":
        gray_f32 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    else:
        gray_f32 = _perceptual_gray(img, sampler_radius=sampler_radius, gamma=gamma)

    return _apply_output_range(gray_f32, output_range)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_inputs(
    img: npt.NDArray[np.uint8],
    mode: str,
    sampler_radius: object,
    gamma: float,
    output_range: tuple[int, int],
) -> None:
    if img.dtype != np.uint8:
        raise ValueError(f"to_grayscale expects dtype uint8; got {img.dtype}.")
    if img.ndim not in (2, 3):
        raise ValueError(
            f"to_grayscale expects a 2-D or 3-D array; got ndim={img.ndim}."
        )
    if img.ndim == 3 and img.shape[2] != 3:
        raise ValueError(
            f"to_grayscale expects 3 channels for a 3-D array; got {img.shape[2]}."
        )
    if mode not in ("standard", "perceptual"):
        raise ValueError(f"mode must be 'standard' or 'perceptual'; got {mode!r}.")
    if not isinstance(sampler_radius, int):
        raise TypeError(
            f"sampler_radius must be an int; got {type(sampler_radius).__name__}."
        )
    if sampler_radius < 0:
        raise ValueError(
            f"sampler_radius must be >= 0; got {sampler_radius}."
            " Use 0 to disable the local-contrast step."
        )
    if gamma <= 0.0:
        raise ValueError(f"gamma must be > 0; got {gamma}.")
    min_out, max_out = output_range
    if min_out >= max_out:
        raise ValueError(f"output_range min must be < max; got ({min_out}, {max_out}).")
    if not (0 <= min_out <= 255 and 0 <= max_out <= 255):
        raise ValueError(
            f"output_range values must be in [0, 255]; got ({min_out}, {max_out})."
        )


def _perceptual_gray(
    img: npt.NDArray[np.uint8],
    *,
    sampler_radius: int,
    gamma: float,
) -> npt.NDArray[np.float32]:
    """Return float32 grayscale using BT.709 weights with perceptual re-encode.

    Pipeline:
    1. Linearise each channel: ``channel / 255 ** gamma`` removes display gamma.
    2. Form linear-light luminance with BT.709 weights.
    3. Apply the optional local-contrast nudge in linear space.
    4. Re-encode to perceptual/display space: ``luminance ** (1.0 / gamma)``.
    5. Return scaled to [0, 255] as float32 for downstream ``_apply_output_range``.

    The local-contrast nudge (when ``sampler_radius >= 1``) computes a box
    mean over a (2*r+1)x(2*r+1) neighbourhood and pulls each pixel 10%
    towards the local mean, increasing local micro-contrast.
    """
    b = img[:, :, 0].astype(np.float32) / 255.0
    g = img[:, :, 1].astype(np.float32) / 255.0
    r = img[:, :, 2].astype(np.float32) / 255.0

    wb, wg, wr = _BT709_BGR
    # Step 1-2: linearise channels, then weight by BT.709 luminance coefficients.
    lin: npt.NDArray[np.float32] = (
        wb * (b**gamma) + wg * (g**gamma) + wr * (r**gamma)
    ).astype(np.float32)

    # Step 3: optional local-contrast nudge in linear space.
    if sampler_radius >= 1:
        ksize = 2 * sampler_radius + 1
        local_mean = cast("npt.NDArray[np.float32]", cv2.blur(lin, (ksize, ksize)))
        # Pull pixel 10% towards local mean to enhance local micro-contrast.
        lin = (lin + 0.10 * (lin - local_mean)).astype(np.float32)
        lin = np.clip(lin, 0.0, 1.0).astype(np.float32)

    # Step 4: re-encode linear luminance back to perceptual/display space.
    # Without this step, the output would be a linear-light signal, which
    # appears dark and crushed compared to the sRGB-encoded input.
    perceptual: npt.NDArray[np.float32] = np.power(
        np.clip(lin, 0.0, 1.0), 1.0 / gamma
    ).astype(np.float32)

    return (perceptual * 255.0).astype(np.float32)


def _apply_output_range(
    gray_f32: npt.NDArray[np.float32],
    output_range: tuple[int, int],
) -> ImageArray:
    """Linearly map gray_f32 so darkest pixel -> min and brightest pixel -> max."""
    min_out, max_out = output_range
    src_min = float(gray_f32.min())
    src_max = float(gray_f32.max())

    if src_min == src_max:
        mid = round((min_out + max_out) / 2.0)
        return np.full(gray_f32.shape, mid, dtype=np.uint8)

    scale = (max_out - min_out) / (src_max - src_min)
    mapped = (gray_f32 - src_min) * scale + min_out
    return np.clip(mapped, min_out, max_out).astype(np.uint8)
