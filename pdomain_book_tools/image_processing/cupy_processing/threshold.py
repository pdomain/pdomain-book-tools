# pyright: reportAny=false
# pyright: reportImplicitStringConcatenation=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# Configure logging
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

import numpy as np

from ._cupy_compat import cp, require_cupy

if TYPE_CHECKING:
    import numpy.typing as npt

    CuPyArray = npt.NDArray[np.generic]
else:
    CuPyArray = object

logger = logging.getLogger(__name__)


def otsu_binary_thresh(img_cp_float: CuPyArray) -> CuPyArray:
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
    require_cupy()
    # Convert to grayscale if it's a color image
    if img_cp_float.ndim == 3 and img_cp_float.shape[2] == 3:
        img_cp_float = (
            0.2989 * img_cp_float[:, :, 2]  # pyright: ignore[reportOperatorIssue]  # CuPy arithmetic on NDArray-like alias
            + 0.5870 * img_cp_float[:, :, 1]  # pyright: ignore[reportOperatorIssue]  # CuPy arithmetic on NDArray-like alias
            + 0.1140 * img_cp_float[:, :, 0]  # pyright: ignore[reportOperatorIssue]  # CuPy arithmetic on NDArray-like alias
        )

    # Ensure input is float32 for precision
    img_cp_float = cast("CuPyArray", img_cp_float.astype(cp.float32))

    # Compute histogram (auto-detect range)
    min_val, max_val = cp.min(img_cp_float), cp.max(img_cp_float)

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
        return cast("CuPyArray", cp.zeros_like(img_cp_float, dtype=cp.uint8))

    hist, bin_edges = cp.histogram(img_cp_float, bins=256, range=(min_val, max_val))
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2  # Midpoints of bins

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
    return cast(
        "CuPyArray",
        cp.where(img_cp_float > otsu_threshold, 255, 0).astype(cp.uint8),  # pyright: ignore[reportOperatorIssue]  # CuPy comparison on NDArray-like alias
    )


def binary_thresh_gpu(img_cp: CuPyArray, level: int = 127) -> CuPyArray:
    """
    Fixed-level binary threshold on a GPU array.

    Pixels > level become 255; all others become 0.
    Equivalent to cv2.threshold(img, level, 255, cv2.THRESH_BINARY).

    img_cp: 2-D uint8 CuPy array.
    Returns uint8 CuPy array.
    """
    require_cupy()
    return cast(
        "CuPyArray",
        (img_cp > level).astype(cp.uint8) * 255,  # pyright: ignore[reportOperatorIssue]  # CuPy comparison on NDArray-like alias
    )


def np_uint8_binary_thresh(img: np.ndarray, level: int = 127) -> np.ndarray:
    """Transfers img to GPU, applies fixed-level threshold, returns CPU uint8 array."""
    require_cupy()
    return cp.asnumpy(binary_thresh_gpu(cast("CuPyArray", cp.asarray(img)), level))


def np_uint8_otsu_binary_thresh(
    img: np.ndarray,
) -> np.ndarray:
    """Transfers img to GPU, applies Otsu binary threshold, returns CPU uint8 array.

    Internally promotes the uint8 input to float32 for Otsu's variance
    minimization, but the input contract and output contract are both
    uint8 — matching the rest of the ``np_uint8_*`` wrapper family.
    """
    require_cupy()
    img_float = img.astype(np.float32) / 255.0
    src = cast("CuPyArray", cp.asarray(img_float))

    cupy_result = otsu_binary_thresh(img_cp_float=src)

    # `otsu_binary_thresh` already returns uint8 0/255 (H-16); just move to CPU.
    return cp.asnumpy(cupy_result)


