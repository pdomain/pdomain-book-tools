# Configure logging
import logging

import numpy as np

logger = logging.getLogger(__name__)


def invert_image(img: np.ndarray) -> np.ndarray:
    return 255 - img
