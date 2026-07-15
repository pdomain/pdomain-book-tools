from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar, overload

import numpy as np
import pytest

if TYPE_CHECKING:
    import numpy.typing as npt

_ScalarT = TypeVar("_ScalarT", bound=np.generic)


class _CupyModule(Protocol):
    """Structural stand-in for the ``cupy`` module returned by the
    ``cupy_module`` fixture (see ``tests/conftest.py``) — narrows the
    otherwise-untyped fixture return to the subset of cupy's API this file
    calls, mirroring the real signatures in ``typings/cupy/__init__.pyi``.
    """

    def asarray(self, a: object) -> npt.NDArray[np.generic]: ...
    @overload
    def asnumpy(self, a: npt.NDArray[_ScalarT]) -> npt.NDArray[_ScalarT]: ...
    @overload
    def asnumpy(self, a: object) -> npt.NDArray[np.generic]: ...


def _lined_page(
    h: int = 900, w: int = 700, n_lines: int = 14, top: int = 90, gap: int = 55
) -> npt.NDArray[np.uint8]:
    import cv2

    img = np.zeros((h, w), np.uint8)
    for i in range(n_lines):
        y = top + i * gap
        for x0 in range(60, w - 60, 70):
            cv2.rectangle(img, (x0, y), (x0 + 50, y + 10), 255, -1)
    return img


def _gradient_page(
    h: int = 900, w: int = 700, n_lines: int = 14, top: int = 90, gap: int = 55
) -> npt.NDArray[np.uint8]:
    """Dark text on a smoothly-varying light background (illumination gradient)."""
    bg = np.linspace(240, 120, w, dtype=np.float32)
    img = np.tile(bg, (h, 1)).astype(np.uint8)
    for i in range(n_lines):
        y = top + i * gap
        for x0 in range(60, w - 60, 70):
            img[y : y + 10, x0 : x0 + 50] = 30
    return img


@pytest.mark.gpu
@pytest.mark.cupy
class TestCuPyTextlineDewarpParity:
    def test_detect_textlines_parity_with_numpy(self, cupy_module: _CupyModule) -> None:
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing import (
            textline_dewarp as gtd,
        )
        from pdomain_book_tools.image_processing.cv2_processing import (
            textline_dewarp as ctd,
        )

        page = _lined_page()
        cpu_lines = ctd.detect_textlines(page, page_width=page.shape[1])
        gpu_lines = gtd.detect_textlines(cp.asarray(page), page_width=page.shape[1])
        assert abs(len(gpu_lines) - len(cpu_lines)) <= 1
        cpu_centers = sorted(float(l.ys.mean()) for l in cpu_lines)
        gpu_centers = sorted(float(cp.asnumpy(l.ys).mean()) for l in gpu_lines)
        n = min(len(cpu_centers), len(gpu_centers))
        np.testing.assert_allclose(gpu_centers[:n], cpu_centers[:n], atol=3.0)

    def test_full_map_parity_with_numpy(self, cupy_module: _CupyModule) -> None:
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing import (
            textline_dewarp as gtd,
        )
        from pdomain_book_tools.image_processing.cv2_processing import (
            textline_dewarp as ctd,
        )

        page = _lined_page(h=1000, w=760, n_lines=14, top=90, gap=60)
        h, w = page.shape
        c_lines = ctd.remove_short_lines(ctd.detect_textlines(page, page_width=w))
        c_mx, c_my = ctd.build_disparity_maps(
            c_lines, ctd.fit_baselines(c_lines), (h, w), gutter_edge="none"
        )

        g_lines = gtd.remove_short_lines(
            gtd.detect_textlines(cp.asarray(page), page_width=w)
        )
        # gtd.build_disparity_maps declares `tuple[Any, Any]` (GPU path returns
        # CuPy arrays through an Any-typed boundary); the real runtime values
        # are float64 disparity maps, matching the CPU counterpart's contract.
        g_mx: npt.NDArray[np.float64]
        g_my: npt.NDArray[np.float64]
        g_mx, g_my = gtd.build_disparity_maps(
            g_lines, gtd.fit_baselines(g_lines), (h, w), gutter_edge="none"
        )
        np.testing.assert_allclose(cp.asnumpy(g_mx), c_mx, atol=2.0)
        np.testing.assert_allclose(cp.asnumpy(g_my), c_my, atol=2.0)

    def test_detect_textlines_sauvola_gpu_close_to_cpu(
        self, cupy_module: _CupyModule
    ) -> None:
        """CuPy detect_textlines with binarization='sauvola' line centers stay close to cv2."""
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing import (
            textline_dewarp as gtd,
        )
        from pdomain_book_tools.image_processing.cv2_processing import (
            textline_dewarp as ctd,
        )

        page = _gradient_page()
        cpu_lines = ctd.detect_textlines(
            page, page_width=page.shape[1], binarization="sauvola"
        )
        gpu_lines = gtd.detect_textlines(
            cp.asarray(page), page_width=page.shape[1], binarization="sauvola"
        )
        # Both backends should find a reasonable number of lines on the gradient page
        assert len(cpu_lines) >= 6
        assert len(gpu_lines) >= 6
        # Line centers should be within 5 px of each other (same method, same image)
        n = min(len(cpu_lines), len(gpu_lines))
        cpu_centers = sorted(float(ln.ys.mean()) for ln in cpu_lines)[:n]
        gpu_centers = sorted(float(cp.asnumpy(ln.ys).mean()) for ln in gpu_lines)[:n]
        np.testing.assert_allclose(gpu_centers, cpu_centers, atol=5.0)
