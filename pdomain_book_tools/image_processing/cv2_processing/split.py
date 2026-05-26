# Configure logging
import logging
from typing import cast

import numpy as np
import numpy.typing as npt

logger = logging.getLogger(__name__)

ImageArray = npt.NDArray[np.uint8]


def split_x_columns(img: ImageArray, x: int) -> tuple[ImageArray, ImageArray]:
    """
    Splits an image into two parts at a specified column index.

    Parameters:
        img (np.ndarray): Input image as a NumPy array.
        x (int): Column index to split the image at.

    Returns:
        tuple[np.ndarray, np.ndarray]: Two images split at column x.

    Raises:
        ValueError: If x is out of bounds.
    """
    _h, w = cast("tuple[int, int]", img.shape[:2])

    if not (0 <= x <= w):
        raise ValueError(f"Column index x={x} is out of bounds for width={w}")

    return img[:, :x], img[:, x:]


def split_y_rows(img: ImageArray, y: int) -> tuple[ImageArray, ImageArray]:
    """
    Splits an image into two parts at a specified row index.

    Parameters:
        img (np.ndarray): Input image as a NumPy array.
        y (int): Row index to split the image at.

    Returns:
        tuple[np.ndarray, np.ndarray]: Two images split at row y.

    Raises:
        ValueError: If y is out of bounds.
    """
    h, _w = cast("tuple[int, int]", img.shape[:2])

    if not (0 <= y <= h):
        raise ValueError(f"Row index y={y} is out of bounds for height={h}")

    return img[:y, :], img[y:, :]
