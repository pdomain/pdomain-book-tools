"""CPU color-to-grayscale converter ops.

Provides three conversion strategies:
- luma: BT.601 (OpenCV default) or BT.709 weighted RGB sum
- lab_l: CIELAB L* channel (perceptually uniform)
- best_channel: named channel or auto-select by variance
"""

from __future__ import annotations

from typing import cast

import cv2
import numpy as np
import numpy.typing as npt

U8 = npt.NDArray[np.uint8]


def luma(img: U8, *, bt709: bool = False) -> U8:
    """Convert BGR uint8 image to grayscale via luminance weights.

    Args:
        img: BGR uint8 ndarray of shape (H, W, 3).
        bt709: If False (default) use BT.601 weights (cv2.COLOR_BGR2GRAY).
               If True use BT.709 weights (0.2126 R + 0.7152 G + 0.0722 B).

    Returns:
        Grayscale uint8 ndarray of shape (H, W).
    """
    if not bt709:
        return cast("U8", cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    b = img[..., 0].astype(np.float32)
    g = img[..., 1].astype(np.float32)
    r = img[..., 2].astype(np.float32)
    y = 0.0722 * b + 0.7152 * g + 0.2126 * r
    return np.clip(y, 0, 255).astype(np.uint8)


def lab_l(img: U8) -> U8:
    """Convert BGR uint8 image to CIELAB L* channel.

    Args:
        img: BGR uint8 ndarray of shape (H, W, 3).

    Returns:
        L* channel as uint8 ndarray of shape (H, W).
        OpenCV encodes L* in [0, 255] (scaled from [0, 100]).
    """
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    return cast("U8", lab[..., 0])


def best_channel(img: U8, channel: str = "green") -> U8:
    """Extract a single channel from a BGR uint8 image.

    Args:
        img: BGR uint8 ndarray of shape (H, W, 3).
        channel: One of "blue", "green", "red" for a named channel,
                 or "auto" to select the channel with highest pixel variance.

    Returns:
        Selected channel as uint8 ndarray of shape (H, W).
    """
    idx: dict[str, int] = {"blue": 0, "green": 1, "red": 2}
    if channel in idx:
        return img[..., idx[channel]].copy()
    variances = [float(img[..., c].var()) for c in range(3)]
    return img[..., int(np.argmax(variances))].copy()


def flatten(img: U8, *, radius: int = 64, strength: float = 1.0) -> U8:
    """Reduce low-frequency illumination gradients via blur-divide normalization.

    Applies per-channel background estimation using a large Gaussian blur,
    then divides each pixel by the local background and rescales.

    Args:
        img: BGR uint8 ndarray of shape (H, W, 3).
        radius: Approximate blur radius in pixels (rounded up to odd).
        strength: Blend factor between original (0.0) and fully flattened (1.0).

    Returns:
        Background-flattened BGR uint8 ndarray of shape (H, W, 3).
    """
    k = max(3, radius | 1)
    out = np.empty_like(img)
    one = np.float32(1.0)
    s = np.float32(strength)
    for c in range(img.shape[2]):
        ch = img[..., c].astype(np.float32) + one
        bg = cv2.GaussianBlur(ch, (k, k), 0).astype(np.float32) + one
        norm = ch / bg * np.float32(np.mean(bg))
        blended = ((one - s) * ch + s * norm).astype(np.float32)
        out[..., c] = np.clip(blended, 0, 255).astype(np.uint8)
    return out


def clahe(gray: U8, *, clip_limit: float = 2.0, tile_grid: int = 8) -> U8:
    """Apply Contrast Limited Adaptive Histogram Equalization to a grayscale image.

    Args:
        gray: Grayscale uint8 ndarray of shape (H, W).
        clip_limit: Contrast clip limit (higher = more contrast enhancement).
        tile_grid: Number of tiles in each dimension for local equalization.

    Returns:
        CLAHE-enhanced grayscale uint8 ndarray of shape (H, W).
    """
    op = cv2.createCLAHE(
        clipLimit=float(clip_limit),
        tileGridSize=(int(tile_grid), int(tile_grid)),
    )
    return cast("U8", op.apply(gray))


def apply_output_range(gray: U8, out_range: tuple[int, int]) -> U8:
    """Stretch a grayscale image to fill a specified output intensity range.

    Performs linear min-max stretch so the darkest pixel maps to out_range[0]
    and the brightest pixel maps to out_range[1].

    Args:
        gray: Grayscale uint8 ndarray.
        out_range: (min, max) output intensity range, both in [0, 255].

    Returns:
        Stretched uint8 ndarray with the same shape as *gray*.
        If the image has no variation (min == max), returns *gray* unchanged.
    """
    lo, hi = float(gray.min()), float(gray.max())
    if hi <= lo:
        return gray
    omin, omax = out_range
    scaled: npt.NDArray[np.float32] = (gray.astype(np.float32) - lo) / (hi - lo) * (
        omax - omin
    ) + omin
    return np.clip(scaled, 0, 255).astype(np.uint8)
