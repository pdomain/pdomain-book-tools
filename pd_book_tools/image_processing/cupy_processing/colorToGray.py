# Configure logging
import logging

import cupy as cp
import numpy as np

logger = logging.getLogger(__name__)


def _compute_envelopes(
    img: cp.array, # type: ignore
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
    X, Y = cp.meshgrid(cp.arange(width), y_range)

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


def cupy_colorToGray(
    img: cp.array, # type: ignore
    radius=300,
    samples=4,
    iterations=10,
    enhance_shadows=False,
    batch_size=100,
) -> cp.array: # type: ignore
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


def np_uint8_float_colorToGray(
    img: np.ndarray,
    radius=300,
    samples=4,
    iterations=10,
    enhance_shadows=False,
    batch_size=100,
):
    img_float = img.astype(np.float32) / 255.0

    # Move source image to GPU
    src: cp.array = cp.asarray(img_float) # type: ignore

    cupy_result = cupy_colorToGray(
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
