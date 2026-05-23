# pyright: reportUnknownMemberType=false
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, cast

from ._cupy_compat import cp, require_cupy

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt

    CuPyArray = npt.NDArray[np.generic]
else:
    CuPyArray = object

# cupyx is part of the CuPy install ([gpu] extra). This guard lets the module
# load on CPU-only installs; require_cupy() in each function gives the
# actionable error before these names are ever dereferenced.
try:
    from cupyx.scipy.ndimage import (  # pyright: ignore[reportMissingImports]
        gaussian_filter,
        median_filter,
        uniform_filter,
    )
except ImportError:  # pragma: no cover - exercised only on CPU-only installs
    gaussian_filter = None
    median_filter = None
    uniform_filter = None

FilterFn = Callable[..., CuPyArray]
gaussian_filter_fn = cast("FilterFn | None", gaussian_filter)
median_filter_fn = cast("FilterFn | None", median_filter)
uniform_filter_fn = cast("FilterFn | None", uniform_filter)

logger = logging.getLogger(__name__)


def gaussian_filter_gpu(
    img_cp: CuPyArray,
    sigma: float = 1.0,
) -> CuPyArray:
    """
    Apply a Gaussian blur to a 2-D or 3-D uint8 CuPy array.

    sigma: standard deviation of the Gaussian kernel (in pixels).
    For 3-D images the filter is applied independently per channel (sigma is
    not applied along the channel axis).

    Returns the same dtype as the input.
    """
    require_cupy()
    _sigma = (sigma, sigma, 0) if img_cp.ndim == 3 else sigma

    result = gaussian_filter_fn(
        cast("CuPyArray", img_cp.astype(cp.float32)),
        sigma=_sigma,
    )  # pyright: ignore[reportOptionalCall]  # guarded by require_cupy()
    return cast("CuPyArray", cp.rint(result).clip(0, 255).astype(img_cp.dtype))


def median_filter_gpu(
    img_cp: CuPyArray,
    size: int = 3,
) -> CuPyArray:
    """
    Apply a median filter to a 2-D or 3-D uint8 CuPy array.

    size: side length of the square neighbourhood (must be odd).
    For 3-D images the filter window is (size, size, 1) — per channel.

    Returns the same dtype as the input.
    """
    require_cupy()
    _size = (size, size, 1) if img_cp.ndim == 3 else size

    return cast(
        "CuPyArray",
        median_filter_fn(img_cp, size=_size).astype(img_cp.dtype),  # pyright: ignore[reportOptionalCall]  # guarded by require_cupy()
    )


def uniform_filter_gpu(
    img_cp: CuPyArray,
    size: int = 3,
) -> CuPyArray:
    """
    Apply a uniform (box / mean) filter to a 2-D or 3-D uint8 CuPy array.

    size: side length of the square neighbourhood.
    For 3-D images the filter window is (size, size, 1) — per channel.

    Returns the same dtype as the input.
    """
    require_cupy()
    _size = (size, size, 1) if img_cp.ndim == 3 else size

    result = uniform_filter_fn(
        cast("CuPyArray", img_cp.astype(cp.float32)),
        size=_size,
    )  # pyright: ignore[reportOptionalCall]  # guarded by require_cupy()
    return cast("CuPyArray", cp.rint(result).clip(0, 255).astype(img_cp.dtype))


def np_uint8_gaussian_filter(img: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """Transfers img to GPU, applies Gaussian blur, returns CPU uint8 array."""
    return cast(
        "np.ndarray",
        cp.asnumpy(gaussian_filter_gpu(cast("CuPyArray", cp.asarray(img)), sigma)),
    )


def np_uint8_median_filter(img: np.ndarray, size: int = 3) -> np.ndarray:
    """Transfers img to GPU, applies median filter, returns CPU uint8 array."""
    return cast(
        "np.ndarray",
        cp.asnumpy(median_filter_gpu(cast("CuPyArray", cp.asarray(img)), size)),
    )


def np_uint8_uniform_filter(img: np.ndarray, size: int = 3) -> np.ndarray:
    """Transfers img to GPU, applies uniform filter, returns CPU uint8 array."""
    return cast(
        "np.ndarray",
        cp.asnumpy(uniform_filter_gpu(cast("CuPyArray", cp.asarray(img)), size)),
    )
