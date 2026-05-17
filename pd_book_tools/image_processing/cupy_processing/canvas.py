from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from pd_book_tools.image_processing.types import Alignment

from ._cupy_compat import cp, require_cupy

if TYPE_CHECKING:
    import numpy as np

logger = logging.getLogger(__name__)


def map_content_onto_scaled_canvas_gpu(
    img_cp: cp.ndarray,
    force_align: Alignment = Alignment.DEFAULT,
    height_width_ratio: float = 1.65,
    whitespace_add: float = 0.051,
) -> cp.ndarray:
    """
    GPU port of cv2_processing.canvas.map_content_onto_scaled_canvas.

    Creates a white canvas with the target aspect ratio and places img_cp on it.
    All geometry computation is scalar (CPU); only canvas allocation and image
    placement run on the GPU.

    img_cp: 2-D uint8 CuPy array (grayscale).
    """
    require_cupy()
    height, width = img_cp.shape[:2]

    current_ratio = float(height) / float(width)

    if current_ratio >= height_width_ratio:
        new_height = math.ceil(height / (1 - (whitespace_add * 2)))
        new_width = math.ceil(new_height / height_width_ratio)
    else:
        new_width = math.ceil(width / (1 - (whitespace_add * 2)))
        new_height = math.ceil(new_width * height_width_ratio)

    canvas = cp.full((new_height, new_width), 255, dtype=cp.uint8)

    if force_align == Alignment.BOTTOM:
        y_offset = new_height - (height + math.ceil(whitespace_add * new_height))
    elif force_align == Alignment.CENTER:
        y_offset = int(new_height / 2) - int(height / 2)
    else:
        y_offset = math.ceil(whitespace_add * new_height)

    x_offset = int(new_width / 2) - int(width / 2)

    canvas[y_offset : y_offset + height, x_offset : x_offset + width] = img_cp

    logger.debug(
        "map_content_onto_scaled_canvas_gpu: %sx%s -> %sx%s offset=(%s,%s) align=%s",
        height,
        width,
        new_height,
        new_width,
        y_offset,
        x_offset,
        force_align,
    )
    return canvas


def np_uint8_map_content_onto_scaled_canvas(
    img: np.ndarray,
    force_align: Alignment = Alignment.DEFAULT,
    height_width_ratio: float = 1.65,
    whitespace_add: float = 0.051,
) -> np.ndarray:
    """Transfers img to GPU, maps onto scaled canvas, returns CPU uint8 array."""
    require_cupy()
    img_cp = cp.asarray(img)
    return cp.asnumpy(
        map_content_onto_scaled_canvas_gpu(
            img_cp, force_align, height_width_ratio, whitespace_add
        )
    )
