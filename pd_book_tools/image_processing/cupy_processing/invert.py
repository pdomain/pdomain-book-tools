# Configure logging
import logging

import cupy as cp

logger = logging.getLogger(__name__)


def invert_image(img: cp.array) -> cp.array:
    return 255 - img
