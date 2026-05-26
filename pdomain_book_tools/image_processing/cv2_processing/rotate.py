# Configure logging
import logging
from typing import cast

import cv2
import numpy as np
import numpy.typing as npt

logger = logging.getLogger(__name__)

ImageArray = npt.NDArray[np.uint8]


def rotate_image(
    img: ImageArray,
    angle: float,
    borderValue: cv2.typing.Scalar = (0.0, 0.0, 0.0),
) -> ImageArray:
    h, w = cast("tuple[int, int]", img.shape[:2])
    center = (w / 2.0, h / 2.0)

    matrix = cast(
        "npt.NDArray[np.float64]", cv2.getRotationMatrix2D(center, -angle, 1.0)
    )
    abs_cos = abs(cast("float", matrix[0, 0]))
    abs_sin = abs(cast("float", matrix[0, 1]))

    # Compute new bounding dimensions
    new_w = int(h * abs_sin + w * abs_cos)
    new_h = int(h * abs_cos + w * abs_sin)

    # Adjust transformation matrix
    matrix[0, 2] += (new_w - w) / 2.0
    matrix[1, 2] += (new_h - h) / 2.0

    return cast(
        "ImageArray",
        cv2.warpAffine(img, matrix, (new_w, new_h), borderValue=borderValue),
    )
