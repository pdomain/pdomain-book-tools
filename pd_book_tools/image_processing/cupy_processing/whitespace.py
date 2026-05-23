# pyright: reportUnknownMemberType=false
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from ._cupy_compat import cp, require_cupy

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt

    CuPyArray = npt.NDArray[np.generic]
else:
    CuPyArray = object

logger = logging.getLogger(__name__)


def add_whitespace_pixels_gpu(
    img_cp: CuPyArray,
    left_px: int,
    right_px: int,
    top_px: int,
    bottom_px: int,
) -> CuPyArray:
    """
    GPU port of cv2_processing.whitespace.add_whitespace_pixels.

    Pads img_cp with white (255) pixels. Supports 2-D and 3-D arrays.
    """
    require_cupy()
    h, w = cast("tuple[int, int]", img_cp.shape[:2])
    new_h = h + top_px + bottom_px
    new_w = w + left_px + right_px

    padded: CuPyArray
    if img_cp.ndim == 2:
        padded = cast("CuPyArray", cp.full((new_h, new_w), 255, dtype=cp.uint8))
    else:
        padded = cast(
            "CuPyArray",
            cp.full((new_h, new_w, img_cp.shape[2]), 255, dtype=cp.uint8),
        )

    padded[top_px : top_px + h, left_px : left_px + w] = img_cp
    return padded


def add_whitespace_percentage_gpu(
    img_cp: CuPyArray,
    left_pct: float = 0,
    right_pct: float = 0,
    top_pct: float = 0,
    bottom_pct: float = 0,
) -> CuPyArray:
    """Percentage-based wrapper around add_whitespace_pixels_gpu."""
    require_cupy()
    h, w = cast("tuple[int, int]", img_cp.shape[:2])
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
    require_cupy()
    img_cp = cast("CuPyArray", cp.asarray(img))
    return cp.asnumpy(
        add_whitespace_pixels_gpu(img_cp, left_px, right_px, top_px, bottom_px)
    )
