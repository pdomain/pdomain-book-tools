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
    """Apply adaptive (local) binarisation to a grayscale image (not yet implemented)."""
    raise NotImplementedError(
        "adaptive_binary_thresh is a stub; the adaptive binarization method is "
        "specified but not yet implemented. See "
        "docs/specs/2026-06-02-threshold-binarization-methods.md."
    )


def sauvola_binary_thresh(
    img: np.ndarray,
    *,
    window_size: int = 25,
    k: float = 0.2,
    r: int = 128,
) -> np.ndarray:
    """Apply Sauvola local binarisation to a grayscale image (not yet implemented)."""
    raise NotImplementedError(
        "sauvola_binary_thresh is a stub; the Sauvola binarization method is "
        "specified but not yet implemented. See "
        "docs/specs/2026-06-02-threshold-binarization-methods.md."
    )


def niblack_binary_thresh(
    img: np.ndarray,
    *,
    window_size: int = 25,
    k: float = -0.2,
) -> np.ndarray:
    """Apply Niblack local binarisation to a grayscale image (not yet implemented)."""
    raise NotImplementedError(
        "niblack_binary_thresh is a stub; the Niblack binarization method is "
        "specified but not yet implemented. See "
        "docs/specs/2026-06-02-threshold-binarization-methods.md."
    )


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
