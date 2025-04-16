# Configure logging
import logging

import numpy as np

logger = logging.getLogger(__name__)


def add_whitespace_percentage(
    img: np.ndarray,
    left_pct: float = 0,
    right_pct: float = 0,
    top_pct: float = 0,
    bottom_pct: float = 0,
) -> np.ndarray:
    """Adds white space as a percentage of the image dimensions."""
    h, w = img.shape[:2]
    left_px = int(w * left_pct)
    right_px = int(w * right_pct)
    top_px = int(h * top_pct)
    bottom_px = int(h * bottom_pct)

    return add_whitespace_pixels(img, left_px, right_px, top_px, bottom_px)


def add_whitespace_pixels(
    img: np.ndarray, left_px: int, right_px: int, top_px: int, bottom_px: int
) -> np.ndarray:
    """Core function that handles the whitespace padding."""
    h, w = img.shape[:2]
    new_h, new_w = h + top_px + bottom_px, w + left_px + right_px

    if len(img.shape) == 2:
        padded_img = np.full((new_h, new_w), 255, dtype=np.uint8)
    else:
        padded_img = np.full((new_h, new_w, img.shape[2]), 255, dtype=np.uint8)

    padded_img[top_px : top_px + h, left_px : left_px + w] = img
    return padded_img
