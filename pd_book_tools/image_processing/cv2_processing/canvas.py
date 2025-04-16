import logging
import math
from enum import Enum

import numpy as np

# Configure logging
logger = logging.getLogger(__name__)


class Alignment(Enum):
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"
    DEFAULT = "default"


def map_content_onto_scaled_canvas(
    image: np.array,
    force_align: Alignment = Alignment.DEFAULT,
    height_width_ratio: float = 1.65,
    whitespace_add: float = 0.051,
) -> np.array:
    """
    Maps an image onto a larger canvas with a fixed aspect ratio and adjustable alignment.

    Parameters:
        image (np.array): Input image array.
        force_align (Alignment): Alignment option (Alignment.TOP, Alignment.CENTER, Alignment.BOTTOM, or Alignment.DEFAULT).
        height_width_ratio (float): Desired height-to-width ratio of the new canvas.
        whitespace_add (float): Percentage of additional whitespace to add.

    Returns:
        np.array: Processed image on a larger canvas.
    """
    logger.debug("map_content_onto_scaled_canvas - Start")

    height, width = image.shape[:2]
    logger.debug("height={} width={}".format(height, width))

    # Calculate new canvas size with white space
    current_ratio = float(height) / float(width)
    logger.debug("current_ratio={}".format(current_ratio))

    if current_ratio >= height_width_ratio:
        new_height = int(math.ceil(height / (1 - (whitespace_add * 2))))
        new_width = int(math.ceil(new_height / height_width_ratio))
    else:
        new_width = int(math.ceil(width / (1 - (whitespace_add * 2))))
        new_height = int(math.ceil(new_width * height_width_ratio))

    logger.debug("new_height={} new_width={}".format(new_height, new_width))

    # Create a blank white canvas
    canvas: np.array = np.full((new_height, new_width), 255, dtype=np.uint8)
    canvas_height, canvas_width = canvas.shape[:2]
    logger.debug("canvas_height={} canvas_width={}".format(canvas_height, canvas_width))

    # Determine vertical alignment
    if force_align == Alignment.BOTTOM:
        logger.debug("Aligning to bottom")
        y_offset = canvas_height - (
            height + int(math.ceil(whitespace_add * canvas_height))
        )
    elif force_align == Alignment.CENTER:
        logger.debug("Aligning to center")
        y_offset = int(canvas_height / 2) - int(height / 2)
    else:
        logger.debug("Aligning to top")
        y_offset = int(math.ceil(whitespace_add * canvas_height))

    x_offset = int(canvas_width / 2) - int(width / 2)

    logger.debug("y_offset={} x_offset={}".format(y_offset, x_offset))

    # Place the image on the blank canvas
    canvas[y_offset : y_offset + height, x_offset : x_offset + width] = image
    return canvas
