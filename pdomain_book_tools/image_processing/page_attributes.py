"""Heuristic page-attribute detection from image arrays or encoded bytes.

Provides two entry points:

- :func:`detect_page_attributes_from_array` — core implementation; accepts a
  BGR ``uint8`` ndarray (the natural form coming out of cv2 decoders and
  pipeline stages that already hold an in-memory image).
- :func:`detect_page_attributes` — convenience wrapper; decodes image bytes
  and delegates to the array variant.  Callers holding bytes can use this to
  avoid an extra numpy conversion; callers holding arrays should call the
  array variant directly to skip the encode/decode round-trip.

Both functions return a :class:`PageCharacteristics` dataclass whose fields
use plain string values so the result is JSON-serialisable without any enum
dependency.

Tuning constants mirror the values used by the original pdomain-prep-for-pgdp
heuristic; they are intentionally kept in sync so both implementations remain
equivalent.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import cast

import cv2
import numpy as np
import numpy.typing as npt

logger = logging.getLogger(__name__)

ImageArray = npt.NDArray[np.uint8]

# Tuning constants — must stay in sync with pdomain-prep-for-pgdp's auto_detect.py.
_BLANK_MEAN_LUMA_THRESHOLD = 245.0
_COLOR_SATURATION_FRACTION = 0.05
_COLOR_SATURATION_LEVEL = 30
_NARROW_CONTENT_FRACTION = 0.5
_CONTENT_DARKNESS_THRESHOLD = 200


@dataclass
class PageCharacteristics:
    """Result of heuristic page-attribute detection.

    Fields use plain strings so no enum dependency is imposed on consumers.

    ``suggested_type`` values: ``"blank"``, ``"plate_p"``, ``"normal"``.
    ``suggested_alignment`` values: ``"default"``, ``"center"``.
    ``confidence`` is in ``[0.0, 1.0]``; ``0.0`` means no confident signal.
    """

    suggested_type: str
    suggested_alignment: str
    confidence: float = field(default=0.0)


def detect_page_attributes_from_array(img: ImageArray) -> PageCharacteristics:
    """Heuristic page-attribute detection from a BGR uint8 ndarray.

    This is the single implementation; :func:`detect_page_attributes` decodes
    bytes and calls this.  Callers in pipeline stages that already hold a
    decoded ndarray should call this directly to avoid an extra encode/decode
    round-trip.

    Args:
        img: BGR ``uint8`` ndarray (H, W, 3).  Greyscale 2-D arrays are also
            accepted and treated as if all channels are equal.

    Returns:
        A :class:`PageCharacteristics` with heuristic suggestions.
    """
    if img.ndim == 2:
        # Treat greyscale as BGR (expand to 3 channels) so downstream logic
        # is uniform.  A true greyscale page has no colour content by definition.
        img = cast("ImageArray", cv2.cvtColor(img, cv2.COLOR_GRAY2BGR))

    # ── Blank detection ───────────────────────────────────────────────────────
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean_luma = float(gray.mean())
    if mean_luma >= _BLANK_MEAN_LUMA_THRESHOLD:
        return PageCharacteristics(
            suggested_type="blank",
            suggested_alignment="default",
            confidence=min(1.0, (mean_luma - _BLANK_MEAN_LUMA_THRESHOLD) / 10.0 + 0.6),
        )

    # ── Colour detection ──────────────────────────────────────────────────────
    b, g, r = cv2.split(img)
    chmax = np.maximum(np.maximum(b, g), r).astype(np.int16)
    chmin = np.minimum(np.minimum(b, g), r).astype(np.int16)
    saturated = (chmax - chmin) > _COLOR_SATURATION_LEVEL
    color_fraction = float(saturated.mean())
    if color_fraction > _COLOR_SATURATION_FRACTION:
        return PageCharacteristics(
            suggested_type="plate_p",
            suggested_alignment="default",
            confidence=min(1.0, color_fraction / 0.2 + 0.4),
        )

    # ── Alignment heuristic ───────────────────────────────────────────────────
    _h, w = gray.shape
    content_mask = gray < _CONTENT_DARKNESS_THRESHOLD
    if not content_mask.any():
        return PageCharacteristics(
            suggested_type="normal",
            suggested_alignment="default",
        )
    cols_with_content = content_mask.any(axis=0)
    xs = np.where(cols_with_content)[0]
    content_width = int(xs.max() - xs.min() + 1)
    if content_width / w < _NARROW_CONTENT_FRACTION:
        return PageCharacteristics(
            suggested_type="normal",
            suggested_alignment="center",
            confidence=1.0 - (content_width / w),
        )

    return PageCharacteristics(
        suggested_type="normal",
        suggested_alignment="default",
    )


def detect_page_attributes(image_bytes: bytes) -> PageCharacteristics:
    """Heuristic page-attribute detection from encoded image bytes.

    Decodes ``image_bytes`` with cv2, then delegates to
    :func:`detect_page_attributes_from_array`.  If the bytes cannot be decoded
    (empty, corrupt, unsupported format) the function returns a safe default
    ``"normal"`` / ``"default"`` result rather than raising.

    Args:
        image_bytes: Any image format cv2 can decode (PNG, JPEG, TIFF, …).

    Returns:
        A :class:`PageCharacteristics` with heuristic suggestions.
    """
    if not image_bytes:
        return PageCharacteristics(
            suggested_type="normal", suggested_alignment="default"
        )

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    decoded = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if decoded is None:
        return PageCharacteristics(
            suggested_type="normal", suggested_alignment="default"
        )

    return detect_page_attributes_from_array(cast("ImageArray", decoded))
