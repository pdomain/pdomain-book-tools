# Configure logging
import logging
from typing import cast

import numpy as np
import numpy.typing as npt

logger = logging.getLogger(__name__)

ImageArray = npt.NDArray[np.uint8]


def crop_to_rectangle(
    img: ImageArray,
    minX: int,
    maxX: int,
    minY: int,
    maxY: int,
) -> ImageArray:
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
    h, w = cast("tuple[int, int]", img.shape[:2])

    # Ensure coordinates are within valid range
    minX = max(0, min(minX, w - 1))
    maxX = max(0, min(maxX, w))
    minY = max(0, min(minY, h - 1))
    maxY = max(0, min(maxY, h))

    # Ensure cropping makes sense
    if minX >= maxX or minY >= maxY:
        logger.warning(
            "%sInvalid crop dimensions: minX=%s, maxX=%s, minY=%s, maxY=%s. Returning original image.",
            log_prefix,
            minX,
            maxX,
            minY,
            maxY,
        )
        return img  # Return original if invalid crop

    logger.debug(
        "%sCropping image to: minX=%s, maxX=%s, minY=%s, maxY=%s",
        log_prefix,
        minX,
        maxX,
        minY,
        maxY,
    )

    # Perform cropping
    return img[minY:maxY, minX:maxX]


def crop_edges(
    img: ImageArray,
    top: int = 0,
    bottom: int = 0,
    left: int = 0,
    right: int = 0,
) -> ImageArray:
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
        ValueError: If any crop value is negative, or if the cropping
            values exceed the image dimensions.
    """
    for name, value in (
        ("top", top),
        ("bottom", bottom),
        ("left", left),
        ("right", right),
    ):
        if value < 0:
            raise ValueError(f"Crop value {name!r} must be non-negative, got {value}.")

    h, w = cast("tuple[int, int]", img.shape[:2])

    if top + bottom >= h or left + right >= w:
        raise ValueError("Cropping values exceed image dimensions.")

    return img[top : h - bottom, left : w - right]
