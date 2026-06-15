"""CPU (numpy) port of the Color2Gray algorithm.

Mirrors the math of
:func:`pdomain_book_tools.image_processing.cupy_processing.color_to_gray.cupy_color_to_gray`
using only NumPy so it runs without a GPU.

Algorithm summary
-----------------
For each pixel, sample ``samples x iterations`` neighbours within ``radius``
pixels. Compute per-pixel min/max colour envelopes from those neighbours.
Then convert to grayscale via:

    num = sqrt(sum(px²))
    den = num + sqrt(sum((px - max_col)²))
    ratio = num / den  (0.5 when den == 0)

With ``enhance_shadows=True`` the numerator uses ``px - min_col`` instead of
``px``:

    num = sqrt(sum((px - min_col)²))
    den = num + sqrt(sum((px - max_col)²))

The RNG is seeded from ``seed`` for reproducible results.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt


def color2gray_cpu(
    img: npt.NDArray[np.uint8],
    *,
    radius: int = 300,
    samples: int = 4,
    iterations: int = 10,
    enhance_shadows: bool = False,
    seed: int = 0,
    batch_size: int = 100,
) -> npt.NDArray[np.uint8]:
    """Convert a BGR/RGB uint8 image to grayscale using the Color2Gray algorithm.

    Parameters
    ----------
    img:
        Input image, uint8, shape ``(H, W, 3)`` or ``(H, W, 4)``.  Alpha is
        silently dropped when 4-channel input is given, matching
        :func:`cupy_color_to_gray` semantics.
    radius:
        Maximum sampling radius in pixels.
    samples:
        Number of neighbour samples per iteration.
    iterations:
        Number of sampling iterations.
    enhance_shadows:
        When ``True`` use the shadow-enhancement variant (numerator relative to
        ``min_col`` instead of origin).
    seed:
        RNG seed for reproducibility.
    batch_size:
        Rows processed per batch (matches the GPU implementation default).

    Returns:
    -------
    numpy.ndarray
        Grayscale image, dtype ``uint8``, shape ``(H, W)``.
    """
    if img.dtype != np.uint8:
        raise TypeError(f"color2gray_cpu requires uint8 input; got dtype={img.dtype}.")
    if img.ndim != 3:
        raise ValueError(
            f"color2gray_cpu expected a 3-channel image with shape (H, W, C); "
            f"got ndim={img.ndim}, shape={img.shape}."
        )
    channels = img.shape[2]
    if channels < 3:
        raise ValueError(
            f"color2gray_cpu expected at least 3 channels; got {channels}."
        )
    if channels > 4:
        raise ValueError(f"color2gray_cpu expected 3 or 4 channels; got {channels}.")

    # Drop alpha silently, matching cupy_color_to_gray.
    src: npt.NDArray[np.float32] = (img[..., :3].astype(np.float32)) / 255.0

    height, width, _ch = src.shape

    rng = np.random.default_rng(seed)

    # Pre-generate ALL random offsets at once (same structure as GPU version):
    # angles shape: (iterations, samples)
    # radii shape:  (iterations, samples)
    angles = rng.uniform(0, 2 * np.pi, (iterations, samples))
    radii = rng.uniform(0, radius, (iterations, samples))

    # Integer pixel offsets, shape (iterations, samples)
    dx = np.round(radii * np.cos(angles)).astype(np.int32)  # (iters, samps)
    dy = np.round(radii * np.sin(angles)).astype(np.int32)  # (iters, samps)

    dst = np.empty((height, width), dtype=np.float32)

    for y_start in range(0, height, batch_size):
        y_end = min(y_start + batch_size, height)

        # Pixel coordinates for this batch
        # y_coords: (batch_h, 1),  x_coords: (1, width)
        y_coords = np.arange(y_start, y_end, dtype=np.int32).reshape(-1, 1)
        x_coords = np.arange(width, dtype=np.int32).reshape(1, -1)

        # Neighbour coordinates: (iters, samps, batch_h, width)
        # dx/dy broadcast: (iters, samps, 1, 1) + (1, 1, batch_h, W)
        nx = np.clip(
            x_coords[np.newaxis, np.newaxis, :, :] + dx[:, :, np.newaxis, np.newaxis],
            0,
            width - 1,
        )  # (iters, samps, batch_h, W)
        ny = np.clip(
            y_coords[np.newaxis, np.newaxis, :, :] + dy[:, :, np.newaxis, np.newaxis],
            0,
            height - 1,
        )  # (iters, samps, batch_h, W)

        # Sampled pixel values: (iters, samps, batch_h, W, 3)
        sampled = src[ny, nx, :]  # advanced indexing into (H, W, 3)

        # Per-pixel min/max envelopes over all (iters x samps) neighbours
        # → shape (batch_h, W, 3)
        min_val = sampled.min(axis=(0, 1))
        max_val = sampled.max(axis=(0, 1))

        # Current pixels in this batch: (batch_h, W, 3)
        pixels = src[y_start:y_end, :, :]

        if enhance_shadows:
            numerator = np.sum((pixels - min_val) ** 2, axis=2)
            denominator_sq = np.sum((pixels - max_val) ** 2, axis=2)
        else:
            numerator = np.sum(pixels**2, axis=2)
            denominator_sq = np.sum((pixels - max_val) ** 2, axis=2)

        num_sqrt = np.sqrt(numerator)
        den = num_sqrt + np.sqrt(denominator_sq)

        ratio = np.where(den > 0.0, num_sqrt / den, 0.5)
        dst[y_start:y_end, :] = ratio

    return np.clip(dst * 255.0, 0, 255).astype(np.uint8)
