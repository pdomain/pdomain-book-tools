"""Tests for cupy_processing.invert module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

import pytest

if TYPE_CHECKING:
    import cupy
    import numpy as np
    import numpy.typing as npt

    CuPyArray = npt.NDArray[np.generic]


class _CupyRandomModule(Protocol):
    def randint(
        self,
        low: int,
        high: int | None = None,
        size: tuple[int, ...] | None = None,
        *,
        dtype: type[np.generic] | None = None,
    ) -> cupy.ndarray[np.generic]: ...


class _CupyModule(Protocol):
    """Structural stand-in for the ``cupy`` module returned by the
    ``cupy_module`` fixture (see ``tests/conftest.py``) — narrows the
    otherwise-untyped fixture return to the subset of cupy's API this file
    calls, mirroring the real signatures in ``typings/cupy/__init__.pyi``.
    """

    uint8: type[np.uint8]
    random: _CupyRandomModule

    def asarray(
        self, a: object, dtype: type[np.generic]
    ) -> cupy.ndarray[np.generic]: ...


class _InvertModule(Protocol):
    """Structural stand-in for the ``invert`` submodule — narrows the
    dynamically imported module to the entry point this file calls.
    """

    def invert_image(self, img: CuPyArray) -> CuPyArray: ...


@pytest.fixture
def cupy_invert(cupy_module: _CupyModule) -> tuple[_InvertModule, _CupyModule]:
    """Import the cupy invert module only when cupy is available."""
    from pdomain_book_tools.image_processing.cupy_processing import invert as invert_mod

    return invert_mod, cupy_module


class TestCupyInvertImage:
    def test_invert_uint8(self, cupy_invert: tuple[_InvertModule, _CupyModule]) -> None:
        invert_mod, cp = cupy_invert
        img = cp.asarray([[0, 1, 127, 254, 255]], dtype=cp.uint8)
        out = invert_mod.invert_image(img)
        expected = cp.asarray([[255, 254, 128, 1, 0]], dtype=cp.uint8)
        assert bool((out == expected).all())

    def test_double_invert_returns_original(
        self, cupy_invert: tuple[_InvertModule, _CupyModule]
    ) -> None:
        invert_mod, cp = cupy_invert
        img = cp.random.randint(0, 256, (8, 8), dtype=cp.uint8)
        out = invert_mod.invert_image(invert_mod.invert_image(img))
        assert bool((out == img).all())
