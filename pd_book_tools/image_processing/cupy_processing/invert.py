# Configure logging
import logging

import cupy as cp

logger = logging.getLogger(__name__)


def invert_image(img: cp.ndarray) -> cp.ndarray:
    return 255 - img
