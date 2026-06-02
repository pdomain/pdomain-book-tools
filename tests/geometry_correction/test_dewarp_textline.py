import numpy as np


def test_v1_geometry_surface_present():
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
