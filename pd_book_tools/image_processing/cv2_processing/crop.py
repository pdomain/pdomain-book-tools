# Configure logging
import logging

import numpy as np

logger = logging.getLogger(__name__)


def crop_to_rectangle(
    img: np.ndarray,
    minX,
    maxX,
    minY,
    maxY,
):
    """
    Crops an image to the given bounding box coordinates, ensuring they are within bounds.

    Args:
        img (np.ndarray): The input image.
        minX (int): Minimum X coordinate.
        maxX (int): Maximum X coordinate.
        minY (int): Minimum Y coordinate.
        maxY (int): Maximum Y coordinate.

    Returns:
        np.ndarray: Cropped image.
    """
    log_prefix = "crop_to_rectangle - "

    # Get image dimensions
    h, w = img.shape[:2]

    # Ensure coordinates are within valid range
    minX = max(0, min(minX, w - 1))
    maxX = max(0, min(maxX, w))
    minY = max(0, min(minY, h - 1))
    maxY = max(0, min(maxY, h))

    # Ensure cropping makes sense
    if minX >= maxX or minY >= maxY:
        logger.warning(
            f"{log_prefix}Invalid crop dimensions: minX={minX}, maxX={maxX}, minY={minY}, maxY={maxY}. Returning original image."
        )
        return img  # Return original if invalid crop

    logger.debug(
        f"{log_prefix}Cropping image to: minX={minX}, maxX={maxX}, minY={minY}, maxY={maxY}"
    )

    # Perform cropping
    return img[minY:maxY, minX:maxX]


def crop_edges(
    img: np.ndarray,
    top: int = 0,
    bottom: int = 0,
    left: int = 0,
    right: int = 0,
) -> np.ndarray:
    """
    Crops the given image by removing pixels from the specified edges.

    Parameters:
        img (np.ndarray): Input image as a NumPy array.
        top (int): Number of pixels to remove from the top. Default is 0.
        bottom (int): Number of pixels to remove from the bottom. Default is 0.
        left (int): Number of pixels to remove from the left. Default is 0.
        right (int): Number of pixels to remove from the right. Default is 0.

    Returns:
        np.ndarray: Cropped image.

    Raises:
        ValueError: If the cropping values exceed the image dimensions.
    """
    h, w = img.shape[:2]

    if top + bottom >= h or left + right >= w:
        raise ValueError("Cropping values exceed image dimensions.")

    return img[top : h - bottom, left : w - right]
