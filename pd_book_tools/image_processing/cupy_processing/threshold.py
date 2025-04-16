# Configure logging
import logging

import cupy as cp
import numpy as np

logger = logging.getLogger(__name__)


def otsu_binary_thresh(img_cp_float: cp.array) -> cp.array:
    """
    Performs Otsu's thresholding on a CuPy GPU array without converting to uint8.

    Args:
        img_cp_float (cp.ndarray): Input image (CuPy array). Supports float32 and uint8.

    Returns:
        cp.ndarray: Thresholded binary image (same dtype as input).
    """
    # Convert to grayscale if it's a color image
    if img_cp_float.ndim == 3 and img_cp_float.shape[2] == 3:
        img_cp_float = (
            0.2989 * img_cp_float[:, :, 2]
            + 0.5870 * img_cp_float[:, :, 1]
            + 0.1140 * img_cp_float[:, :, 0]
        )

    # Ensure input is float32 for precision
    img_cp_float = img_cp_float.astype(cp.float32)

    # Compute histogram (auto-detect range)
    min_val, max_val = img_cp_float.min(), img_cp_float.max()
    hist, bin_edges = cp.histogram(img_cp_float, bins=256, range=(min_val, max_val))
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2  # Midpoints of bins

    # Compute cumulative sums and means
    weight1 = cp.cumsum(hist)
    weight2 = weight1[-1] - weight1
    mean1 = cp.cumsum(hist * bin_centers) / (weight1 + 1e-7)
    mean2 = (cp.cumsum(hist[::-1] * bin_centers[::-1]) / (weight2[::-1] + 1e-7))[::-1]

    # Compute between-class variance
    between_class_variance = weight1[:-1] * weight2[1:] * (mean1[:-1] - mean2[1:]) ** 2

    # Get the Otsu threshold (index with max variance)
    otsu_threshold = bin_centers[:-1][cp.argmax(between_class_variance)]

    # Apply binary thresholding
    binary_img_cp_float = cp.where(img_cp_float > otsu_threshold, 1.0, 0.0).astype(
        cp.float32
    )  # Keep float32

    return binary_img_cp_float


def np_uint8_float_binary_thresh(
    img: np.array,
):
    img_float = img.astype(np.float32) / 255.0
    src: cp.array = cp.asarray(img_float)

    cupy_result = otsu_binary_thresh(img_cp_float=src)

    np_result: np.array = cupy_result.get()  # Move result back to CPU

    uint8_image: np.array = (
        (np_result * 255).clip(0, 255).astype(np.uint8)
    )  # Ensure proper range

    return uint8_image
