"""GPU (CuPy) color-to-grayscale converter ops.

Numpy-in / numpy-out wrappers that upload to GPU, compute, and download.
Each function matches the CPU counterpart in ``ops_cpu`` within the tolerance
documented in ``tests/image_processing/grayscale_pipeline/test_ops_gpu.py``.

Delegation notes
----------------
- ``lab_l_gpu``:  CuPy has no built-in CIELAB colour transform and faithful
  re-implementation of the D65-illuminant sRGB→LAB pipeline is non-trivial.
  This op delegates to ``ops_cpu.lab_l`` so callers get a correct L* channel;
  the GPU code path for this op is intentionally CPU-backed.
- ``clahe_gpu``: CLAHE requires per-tile histogram manipulation that cv2 handles
  efficiently on the CPU.  ``cupyx`` offers no equivalent.  This op delegates
  to ``ops_cpu.clahe``; the GPU code path is intentionally CPU-backed.
- ``luma_gpu``, ``best_channel_gpu``, ``flatten_gpu``: genuinely CuPy-computed.
"""

# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnnecessaryCast=false
from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np
import numpy.typing as npt

from pdomain_book_tools.image_processing.cupy_processing._cupy_compat import (
    cp,
    require_cupy,
)
from pdomain_book_tools.image_processing.grayscale_pipeline import ops_cpu

# cupyx.scipy.ndimage is part of the CuPy install ([gpu] extra).  This guard
# lets the module load on CPU-only installs; require_cupy() in each function
# gives the actionable error before these names are dereferenced.
try:
    from cupyx.scipy.ndimage import (  # pyright: ignore[reportMissingImports]  # optional GPU import is guarded
        gaussian_filter as _cupy_gaussian_filter,
    )
except ImportError:  # pragma: no cover - exercised only on CPU-only installs
    _cupy_gaussian_filter = None  # type: ignore[assignment]

if TYPE_CHECKING:
    CuPyArray = npt.NDArray[np.generic]
else:
    CuPyArray = object

U8 = npt.NDArray[np.uint8]


def luma_gpu(img: U8, *, bt709: bool = False) -> U8:
    """GPU equivalent of ``ops_cpu.luma`` — weighted BGR→grayscale sum.

    Genuinely CuPy-computed: uploads ``img``, performs the weighted sum on the
    GPU, and downloads the result.

    Args:
        img: BGR uint8 ndarray of shape (H, W, 3).
        bt709: If False (default) use BT.601 weights matching
               ``cv2.COLOR_BGR2GRAY``.  If True use BT.709 weights.

    Returns:
        Grayscale uint8 ndarray of shape (H, W).
    """
    require_cupy()
    img_cp = cast("CuPyArray", cp.asarray(img, dtype=cp.float32))
    if bt709:
        # BT.709: 0.0722 B + 0.7152 G + 0.2126 R
        weights = cast(
            "CuPyArray", cp.array([0.0722, 0.7152, 0.2126], dtype=cp.float32)
        )
    else:
        # BT.601 (matches cv2.COLOR_BGR2GRAY)
        weights = cast("CuPyArray", cp.array([0.114, 0.587, 0.299], dtype=cp.float32))
    y = cast(
        "CuPyArray",
        weights[0] * img_cp[..., 0]
        + weights[1] * img_cp[..., 1]
        + weights[2] * img_cp[..., 2],
    )
    result = cast("CuPyArray", cp.clip(y, 0, 255).astype(cp.uint8))
    return cast("U8", cp.asnumpy(result))


def lab_l_gpu(img: U8) -> U8:
    """GPU code path for CIELAB L* extraction — delegates to ``ops_cpu.lab_l``.

    CuPy has no built-in sRGB→CIELAB colour transform.  A faithful GPU
    re-implementation would require the full D65-illuminant linearisation
    and the perceptual compression curve, offering no practical benefit over
    the highly-optimised cv2 path.  This function delegates to the CPU
    implementation and is provided so callers on the GPU code path get a
    consistent import name.

    Args:
        img: BGR uint8 ndarray of shape (H, W, 3).

    Returns:
        L* channel as uint8 ndarray of shape (H, W).
    """
    # Require CuPy so callers on CPU-only installs get the standard error
    # rather than silent fallback.
    require_cupy()
    return ops_cpu.lab_l(img)


