import logging

import cupy as cp
import numpy as np

logger = logging.getLogger(__name__)


def add_whitespace_pixels_gpu(
    img_cp: cp.ndarray,
    left_px: int,
    right_px: int,
    top_px: int,
    bottom_px: int,
) -> cp.ndarray:
    """
    GPU port of cv2_processing.whitespace.add_whitespace_pixels.

    Pads img_cp with white (255) pixels. Supports 2-D and 3-D arrays.
    """
    h, w = img_cp.shape[:2]
    new_h = h + top_px + bottom_px
    new_w = w + left_px + right_px

    if img_cp.ndim == 2:
        padded = cp.full((new_h, new_w), 255, dtype=cp.uint8)
    else:
        padded = cp.full((new_h, new_w, img_cp.shape[2]), 255, dtype=cp.uint8)

    padded[top_px : top_px + h, left_px : left_px + w] = img_cp
    return padded


def add_whitespace_percentage_gpu(
    img_cp: cp.ndarray,
    left_pct: float = 0,
    right_pct: float = 0,
    top_pct: float = 0,
    bottom_pct: float = 0,
) -> cp.ndarray:
    """Percentage-based wrapper around add_whitespace_pixels_gpu."""
    h, w = img_cp.shape[:2]
    return add_whitespace_pixels_gpu(
        img_cp,
        left_px=int(w * left_pct),
        right_px=int(w * right_pct),
        top_px=int(h * top_pct),
        bottom_px=int(h * bottom_pct),
    )


def np_uint8_add_whitespace_pixels(
    img: np.ndarray,
    left_px: int,
    right_px: int,
    top_px: int,
    bottom_px: int,
) -> np.ndarray:
    """Transfers img to GPU, pads with whitespace, returns CPU uint8 array."""
    img_cp = cp.asarray(img)
    return cp.asnumpy(
        add_whitespace_pixels_gpu(img_cp, left_px, right_px, top_px, bottom_px)
    )
