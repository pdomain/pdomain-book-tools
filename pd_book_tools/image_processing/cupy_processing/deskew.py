# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, cast

from ._cupy_compat import cp, require_cupy
from .edge_finding import find_edges_gpu
from .rotate import rotate_image_gpu

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt

    CuPyArray = npt.NDArray[np.generic]
else:
    CuPyArray = object

logger = logging.getLogger(__name__)

# Keep private alias so existing internal callers and tests still work.
_rotate_gpu = rotate_image_gpu


def auto_deskew_gpu(
    img_cp: CuPyArray,
    pct: float = 0.30,
) -> tuple[CuPyArray, CuPyArray, CuPyArray]:
    """
    GPU port of cv2_processing.perspective_adjustment.auto_deskew.

    img_cp: 2-D uint8 CuPy array, inverted (content=255, background=0).
    pct:    fraction of content height to sample at top and bottom.

    Returns (deskewed_image, top_slice_used, bottom_slice_used).
    Always returns a 3-tuple; top/bottom slices are empty arrays when the
    early-exit path is taken (pct=0 or degenerate image).
    """
    require_cupy()
    _img_h, img_w = cast("tuple[int, int]", img_cp.shape[:2])

    _minX, _maxX, minY, maxY = find_edges_gpu(
        img_cp, fuzzy_pct=0, pixel_count_columns=1, pixel_count_rows=1
    )

    h_percent = int((maxY - minY) * pct)
    w_ten_percent = int((maxY - minY) * 0.10)

    empty = cast("CuPyArray", cp.empty((0, 0), dtype=img_cp.dtype))

    if w_ten_percent == 0 or h_percent == 0:
        logger.debug("auto_deskew_gpu: not deskewing — pct slice is zero")
        return img_cp, empty, empty

    # Top slice: rows [minY, minY+h_percent), cols [0, img_w-1) — matches CPU
    top_slice = img_cp[minY : minY + h_percent, 0 : img_w - 1]
    col_sums_top = cp.sum(top_slice, axis=0)
    nonzero_top = col_sums_top.nonzero()[0]
    top_left_column = cast("int", nonzero_top[0]) if nonzero_top.size > 0 else 0

    # Bottom slice: rows [maxY-h_percent, maxY), cols [0, img_w-1)
    bottom_slice = img_cp[maxY - h_percent : maxY, 0 : img_w - 1]
    col_sums_bot = cp.sum(bottom_slice, axis=0)
    nonzero_bot = col_sums_bot.nonzero()[0]
    bottom_left_column = cast("int", nonzero_bot[0]) if nonzero_bot.size > 0 else 0

    logger.debug(
        f"auto_deskew_gpu: top_left_col={top_left_column}, bottom_left_col={bottom_left_column}"
    )

    if bottom_left_column == top_left_column:
        logger.debug("auto_deskew_gpu: no skew detected")
        return img_cp, top_slice, bottom_slice

    dist_b = float(maxY - minY)
    dist_c = math.sqrt((bottom_left_column - top_left_column) ** 2 + (maxY - minY) ** 2)

    # The early-return guard above (bottom_left_column == top_left_column)
    # ensures (bottom_left_column - top_left_column)**2 > 0, so dist_c > dist_b
    # is guaranteed at this point. No dist_b == dist_c floating-point check
    # is needed (and a == comparison on floats would be unreliable anyway).
    angle = math.acos(dist_b / dist_c) * (180.0 / math.pi)

    if bottom_left_column > top_left_column:
        logger.debug(f"auto_deskew_gpu: rotating CW {angle:.3f}°")
        result = _rotate_gpu(img_cp, angle_deg=+angle)
    else:
        logger.debug(f"auto_deskew_gpu: rotating CCW {angle:.3f}°")
        result = _rotate_gpu(img_cp, angle_deg=-angle)

    return result, top_slice, bottom_slice


def np_uint8_auto_deskew(
    img: np.ndarray,
    pct: float = 0.30,
) -> np.ndarray:
    """Convenience wrapper. Moves to GPU, deskews, returns CPU array."""
    require_cupy()
    img_cp = cast("CuPyArray", cp.asarray(img))
    result_cp, _, _ = auto_deskew_gpu(img_cp, pct)
    return cp.asnumpy(result_cp)
