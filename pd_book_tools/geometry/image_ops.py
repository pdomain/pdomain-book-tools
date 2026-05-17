"""Image-processing operations on :class:`BoundingBox`.

These functions are the canonical implementation of the bbox image
ops that historically lived as methods on :class:`BoundingBox`
(``refine``, ``crop_top``, ``crop_bottom``). The methods on
``BoundingBox`` now thin-wrap these free functions and remain in
place for backward compatibility (R-01/R-03 deprecation-overlap
strategy).

Structurally this is the cv2-using sibling of
:mod:`pd_book_tools.geometry.bounding_box`. New code should call the
free functions here directly; old code calling
``bbox.refine(image, ...)`` etc. continues to work.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

import cv2
from cv2 import (
    COLOR_BGR2GRAY,
    THRESH_BINARY,
    THRESH_OTSU,
    cvtColor,
    findNonZero,
    threshold,
)

from pd_book_tools.geometry.bounding_box import BoundingBox

if TYPE_CHECKING:
    from numpy import ndarray

__all__ = [
    "crop_bottom_bbox",
    "crop_top_bbox",
    "refine_bbox",
]


# ---------------------------------------------------------------------------
# Internal helpers (image -> threshold -> tight bbox)
# ---------------------------------------------------------------------------


def _extract_roi(
    bbox: BoundingBox, image: ndarray
) -> tuple[ndarray, float, float, float, float, int, int, bool]:
    """Return ``(roi, x1, y1, x2, y2, img_w, img_h, original_is_normalized)``.

    Scales ``bbox`` to pixel coordinates if it was normalized.
    """
    img_h, img_w = image.shape[:2]
    original_is_normalized = bool(bbox.is_normalized)
    box = bbox.scale(img_w, img_h) if original_is_normalized else bbox
    x1, y1, x2, y2 = box.to_ltrb()
    roi = image[y1:y2, x1:x2]
    return roi, x1, y1, x2, y2, img_w, img_h, original_is_normalized


def _threshold_inverted(roi: ndarray) -> tuple[ndarray, ndarray]:
    """Convert ROI to grayscale (if needed), invert, OTSU threshold.

    Returns ``(thresh, grayscale_roi)``.
    """
    roi_gray = cvtColor(roi, COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi
    inverted = cv2.bitwise_not(roi_gray)
    _, thresh = threshold(inverted, 0, 255, THRESH_BINARY + THRESH_OTSU)
    return thresh, roi_gray


def _tight_bbox_from_thresh(thresh: ndarray) -> tuple[int, int, int, int] | None:
    non_zero = findNonZero(thresh)
    if non_zero is None:
        return None
    x, y, w, h = cv2.boundingRect(non_zero)
    return x, y, w, h


def _connected_content_bbox_from_image_thresh(
    thresh: ndarray,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
) -> tuple[float, float, float, float] | None:
    """Return bbox for connected components that intersect the original ROI.

    Coordinates are in image pixel space and returned as
    ``(x_min, y_min, x_max, y_max)``.
    """
    if x1 >= x2 or y1 >= y2:
        return None

    components = cv2.connectedComponentsWithStats(thresh, connectivity=8)
    num_labels, labels, stats, _ = components
    if num_labels <= 1:
        return None

    roi_labels = labels[y1:y2, x1:x2]
    touching_labels = {int(label) for label in roi_labels.ravel() if int(label) != 0}
    if not touching_labels:
        return None

    x_min = float("inf")
    y_min = float("inf")
    x_max = float("-inf")
    y_max = float("-inf")

    for label in touching_labels:
        comp_x = float(stats[label, cv2.CC_STAT_LEFT])
        comp_y = float(stats[label, cv2.CC_STAT_TOP])
        comp_w = float(stats[label, cv2.CC_STAT_WIDTH])
        comp_h = float(stats[label, cv2.CC_STAT_HEIGHT])
        x_min = min(x_min, comp_x)
        y_min = min(y_min, comp_y)
        x_max = max(x_max, comp_x + comp_w)
        y_max = max(y_max, comp_y + comp_h)

    return x_min, y_min, x_max, y_max


def _finalize_pixel_bbox(
    x_min: float,
    y_min: float,
    x_max: float,
    y_max: float,
    img_w: int,
    img_h: int,
    original_is_normalized: bool,
) -> BoundingBox:
    out = BoundingBox.from_ltrb(x_min, y_min, x_max, y_max)
    if original_is_normalized:
        out = BoundingBox.from_ltrb(
            round(x_min),
            round(y_min),
            round(x_max),
            round(y_max),
        ).normalize(img_w, img_h)
    return out


# ---------------------------------------------------------------------------
# Public free functions
# ---------------------------------------------------------------------------


def refine_bbox(
    bbox: BoundingBox,
    image: ndarray,
    padding_px: int = 0,
    expand_beyond_original: bool = False,
) -> BoundingBox:
    """Tighten ``bbox`` around its image content via OTSU thresholding.

    Returns a new :class:`BoundingBox`. The input is not mutated.
    Coordinate space (pixel vs normalized) is preserved.
    """
    roi, x1, y1, x2, y2, img_w, img_h, original_is_normalized = _extract_roi(
        bbox, image
    )
    orig_x1, orig_y1, orig_x2, orig_y2 = x1, y1, x2, y2
    if expand_beyond_original:
        thresh_full, _ = _threshold_inverted(image)
        connected_bbox = _connected_content_bbox_from_image_thresh(
            thresh_full, x1, y1, x2, y2
        )
        if connected_bbox is None:
            return replace(bbox)
        x_min, y_min, x_max, y_max = connected_bbox
    else:
        thresh, _ = _threshold_inverted(roi)
        tight = _tight_bbox_from_thresh(thresh)
        if tight is None:
            return replace(bbox)
        x, y, w, h = tight
        x_min = x1 + x
        y_min = y1 + y
        x_max = x1 + x + w
        y_max = y1 + y + h
    tight_width = x_max - x_min
    tight_height = y_max - y_min
    if expand_beyond_original:
        slack_w = max(0.0, (orig_x2 - orig_x1) - tight_width)
        slack_h = max(0.0, (orig_y2 - orig_y1) - tight_height)
        extra_w = padding_px + slack_w / 2.0
        extra_h = padding_px + slack_h / 2.0
        x_min = max(0.0, x_min - extra_w)
        y_min = max(0.0, y_min - extra_h)
        x_max = min(float(img_w), x_max + extra_w)
        y_max = min(float(img_h), y_max + extra_h)
    else:
        x_min = max(orig_x1, 0.0, x_min - padding_px)
        y_min = max(orig_y1, 0.0, y_min - padding_px)
        x_max = min(orig_x2, float(img_w), x_max + padding_px)
        y_max = min(orig_y2, float(img_h), y_max + padding_px)
    return _finalize_pixel_bbox(
        x_min, y_min, x_max, y_max, img_w, img_h, original_is_normalized
    )


def _vertical_crop(bbox: BoundingBox, image: ndarray, keep: str) -> BoundingBox:
    """Shared implementation for :func:`crop_top_bbox` (``keep='top'``) and
    :func:`crop_bottom_bbox` (``keep='bottom'``).
    """
    roi, x1, y1, x2, y2, img_w, img_h, original_is_normalized = _extract_roi(
        bbox, image
    )
    thresh, _ = _threshold_inverted(roi)
    non_zero = findNonZero(thresh)
    if non_zero is None:
        return replace(bbox)
    coords = non_zero.reshape(-1, 2)
    roi_h, _ = thresh.shape
    center_y = roi_h // 2
    if keep == "top":
        coords = coords[coords[:, 1] <= center_y]
        if coords.size == 0:
            return replace(bbox)
        for y in range(center_y - 1, -1, -1):
            current = set(coords[coords[:, 1] == y][:, 0])
            prev = set(coords[coords[:, 1] == y + 1][:, 0])
            if not prev and current:
                continue
            if current & prev:
                continue
            y1 = y1 + y
            break
    else:  # keep == bottom
        coords = coords[coords[:, 1] >= center_y]
        if coords.size == 0:
            return replace(bbox)
        roi_h = thresh.shape[0]
        for y in range(center_y + 1, roi_h):
            current = set(coords[coords[:, 1] == y][:, 0])
            prev = set(coords[coords[:, 1] == y - 1][:, 0])
            if not prev and current:
                continue
            if current & prev:
                continue
            y2 = y1 + y
            break
    return _finalize_pixel_bbox(x1, y1, x2, y2, img_w, img_h, original_is_normalized)


def crop_top_bbox(bbox: BoundingBox, image: ndarray) -> BoundingBox:
    """Return a new bbox cropped to the top half of its image content."""
    return _vertical_crop(bbox, image, keep="top")


def crop_bottom_bbox(bbox: BoundingBox, image: ndarray) -> BoundingBox:
    """Return a new bbox cropped to the bottom half of its image content."""
    return _vertical_crop(bbox, image, keep="bottom")
