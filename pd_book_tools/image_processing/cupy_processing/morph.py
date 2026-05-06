# Configure logging
import logging

import cupy as cp
import numpy as np
from cupy.lib.stride_tricks import sliding_window_view

logger = logging.getLogger(__name__)


def dilate(img: cp.ndarray, kernel: cp.ndarray):
    """Performs dilation using a fully vectorized approach on a cupy image array."""
    kh, kw = kernel.shape
    pad_h, pad_w = kh // 2, kw // 2

    # Pad the image
    # Use 'reflect' padding to mirror cv2's default BORDER_REFLECT_101
    # (numpy/cupy 'reflect' excludes the edge pixel: dcb|abcd|cba). Constant-0
    # padding silently eroded foreground pixels touching the image border —
    # see M-08 in docs/review/bugs-medium.md.
    img_padded = cp.pad(img, ((pad_h, pad_h), (pad_w, pad_w)), mode="reflect")

    # Create sliding windows over the image
    windows = sliding_window_view(img_padded, (kh, kw))

    # Apply max operation over the windows.
    # NOTE: the only call site (`morph_fill`) builds `kernel` as
    # `cp.ones(...)`, so multiplying `windows * kernel` is a no-op that
    # nonetheless materializes a full `(H, W, kh, kw)` intermediate
    # (~432 MB for a 3000x4000 page with a 6x6 kernel) before reducing.
    # Reducing directly over `windows` cuts peak GPU memory dramatically
    # without changing output. See M-09 in docs/review/bugs-medium.md.
    # If a non-trivial (non-rectangular) structuring element is ever
    # needed, use `cupyx.scipy.ndimage.grey_dilation` rather than
    # reintroducing a multiplied intermediate.
    return cp.max(windows, axis=(-2, -1))


def erode(img: cp.ndarray, kernel: cp.ndarray):
    """Performs erosion using a fully vectorized approach on a cupy image array."""
    kh, kw = kernel.shape
    pad_h, pad_w = kh // 2, kw // 2

    # Pad the image
    # Use 'reflect' padding to mirror cv2's default BORDER_REFLECT_101
    # (numpy/cupy 'reflect' excludes the edge pixel: dcb|abcd|cba). Constant-0
    # padding silently eroded foreground pixels touching the image border —
    # see M-08 in docs/review/bugs-medium.md.
    img_padded = cp.pad(img, ((pad_h, pad_h), (pad_w, pad_w)), mode="reflect")

    # Create sliding windows over the image
    windows = sliding_window_view(img_padded, (kh, kw))

    # Apply min operation over the windows.
    # Same M-09 optimization as in `dilate`: the only call site builds an
    # all-ones kernel, so multiplying is a no-op that materializes a
    # large intermediate. Reduce over `windows` directly.
    return cp.min(windows, axis=(-2, -1))


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


def np_uint8_morph_fill(img: np.ndarray, shape=(6, 6)) -> np.ndarray:
    """Transfers img to GPU, applies morph_fill, returns CPU uint8 array."""
    return cp.asnumpy(morph_fill(cp.asarray(img), shape=shape))
