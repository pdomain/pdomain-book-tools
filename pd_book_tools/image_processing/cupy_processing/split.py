import logging
from typing import Tuple

import cupy as cp
import numpy as np

logger = logging.getLogger(__name__)


def split_x_columns_gpu(img_cp: cp.ndarray, x: int) -> Tuple[cp.ndarray, cp.ndarray]:
    """Split img_cp into two parts at column index x."""
    h, w = img_cp.shape[:2]
    if not (0 <= x <= w):
        raise ValueError(f"Column index x={x} is out of bounds for width={w}")
    return img_cp[:, :x], img_cp[:, x:]


def split_y_rows_gpu(img_cp: cp.ndarray, y: int) -> Tuple[cp.ndarray, cp.ndarray]:
    """Split img_cp into two parts at row index y."""
    h, w = img_cp.shape[:2]
    if not (0 <= y <= h):
        raise ValueError(f"Row index y={y} is out of bounds for height={h}")
    return img_cp[:y, :], img_cp[y:, :]


def np_uint8_split_x_columns(img: np.ndarray, x: int) -> Tuple[np.ndarray, np.ndarray]:
    """Transfers img to GPU, splits at column x, returns two CPU uint8 arrays."""
    left, right = split_x_columns_gpu(cp.asarray(img), x)
    return cp.asnumpy(left), cp.asnumpy(right)


def np_uint8_split_y_rows(img: np.ndarray, y: int) -> Tuple[np.ndarray, np.ndarray]:
    """Transfers img to GPU, splits at row y, returns two CPU uint8 arrays."""
    top, bottom = split_y_rows_gpu(cp.asarray(img), y)
    return cp.asnumpy(top), cp.asnumpy(bottom)
