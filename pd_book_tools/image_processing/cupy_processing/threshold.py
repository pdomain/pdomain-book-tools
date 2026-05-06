# Configure logging
import logging

import cupy as cp
import numpy as np

logger = logging.getLogger(__name__)


def otsu_binary_thresh(img_cp_float: cp.ndarray) -> cp.ndarray:
    """
    Performs Otsu's thresholding on a CuPy GPU array.

    The return contract matches the cv2 backend's
    `otsu_binary_thresh` (which wraps `cv2.threshold(..., THRESH_BINARY +
    THRESH_OTSU)`): a `cp.uint8` array with values in `{0, 255}`. This makes
    the cupy and cv2 implementations drop-in interchangeable for downstream
    consumers like `invert_image` that assume the uint8 0/255 convention
    (review issue H-16).

    Args:
        img_cp_float (cp.ndarray): Input image (CuPy array). Supports float32 and uint8.

    Returns:
        cp.ndarray: Thresholded binary image, dtype `cp.uint8`, values in `{0, 255}`.
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

    # Degenerate case: a uniform-valued image has no meaningful Otsu split.
    # Older cupy versions raised `ValueError: max must be larger than min` from
    # `cp.histogram(..., range=(min, max))` here; current cupy silently
    # produces a bogus histogram (single nonzero bin at index 128 over an
    # arbitrary edge span), which downstream collapses to `argmax` of an
    # all-zero between-class variance returning 0 — yielding a meaningless
    # threshold and a misclassified output. Match skimage/cv2 semantics:
    # treat the uniform value itself as the threshold so the strict-`>`
    # binarization produces an all-zero mask without crashing (review H-15).
    if min_val == max_val:
        return cp.zeros_like(img_cp_float, dtype=cp.uint8)

    hist, bin_edges = cp.histogram(img_cp_float, bins=256, range=(min_val, max_val))
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2  # type: ignore # Midpoints of bins

    # Compute cumulative sums and means.
    #
    # weight2 must be the suffix sum sum(hist[i:]) so that the standard
    # between-class-variance formulation (weight1[:-1], weight2[1:]) pairs
    # class 1 = hist[:k+1] with class 2 = hist[k+1:] without dropping any bin.
    # An earlier version used `weight2 = weight1[-1] - weight1`, i.e. the
    # *exclusive* suffix sum sum(hist[i+1:]); paired with `weight2[1:]` that
    # silently excluded bin k+1 from both classes and biased the threshold
    # high on non-trivial bimodal images (review issue H-14).
    weight1 = cp.cumsum(hist)
    weight2 = cp.flip(cp.cumsum(cp.flip(hist)))
    mean1 = cp.cumsum(hist * bin_centers) / (weight1 + 1e-7)
    mean2 = (cp.cumsum(hist[::-1] * bin_centers[::-1]) / (weight2[::-1] + 1e-7))[::-1]

    # Compute between-class variance (matches skimage.filters.threshold_otsu).
    between_class_variance = weight1[:-1] * weight2[1:] * (mean1[:-1] - mean2[1:]) ** 2

    # Get the Otsu threshold (index with max variance)
    otsu_threshold = bin_centers[:-1][cp.argmax(between_class_variance)]

    # Apply binary thresholding. Return uint8 0/255 to match the cv2 backend's
    # `otsu_binary_thresh` contract so downstream code can switch backends
    # without dtype/range surprises (review issue H-16).
    binary_img_cp_uint8 = cp.where(img_cp_float > otsu_threshold, 255, 0).astype(
        cp.uint8
    )

    return binary_img_cp_uint8


def binary_thresh_gpu(img_cp: cp.ndarray, level: int = 127) -> cp.ndarray:
    """
    Fixed-level binary threshold on a GPU array.

    Pixels > level become 255; all others become 0.
    Equivalent to cv2.threshold(img, level, 255, cv2.THRESH_BINARY).

    img_cp: 2-D uint8 CuPy array.
    Returns uint8 CuPy array.
    """
    return (img_cp > level).astype(cp.uint8) * 255


def np_uint8_binary_thresh(img: np.ndarray, level: int = 127) -> np.ndarray:
    """Transfers img to GPU, applies fixed-level threshold, returns CPU uint8 array."""
    return cp.asnumpy(binary_thresh_gpu(cp.asarray(img), level))


def np_uint8_float_binary_thresh(
    img: np.ndarray,
):
    img_float = img.astype(np.float32) / 255.0
    src: cp.ndarray = cp.asarray(img_float)

    cupy_result = otsu_binary_thresh(img_cp_float=src)

    # `otsu_binary_thresh` already returns uint8 0/255 (H-16); just move to CPU.
    uint8_image: np.ndarray = cupy_result.get()

    return uint8_image
