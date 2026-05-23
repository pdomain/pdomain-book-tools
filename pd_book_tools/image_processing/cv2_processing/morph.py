# Configure logging
import logging
from typing import cast

import cv2
import numpy as np
import numpy.typing as npt

logger = logging.getLogger(__name__)

ImageArray = npt.NDArray[np.uint8]


def morph_fill(img: ImageArray, shape: tuple[int, int] = (6, 6)) -> ImageArray:
    """
    Apply close and open morphology to fill
    small holes and save as mask.
    """
    kernel = np.ones(shape, np.uint8)
    closed = cast("ImageArray", cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel))
    return cast("ImageArray", cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel))
