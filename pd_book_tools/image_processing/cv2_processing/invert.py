# Configure logging
import logging

import numpy as np

logger = logging.getLogger(__name__)


def invert_image(img: np.ndarray) -> np.ndarray:
    """Invert a uint8 numpy image (255 - pixel value for each element)."""
    return 255 - img