def np_uint8_float_binary_thresh(img: np.ndarray) -> np.ndarray:
    """Deprecated alias for :func:`np_uint8_otsu_binary_thresh` (R-30).

    The ``_float_`` infix was misleading — the function takes/returns
    uint8 like every other ``np_uint8_*`` wrapper in this package; the
    float intermediate is an internal implementation detail. Use
    ``np_uint8_otsu_binary_thresh`` directly.
    """
    import warnings as _w

    _w.warn(
        "np_uint8_float_binary_thresh is deprecated; use "
        "np_uint8_otsu_binary_thresh "
        "(the '_float_' infix was misleading - the function takes and returns "
        "uint8). Will be removed in a future major.",
        DeprecationWarning,
        stacklevel=2,
    )
    return np_uint8_otsu_binary_thresh(img)


def adaptive_binary_thresh(
    img: CuPyArray,
    *,
    block_size: int = 31,
    c: int = 10,
    mode: str = "gaussian",
) -> CuPyArray:
    """Adaptive (local) binarisation on a GPU array.

    Computes a local mean over each pixel's ``block_size x block_size``
    neighbourhood (using a Gaussian-weighted kernel when ``mode="gaussian"``,
    or a uniform mean when ``mode="mean"``), then thresholds
    ``img > (local_mean - c)``.  Pixels above the threshold become 255
    (background); pixels at or below become 0 (text).

    All computation stays on-device — no CPU/NumPy round-trips.

    Args:
        img: 2-D uint8 CuPy array (grayscale image, on GPU).
        block_size: Side length of the local neighbourhood (must be odd >= 3).
        c: Constant subtracted from the local mean. Increase to bias more
            pixels towards 0 (darker output).
        mode: ``"gaussian"`` (default) — Gaussian-weighted local mean;
            ``"mean"`` — uniform local mean.

    Returns:
        cp.ndarray: uint8 CuPy array with values in {0, 255}, same shape as *img*.
    """
    require_cupy()
    import cupyx.scipy.ndimage as cpnd  # cupyx is part of the cupy GPU extra

    img_f = cast("CuPyArray", img.astype(cp.float32))

    if mode == "gaussian":
        # sigma chosen to match OpenCV's formula: sigma = 0.3 * ((block_size-1)/2 - 1) + 0.8
        sigma = 0.3 * ((block_size - 1) / 2 - 1) + 0.8
        local_mean = cast(
            "CuPyArray",
            cpnd.gaussian_filter(img_f, sigma=sigma),
        )
    elif mode == "mean":
        local_mean = cast(
            "CuPyArray",
            cpnd.uniform_filter(img_f, size=block_size),
        )
    else:
        raise ValueError(
            f"Unknown adaptive mode {mode!r}; valid modes are: 'gaussian', 'mean'."
        )

    threshold = local_mean - c  # pyright: ignore[reportOperatorIssue]
    return cast(
        "CuPyArray",
        cp.where(img_f > threshold, 255, 0).astype(cp.uint8),
    )


def sauvola_binary_thresh(
    img: CuPyArray,
    *,
    window_size: int = 25,
    k: float = 0.2,
    r: int = 128,
) -> CuPyArray:
    """Sauvola local binarisation on a GPU array.

    The Sauvola threshold at each pixel is::

        T = m * (1 + k * (s / r - 1))

    where *m* is the local mean and *s* is the local standard deviation over a
    ``window_size x window_size`` neighbourhood.  Pixels with value ``> T``
    become 255 (background); pixels ``<= T`` become 0 (text).

    All computation stays on-device — no CPU/NumPy round-trips.  Local
    statistics are computed via ``cupyx.scipy.ndimage.uniform_filter``:
    variance = E[x^2] - E[x]^2.

    Args:
        img: 2-D uint8 CuPy array (grayscale image, on GPU).
        window_size: Side length of the local neighbourhood (should be odd).
        k: Sauvola sensitivity parameter (typically 0.2).
        r: Dynamic range of the standard deviation (typically 128 for uint8
            images; controls the weight of the local contrast term).

    Returns:
        cp.ndarray: uint8 CuPy array with values in {0, 255}, same shape as *img*.
    """
    require_cupy()
    import cupyx.scipy.ndimage as cpnd  # cupyx is part of the cupy GPU extra

    img_f = cast("CuPyArray", img.astype(cp.float64))

    # Local mean: E[x]
    local_mean = cast("CuPyArray", cpnd.uniform_filter(img_f, size=window_size))
    # Local mean of squares: E[x²]
    local_mean_sq = cast("CuPyArray", cpnd.uniform_filter(img_f**2, size=window_size))  # pyright: ignore[reportOperatorIssue]
    # Variance = E[x²] - E[x]² (clamp to 0 to avoid negative-float artifacts)
    local_var = cp.maximum(local_mean_sq - local_mean**2, 0.0)  # pyright: ignore[reportOperatorIssue]
    local_std = cp.sqrt(local_var)

    threshold = local_mean * (1.0 + k * (local_std / r - 1.0))  # pyright: ignore[reportOperatorIssue]
    return cast(
        "CuPyArray",
        cp.where(img_f > threshold, 255, 0).astype(cp.uint8),
    )


