# Configure logging
import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def morph_fill(img: np.ndarray, shape=(6, 6)):
    """
    apply close and open morphology to fill
    small holes and save as mask
    """
    kernel = np.ones(shape, np.uint8)
    mask: cv2.Mat = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)  # type: ignore
    mask: cv2.Mat = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)  # type: ignore

    return mask
