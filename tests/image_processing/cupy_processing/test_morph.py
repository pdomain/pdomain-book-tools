"""Tests for cupy_processing.morph module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

import pytest

if TYPE_CHECKING:
    import cupy
    import numpy as np
    import numpy.typing as npt

    CuPyArray = npt.NDArray[np.generic]
    Shape2D = tuple[int, int]


class _CupyModule(Protocol):
    """Structural stand-in for the ``cupy`` module returned by the
    ``cupy_module`` fixture (see ``tests/conftest.py``) — narrows the
    otherwise-untyped fixture return to the subset of cupy's API this file
    calls, mirroring the real signatures in ``typings/cupy/__init__.pyi``.
    """

    uint8: type[np.uint8]

    def zeros(
        self, shape: tuple[int, ...], dtype: type[np.generic]
    ) -> cupy.ndarray[np.generic]: ...
    def ones(
        self, shape: tuple[int, ...], dtype: type[np.generic]
    ) -> cupy.ndarray[np.generic]: ...
    def asarray(self, a: object) -> cupy.ndarray[np.generic]: ...
    def asnumpy(self, a: object) -> npt.NDArray[np.generic]: ...


class _MorphModule(Protocol):
    """Structural stand-in for the ``morph`` submodule — narrows the
    dynamically imported module to the entry points this file calls.
    """

    def dilate(self, img: CuPyArray, kernel: CuPyArray) -> CuPyArray: ...
    def erode(self, img: CuPyArray, kernel: CuPyArray) -> CuPyArray: ...
    def morph_fill(self, img: CuPyArray, shape: Shape2D = (6, 6)) -> CuPyArray: ...


@pytest.fixture
def cupy_morph(cupy_module: _CupyModule) -> tuple[_MorphModule, _CupyModule]:
    from pdomain_book_tools.image_processing.cupy_processing import morph as morph_mod

    return morph_mod, cupy_module


class TestCupyMorph:
    def test_dilate_expands_single_pixel(
        self, cupy_morph: tuple[_MorphModule, _CupyModule]
    ) -> None:
        morph_mod, cp = cupy_morph
        img = cp.zeros((5, 5), dtype=cp.uint8)
        img[2, 2] = 1
        kernel = cp.ones((3, 3), dtype=cp.uint8)
        out = morph_mod.dilate(img, kernel)
        # Dilation with a 3x3 kernel expands the single 1 to a 3x3 square
        assert int(out.sum()) >= 9

    def test_erode_removes_lone_pixel(
        self, cupy_morph: tuple[_MorphModule, _CupyModule]
    ) -> None:
        morph_mod, cp = cupy_morph
        img = cp.zeros((5, 5), dtype=cp.uint8)
        img[2, 2] = 1
        kernel = cp.ones((3, 3), dtype=cp.uint8)
        out = morph_mod.erode(img, kernel)
        # Erosion of a single pixel with a 3x3 kernel removes it
        assert int(out.sum()) == 0

    def test_morph_fill_preserves_blob(
        self, cupy_morph: tuple[_MorphModule, _CupyModule]
    ) -> None:
        morph_mod, cp = cupy_morph
        img = cp.zeros((10, 10), dtype=cp.uint8)
        img[3:7, 3:7] = 1
        out = morph_mod.morph_fill(img, shape=(3, 3))
        assert tuple(out.shape) == (10, 10)

    def test_erode_preserves_border_touching_foreground(
        self, cupy_morph: tuple[_MorphModule, _CupyModule]
    ) -> None:
        """M-08: cv2.erode defaults to BORDER_REFLECT_101 which preserves
        foreground pixels touching the image border. The cupy backend used
        constant zero padding, which silently eroded those pixels away. After
        the fix, both backends agree on a thick border-touching block.
        """
        import cv2
        import numpy as np

        morph_mod, cp = cupy_morph
        # Solid block from row 0 (touches the top border) down to row 5.
        img_np = np.zeros((10, 10), dtype=np.uint8)
        img_np[0:6, 1:9] = 1
        kernel_np = np.ones((3, 3), dtype=np.uint8)

        cv2_eroded = cv2.erode(img_np, kernel_np, borderType=cv2.BORDER_REFLECT_101)
        cp_eroded = cp.asnumpy(
            morph_mod.erode(cp.asarray(img_np), cp.asarray(kernel_np))
        )

        # cv2 keeps the top row of the eroded interior; the buggy cupy backend
        # would zero it out because the zero-padding floods the min-window.
        assert cv2_eroded[0, 2:8].sum() > 0, "cv2 reference should preserve top row"
        assert np.array_equal(cp_eroded, cv2_eroded), (
            "cupy erode must match cv2 BORDER_REFLECT_101 behavior on "
            "border-touching foreground"
        )

    def test_dilate_erode_match_cv2_after_kernel_multiply_drop(
        self, cupy_morph: tuple[_MorphModule, _CupyModule]
    ) -> None:
        """M-09 parity: dropping the redundant `* kernel` factor (the kernel
        is always all-ones in the only call site, `morph_fill`) must not
        change `dilate` / `erode` output. Lock cupy output to cv2 reference
        for an all-ones kernel on a non-trivial pattern, so any future
        change that breaks parity (e.g. accidentally reintroducing a
        non-identity multiply) trips this test.
        """
        import cv2
        import numpy as np

        morph_mod, cp = cupy_morph
        rng = np.random.default_rng(42)
        img_np = rng.integers(0, 2, size=(32, 48), dtype=np.uint8)
        # Use an odd kernel size so cupy and cv2 agree on output shape;
        # the M-09 invariant under test is "dropping the all-ones multiply
        # leaves output bit-identical", which is independent of kernel
        # parity.
        kernel_np = np.ones((5, 5), dtype=np.uint8)

        cv2_dilated = cv2.dilate(img_np, kernel_np, borderType=cv2.BORDER_REFLECT_101)
        cv2_eroded = cv2.erode(img_np, kernel_np, borderType=cv2.BORDER_REFLECT_101)

        cp_dilated = cp.asnumpy(
            morph_mod.dilate(cp.asarray(img_np), cp.asarray(kernel_np))
        )
        cp_eroded = cp.asnumpy(
            morph_mod.erode(cp.asarray(img_np), cp.asarray(kernel_np))
        )

        assert np.array_equal(cp_dilated, cv2_dilated), (
            "cupy dilate must match cv2 dilate for an all-ones kernel "
            "(M-09: dropping `* kernel` is a no-op)"
        )
        assert np.array_equal(cp_eroded, cv2_eroded), (
            "cupy erode must match cv2 erode for an all-ones kernel "
            "(M-09: dropping `* kernel` is a no-op)"
        )

    def test_morph_fill_matches_cv2_on_border_blob(
        self, cupy_morph: tuple[_MorphModule, _CupyModule]
    ) -> None:
        """M-08 parity: morph_fill on a foreground blob touching the top edge
        should agree between cupy and cv2 backends."""
        import cv2
        import numpy as np

        morph_mod, cp = cupy_morph
        img_np = np.zeros((20, 20), dtype=np.uint8)
        img_np[0:8, 4:16] = 1  # block flush against top edge

        kernel_np = np.ones((3, 3), dtype=np.uint8)
        closed = cv2.morphologyEx(img_np, cv2.MORPH_CLOSE, kernel_np)
        cv2_out = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_np)

        cp_out = cp.asnumpy(morph_mod.morph_fill(cp.asarray(img_np), shape=(3, 3)))

        assert np.array_equal(cp_out, cv2_out), (
            "cupy morph_fill must match cv2 morphologyEx for border-touching content"
        )
