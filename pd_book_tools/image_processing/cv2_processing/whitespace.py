# Configure logging
import logging
from typing import cast

import numpy as np
import numpy.typing as npt

logger = logging.getLogger(__name__)

ImageArray = npt.NDArray[np.uint8]


def add_whitespace_percentage(
    img: ImageArray,
    left_pct: float = 0,
    right_pct: float = 0,
    top_pct: float = 0,
    bottom_pct: float = 0,
) -> ImageArray:
    """Adds white space as a percentage of the image dimensions."""
    h, w = cast("tuple[int, int]", img.shape[:2])
    left_px = int(w * left_pct)
    right_px = int(w * right_pct)
    top_px = int(h * top_pct)
    bottom_px = int(h * bottom_pct)

    return add_whitespace_pixels(img, left_px, right_px, top_px, bottom_px)


def add_whitespace_pixels(
    img: ImageArray, left_px: int, right_px: int, top_px: int, bottom_px: int
) -> ImageArray:
    """Core function that handles the whitespace padding."""
    h, w = cast("tuple[int, int]", img.shape[:2])
    new_h, new_w = h + top_px + bottom_px, w + left_px + right_px

    if len(img.shape) == 2:
        padded_img = np.full((new_h, new_w), 255, dtype=np.uint8)
    else:
        padded_img = np.full((new_h, new_w, img.shape[2]), 255, dtype=np.uint8)

    padded_img[top_px : top_px + h, left_px : left_px + w] = img
    return padded_img
