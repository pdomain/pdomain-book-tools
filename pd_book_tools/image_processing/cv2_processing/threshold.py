# Configure logging
import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def otsu_binary_thresh(img: np.ndarray):
    return cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def binary_thresh(img: np.ndarray, level=127):
    return cv2.threshold(img, level, 255, cv2.THRESH_BINARY)[1]
