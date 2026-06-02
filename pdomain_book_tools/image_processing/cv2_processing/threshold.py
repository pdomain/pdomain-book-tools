# Configure logging
import logging
from typing import Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def otsu_binary_thresh(img: np.ndarray) -> np.ndarray:
    """Apply Otsu binarisation to a grayscale image, returning the binary result."""
    return cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def binary_thresh(img: np.ndarray, level: int = 127) -> np.ndarray:
    """Apply a fixed-level binary threshold to a grayscale image."""
    return cv2.threshold(img, level, 255, cv2.THRESH_BINARY)[1]


def adaptive_binary_thresh(
    img: np.ndarray,
    *,
    block_size: int = 31,
    c: int = 10,
    mode: str = "gaussian",
) -> np.ndarray:
    """Apply adaptive (local) binarisation to a grayscale image.

    Uses ``cv2.adaptiveThreshold`` with either Gaussian-weighted local means
    (``mode="gaussian"``) or plain uniform local means (``mode="mean"``).
    Output polarity matches ``otsu_binary_thresh``: pixels whose value exceeds
    the local threshold are set to 255 (background); pixels at or below it are
    set to 0 (text).

    Args:
        img: 2-D uint8 grayscale image.
        block_size: Side length of the local neighbourhood (must be an odd
            integer >= 3).
        c: Constant subtracted from the local mean before thresholding.
            Increase to bias more pixels towards 0 (darker output).
        mode: ``"gaussian"`` (default) or ``"mean"``.

    Returns:
        uint8 array with the same shape as *img*, values in {0, 255}.
    """
    if mode == "gaussian":
        adaptive_method = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
    elif mode == "mean":
        adaptive_method = cv2.ADAPTIVE_THRESH_MEAN_C
    else:
        raise ValueError(
            f"Unknown adaptive mode {mode!r}; valid modes are: 'gaussian', 'mean'."
        )
    return cv2.adaptiveThreshold(
        img,
        255,
        adaptive_method,
        cv2.THRESH_BINARY,
        block_size,
        c,
    )


def sauvola_binary_thresh(
    img: np.ndarray,
    *,
    window_size: int = 25,
    k: float = 0.2,
    r: int = 128,
) -> np.ndarray:
    """Apply Sauvola local binarisation to a grayscale image.

    The Sauvola threshold at each pixel is::

        T = m * (1 + k * (s / r - 1))

    where *m* is the local mean and *s* is the local standard deviation over a
    ``window_size x window_size`` neighbourhood. Pixels with value ``> T``
    become 255 (background); pixels ``<= T`` become 0 (text).

    Args:
        img: 2-D uint8 grayscale image.
        window_size: Side length of the local neighbourhood (should be odd).
        k: Sauvola sensitivity parameter (typically 0.2).
        r: Dynamic range of the standard deviation (typically 128 for uint8
            images; controls the weight of the local contrast term).

    Returns:
        uint8 array with the same shape as *img*, values in {0, 255}.
    """
    img_f = img.astype(np.float64)
    # Local mean via uniform box filter (border replicated to avoid edge artefacts)
    local_mean = cv2.boxFilter(
        img_f,
        ddepth=-1,
        ksize=(window_size, window_size),
        borderType=cv2.BORDER_REPLICATE,
    )
    # Local mean of squares → variance → std
    local_mean_sq = cv2.boxFilter(
        img_f**2,
        ddepth=-1,
        ksize=(window_size, window_size),
        borderType=cv2.BORDER_REPLICATE,
    )
    local_var = np.maximum(local_mean_sq - local_mean**2, 0.0)
    local_std = np.sqrt(local_var)

    threshold = local_mean * (1.0 + k * (local_std / r - 1.0))
    return np.where(img_f > threshold, 255, 0).astype(np.uint8)


def niblack_binary_thresh(
    img: np.ndarray,
    *,
    window_size: int = 25,
    k: float = -0.2,
) -> np.ndarray:
    """Apply Niblack local binarisation to a grayscale image.

    The Niblack threshold at each pixel is::

        T = m + k * s

    where *m* is the local mean and *s* is the local standard deviation over a
    ``window_size x window_size`` neighbourhood. Pixels with value ``> T``
    become 255 (background); pixels ``<= T`` become 0 (text). The default
    ``k=-0.2`` biases the threshold slightly below the mean, which is the
    standard setting for documents where dark text on light paper is the
    foreground.

    Args:
        img: 2-D uint8 grayscale image.
        window_size: Side length of the local neighbourhood (should be odd).
        k: Niblack sensitivity parameter (typically -0.2).

    Returns:
        uint8 array with the same shape as *img*, values in {0, 255}.
    """
    img_f = img.astype(np.float64)
    local_mean = cv2.boxFilter(
        img_f,
        ddepth=-1,
        ksize=(window_size, window_size),
        borderType=cv2.BORDER_REPLICATE,
    )
    local_mean_sq = cv2.boxFilter(
        img_f**2,
        ddepth=-1,
        ksize=(window_size, window_size),
        borderType=cv2.BORDER_REPLICATE,
    )
    local_var = np.maximum(local_mean_sq - local_mean**2, 0.0)
    local_std = np.sqrt(local_var)

    threshold = local_mean + k * local_std
    return np.where(img_f > threshold, 255, 0).astype(np.uint8)


def binarize(img: np.ndarray, *, method: str = "otsu", **params: Any) -> np.ndarray:
    """Binarise a grayscale image via the named method, dispatching to its helper."""
    if method == "otsu":
        return otsu_binary_thresh(img)
    if method == "adaptive":
        return adaptive_binary_thresh(img, **params)
    if method == "sauvola":
        return sauvola_binary_thresh(img, **params)
    if method == "niblack":
        return niblack_binary_thresh(img, **params)
    raise ValueError(
        f"Unknown binarization method {method!r}; "
        "valid methods are: 'otsu', 'adaptive', 'sauvola', 'niblack'."
    )
