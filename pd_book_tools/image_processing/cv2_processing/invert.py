# Configure logging
import logging

import numpy as np

logger = logging.getLogger(__name__)


def invert_image(img: np.array) -> np.array:
    return 255 - img
