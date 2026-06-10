"""Binary-image speckle removal for binarized book-scan pages.

Polarity convention: this module follows the repository convention where text
pixels are 0 (dark) and background pixels are 255 (light), matching the
output of ``otsu_binary_thresh`` and ``binary_thresh``.  Pass your binary
image in that polarity and you get the same polarity back.

The algorithm uses connected-component area filtering to remove isolated
speckle while preserving genuine glyph features, including small marks such
as periods, diacritics, and thin serifs.  An optional median-blur pre-pass
can first suppress salt-and-pepper noise before the component filter runs.
"""

from __future__ import annotations

import logging
from typing import cast

import cv2
import numpy as np
import numpy.typing as npt

logger = logging.getLogger(__name__)

ImageArray = npt.NDArray[np.uint8]


def denoise_binary(
    img: ImageArray,
    *,
    min_component_area: int = 6,
    median_kernel_size: int = 0,
) -> ImageArray:
    """Remove speckle noise from a binarized page image using connected-component
    area filtering, with an optional median-blur pre-pass.

    Input and output polarity: text=0 (dark), background=255 (light) — the
    standard convention for this library (matches ``otsu_binary_thresh``).

    The function operates by inverting the image internally so that ink (text)
    forms white foreground components, labelling connected components with
    ``cv2.connectedComponents``, and zeroing out any component whose area
    (pixel count) is strictly below ``min_component_area``.  Components at or
    above the threshold are preserved unchanged.

    If ``median_kernel_size`` is a positive odd integer, a median blur is
    applied to the inverted image before component filtering.  This suppresses
    individual salt-and-pepper pixels before the component stage runs.

    Parameters are tuned for ~300 DPI scanned book pages.  At that resolution
    a period is approximately 6-9 px², so the default ``min_component_area=6``
    preserves periods and all genuine glyph features while removing 1-5 px
    single-pixel and 2-4 px cluster speckle.  Increase ``min_component_area``
    to also remove small diacritic-sized marks, but audit results on real pages
    first.

    Args:
        img: 2-D uint8 binary image with text=0, background=255.
        min_component_area: Connected components with fewer pixels than this
            value are removed.  Default 6 px² (period-safe at 300 DPI).
        median_kernel_size: Kernel size for an optional median blur pre-pass
            (must be a positive odd integer, or 0 to skip).  Default 0 (off).

    Returns:
        uint8 array with the same shape and dtype as *img*, with speckle
        components removed.  The caller's input is never mutated.

    Raises:
        ValueError: If *img* is not a 2-D array, not dtype uint8, or if
            *median_kernel_size* is given but is not a positive odd integer.
    """
    if img.ndim != 2:
        raise ValueError(f"denoise_binary expects a 2-D array; got ndim={img.ndim}.")
    if img.dtype != np.uint8:
        raise ValueError(f"denoise_binary expects dtype uint8; got dtype={img.dtype}.")
    if median_kernel_size != 0 and (
        median_kernel_size < 1 or median_kernel_size % 2 == 0
    ):
        raise ValueError(
            f"median_kernel_size must be 0 (off) or a positive odd integer; "
            f"got {median_kernel_size}."
        )

    # Invert: text (0) becomes foreground (255) for connected-component labelling.
    fg = cast("ImageArray", cv2.bitwise_not(img))

    if median_kernel_size > 0:
        fg = cast("ImageArray", cv2.medianBlur(fg, median_kernel_size))

    # Label connected components.  Background label is 0; ink labels are 1..n_labels-1.
    n_labels, labels_raw = cv2.connectedComponents(fg)
    labels: npt.NDArray[np.int32] = labels_raw.astype(np.int32)

    if n_labels <= 1:
        # No ink components remain — return a fully clean image.
        return cast("ImageArray", cv2.bitwise_not(fg))

    # Count pixel area per label using bincount; exclude background (label 0).
    counts = np.bincount(labels.ravel(), minlength=n_labels)
    # Build a boolean keep mask indexed by label.
    keep: npt.NDArray[np.bool_] = counts >= min_component_area
    keep[0] = False  # never keep the background label as ink

    # Reconstruct foreground with small components zeroed.
    clean_fg = np.where(keep[labels], np.uint8(255), np.uint8(0)).astype(np.uint8)

    # Invert back: text=0, background=255.
    return cast("ImageArray", cv2.bitwise_not(clean_fg))
