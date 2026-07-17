# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""CuPy mirror of cv2_processing/denoise.py — identical public API.

Polarity convention: text=0 (dark), background=255 (light), matching the
output of ``otsu_binary_thresh`` and ``binary_thresh``.

Algorithm:
- Optional median-blur pre-pass via ``cupyx.scipy.ndimage.median_filter``.
- Connected-component labelling via ``cupyx.scipy.ndimage.label``.
- Area-threshold filter: components with fewer pixels than ``min_component_area``
  are zeroed; all others are preserved unchanged.

The GPU path produces **array-equal** output to the cv2 CPU path on binary
images because connected-component area filtering is deterministic (no
floating-point arithmetic, no approximations).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

import numpy as np

from ._cupy_compat import cp, require_cupy

if TYPE_CHECKING:
    import numpy.typing as npt

    CuPyArray = npt.NDArray[np.generic]
else:
    CuPyArray = object

# cupyx is part of the CuPy install ([gpu] extra). This guard lets the module
# load on CPU-only installs; require_cupy() in each function gives the
# actionable error before these names are ever dereferenced.
try:
    from cupyx.scipy.ndimage import (
        label as _cupyx_label,
    )
    from cupyx.scipy.ndimage import (
        median_filter as _cupyx_median_filter,
    )
except ImportError:  # pragma: no cover - exercised only on CPU-only installs
    _cupyx_label = None
    _cupyx_median_filter = None

logger = logging.getLogger(__name__)


def denoise_binary_gpu(
    img_cp: CuPyArray,
    *,
    min_component_area: int = 6,
    median_kernel_size: int = 0,
) -> CuPyArray:
    """Remove speckle noise from a binarized page image using connected-component
    area filtering, with an optional median-blur pre-pass (GPU path).

    Input and output polarity: text=0 (dark), background=255 (light) — the
    standard convention for this library (matches ``otsu_binary_thresh``).

    This is the CuPy mirror of ``cv2_processing.denoise.denoise_binary``.
    On binary images the output is **array-equal** to the CPU result because
    component filtering involves no floating-point arithmetic.

    Parameters are identical to the CPU counterpart:

    Args:
        img_cp: 2-D uint8 CuPy array with text=0, background=255.
        min_component_area: Connected components with fewer pixels than this
            value are removed.  Default 6 px² (period-safe at 300 DPI).
        median_kernel_size: Kernel size for an optional median blur pre-pass
            (must be a positive odd integer, or 0 to skip).  Default 0 (off).

    Returns:
        uint8 CuPy array with the same shape and dtype as *img_cp*, with speckle
        components removed.  The caller's input is never mutated.

    Raises:
        ValueError: If *img_cp* is not a 2-D array, not dtype uint8, or if
            *median_kernel_size* is given but is not a positive odd integer.
        ImportError: If CuPy is not installed (``[gpu]`` extra missing).
    """
    require_cupy()
    if img_cp.ndim != 2:
        raise ValueError(
            f"denoise_binary_gpu expects a 2-D array; got ndim={img_cp.ndim}."
        )
    if img_cp.dtype != cp.uint8:
        raise ValueError(
            f"denoise_binary_gpu expects dtype uint8; got dtype={img_cp.dtype}."
        )
    if median_kernel_size != 0 and (
        median_kernel_size < 1 or median_kernel_size % 2 == 0
    ):
        raise ValueError(
            f"median_kernel_size must be 0 (off) or a positive odd integer; "
            f"got {median_kernel_size}."
        )

    # Invert: text (0) becomes foreground (255) for connected-component labelling.
    fg = cast("CuPyArray", cp.bitwise_not(img_cp))

    if median_kernel_size > 0:
        fg = cast(
            "CuPyArray",
            _cupyx_median_filter(fg, size=median_kernel_size),  # pyright: ignore[reportOptionalCall]  # guarded by require_cupy()
        )

    # Label connected components.  Background label is 0; ink labels are 1..n_labels.
    fg_binary = cast("CuPyArray", fg > 0)  # pyright: ignore[reportOperatorIssue]
    labels_raw, n_labels = cast(
        "tuple[CuPyArray, int]",
        _cupyx_label(fg_binary),  # pyright: ignore[reportOptionalCall]  # guarded by require_cupy()
    )

    if n_labels == 0:
        # No ink components — return a fully clean (all-255) image.
        return cast("CuPyArray", cp.bitwise_not(fg))

    # Count pixel area per label using bincount; label 0 = background.
    labels_flat = cast("CuPyArray", labels_raw.ravel().astype(cp.intp))
    counts = cast("CuPyArray", cp.bincount(labels_flat, minlength=n_labels + 1))

    # Build keep mask (True = keep as ink).
    keep = cast("CuPyArray", counts >= min_component_area)  # pyright: ignore[reportOperatorIssue]
    keep[0] = False  # never keep the background label as ink

    # Reconstruct foreground with small components zeroed.
    # fancy-index keep[labels_raw]: cupy supports ndarray indexing at runtime;
    # the numpy stub types don't model this case so we cast to silence pyright.
    keep_mask = cast("CuPyArray", keep[labels_raw])  # pyright: ignore[reportArgumentType, reportCallIssue]
    clean_fg = cast(
        "CuPyArray",
        cp.where(keep_mask, cp.uint8(255), cp.uint8(0)).astype(cp.uint8),
    )

    # Invert back: text=0, background=255.
    return cast("CuPyArray", cp.bitwise_not(clean_fg))


def np_uint8_denoise_binary(
    img: np.ndarray,
    *,
    min_component_area: int = 6,
    median_kernel_size: int = 0,
) -> np.ndarray:
    """Convenience wrapper: moves *img* to GPU, denoises, returns a CPU uint8 array."""
    require_cupy()
    img_cp = cast("CuPyArray", cp.asarray(img))
    result_cp = denoise_binary_gpu(
        img_cp,
        min_component_area=min_component_area,
        median_kernel_size=median_kernel_size,
    )
    return np.asarray(cp.asnumpy(result_cp), dtype=np.uint8)
