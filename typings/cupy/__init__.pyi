"""Local type stub for the ``cupy`` GPU array library.

CuPy ships no ``py.typed`` marker (see
``.venv/lib/python3.13/site-packages/cupy``), so basedpyright treats it as
untyped even though the installed source carries some inline PEP 484
annotations. This stub covers only the API surface this repo actually calls
(grepped from ``pdomain_book_tools/image_processing/cupy_processing/*``,
``pdomain_book_tools/geometry_correction/transforms.py``,
``pdomain_book_tools/image_processing/grayscale_pipeline/ops_gpu.py``, and
the corresponding tests) — it is not a general-purpose CuPy stub.

Design notes:

- ``cupy.ndarray`` subclasses ``numpy.ndarray`` for typing purposes. CuPy's
  array API is deliberately a mirror of NumPy's (documented CuPy design
  goal), and this repo's own convention already treats CuPy arrays as
  ``numpy.typing.NDArray[np.generic]`` for static-typing purposes (see e.g.
  ``CuPyArray = npt.NDArray[np.generic]`` in ``cupy_processing/morph.py``).
  Subclassing gives ``cupy.ndarray`` every NumPy-mirrored method/operator for
  free and keeps it assignable to the many ``np.ndarray``-typed fields that
  hold either backend's array (e.g.
  ``pdomain_book_tools.geometry_correction.transforms.GeometryTransform``).
  Only the CuPy-specific additions (``.get()``, ``.device``) are declared
  here explicitly.
- Functions whose result dtype genuinely depends on runtime data (e.g.
  ``where``, ``maximum``) return ``ndarray[np.generic]`` — the same
  "give up precisely, stay honest" fallback this repo's own ``CuPyArray``
  alias already uses — rather than ``Any``.
- Reduction functions (``sum``, ``max``, ``min``, ...) always return
  ``cupy.ndarray`` (never a bare scalar): unlike NumPy, CuPy keeps reduction
  results as 0-d device arrays so a host round-trip stays explicit via
  ``.get()``. Verified against the installed cupy-cuda12x runtime.
"""

from collections.abc import Sequence
from typing import Any, Generic, SupportsIndex, TypeVar, overload, override

import numpy as np
import numpy.typing as npt

from . import lib as lib
from .cuda import Device as _Device

_ScalarT = TypeVar("_ScalarT", bound=np.generic)
_ScalarT2 = TypeVar("_ScalarT2", bound=np.generic)

_ShapeLike = SupportsIndex | Sequence[SupportsIndex]
_DTypeLike = type[_ScalarT] | np.dtype[_ScalarT]

pi: float

# CuPy re-exports NumPy's scalar type hierarchy directly (``cupy.uint8 is
# numpy.uint8`` etc. — verified against the installed runtime), so these are
# plain aliases, not redeclarations.
uint8 = np.uint8
int16 = np.int16
int32 = np.int32
int64 = np.int64
float32 = np.float32
float64 = np.float64
intp = np.intp
generic = np.generic

class ndarray(np.ndarray[tuple[Any, ...], np.dtype[_ScalarT]], Generic[_ScalarT]):
    # ``numpy.ndarray.device`` types the Python Array API's fixed
    # ``Literal["cpu"]`` device attribute — NumPy only ever runs on the CPU.
    # CuPy overrides this with a real ``cupy.cuda.Device`` handle (see
    # ``result.device.id`` in ``tests/gpu/test_cuda_functionality.py``); the
    # two are genuinely incompatible types by design, not a stub mistake.
    @property
    @override
    def device(self) -> _Device: ...  # pyright: ignore[reportIncompatibleMethodOverride]  # real CuPy/NumPy API divergence, see comment above
    def get(
        self,
        stream: object | None = None,
        order: str = "C",
        out: npt.NDArray[_ScalarT] | None = None,
        *,
        blocking: bool = True,
    ) -> npt.NDArray[_ScalarT]: ...

class _UFunc:
    """Stand-in for CuPy's ufunc type (``cupy._core._kernel.ufunc``).

    Only the ``__call__``/``at`` surface this repo uses (``cp.add.at`` in
    ``cupy_processing/textline_dewarp.py``) is modeled.
    """

    def __call__(
        self,
        x1: _ArrayLike,
        x2: _ArrayLike | None = None,
        out: ndarray[Any] | None = None,
    ) -> ndarray[np.generic]: ...
    def at(
        self,
        a: ndarray[Any],
        indices: _ArrayLike,
        b: _ArrayLike | None = None,
    ) -> None: ...

add: _UFunc

_ArrayLike = npt.ArrayLike

# -- array creation -----------------------------------------------------

