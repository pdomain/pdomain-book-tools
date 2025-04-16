# Configure logging
import logging
from typing import Tuple

import numpy as np

logger = logging.getLogger(__name__)


def split_x_columns(img: np.ndarray, x: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Splits an image into two parts at a specified column index.

    Parameters:
        img (np.ndarray): Input image as a NumPy array.
        x (int): Column index to split the image at.

    Returns:
        Tuple[np.ndarray, np.ndarray]: Two images split at column x.

    Raises:
        ValueError: If x is out of bounds.
    """
    h, w = img.shape[:2]

    if not (0 <= x <= w):
        raise ValueError(f"Column index x={x} is out of bounds for width={w}")

    return img[:, :x], img[:, x:]


def split_y_rows(img: np.ndarray, y: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Splits an image into two parts at a specified row index.

    Parameters:
        img (np.ndarray): Input image as a NumPy array.
        y (int): Row index to split the image at.

    Returns:
        Tuple[np.ndarray, np.ndarray]: Two images split at row y.

    Raises:
        ValueError: If y is out of bounds.
    """
    h, w = img.shape[:2]

    if not (0 <= y <= h):
        raise ValueError(f"Row index y={y} is out of bounds for height={h}")

    return img[:y, :], img[y:, :]
