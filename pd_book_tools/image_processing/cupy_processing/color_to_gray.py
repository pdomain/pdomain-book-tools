# Configure logging
from __future__ import annotations

import logging

import numpy as np

from ._cupy_compat import cp, require_cupy

logger = logging.getLogger(__name__)


def _compute_envelopes(
    img: cp.ndarray,  # pyright: ignore[reportAttributeAccessIssue]  # CuPy stubs expose ndarray but not as a plain class annotation
    radius,
    samples,
    iterations,
    y_range,
):
    height, width, _ = img.shape

    # Generate random sampling offsets once and in vectorized form
    angles = cp.random.uniform(0, 2 * cp.pi, (iterations, samples, 1, 1))
    radii = cp.random.uniform(0, radius, (iterations, samples, 1, 1))
    dx = cp.round(radii * cp.cos(angles)).astype(cp.int32)
    dy = cp.round(radii * cp.sin(angles)).astype(cp.int32)

    # Create meshgrid for batch processing
    X, Y = cp.meshgrid(cp.arange(width), y_range)  # pyright: ignore[reportAssignmentType]  # cp.meshgrid returns list[ndarray]; unpacking is always 2 items for 2 inputs

    # Compute sampled coordinates in a single batch operation
    nx = cp.clip(X[None, None, :, :] + dx, 0, width - 1)
    ny = cp.clip(Y[None, None, :, :] + dy, 0, height - 1)

    # Fetch sampled pixels in parallel using advanced indexing
    sampled_pixels = img[
        ny, nx, :3
    ]  # Shape: (iterations, samples, batch_size, width, 3)

    # Compute min/max envelopes in a single operation
    min_val = cp.min(sampled_pixels, axis=(0, 1))
    max_val = cp.max(sampled_pixels, axis=(0, 1))

    return min_val, max_val, img[y_range, :, :3]


_RGBA_NOTICE_LOGGED = False


def cupy_color_to_gray(
    img: cp.ndarray,  # pyright: ignore[reportAttributeAccessIssue]  # CuPy stubs expose ndarray but not as a plain class annotation
    radius=300,
    samples=4,
    iterations=10,
    enhance_shadows=False,
    batch_size=100,
) -> cp.ndarray:  # pyright: ignore[reportAttributeAccessIssue]  # CuPy stubs
    # Validate input shape at the public boundary so callers see a clear
    # error here instead of a confusing `ValueError: not enough values to
    # unpack` deep inside `_compute_envelopes`. Also catch silent alpha
    # drop on 4-channel input by handling it explicitly with a one-time
    # log notice (mirrors cv2.cvtColor(..., COLOR_BGRA2GRAY) policy of
    # ignoring alpha rather than alpha-blending). (M-18)
    if img.ndim != 3:
        raise ValueError(
            "cupy_color_to_gray expected a 3-channel BGR/RGB image with "
            f"shape (H, W, C); got ndim={img.ndim} shape={tuple(img.shape)}. "
            "2-D grayscale input is not supported — pass a 3-channel image."
        )
    channels = img.shape[2]
    if channels < 3:
        raise ValueError(
            "cupy_color_to_gray expected at least 3 channels (BGR/RGB); "
            f"got shape={tuple(img.shape)} with {channels} channel(s)."
        )
    if channels > 4:
        raise ValueError(
            "cupy_color_to_gray expected 3-channel BGR/RGB or 4-channel "
            f"BGRA/RGBA input; got shape={tuple(img.shape)} with "
            f"{channels} channels."
        )
    if channels == 4:
        global _RGBA_NOTICE_LOGGED  # noqa: PLW0603  # once-per-process notice flag
        if not _RGBA_NOTICE_LOGGED:
            logger.info(
                "cupy_color_to_gray received 4-channel input; dropping alpha "
                "channel (matches cv2 COLOR_BGRA2GRAY semantics). This "
                "notice is logged once per process."
            )
            _RGBA_NOTICE_LOGGED = True  # pyright: ignore[reportConstantRedefinition]  # once-per-process flag; uppercase but not a true constant
        img = img[..., :3]

    # Shape validation above is backend-agnostic. Only require CuPy here,
    # past the boundary where actual GPU operations begin — so wrappers like
    # `np_uint8_color_to_gray` can perform their own pre-checks before
    # the GPU dependency kicks in.
    require_cupy()

    height, width, _ = img.shape

    dst = cp.zeros((height, width), dtype=cp.float32)

    # Process in batches to reduce memory usage
    for y_start in range(0, height, batch_size):
        y_end = min(y_start + batch_size, height)
        y_range = cp.arange(y_start, y_end)

        min_val, max_val, pixels = _compute_envelopes(
            img, radius, samples, iterations, y_range
        )

        if enhance_shadows:
            numerator = cp.sum((pixels - min_val) ** 2, axis=2)
            denominator = cp.sum((pixels - max_val) ** 2, axis=2)
        else:
            numerator = cp.sum(pixels**2, axis=2)
            denominator = cp.sum((pixels - max_val) ** 2, axis=2)

        numerator = cp.sqrt(numerator)
        denominator = cp.sqrt(denominator) + numerator
        dst[y_range, :] = cp.where(denominator > 0.000, numerator / denominator, 0.5)

    return dst


def np_uint8_color_to_gray(
    img: np.ndarray,
    radius=300,
    samples=4,
    iterations=10,
    enhance_shadows=False,
    batch_size=100,
):
    # The function name documents the contract: input must be uint8 in [0, 255].
    # Accepting float input here would silently divide already-normalized [0, 1]
    # data by 255 and collapse it to [0, 0.004] — a near-black output with no
    # warning. Reject any other dtype explicitly so callers see the contract
    # violation instead of a silent black image. (M-17)
    if img.dtype != np.uint8:
        raise TypeError(
            "np_uint8_color_to_gray requires a uint8 image in [0, 255]; "
            f"got dtype={img.dtype}. If your input is already float in [0, 1], "
            "call cupy_color_to_gray directly with a cupy array instead."
        )

    # The dtype gate above is intentionally placed BEFORE the CuPy requirement
    # so callers see the precise contract violation (TypeError) on CPU-only
    # installs too, rather than a less specific ImportError that hides the
    # real problem.
    require_cupy()

    img_float = img.astype(np.float32) / 255.0

    # Move source image to GPU
    src: cp.ndarray = cp.asarray(img_float)  # pyright: ignore[reportAttributeAccessIssue]  # CuPy stubs

    cupy_result = cupy_color_to_gray(
        img=src,
        radius=radius,
        samples=samples,
        iterations=iterations,
        enhance_shadows=enhance_shadows,
        batch_size=batch_size,
    )

    np_result: np.ndarray = cupy_result.get()  # Move result back to CPU

    uint8_image: np.ndarray = (
        (np_result * 255).clip(0, 255).astype(np.uint8)
    )  # Ensure proper range

    return uint8_image
