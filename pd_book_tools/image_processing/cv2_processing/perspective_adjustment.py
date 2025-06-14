# Configure logging
import logging
import math

import numpy as np

from .edge_finding import find_edges
from .rotate import rotate_image

logger = logging.getLogger(__name__)


def auto_deskew(img, pct=0.30):
    logger.debug("auto deskewing")

    img_h, img_w = img.shape[:2]

    minX, maxX, minY, maxY = find_edges(
        img=img,
        fuzzy_pct=0,
        pixel_count_columns=1,
        pixel_count_rows=1,
    )

    h_percent = int((maxY - minY) * pct)

    logger.debug("h % = {}".format(h_percent))

    w_ten_percent = int((maxY - minY) * 0.10)

    if w_ten_percent == 0 or h_percent == 0:
        logger.debug("Not Deskewing, width/height pct is 0")
        return img

    # Find Top Left first Column pixel, starting at top row and going down by 10%
    X1 = 0
    X2 = img_w - 1
    Y1 = 0
    Y2 = min(maxY, (minY + h_percent))
    top_of_img: np.ndarray = img[Y1:Y2, X1:X2]
    logger.debug("Top of Img: {}:{},{}:{}".format(X1, X2, Y1, Y2))
    columns: np.ndarray = np.sum(top_of_img, axis=0)

    top_left_column = 0
    for idx, _ in enumerate(columns):
        sum = np.sum(columns[idx])
        if sum > 0:
            top_left_column = idx
            break

    logger.debug("Top Left Col = {}".format(top_left_column))

    # Find Bottom Left first Column pixel, starting at bottom row and going up by 10%
    X1 = 0
    X2 = img_w - 1
    Y1 = min(maxY, (maxY - h_percent))
    Y2 = maxY
    bottom_of_img: np.ndarray = img[Y1:Y2, X1:X2]
    logger.debug("Bottom of Img: {}:{},{}:{}".format(X1, X2, Y1, Y2))

    columns2: np.ndarray = np.sum(bottom_of_img, axis=0)

    bottom_left_column = 0
    for idx2, _ in enumerate(columns2):
        sum = np.sum(columns2[idx2])
        if sum > 0:
            bottom_left_column = idx2
            break

    logger.debug("Bottom Left Col = {}".format(bottom_left_column))

    # Find the angle between the two
    top_point_x_y = (top_left_column, minY)
    logger.debug("Top Point = {}".format(top_point_x_y))

    perpendicular_line_bottom_x_y = (top_left_column, maxY)
    logger.debug("B Bottom Point = {}".format(perpendicular_line_bottom_x_y))

    bottom_left_bottom_x_y = (bottom_left_column, maxY)
    logger.debug("C Bottom Point = {}".format(bottom_left_bottom_x_y))

    # Right Triangle formulas. a^2 + b^2 = c^2, angle between b and c = arccos (b / c)

    # Compute length of b and c
    dist_b = math.sqrt(
        math.pow((perpendicular_line_bottom_x_y[0] - top_point_x_y[0]), 2)
        + math.pow((perpendicular_line_bottom_x_y[1] - top_point_x_y[1]), 2)
    )
    logger.debug("Dist B = {}".format(dist_b))

    dist_c = math.sqrt(
        math.pow((bottom_left_bottom_x_y[0] - top_point_x_y[0]), 2)
        + math.pow((bottom_left_bottom_x_y[1] - top_point_x_y[1]), 2)
    )
    logger.debug("Dist C = {}".format(dist_c))

    if dist_b != dist_c:
        angle = math.acos(dist_b / dist_c) * (180 / math.pi)
        logger.debug("Angle = {}".format(angle))

        rotate = angle
        logger.debug("Dist C = {}".format(rotate))

        if bottom_left_bottom_x_y[0] > perpendicular_line_bottom_x_y[0]:
            # Rotate Clockwise
            logger.debug("Clockwise")
            new_img = rotate_image(img=img, angle=rotate, borderValue=(0, 0, 0))
            return new_img, top_of_img, bottom_of_img
        elif bottom_left_bottom_x_y[0] < perpendicular_line_bottom_x_y[0]:
            # Rotate Counter-Clockwise
            logger.debug("Counter-Clockwise")
            new_img = rotate_image(img=img, angle=(-1 * rotate), borderValue=(0, 0, 0))
            return new_img, top_of_img, bottom_of_img
        else:
            # Nothing
            logger.debug("Rotate - Do Nothing")
            return img, top_of_img, bottom_of_img
    else:
        # Nothing
        logger.debug("Rotate - Do Nothing 2")
        return img, top_of_img, bottom_of_img
