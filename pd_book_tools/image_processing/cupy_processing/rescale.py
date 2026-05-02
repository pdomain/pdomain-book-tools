import logging

import cupy as cp
import numpy as np
from cupyx.scipy.ndimage import zoom

logger = logging.getLogger(__name__)


def rescale_image_gpu(
    img_cp: cp.ndarray,
    aspect_ratio: float = 1.65,
    target_short_side: int = 1000,
) -> cp.ndarray:
    """
    GPU port of cv2_processing.rescale.rescale_image.

    Rescales img_cp so its short side equals target_short_side, preserving the
    original aspect ratio.  Uses bilinear interpolation (order=1).

    img_cp: 2-D (grayscale) or 3-D (colour) uint8 CuPy array.
    """
    height, width = img_cp.shape[:2]

    short_side = width if height > width else height
    long_side = height if height > width else width

    scale = target_short_side / float(short_side)
    new_short = target_short_side
    new_long = int(long_side * scale)

    new_h = new_long if height > width else new_short
    new_w = new_short if height > width else new_long

    zoom_h = new_h / height
    zoom_w = new_w / width

    zoom_factors = (zoom_h, zoom_w) if img_cp.ndim == 2 else (zoom_h, zoom_w, 1.0)

    logger.debug(f"rescale_image_gpu: {height}x{width} -> {new_h}x{new_w}")
    result = zoom(img_cp.astype(cp.float32), zoom_factors, order=1)
    return result.clip(0, 255).astype(cp.uint8)


def np_uint8_rescale_image(
    img: np.ndarray,
    aspect_ratio: float = 1.65,
    target_short_side: int = 1000,
) -> np.ndarray:
    """Transfers img to GPU, rescales, returns CPU uint8 array."""
    img_cp = cp.asarray(img)
    return cp.asnumpy(rescale_image_gpu(img_cp, aspect_ratio, target_short_side))