def best_channel_gpu(img: U8, channel: str = "green") -> U8:
    """GPU equivalent of ``ops_cpu.best_channel`` — channel selection.

    Genuinely CuPy-computed: uploads ``img``, picks the channel (or computes
    per-channel variance for ``"auto"``), and downloads the result.

    Args:
        img: BGR uint8 ndarray of shape (H, W, 3).
        channel: One of ``"blue"``, ``"green"``, ``"red"`` or ``"auto"``.

    Returns:
        Selected channel as uint8 ndarray of shape (H, W).
    """
    require_cupy()
    idx: dict[str, int] = {"blue": 0, "green": 1, "red": 2}
    img_cp = cast("CuPyArray", cp.asarray(img))
    if channel in idx:
        ch = cast("CuPyArray", img_cp[..., idx[channel]].copy())
    else:
        # Auto: select channel with highest variance (computed on GPU)
        variances = [float(cp.var(img_cp[..., c])) for c in range(3)]
        best = int(np.argmax(variances))
        ch = cast("CuPyArray", img_cp[..., best].copy())
    return cast("U8", cp.asnumpy(ch))


def flatten_gpu(img: U8, *, radius: int = 64, strength: float = 1.0) -> U8:
    """GPU equivalent of ``ops_cpu.flatten`` — background normalisation.

    Genuinely CuPy-computed: uses ``cupyx.scipy.ndimage.gaussian_filter``
    with the sigma that matches ``cv2.GaussianBlur(... sigma=0)``.

    ``cv2`` computes sigma from kernel size as:
    ``sigma = 0.3 * ((k-1)*0.5 - 1) + 0.8``

    Args:
        img: BGR uint8 ndarray of shape (H, W, 3).
        radius: Approximate blur radius in pixels (rounded up to odd).
        strength: Blend factor 0.0 (original) → 1.0 (fully flattened).

    Returns:
        Background-flattened BGR uint8 ndarray of shape (H, W, 3).
    """
    require_cupy()
    k = max(3, radius | 1)
    # Match cv2.GaussianBlur sigma=0 auto formula
    sigma = float(0.3 * ((k - 1) * 0.5 - 1) + 0.8)
    img_cp = cast("CuPyArray", cp.asarray(img))
    out = cast("CuPyArray", cp.empty_like(img_cp))
    one = cp.float32(1.0)
    s = cp.float32(strength)
    for c in range(img.shape[2]):
        ch = cast("CuPyArray", img_cp[..., c].astype(cp.float32) + one)
        bg = cast(
            "CuPyArray",
            _cupy_gaussian_filter(ch, sigma=sigma).astype(cp.float32)  # pyright: ignore[reportOptionalCall,reportOptionalMemberAccess]  # guarded by require_cupy()
            + one,
        )
        norm = cast("CuPyArray", ch / bg * cp.float32(float(cp.mean(bg))))  # pyright: ignore[reportOperatorIssue]  # CuPy arithmetic on NDArray-like alias
        blended = cast("CuPyArray", ((one - s) * ch + s * norm).astype(cp.float32))  # pyright: ignore[reportOperatorIssue]  # CuPy arithmetic on NDArray-like alias
        out[..., c] = cp.clip(blended, 0, 255).astype(cp.uint8)
    return cast("U8", cp.asnumpy(out))


def clahe_gpu(gray: U8, *, clip_limit: float = 2.0, tile_grid: int = 8) -> U8:
    """GPU code path for CLAHE — delegates to ``ops_cpu.clahe``.

    ``cupyx`` offers no CLAHE implementation.  The per-tile histogram
    manipulation is handled efficiently by ``cv2`` on the CPU.  This function
    delegates to the CPU implementation and is provided so callers on the GPU
    code path get a consistent import name.

    Args:
        gray: Grayscale uint8 ndarray of shape (H, W).
        clip_limit: Contrast clip limit.
        tile_grid: Number of tiles per dimension.

    Returns:
        CLAHE-enhanced grayscale uint8 ndarray of shape (H, W).
    """
    require_cupy()
    return ops_cpu.clahe(gray, clip_limit=clip_limit, tile_grid=tile_grid)
