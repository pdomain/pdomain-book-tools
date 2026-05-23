# Configure logging
import logging
from typing import cast

import cv2
import numpy as np
import numpy.typing as npt

logger = logging.getLogger(__name__)

ImageArray = npt.NDArray[np.uint8]


def rescale_image(
    img: ImageArray,
    target_short_side: int = 1000,
) -> ImageArray:
    """Resize ``img`` so its short side equals ``target_short_side``.

    The original aspect ratio is always preserved. Width and height scale
    by a single factor of ``target_short_side / min(height, width)``.

    The deprecated ``aspect_ratio`` parameter was removed entirely (see
    ROADMAP "Done"). Aspect-shape clamping, when needed, is applied
    downstream by ``map_content_onto_scaled_canvas`` in pd-prep-for-pgdp,
    not at rescale time.
    """
    height, width = cast("tuple[int, int]", img.shape[:2])

    logger.debug(f"height: {height} width: {width}")

    short_side, long_side = (width, height) if height > width else (height, width)
    logger.debug(f"short_side: {short_side} long_side: {long_side}")

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

    return cast(
        "ImageArray",
        cv2.resize(src=img, dsize=new_size, interpolation=cv2.INTER_AREA),
    )
