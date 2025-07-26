# Configure logging
import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def rotate_image(
    img: np.ndarray, angle, borderValue: cv2.typing.Scalar = (0.0, 0.0, 0.0)
):
    h, w = img.shape[:2]
    center = (w / 2.0, h / 2.0)

    M = cv2.getRotationMatrix2D(center, -angle, 1.0)
    abs_cos, abs_sin = abs(M[0, 0]), abs(M[0, 1])

    # Compute new bounding dimensions
    new_w = int(h * abs_sin + w * abs_cos)
    new_h = int(h * abs_cos + w * abs_sin)

    # Adjust transformation matrix
    M[0, 2] += (new_w - w) / 2.0
    M[1, 2] += (new_h - h) / 2.0

    return cv2.warpAffine(img, M, (new_w, new_h), borderValue=borderValue)
