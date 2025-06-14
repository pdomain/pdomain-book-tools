# Configure logging
import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def cv2_convert_to_grayscale(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
