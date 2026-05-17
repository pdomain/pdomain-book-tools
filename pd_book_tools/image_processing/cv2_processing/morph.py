# Configure logging
import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def morph_fill(img: np.ndarray, shape: tuple[int, int] = (6, 6)) -> np.ndarray:
    """
    Apply close and open morphology to fill
    small holes and save as mask.
    """
    kernel = np.ones(shape, np.uint8)
    closed: np.ndarray = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)  # pyright: ignore[reportAssignmentType]  # cv2.morphologyEx returns MatLike; ndarray annotation is safe
    return cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel)  # pyright: ignore[reportReturnType]  # MatLike is ndarray-compatible at runtime
