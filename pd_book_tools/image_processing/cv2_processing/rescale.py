# Configure logging
import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def rescale_image(
    img: np.array, aspect_ratio: float = 1.65, target_short_side: int = 1000
):
    height, width = img.shape[:2]

    logger.debug(f"height: {height} width: {width} aspect_ratio: {aspect_ratio}")

    short_side, long_side = (width, height) if height > width else (height, width)
    logger.debug(f"short_side: {short_side} long_side: {long_side}")

    # Scale down the long side to maintain aspect ratio
    target_long_side = (
        int(target_short_side * aspect_ratio)
        if aspect_ratio >= 1
        else int(target_short_side / aspect_ratio)
    )

    logger.debug(f"target_long_side: {target_long_side}")

    scale = target_short_side / float(short_side)
    new_short_side = target_short_side
    new_long_side = int(long_side * scale)

    logger.debug(f"Scale: {scale}")
    logger.debug(f"new_short_side: {new_short_side} new_long_side: {new_long_side}")

    new_size = (
        (new_short_side, new_long_side)
        if height > width
        else (new_long_side, new_short_side)
    )

    img = cv2.resize(src=img, dsize=new_size, interpolation=cv2.INTER_AREA)
    return img
