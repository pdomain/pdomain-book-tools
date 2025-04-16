# Configure logging
import logging

import numpy as np

logger = logging.getLogger(__name__)


def find_edges(
    img: np.array,
    fuzzy_pct=0.02,
    pixel_count_columns=150,
    pixel_count_rows=75,
    fuzzy_px_w_override=None,
    fuzzy_px_h_override=None,
):
    """
    Optimized version of finding edges in a binary image using vectorized NumPy operations.
    """
    log_prefix = "find_edges - "
    logger.debug(log_prefix + "Start")

    # Compute sum across columns and rows
    columns = np.sum(img, axis=0)
    rows = np.sum(img, axis=1)

    pixel_value_col_min = pixel_count_columns * 256
    pixel_value_row_min = pixel_count_rows * 256

    logger.debug(
        f"{log_prefix}pixel_value_col_min={pixel_value_col_min}, pixel_value_row_min={pixel_value_row_min}"
    )

    h, w = img.shape[:2]

    # Compute fuzzy pixel width and height
    fuzzy_px_w = fuzzy_px_w_override if fuzzy_px_w_override else int(w * fuzzy_pct)
    fuzzy_px_h = fuzzy_px_h_override if fuzzy_px_h_override else int(h * fuzzy_pct)

    logger.debug(f"{log_prefix}fuzzy_px_w={fuzzy_px_w}, fuzzy_px_h={fuzzy_px_h}")

    # Compute fuzzy sum using convolution
    kernel_w = np.ones((2 * fuzzy_px_w + 1,), dtype=int)
    kernel_h = np.ones((2 * fuzzy_px_h + 1,), dtype=int)

    fuzzy_columns = np.convolve(columns, kernel_w, mode="same")
    fuzzy_rows = np.convolve(rows, kernel_h, mode="same")

    # Find min and max X using vectorized conditions
    x_indices = np.where(fuzzy_columns >= pixel_value_col_min)[0]
    minX = x_indices[0] if x_indices.size > 0 else 0
    maxX = x_indices[-1] if x_indices.size > 0 else w

    # Find min and max Y using vectorized conditions
    y_indices = np.where(fuzzy_rows >= pixel_value_row_min)[0]
    minY = y_indices[0] if y_indices.size > 0 else 0
    maxY = y_indices[-1] if y_indices.size > 0 else h

    logger.debug(f"{log_prefix}minX={minX}, maxX={maxX}, minY={minY}, maxY={maxY}")
    logger.debug(log_prefix + "Completed")

    return minX, maxX, minY, maxY
