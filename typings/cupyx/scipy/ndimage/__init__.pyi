"""Stub for ``cupyx.scipy.ndimage`` — only the functions this repo imports
directly (``from cupyx.scipy.ndimage import ...``).

Other ``cupyx.scipy.ndimage`` functions (``grey_dilation``, ``grey_erosion``,
``grey_opening``, ``grey_closing``, ``map_coordinates``, ``label`` called
dynamically) are reached in this repo only via
``importlib.import_module("cupyx.scipy.ndimage")``, which basedpyright
already types as ``types.ModuleType`` (whose ``__getattr__`` resolves to
``Any`` in typeshed) — no stub coverage needed for those call sites.
"""

from typing import TypeVar

import numpy as np
import numpy.typing as npt
from cupy import ndarray

_ScalarT = TypeVar("_ScalarT", bound=np.generic)
_Array = ndarray[_ScalarT] | npt.NDArray[_ScalarT]

def gaussian_filter(
    input: _Array[_ScalarT],
    sigma: float | tuple[float, ...],
    mode: str = "reflect",
) -> ndarray[_ScalarT]: ...
def uniform_filter(
    input: _Array[_ScalarT],
    size: int | tuple[int, ...] = 3,
    mode: str = "reflect",
) -> ndarray[_ScalarT]: ...
def median_filter(
    input: _Array[_ScalarT],
    size: int | tuple[int, ...] | None = None,
    mode: str = "reflect",
) -> ndarray[_ScalarT]: ...
def convolve1d(
    input: _Array[_ScalarT],
    weights: ndarray[np.generic] | npt.NDArray[np.generic],
    axis: int = -1,
    mode: str = "reflect",
) -> ndarray[_ScalarT]: ...
def affine_transform(
    input: _Array[_ScalarT],
    matrix: ndarray[np.generic] | npt.NDArray[np.generic],
    offset: float | tuple[float, ...] = 0.0,
    output_shape: tuple[int, ...] | None = None,
    order: int = 3,
    mode: str = "constant",
    cval: float = 0.0,
    prefilter: bool = True,
) -> ndarray[_ScalarT]: ...
def zoom(
    input: _Array[_ScalarT],
    zoom: float | tuple[float, ...],
    order: int = 3,
    mode: str = "constant",
    cval: float = 0.0,
    prefilter: bool = True,
) -> ndarray[_ScalarT]: ...
def find_objects(
    input: _Array[np.integer], max_label: int = 0
) -> list[tuple[slice, ...] | None]: ...
def label(
    input: _Array[np.generic],
    structure: _Array[np.generic] | None = None,
) -> tuple[ndarray[np.int32], int]: ...
