import logging
import math

import cupy as cp
import numpy as np
from cupyx.scipy.ndimage import affine_transform

logger = logging.getLogger(__name__)


def rotate_image_gpu(
    img_cp: cp.ndarray,
    angle_deg: float,
    cval: int = 0,
) -> cp.ndarray:
    """
    Rotate img_cp by angle_deg degrees (positive=CW, negative=CCW).
    Canvas expands to fit the rotated content; border fills with cval.

    Matches cv2_processing.rotate.rotate_image behaviour.
    Handles both 2-D (H, W) and 3-D (H, W, C) uint8 CuPy arrays.
    """
    if angle_deg == 0.0:
        return img_cp

    h, w = img_cp.shape[:2]
    alpha = math.radians(abs(angle_deg))
    cos_a = math.cos(alpha)
    sin_a = math.sin(alpha)

    new_h = int(h * cos_a + w * sin_a)
    new_w = int(h * sin_a + w * cos_a)

    cy, cx = h / 2.0, w / 2.0
    new_cy, new_cx = new_h / 2.0, new_w / 2.0

    # affine_transform uses inverse mapping (output → input).
    # CW rotation by alpha → inverse is CCW by alpha.
    if angle_deg > 0:
        matrix = [[cos_a, -sin_a], [sin_a, cos_a]]
        offset = [
            cy - cos_a * new_cy + sin_a * new_cx,
            cx - sin_a * new_cy - cos_a * new_cx,
        ]
    else:
        matrix = [[cos_a, sin_a], [-sin_a, cos_a]]
        offset = [
            cy - cos_a * new_cy - sin_a * new_cx,
            cx + sin_a * new_cy - cos_a * new_cx,
        ]

    if img_cp.ndim == 3:
        n_ch = img_cp.shape[2]
        matrix_3d = cp.array(
            [
                [matrix[0][0], matrix[0][1], 0],
                [matrix[1][0], matrix[1][1], 0],
                [0, 0, 1],
            ],
            dtype=cp.float64,
        )
        return affine_transform(
            img_cp,
            matrix_3d,
            offset=[offset[0], offset[1], 0],
            output_shape=(new_h, new_w, n_ch),
            order=1,
            mode="constant",
            cval=cval,
        )

    return affine_transform(
        img_cp,
        cp.array(matrix, dtype=cp.float64),
        offset=offset,
        output_shape=(new_h, new_w),
        order=1,
        mode="constant",
        cval=cval,
    )


def np_uint8_rotate_image(
    img: np.ndarray,
    angle_deg: float,
    cval: int = 0,
) -> np.ndarray:
    """Transfers img to GPU, rotates by angle_deg degrees, returns CPU uint8 array."""
    return cp.asnumpy(rotate_image_gpu(cp.asarray(img), angle_deg, cval=cval))