@overload
def array(
    obj: object, dtype: _DTypeLike[_ScalarT], copy: bool = True
) -> ndarray[_ScalarT]: ...
@overload
def array(obj: object, copy: bool = True) -> ndarray[np.generic]: ...
@overload
def asarray(
    a: object, dtype: _DTypeLike[_ScalarT], order: str | None = None
) -> ndarray[_ScalarT]: ...
@overload
def asarray(a: object, order: str | None = None) -> ndarray[np.generic]: ...
@overload
def asnumpy(a: ndarray[_ScalarT] | npt.NDArray[_ScalarT]) -> npt.NDArray[_ScalarT]: ...
@overload
def asnumpy(a: object) -> npt.NDArray[np.generic]: ...
@overload
def zeros(shape: _ShapeLike, dtype: _DTypeLike[_ScalarT]) -> ndarray[_ScalarT]: ...
@overload
def zeros(shape: _ShapeLike) -> ndarray[np.float64]: ...
@overload
def ones(shape: _ShapeLike, dtype: _DTypeLike[_ScalarT]) -> ndarray[_ScalarT]: ...
@overload
def ones(shape: _ShapeLike) -> ndarray[np.float64]: ...
@overload
def empty(shape: _ShapeLike, dtype: _DTypeLike[_ScalarT]) -> ndarray[_ScalarT]: ...
@overload
def empty(shape: _ShapeLike) -> ndarray[np.float64]: ...
@overload
def zeros_like(a: object, dtype: _DTypeLike[_ScalarT2]) -> ndarray[_ScalarT2]: ...
@overload
def zeros_like(a: ndarray[_ScalarT] | npt.NDArray[_ScalarT]) -> ndarray[_ScalarT]: ...
@overload
def empty_like(a: object, dtype: _DTypeLike[_ScalarT2]) -> ndarray[_ScalarT2]: ...
@overload
def empty_like(a: ndarray[_ScalarT] | npt.NDArray[_ScalarT]) -> ndarray[_ScalarT]: ...
@overload
def full(
    shape: _ShapeLike, fill_value: object, dtype: _DTypeLike[_ScalarT]
) -> ndarray[_ScalarT]: ...
@overload
def full(shape: _ShapeLike, fill_value: object) -> ndarray[np.generic]: ...
@overload
def arange(
    start: float,
    stop: float | None = None,
    step: float | None = None,
    *,
    dtype: _DTypeLike[_ScalarT],
) -> ndarray[_ScalarT]: ...
@overload
def arange(
    start: float, stop: float | None = None, step: float | None = None
) -> ndarray[np.generic]: ...

# -- shape / combination -------------------------------------------------

def pad(
    array: ndarray[_ScalarT] | npt.NDArray[_ScalarT],
    pad_width: SupportsIndex | Sequence[SupportsIndex] | Sequence[Sequence[int]],
    mode: str = "constant",
    **kwargs: object,
) -> ndarray[_ScalarT]: ...
def stack(arrays: Sequence[_ArrayLike], axis: int = 0) -> ndarray[np.generic]: ...
def concatenate(
    arrays: Sequence[_ArrayLike], axis: int | None = 0
) -> ndarray[np.generic]: ...
def meshgrid(*xi: _ArrayLike, **kwargs: object) -> list[ndarray[np.generic]]: ...
def flip(
    a: ndarray[_ScalarT] | npt.NDArray[_ScalarT],
    axis: int | tuple[int, ...] | None = None,
) -> ndarray[_ScalarT]: ...

# -- elementwise / comparison ---------------------------------------------

def clip(
    a: ndarray[_ScalarT] | npt.NDArray[_ScalarT],
    a_min: object,
    a_max: object,
    out: ndarray[_ScalarT] | None = None,
) -> ndarray[_ScalarT]: ...
@overload
def where(condition: _ArrayLike) -> tuple[ndarray[np.intp], ...]: ...
@overload
def where(
    condition: _ArrayLike, x: _ArrayLike, y: _ArrayLike
) -> ndarray[np.generic]: ...
def maximum(
    x1: _ArrayLike, x2: _ArrayLike, out: ndarray[Any] | None = None
) -> ndarray[np.generic]: ...
def minimum(
    x1: _ArrayLike, x2: _ArrayLike, out: ndarray[Any] | None = None
) -> ndarray[np.generic]: ...
def greater(x1: _ArrayLike, x2: _ArrayLike) -> ndarray[np.bool_]: ...
def divide(
    x1: _ArrayLike, x2: _ArrayLike, out: ndarray[Any] | None = None
) -> ndarray[np.float64]: ...
def bitwise_not(
    x: ndarray[_ScalarT] | npt.NDArray[_ScalarT], out: ndarray[_ScalarT] | None = None
) -> ndarray[_ScalarT]: ...
def cos(x: _ArrayLike, out: ndarray[Any] | None = None) -> ndarray[np.float64]: ...
def sin(x: _ArrayLike, out: ndarray[Any] | None = None) -> ndarray[np.float64]: ...
def sqrt(x: _ArrayLike, out: ndarray[Any] | None = None) -> ndarray[np.float64]: ...
def rint(
    x: ndarray[_ScalarT] | npt.NDArray[_ScalarT], out: ndarray[_ScalarT] | None = None
) -> ndarray[_ScalarT]: ...
def round(
    a: ndarray[_ScalarT] | npt.NDArray[_ScalarT],
    decimals: int = 0,
    out: ndarray[_ScalarT] | None = None,
) -> ndarray[_ScalarT]: ...

