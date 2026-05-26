# pyright: reportUnknownMemberType=false
# pyright: reportUnnecessaryCast=false
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

logger = logging.getLogger(__name__)

# ITU-R BT.601 weights, matching cv2.COLOR_BGR2GRAY:
#   Y = 0.114*B + 0.587*G + 0.299*R  # noqa: ERA001  # mathematical formula, not dead code
#
# Built lazily on first use so this module imports cleanly when CuPy isn't
# installed (the `gpu` extra is opt-in). require_cupy() inside the helper
# raises a clear error if the GPU extra is missing.
_bgr2gray_weights_cache: CuPyArray | None = None


def _bgr2gray_weights() -> CuPyArray:
    global _bgr2gray_weights_cache  # noqa: PLW0603  # lazy singleton — avoids CuPy import on module load
    if _bgr2gray_weights_cache is None:
        require_cupy()
        _bgr2gray_weights_cache = cast(
            "CuPyArray",
            cp.array([0.114, 0.587, 0.299], dtype=np.float32),
        )
    return _bgr2gray_weights_cache


def bgr_to_gray_gpu(img_cp: CuPyArray) -> CuPyArray:
    """
    Convert a BGR uint8 image to grayscale using ITU-R BT.601 weights.
    Matches cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).

    img_cp: (H, W, 3) uint8 CuPy array.
    Returns: (H, W) uint8 CuPy array.
    """
    require_cupy()
    weights = _bgr2gray_weights()
    float_img = cast("CuPyArray", img_cp.astype(np.float32))
    gray = cast(
        "CuPyArray",
        weights[0] * float_img[:, :, 0]
        + weights[1] * float_img[:, :, 1]
        + weights[2] * float_img[:, :, 2],
    )
    return cast("CuPyArray", gray.clip(0, 255).astype(np.uint8))


def gray_to_bgr_gpu(img_cp: CuPyArray) -> CuPyArray:
    """
    Convert a grayscale uint8 image to 3-channel BGR by replicating the channel.
    Matches cv2.cvtColor(img, cv2.COLOR_GRAY2BGR).

    img_cp: (H, W) uint8 CuPy array.
    Returns: (H, W, 3) uint8 CuPy array.
    """
    require_cupy()
    return cast("CuPyArray", cp.stack([img_cp, img_cp, img_cp], axis=-1))


def bgr_to_rgb_gpu(img_cp: CuPyArray) -> CuPyArray:
    """
    Reverse channel order: BGR → RGB (or RGB → BGR — same operation).
    Matches cv2.cvtColor(img, cv2.COLOR_BGR2RGB).

    img_cp: (H, W, 3) CuPy array.
    Returns: (H, W, 3) CuPy array (contiguous copy).
    """
    require_cupy()
    return cast("CuPyArray", img_cp[:, :, [2, 1, 0]])


# Alias — the operation is its own inverse
rgb_to_bgr_gpu = bgr_to_rgb_gpu


def np_uint8_bgr_to_gray(img: np.ndarray) -> np.ndarray:
    """Transfers img to GPU, converts BGR→gray, returns CPU uint8 array."""
    require_cupy()
    return cast(
        "np.ndarray", cp.asnumpy(bgr_to_gray_gpu(cast("CuPyArray", cp.asarray(img))))
    )


def np_uint8_gray_to_bgr(img: np.ndarray) -> np.ndarray:
    """Transfers img to GPU, converts gray→BGR, returns CPU uint8 array."""
    require_cupy()
    return cast(
        "np.ndarray", cp.asnumpy(gray_to_bgr_gpu(cast("CuPyArray", cp.asarray(img))))
    )


def np_uint8_bgr_to_rgb(img: np.ndarray) -> np.ndarray:
    """Transfers img to GPU, flips channel order, returns CPU uint8 array."""
    require_cupy()
    return cast(
        "np.ndarray", cp.asnumpy(bgr_to_rgb_gpu(cast("CuPyArray", cp.asarray(img))))
    )
