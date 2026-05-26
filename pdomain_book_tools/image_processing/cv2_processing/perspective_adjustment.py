# Configure logging
import logging
import math
from typing import cast

import numpy as np
import numpy.typing as npt

from .edge_finding import find_edges
from .rotate import rotate_image

logger = logging.getLogger(__name__)

ImageArray = npt.NDArray[np.uint8]


def auto_deskew(
    img: ImageArray, pct: float = 0.30
) -> tuple[ImageArray, ImageArray, ImageArray]:
    logger.debug("auto deskewing")

    _img_h, img_w = cast("tuple[int, int]", img.shape[:2])

    _minX, _maxX, minY, maxY = find_edges(
        img=img,
        fuzzy_pct=0,
        pixel_count_columns=1,
        pixel_count_rows=1,
    )

    h_percent = int((maxY - minY) * pct)

    logger.debug(f"h % = {h_percent}")

    w_ten_percent = int((maxY - minY) * 0.10)

    if w_ten_percent == 0 or h_percent == 0:
        logger.debug("Not Deskewing, width/height pct is 0")
        # Always return a 3-tuple to mirror cupy's auto_deskew_gpu contract
        # (image, top_slice, bottom_slice). Empty placeholders match cupy's
        # cp.empty((0, 0), dtype=img_cp.dtype) on the same early-exit path,
        # so callers do not need isinstance(out, tuple) backend dispatch.
        empty = cast("ImageArray", np.empty((0, 0), dtype=img.dtype))
        return img, empty, empty

    # Find Top Left first Column pixel, starting at top row and going down by 10%
    x1 = 0
    x2 = img_w - 1
    # Use minY (detected content top edge) rather than 0; otherwise stray
    # noise pixels above the text block corrupt the column-sum scan and
    # bias the detected skew angle. Mirrors the cupy backend.
    y1 = minY
    y2 = min(maxY, minY + h_percent)
    top_of_img: ImageArray = img[y1:y2, x1:x2]
    logger.debug(f"Top of Img: {x1}:{x2},{y1}:{y2}")
    columns = cast("npt.NDArray[np.int64]", np.sum(top_of_img, axis=0, dtype=np.int64))

    positive_top_columns = np.flatnonzero(columns > 0)
    top_left_column = (
        cast("int", positive_top_columns[0]) if positive_top_columns.size > 0 else 0
    )

    logger.debug(f"Top Left Col = {top_left_column}")

    # Find Bottom Left first Column pixel, starting at bottom row and going up by 10%
    x1 = 0
    x2 = img_w - 1
    y1 = min(maxY, maxY - h_percent)
    y2 = maxY
    bottom_of_img: ImageArray = img[y1:y2, x1:x2]
    logger.debug(f"Bottom of Img: {x1}:{x2},{y1}:{y2}")

    columns2 = cast(
        "npt.NDArray[np.int64]", np.sum(bottom_of_img, axis=0, dtype=np.int64)
    )

    positive_bottom_columns = np.flatnonzero(columns2 > 0)
    bottom_left_column = (
        cast("int", positive_bottom_columns[0])
        if positive_bottom_columns.size > 0
        else 0
    )

    logger.debug(f"Bottom Left Col = {bottom_left_column}")

    # Find the angle between the two
    top_point_x_y = (top_left_column, minY)
    logger.debug(f"Top Point = {top_point_x_y}")

    perpendicular_line_bottom_x_y = (top_left_column, maxY)
    logger.debug(f"B Bottom Point = {perpendicular_line_bottom_x_y}")

    bottom_left_bottom_x_y = (bottom_left_column, maxY)
    logger.debug(f"C Bottom Point = {bottom_left_bottom_x_y}")

    # Right Triangle formulas. a^2 + b^2 = c^2, angle between b and c = arccos (b / c)

    # Compute length of b and c
    dist_b = math.sqrt(
        math.pow((perpendicular_line_bottom_x_y[0] - top_point_x_y[0]), 2)
        + math.pow((perpendicular_line_bottom_x_y[1] - top_point_x_y[1]), 2)
    )
    logger.debug(f"Dist B = {dist_b}")

    dist_c = math.sqrt(
        math.pow((bottom_left_bottom_x_y[0] - top_point_x_y[0]), 2)
        + math.pow((bottom_left_bottom_x_y[1] - top_point_x_y[1]), 2)
    )
    logger.debug(f"Dist C = {dist_c}")

    if dist_b != dist_c:
        angle = math.acos(dist_b / dist_c) * (180 / math.pi)
        logger.debug(f"Angle = {angle}")

        rotate = angle
        logger.debug(f"Dist C = {rotate}")

        if bottom_left_bottom_x_y[0] > perpendicular_line_bottom_x_y[0]:
            # Rotate Clockwise
            logger.debug("Clockwise")
            new_img = rotate_image(img=img, angle=rotate, borderValue=(0, 0, 0))
            return new_img, top_of_img, bottom_of_img
        if bottom_left_bottom_x_y[0] < perpendicular_line_bottom_x_y[0]:
            # Rotate Counter-Clockwise
            logger.debug("Counter-Clockwise")
            new_img = rotate_image(img=img, angle=(-1 * rotate), borderValue=(0, 0, 0))
            return new_img, top_of_img, bottom_of_img
        # Nothing
        logger.debug("Rotate - Do Nothing")
        return img, top_of_img, bottom_of_img
    # Nothing
    logger.debug("Rotate - Do Nothing 2")
    return img, top_of_img, bottom_of_img
