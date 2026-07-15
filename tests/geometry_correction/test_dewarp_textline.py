from __future__ import annotations

from typing import TYPE_CHECKING

import cv2
import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


def test_v1_geometry_surface_present() -> None:
    """This plan gates behind the v1 geometry_correction package. If this fails,
    implement docs/plans/2026-06-02-geometry-correction-book-tools.md first."""
    from pdomain_book_tools.geometry_correction import registry
    from pdomain_book_tools.geometry_correction.protocols import DewarpResult
    from pdomain_book_tools.geometry_correction.transforms import GeometryTransform

    # grid + identity factories exist (v1 Tasks 1-2)
    h, w = 8, 10
    mx, my = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    grid = GeometryTransform.grid(mx, my, (h, w))
    assert grid.kind == "grid"
    ident = GeometryTransform.identity((h, w))
    out = ident.apply(np.zeros((h, w), np.uint8))
    assert out.shape == (h, w)

    # dewarp registry hooks exist (v1 Task 4)
    assert hasattr(registry, "register_dewarp")
    assert hasattr(registry, "get_dewarp")
    assert callable(registry.ensure_defaults)

    # result dataclass shape (v1 Task 3)
    res = DewarpResult(transform=ident, confidence=1.0, method="probe")
    assert res.confidence == 1.0


def _lined_gray(
    h: int = 1000, w: int = 760, n_lines: int = 16, top: int = 90, gap: int = 58
) -> NDArray[np.uint8]:
    img = np.full((h, w), 255, np.uint8)
    for i in range(n_lines):
        y = top + i * gap
        for x0 in range(60, w - 60, 70):
            cv2.rectangle(img, (x0, y), (x0 + 50, y + 10), 0, -1)
    return img


def test_backend_satisfies_protocol_and_builds_grid() -> None:
    from pdomain_book_tools.geometry_correction import Dewarp, DewarpResult
    from pdomain_book_tools.geometry_correction.backends.dewarp.textline import (
        TextlineDisparityDewarp,
    )

    backend = TextlineDisparityDewarp()
    assert backend.name == "textline_disparity"
    assert isinstance(backend, Dewarp)
    res = backend.estimate(_lined_gray(), gutter_edge="right")
    assert isinstance(res, DewarpResult)
    assert res.method == "textline_disparity"
    assert res.transform.kind == "grid"
    assert res.confidence > 0.0
    assert res.transform.map_x is not None
    assert res.transform.map_x.shape == (1000, 760)


def test_backend_sparse_page_falls_back_to_identity() -> None:
    from pdomain_book_tools.geometry_correction.backends.dewarp.textline import (
        TextlineDisparityDewarp,
    )

    backend = TextlineDisparityDewarp()
    sparse = _lined_gray(n_lines=4, top=200, gap=120)  # < DefaultMinLines (15)
    res = backend.estimate(sparse)
    assert res.transform.kind == "identity"
    assert res.confidence == 0.0


def test_backend_min_textlines_default_is_leptonica_15() -> None:
    from pdomain_book_tools.geometry_correction.backends.dewarp.textline import (
        TextlineDisparityDewarp,
    )

    assert TextlineDisparityDewarp().min_textlines == 15


def test_textline_backend_registered_as_default() -> None:
    from pdomain_book_tools.geometry_correction import Dewarp, registry

    registry.ensure_defaults()
    assert "textline_disparity" in registry.available("dewarp")
    backend = registry.get_dewarp("textline_disparity")
    assert isinstance(backend, Dewarp)
    assert backend.name == "textline_disparity"


def test_scanned_pipeline_routes_flat_curl_to_textline() -> None:
    from pdomain_book_tools.geometry_correction.defaults import scanned_pipeline

    pipe = scanned_pipeline()
    # the flat_curl regime resolves to the textline backend in the routing map
    assert "textline_disparity" in pipe.dewarp_backends
    assert pipe.regime is not None


# ---------------------------------------------------------------------------
# Binarization-parameter wiring — TextlineDisparityDewarp
# ---------------------------------------------------------------------------


def _gradient_gray(
    h: int = 1000, w: int = 760, n_lines: int = 16, top: int = 90, gap: int = 58
) -> NDArray[np.uint8]:
    """Dark-text-on-light-background page with an illumination gradient (for binarize tests)."""
    bg = np.linspace(240, 120, w, dtype=np.float32)
    img = np.tile(bg, (h, 1)).astype(np.uint8)
    for i in range(n_lines):
        y = top + i * gap
        for x0 in range(60, w - 60, 70):
            img[y : y + 10, x0 : x0 + 50] = 30
    return img


def test_backend_default_binarization_is_otsu() -> None:
    from pdomain_book_tools.geometry_correction.backends.dewarp.textline import (
        TextlineDisparityDewarp,
    )

    backend = TextlineDisparityDewarp()
    assert backend.binarization == "otsu"
    assert backend.binarization_params is None


def test_backend_sauvola_returns_valid_result() -> None:
    """TextlineDisparityDewarp(binarization='sauvola').estimate() must not raise."""
    from pdomain_book_tools.geometry_correction.backends.dewarp.textline import (
        TextlineDisparityDewarp,
    )

    backend = TextlineDisparityDewarp(binarization="sauvola")
    page = _gradient_gray()
    res = backend.estimate(page)
    # Either a grid (enough lines) or identity+conf0 (too few after gradient binarization)
    assert res.transform.kind in {"grid", "identity"}
    assert res.confidence >= 0.0


def test_backend_injected_detector_ignores_binarization_params() -> None:
    """When a detector is injected explicitly, it's used as-is regardless of binarization."""

    from pdomain_book_tools.geometry_correction.backends.dewarp.textline import (
        TextlineDisparityDewarp,
    )
    from pdomain_book_tools.geometry_correction.detectors.textline import (
        MorphCentroidDetector,
    )

    injected = MorphCentroidDetector(binarization="niblack")
    backend = TextlineDisparityDewarp(detector=injected, binarization="sauvola")
    # The injected detector takes precedence; the backend wraps it unchanged
    assert backend.detector is injected
    assert isinstance(backend.detector, MorphCentroidDetector)
    assert backend.detector.binarization == "niblack"  # not overridden to "sauvola"
