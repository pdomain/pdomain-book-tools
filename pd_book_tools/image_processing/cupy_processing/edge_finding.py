from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ._cupy_compat import cp, require_cupy

if TYPE_CHECKING:
    import numpy as np

# cupyx is part of the CuPy install ([gpu] extra). This guard lets the module
# load on CPU-only installs; require_cupy() in each function gives the
# actionable error before these names are ever dereferenced.
try:
    from cupyx.scipy.ndimage import convolve1d  # pyright: ignore[reportMissingImports]
except ImportError:  # pragma: no cover - exercised only on CPU-only installs
    convolve1d = None

logger = logging.getLogger(__name__)


def find_edges_gpu(
    img_cp: cp.ndarray,
    fuzzy_pct: float = 0.02,
    pixel_count_columns: int = 150,
    pixel_count_rows: int = 75,
    fuzzy_px_w_override: int | None = None,
    fuzzy_px_h_override: int | None = None,
) -> tuple[int, int, int, int]:
    """
    Returns (minX, maxX, minY, maxY).
    img_cp must be a 2-D uint8 CuPy array, inverted (content=255, background=0).
    """
    require_cupy()
    h, w = img_cp.shape[:2]

    columns = cp.sum(img_cp, axis=0).astype(cp.int64)  # shape (W,)
    rows = cp.sum(img_cp, axis=1).astype(cp.int64)  # shape (H,)

    pixel_value_col_min = pixel_count_columns * 255
    pixel_value_row_min = pixel_count_rows * 255

    fuzzy_px_w = (
        fuzzy_px_w_override if fuzzy_px_w_override is not None else int(w * fuzzy_pct)
    )
    fuzzy_px_h = (
        fuzzy_px_h_override if fuzzy_px_h_override is not None else int(h * fuzzy_pct)
    )

    kernel_w = cp.ones((2 * fuzzy_px_w + 1,), dtype=cp.int64)
    kernel_h = cp.ones((2 * fuzzy_px_h + 1,), dtype=cp.int64)

    # convolve1d is the 1-D equivalent of np.convolve(..., mode='same').
    # mode='nearest' extends borders with the nearest edge value.
    fuzzy_columns = convolve1d(columns, kernel_w, mode="nearest")  # pyright: ignore[reportOptionalCall]  # guarded by require_cupy() in callers
    fuzzy_rows = convolve1d(rows, kernel_h, mode="nearest")  # pyright: ignore[reportOptionalCall]  # guarded by require_cupy() in callers

    x_indices = cp.where(fuzzy_columns >= pixel_value_col_min)[0]
    y_indices = cp.where(fuzzy_rows >= pixel_value_row_min)[0]

    minX = int(x_indices[0]) if x_indices.size > 0 else 0
    maxX = int(x_indices[-1]) if x_indices.size > 0 else w
    minY = int(y_indices[0]) if y_indices.size > 0 else 0
    maxY = int(y_indices[-1]) if y_indices.size > 0 else h

    logger.debug(
        "find_edges_gpu: minX=%s, maxX=%s, minY=%s, maxY=%s", minX, maxX, minY, maxY
    )
    return minX, maxX, minY, maxY


def np_uint8_find_edges(
    img: np.ndarray,
    **kwargs,
) -> tuple[int, int, int, int]:
    """Transfers img to GPU, runs find_edges_gpu, returns result."""
    require_cupy()
    img_cp = cp.asarray(img)
    return find_edges_gpu(img_cp, **kwargs)