def niblack_binary_thresh(
    img: CuPyArray,
    *,
    window_size: int = 25,
    k: float = -0.2,
) -> CuPyArray:
    """Niblack local binarisation on a GPU array.

    The Niblack threshold at each pixel is::

        T = m + k * s

    where *m* is the local mean and *s* is the local standard deviation over a
    ``window_size x window_size`` neighbourhood.  Pixels with value ``> T``
    become 255 (background); pixels ``<= T`` become 0 (text).

    All computation stays on-device — no CPU/NumPy round-trips.  Local
    statistics are computed via ``cupyx.scipy.ndimage.uniform_filter``:
    variance = E[x^2] - E[x]^2.

    Args:
        img: 2-D uint8 CuPy array (grayscale image, on GPU).
        window_size: Side length of the local neighbourhood (should be odd).
        k: Niblack sensitivity parameter (typically -0.2).

    Returns:
        cp.ndarray: uint8 CuPy array with values in {0, 255}, same shape as *img*.
    """
    require_cupy()
    import cupyx.scipy.ndimage as cpnd  # cupyx is part of the cupy GPU extra

    img_f = cast("CuPyArray", img.astype(cp.float64))

    local_mean = cast("CuPyArray", cpnd.uniform_filter(img_f, size=window_size))
    local_mean_sq = cast("CuPyArray", cpnd.uniform_filter(img_f**2, size=window_size))  # pyright: ignore[reportOperatorIssue]
    local_var = cp.maximum(local_mean_sq - local_mean**2, 0.0)  # pyright: ignore[reportOperatorIssue]
    local_std = cp.sqrt(local_var)

    threshold = local_mean + k * local_std  # pyright: ignore[reportOperatorIssue]
    return cast(
        "CuPyArray",
        cp.where(img_f > threshold, 255, 0).astype(cp.uint8),
    )


def binarize(img: CuPyArray, *, method: str = "otsu", **params: Any) -> CuPyArray:
    """Binarise a grayscale GPU image via the named method, dispatching to its helper.

    Mirrors the cv2_processing ``binarize`` dispatcher but operates entirely
    on-device — all operations stay on the GPU; no host (CPU/NumPy) transfers.

    Args:
        img: 2-D CuPy array (grayscale image, on GPU).
        method: One of ``"otsu"`` (default), ``"adaptive"``, ``"sauvola"``,
            ``"niblack"``.
        **params: Additional keyword arguments forwarded to the selected method.

    Returns:
        cp.ndarray: uint8 CuPy array with values in {0, 255}, same shape as *img*.
    """
    require_cupy()
    if method == "otsu":
        return otsu_binary_thresh(img)
    if method == "adaptive":
        return adaptive_binary_thresh(img, **params)
    if method == "sauvola":
        return sauvola_binary_thresh(img, **params)
    if method == "niblack":
        return niblack_binary_thresh(img, **params)
    raise ValueError(
        f"Unknown binarization method {method!r}; "
        "valid methods are: 'otsu', 'adaptive', 'sauvola', 'niblack'."
    )
