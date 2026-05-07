from __future__ import annotations

import logging
import warnings

import numpy as np

from ._cupy_compat import cp, require_cupy

# R-24: aspect_ratio is unused; warn when callers pass a non-default value.
# Match the cv2 backend's sentinel-default approach for parity.
_ASPECT_RATIO_DEFAULT = 1.65


def _warn_deprecated_aspect_ratio(aspect_ratio: float) -> None:
    if aspect_ratio != _ASPECT_RATIO_DEFAULT:
        warnings.warn(
            "rescale_image_gpu / np_uint8_rescale_image: aspect_ratio is "
            "deprecated and has no effect. The function always preserves the "
            "source image's aspect ratio. Drop the keyword argument; it will "
            "be removed in a future major.",
            DeprecationWarning,
            stacklevel=3,  # surface caller of the public function
        )


try:
    from cupyx.scipy.ndimage import (  # type: ignore[import-not-found]
        uniform_filter,
        zoom,
    )
except ImportError:  # pragma: no cover - exercised only on CPU-only installs
    uniform_filter = None
    zoom = None

logger = logging.getLogger(__name__)


def rescale_image_gpu(
    img_cp: cp.ndarray,
    aspect_ratio: float = _ASPECT_RATIO_DEFAULT,
    target_short_side: int = 1000,
) -> cp.ndarray:
    """
    GPU port of cv2_processing.rescale.rescale_image.

    Rescales img_cp so its short side equals target_short_side, preserving the
    original aspect ratio.  Uses bilinear interpolation (order=1) plus a
    pre-pass uniform (box) filter when downscaling, so the result approximates
    cv2.resize(..., INTER_AREA) and is free of aliasing for the typical
    600 -> 150 / 200 DPI book-scan reductions.

    img_cp: 2-D (grayscale) or 3-D (colour) uint8 CuPy array.

    The ``aspect_ratio`` parameter is **deprecated and unused** (R-24);
    a non-default value emits a ``DeprecationWarning``.
    """
    _warn_deprecated_aspect_ratio(aspect_ratio)
    require_cupy()
    height, width = img_cp.shape[:2]

    short_side = width if height > width else height
    long_side = height if height > width else width

    scale = target_short_side / float(short_side)
    new_short = target_short_side
    new_long = int(long_side * scale)

    new_h = new_long if height > width else new_short
    new_w = new_short if height > width else new_long

    zoom_h = new_h / height
    zoom_w = new_w / width

    logger.debug(f"rescale_image_gpu: {height}x{width} -> {new_h}x{new_w}")

    src = img_cp.astype(cp.float32)

    # Anti-alias before subsampling. Bare bilinear (order=1) zoom aliases on
    # high-frequency content when zoom_factor < 1; cv2 sidesteps this with
    # INTER_AREA's pixel-area averaging. Approximate that here with a
    # uniform_filter whose window equals the source-pixels-per-output-pixel
    # ratio, applied only on axes that are actually shrinking.
    # Use ceil so any downscale (even sub-2x) still picks up a >=2 box; this
    # matches cv2.resize(INTER_AREA) which averages over partial source pixels
    # even at non-integer ratios. Round-to-int would leave 1.33x reductions
    # (e.g. 800->600) running with no pre-filter and aliasing high-frequency
    # patterns visibly.
    pre_filter_size_h = max(2, int(np.ceil(1.0 / zoom_h))) if zoom_h < 1.0 else 1
    pre_filter_size_w = max(2, int(np.ceil(1.0 / zoom_w))) if zoom_w < 1.0 else 1
    if pre_filter_size_h > 1 or pre_filter_size_w > 1:
        if src.ndim == 2:
            filter_size = (pre_filter_size_h, pre_filter_size_w)
        else:
            filter_size = (pre_filter_size_h, pre_filter_size_w, 1)
        src = uniform_filter(src, size=filter_size, mode="reflect")

    zoom_factors = (zoom_h, zoom_w) if img_cp.ndim == 2 else (zoom_h, zoom_w, 1.0)
    result = zoom(src, zoom_factors, order=1)
    return result.clip(0, 255).astype(cp.uint8)


def np_uint8_rescale_image(
    img: np.ndarray,
    aspect_ratio: float = _ASPECT_RATIO_DEFAULT,
    target_short_side: int = 1000,
) -> np.ndarray:
    """Transfers img to GPU, rescales, returns CPU uint8 array.

    The ``aspect_ratio`` parameter is **deprecated and unused** (R-24);
    a non-default value emits a ``DeprecationWarning``.
    """
    _warn_deprecated_aspect_ratio(aspect_ratio)
    require_cupy()
    img_cp = cp.asarray(img)
    # Pass the default through so rescale_image_gpu doesn't re-warn.
    return cp.asnumpy(
        rescale_image_gpu(img_cp, _ASPECT_RATIO_DEFAULT, target_short_side)
    )
