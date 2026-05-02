import logging

import cupy as cp
import numpy as np

logger = logging.getLogger(__name__)

# ITU-R BT.601 weights, matching cv2.COLOR_BGR2GRAY:
#   Y = 0.114*B + 0.587*G + 0.299*R
_BGR2GRAY_WEIGHTS = cp.array([0.114, 0.587, 0.299], dtype=cp.float32)


def bgr_to_gray_gpu(img_cp: cp.ndarray) -> cp.ndarray:
    """
    Convert a BGR uint8 image to grayscale using ITU-R BT.601 weights.
    Matches cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).

    img_cp: (H, W, 3) uint8 CuPy array.
    Returns: (H, W) uint8 CuPy array.
    """
    float_img = img_cp.astype(cp.float32)
    gray = (
        _BGR2GRAY_WEIGHTS[0] * float_img[:, :, 0]
        + _BGR2GRAY_WEIGHTS[1] * float_img[:, :, 1]
        + _BGR2GRAY_WEIGHTS[2] * float_img[:, :, 2]
    )
    return gray.clip(0, 255).astype(cp.uint8)


def gray_to_bgr_gpu(img_cp: cp.ndarray) -> cp.ndarray:
    """
    Convert a grayscale uint8 image to 3-channel BGR by replicating the channel.
    Matches cv2.cvtColor(img, cv2.COLOR_GRAY2BGR).

    img_cp: (H, W) uint8 CuPy array.
    Returns: (H, W, 3) uint8 CuPy array.
    """
    return cp.stack([img_cp, img_cp, img_cp], axis=-1)


def bgr_to_rgb_gpu(img_cp: cp.ndarray) -> cp.ndarray:
    """
    Reverse channel order: BGR → RGB (or RGB → BGR — same operation).
    Matches cv2.cvtColor(img, cv2.COLOR_BGR2RGB).

    img_cp: (H, W, 3) CuPy array.
    Returns: (H, W, 3) CuPy array (contiguous copy).
    """
    return img_cp[:, :, [2, 1, 0]]


# Alias — the operation is its own inverse
rgb_to_bgr_gpu = bgr_to_rgb_gpu


def np_uint8_bgr_to_gray(img: np.ndarray) -> np.ndarray:
    """Transfers img to GPU, converts BGR→gray, returns CPU uint8 array."""
    return cp.asnumpy(bgr_to_gray_gpu(cp.asarray(img)))


def np_uint8_gray_to_bgr(img: np.ndarray) -> np.ndarray:
    """Transfers img to GPU, converts gray→BGR, returns CPU uint8 array."""
    return cp.asnumpy(gray_to_bgr_gpu(cp.asarray(img)))


def np_uint8_bgr_to_rgb(img: np.ndarray) -> np.ndarray:
    """Transfers img to GPU, flips channel order, returns CPU uint8 array."""
    return cp.asnumpy(bgr_to_rgb_gpu(cp.asarray(img)))