# -- reductions ------------------------------------------------------------
# CuPy reductions always return a (possibly 0-d) ``cupy.ndarray``, never a
# bare scalar — see module docstring.

@overload
def sum(
    a: ndarray[_ScalarT] | npt.NDArray[_ScalarT],
    axis: int | tuple[int, ...] | None = None,
    dtype: None = None,
) -> ndarray[_ScalarT]: ...
@overload
def sum(
    a: object,
    axis: int | tuple[int, ...] | None,
    dtype: _DTypeLike[_ScalarT2],
) -> ndarray[_ScalarT2]: ...
def max(
    a: ndarray[_ScalarT] | npt.NDArray[_ScalarT],
    axis: int | tuple[int, ...] | None = None,
) -> ndarray[_ScalarT]: ...
def min(
    a: ndarray[_ScalarT] | npt.NDArray[_ScalarT],
    axis: int | tuple[int, ...] | None = None,
) -> ndarray[_ScalarT]: ...
def mean(
    a: _ArrayLike, axis: int | tuple[int, ...] | None = None
) -> ndarray[np.float64]: ...
def var(
    a: _ArrayLike, axis: int | tuple[int, ...] | None = None
) -> ndarray[np.float64]: ...
def all(
    a: _ArrayLike, axis: int | tuple[int, ...] | None = None
) -> ndarray[np.bool_]: ...
def any(
    a: _ArrayLike, axis: int | tuple[int, ...] | None = None
) -> ndarray[np.bool_]: ...
def argmax(a: _ArrayLike, axis: int | None = None) -> ndarray[np.intp]: ...
def argsort(a: _ArrayLike, axis: int = -1) -> ndarray[np.intp]: ...
def nonzero(a: _ArrayLike) -> tuple[ndarray[np.intp], ...]: ...
def cumsum(
    a: ndarray[_ScalarT] | npt.NDArray[_ScalarT],
    axis: int | None = None,
) -> ndarray[_ScalarT]: ...

# -- set / search / statistics ---------------------------------------------

def unique(ar: ndarray[_ScalarT] | npt.NDArray[_ScalarT]) -> ndarray[_ScalarT]: ...
def isin(element: _ArrayLike, test_elements: _ArrayLike) -> ndarray[np.bool_]: ...
def searchsorted(
    a: _ArrayLike, v: _ArrayLike, side: str = "left"
) -> ndarray[np.intp]: ...
def bincount(
    x: _ArrayLike, weights: _ArrayLike | None = None, minlength: int | None = None
) -> ndarray[np.intp]: ...
def histogram(
    a: _ArrayLike,
    bins: int = 10,
    # CuPy accepts 0-d array bounds here (e.g. the output of ``cp.min``/
    # ``cp.max``, which are always arrays — see module docstring), not just
    # plain floats.
    range: tuple[_ArrayLike, _ArrayLike] | None = None,
) -> tuple[ndarray[np.int64], ndarray[np.float64]]: ...
def interp(
    x: _ArrayLike,
    xp: _ArrayLike,
    fp: _ArrayLike,
    left: float | None = None,
    right: float | None = None,
    period: float | None = None,
) -> ndarray[np.float64]: ...
def polyfit(x: _ArrayLike, y: _ArrayLike, deg: int) -> ndarray[np.float64]: ...
def polyval(p: _ArrayLike, x: _ArrayLike) -> ndarray[np.float64]: ...
def allclose(
    a: _ArrayLike, b: _ArrayLike, rtol: float = 1e-05, atol: float = 1e-08
) -> bool: ...
def array_equal(a1: _ArrayLike, a2: _ArrayLike, equal_nan: bool = False) -> bool: ...

# -- random ------------------------------------------------------------

class _Generator:
    @overload
    def integers(
        self,
        low: int,
        high: int | None = None,
        size: _ShapeLike | None = None,
        *,
        dtype: _DTypeLike[_ScalarT],
    ) -> ndarray[_ScalarT]: ...
    @overload
    def integers(
        self,
        low: int,
        high: int | None = None,
        size: _ShapeLike | None = None,
    ) -> ndarray[np.int64]: ...

class _RandomModule:
    def default_rng(self, seed: int | None = None) -> _Generator: ...
    def seed(self, seed: int | None = None) -> None: ...
    def uniform(
        self,
        low: float = 0.0,
        high: float = 1.0,
        size: _ShapeLike | None = None,
    ) -> ndarray[np.float64]: ...
    @overload
    def randint(
        self,
        low: int,
        high: int | None = None,
        size: _ShapeLike | None = None,
        *,
        dtype: _DTypeLike[_ScalarT],
    ) -> ndarray[_ScalarT]: ...
    @overload
    def randint(
        self,
        low: int,
        high: int | None = None,
        size: _ShapeLike | None = None,
    ) -> ndarray[np.int_]: ...

random: _RandomModule
