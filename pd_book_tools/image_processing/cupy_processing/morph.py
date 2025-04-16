# Configure logging
import logging

import cupy as cp
from cupy.lib.stride_tricks import sliding_window_view

logger = logging.getLogger(__name__)


def dilate(img: cp.ndarray, kernel: cp.ndarray):
    """Performs dilation using a fully vectorized approach on a cupy image array."""
    kh, kw = kernel.shape
    pad_h, pad_w = kh // 2, kw // 2

    # Pad the image
    img_padded = cp.pad(
        img, ((pad_h, pad_h), (pad_w, pad_w)), mode="constant", constant_values=0
    )

    # Create sliding windows over the image
    windows = sliding_window_view(img_padded, (kh, kw))

    # Apply max operation over the windows
    return cp.max(windows * kernel, axis=(-2, -1))


def erode(img: cp.ndarray, kernel: cp.ndarray):
    """Performs erosion using a fully vectorized approach on a cupy image array."""
    kh, kw = kernel.shape
    pad_h, pad_w = kh // 2, kw // 2

    # Pad the image
    img_padded = cp.pad(
        img, ((pad_h, pad_h), (pad_w, pad_w)), mode="constant", constant_values=0
    )

    # Create sliding windows over the image
    windows = sliding_window_view(img_padded, (kh, kw))

    # Apply min operation over the windows
    return cp.min(windows * kernel, axis=(-2, -1))


def morph_fill(img: cp.ndarray, shape=(6, 6)):
    """
    Apply closing followed by opening morphology using fully vectorized operations.
    """
    kernel = cp.ones(shape, dtype=cp.uint8)

    # Morphological closing (dilate then erode)
    closed = dilate(img, kernel)
    closed = erode(closed, kernel)

    # Morphological opening (erode then dilate)
    opened = erode(closed, kernel)
    opened = dilate(opened, kernel)

    return opened
