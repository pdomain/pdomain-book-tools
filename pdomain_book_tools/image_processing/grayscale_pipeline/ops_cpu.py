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
