# Configure logging
import logging
from typing import cast

import numpy as np
import numpy.typing as npt

logger = logging.getLogger(__name__)

ImageArray = npt.NDArray[np.uint8]


def find_edges(
    img: ImageArray,
    fuzzy_pct: float = 0.02,
    pixel_count_columns: int = 150,
    pixel_count_rows: int = 75,
    fuzzy_px_w_override: int | None = None,
    fuzzy_px_h_override: int | None = None,
) -> tuple[int, int, int, int]:
    """Optimized version of finding edges in a binary image using vectorized NumPy operations."""
    log_prefix = "find_edges - "
    logger.debug(log_prefix + "Start")

    # Compute sum across columns and rows
    columns = cast("npt.NDArray[np.int64]", np.sum(img, axis=0, dtype=np.int64))
    rows = cast("npt.NDArray[np.int64]", np.sum(img, axis=1, dtype=np.int64))

    pixel_value_col_min = pixel_count_columns * 255
    pixel_value_row_min = pixel_count_rows * 255

    logger.debug(
        f"{log_prefix}pixel_value_col_min={pixel_value_col_min}, pixel_value_row_min={pixel_value_row_min}"
    )

    h, w = cast("tuple[int, int]", img.shape[:2])

    # Compute fuzzy pixel width and height
    fuzzy_px_w = (
        fuzzy_px_w_override if fuzzy_px_w_override is not None else int(w * fuzzy_pct)
    )
    fuzzy_px_h = (
        fuzzy_px_h_override if fuzzy_px_h_override is not None else int(h * fuzzy_pct)
    )

    logger.debug(f"{log_prefix}fuzzy_px_w={fuzzy_px_w}, fuzzy_px_h={fuzzy_px_h}")

    # Compute fuzzy sum using convolution
    kernel_w = np.ones((2 * fuzzy_px_w + 1,), dtype=int)
    kernel_h = np.ones((2 * fuzzy_px_h + 1,), dtype=int)

    fuzzy_columns = cast(
        "npt.NDArray[np.int64]", np.convolve(columns, kernel_w, mode="same")
    )
    fuzzy_rows = cast("npt.NDArray[np.int64]", np.convolve(rows, kernel_h, mode="same"))

    # Find min and max X using vectorized conditions
    x_indices = np.where(fuzzy_columns >= pixel_value_col_min)[0]
    minX = cast("int", x_indices[0]) if x_indices.size > 0 else 0
    maxX = cast("int", x_indices[-1]) if x_indices.size > 0 else w

    # Find min and max Y using vectorized conditions
    y_indices = np.where(fuzzy_rows >= pixel_value_row_min)[0]
    minY = cast("int", y_indices[0]) if y_indices.size > 0 else 0
    maxY = cast("int", y_indices[-1]) if y_indices.size > 0 else h

    logger.debug(f"{log_prefix}minX={minX}, maxX={maxX}, minY={minY}, maxY={maxY}")
    logger.debug(log_prefix + "Completed")

    return minX, maxX, minY, maxY
