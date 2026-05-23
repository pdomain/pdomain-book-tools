# pyright: reportUnknownMemberType=false
# Configure logging
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, cast

from ._cupy_compat import cp, require_cupy

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt

    CuPyArray = npt.NDArray[np.generic]
    Shape2D = tuple[int, int]
else:
    CuPyArray = object
    Shape2D = tuple[int, int]

# cupy is an optional [gpu]-extra dependency (see pyproject.toml). This guard
# lets the module load on CPU-only installs; require_cupy() in each function
# raises the actionable error before these names are ever dereferenced.
try:
    from cupy.lib.stride_tricks import (  # pyright: ignore[reportMissingImports]
        sliding_window_view,
    )
except ImportError:  # pragma: no cover - exercised only on CPU-only installs
    sliding_window_view = None

SlidingWindowViewFn = Callable[..., CuPyArray]
sliding_window_view_fn: SlidingWindowViewFn | None = sliding_window_view

logger = logging.getLogger(__name__)


def dilate(img: CuPyArray, kernel: CuPyArray) -> CuPyArray:
    """Performs dilation using a fully vectorized approach on a cupy image array."""
    require_cupy()
    kh, kw = cast("Shape2D", kernel.shape)
    pad_h, pad_w = kh // 2, kw // 2

    # Pad the image
    # Use 'reflect' padding to mirror cv2's default BORDER_REFLECT_101
    # (numpy/cupy 'reflect' excludes the edge pixel: dcb|abcd|cba). Constant-0
    # padding silently eroded foreground pixels touching the image border —
    # see M-08 in docs/review/bugs-medium.md.
    img_padded = cast(
        "CuPyArray",
        cp.pad(img, ((pad_h, pad_h), (pad_w, pad_w)), mode="reflect"),
    )

    # Create sliding windows over the image
    windows = sliding_window_view_fn(img_padded, (kh, kw))  # pyright: ignore[reportOptionalCall]  # guarded by require_cupy()

    # Apply max operation over the windows.
    # NOTE: the only call site (`morph_fill`) builds `kernel` as
    # `cp.ones(...)`, so multiplying `windows * kernel` is a no-op that
    # nonetheless materializes a full `(H, W, kh, kw)` intermediate
    # (~432 MB for a 3000x4000 page with a 6x6 kernel) before reducing.
    # Reducing directly over `windows` cuts peak GPU memory dramatically
    # without changing output. See M-09 in docs/review/bugs-medium.md.
    # If a non-trivial (non-rectangular) structuring element is ever
    # needed, use `cupyx.scipy.ndimage.grey_dilation` rather than
    # reintroducing a multiplied intermediate.
    return cast("CuPyArray", cp.max(windows, axis=(-2, -1)))


def erode(img: CuPyArray, kernel: CuPyArray) -> CuPyArray:
    """Performs erosion using a fully vectorized approach on a cupy image array."""
    require_cupy()
    kh, kw = cast("Shape2D", kernel.shape)
    pad_h, pad_w = kh // 2, kw // 2

    # Pad the image
    # Use 'reflect' padding to mirror cv2's default BORDER_REFLECT_101
    # (numpy/cupy 'reflect' excludes the edge pixel: dcb|abcd|cba). Constant-0
    # padding silently eroded foreground pixels touching the image border —
    # see M-08 in docs/review/bugs-medium.md.
    img_padded = cast(
        "CuPyArray",
        cp.pad(img, ((pad_h, pad_h), (pad_w, pad_w)), mode="reflect"),
    )

    # Create sliding windows over the image
    windows = sliding_window_view_fn(img_padded, (kh, kw))  # pyright: ignore[reportOptionalCall]  # guarded by require_cupy()

    # Apply min operation over the windows.
    # Same M-09 optimization as in `dilate`: the only call site builds an
    # all-ones kernel, so multiplying is a no-op that materializes a
    # large intermediate. Reduce over `windows` directly.
    return cast("CuPyArray", cp.min(windows, axis=(-2, -1)))


def morph_fill(img: CuPyArray, shape: Shape2D = (6, 6)) -> CuPyArray:
    """Apply closing followed by opening morphology using fully vectorized operations."""
    require_cupy()
    kernel = cast("CuPyArray", cp.ones(shape, dtype=cp.uint8))

    # Morphological closing (dilate then erode)
    closed = dilate(img, kernel)
    closed = erode(closed, kernel)

    # Morphological opening (erode then dilate)
    opened = erode(closed, kernel)
    return dilate(opened, kernel)


def np_uint8_morph_fill(img: np.ndarray, shape: Shape2D = (6, 6)) -> np.ndarray:
    """Transfers img to GPU, applies morph_fill, returns CPU uint8 array."""
    require_cupy()
    return cp.asnumpy(morph_fill(cast("CuPyArray", cp.asarray(img)), shape=shape))
