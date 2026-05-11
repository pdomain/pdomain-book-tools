import logging
import math

import numpy as np

# Re-export `Alignment` from the backend-neutral types module so existing
# callers (`from pd_book_tools.image_processing.cv2_processing.canvas
# import Alignment`) keep working. The canonical location is
# `pd_book_tools.image_processing.types`; the cupy backend imports from
# there directly so it does not pull cv2_processing in. (M-27)
from pd_book_tools.image_processing.types import Alignment

# Configure logging
logger = logging.getLogger(__name__)


__all__ = ["Alignment", "map_content_onto_scaled_canvas"]


def map_content_onto_scaled_canvas(
    image: np.ndarray,
    force_align: Alignment = Alignment.DEFAULT,
    height_width_ratio: float = 1.65,
    whitespace_add: float = 0.051,
) -> np.ndarray:
    """
    Maps an image onto a larger canvas with a fixed aspect ratio and adjustable alignment.

    Parameters:
        image (np.ndarray): Input image array.
        force_align (Alignment): Alignment option (Alignment.TOP, Alignment.CENTER, Alignment.BOTTOM, or Alignment.DEFAULT).
        height_width_ratio (float): Desired height-to-width ratio of the new canvas.
        whitespace_add (float): Percentage of additional whitespace to add.

    Returns:
        np.ndarray: Processed image on a larger canvas.
    """
    logger.debug("map_content_onto_scaled_canvas - Start")

    height, width = image.shape[:2]
    logger.debug(f"height={height} width={width}")

    # Calculate new canvas size with white space
    current_ratio = float(height) / float(width)
    logger.debug(f"current_ratio={current_ratio}")

    if current_ratio >= height_width_ratio:
        new_height = math.ceil(height / (1 - (whitespace_add * 2)))
        new_width = math.ceil(new_height / height_width_ratio)
    else:
        new_width = math.ceil(width / (1 - (whitespace_add * 2)))
        new_height = math.ceil(new_width * height_width_ratio)

    logger.debug(f"new_height={new_height} new_width={new_width}")

    # Create a blank white canvas matching the input's channel layout.
    # 2D (grayscale) input -> 2D canvas; 3-channel input -> 3-channel
    # canvas. Without this, a 3-channel input crashes the placement step
    # at ``canvas[...] = image`` with a broadcast error and silently
    # implies a grayscale-only contract that nothing documents (M-12).
    if image.ndim == 3:
        canvas_shape: tuple[int, ...] = (new_height, new_width, image.shape[2])
    else:
        canvas_shape = (new_height, new_width)
    canvas: np.ndarray = np.full(canvas_shape, 255, dtype=np.uint8)
    canvas_height, canvas_width = canvas.shape[:2]
    logger.debug(f"canvas_height={canvas_height} canvas_width={canvas_width}")

    # Determine vertical alignment
    if force_align == Alignment.BOTTOM:
        logger.debug("Aligning to bottom")
        y_offset = canvas_height - (height + math.ceil(whitespace_add * canvas_height))
    elif force_align == Alignment.CENTER:
        logger.debug("Aligning to center")
        y_offset = int(canvas_height / 2) - int(height / 2)
    else:
        logger.debug("Aligning to top")
        y_offset = math.ceil(whitespace_add * canvas_height)

    x_offset = int(canvas_width / 2) - int(width / 2)

    logger.debug(f"y_offset={y_offset} x_offset={x_offset}")

    # Place the image on the blank canvas
    canvas[y_offset : y_offset + height, x_offset : x_offset + width] = image
    return canvas
