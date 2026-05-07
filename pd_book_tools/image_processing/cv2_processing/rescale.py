# Configure logging
import logging
import warnings

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Sentinel for "caller did not pass aspect_ratio" so we can distinguish a
# deliberate (legacy, no-op) call from a default-valued one and only warn
# in the former case. R-24: the parameter is unused — the function always
# preserves the source aspect ratio — but downstream callers
# (pd-prep-for-pgdp/core/pipeline/process_page.py:154) pass it expecting
# it to clamp the long side. Warn loudly rather than silently honor.
_ASPECT_RATIO_DEFAULT = 1.65


def rescale_image(
    img: np.ndarray,
    aspect_ratio: float = _ASPECT_RATIO_DEFAULT,
    target_short_side: int = 1000,
):
    """Resize ``img`` so its short side equals ``target_short_side``.

    The original aspect ratio is always preserved. The ``aspect_ratio``
    parameter is **deprecated and unused**: a non-default value emits a
    ``DeprecationWarning``. It will be removed in a future major. See
    R-24 in ``docs/review/refactors.md``.
    """
    if aspect_ratio != _ASPECT_RATIO_DEFAULT:
        warnings.warn(
            "rescale_image(aspect_ratio=...) is deprecated and has no effect. "
            "The function always preserves the source image's aspect ratio. "
            "Drop the keyword argument; it will be removed in a future major.",
            DeprecationWarning,
            stacklevel=2,
        )

    height, width = img.shape[:2]

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

    img = cv2.resize(src=img, dsize=new_size, interpolation=cv2.INTER_AREA)
    return img
