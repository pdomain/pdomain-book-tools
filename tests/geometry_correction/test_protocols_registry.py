from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pdomain_book_tools.geometry_correction.protocols import (
    CurvatureReport,
    DeskewResult,
    DewarpResult,
    PageSide,
    PageSideResult,
)
from pdomain_book_tools.geometry_correction.transforms import GeometryTransform

if TYPE_CHECKING:
    from collections.abc import Sequence

    import numpy as np

    from pdomain_book_tools.geometry_correction.protocols import BBox


def test_pageside_enum_members() -> None:
    assert {m.name for m in PageSide} == {"LEFT", "RIGHT", "SINGLE", "UNKNOWN"}


def test_result_dataclasses_hold_transform() -> None:
    t = GeometryTransform.identity((10, 10))
    d = DeskewResult(angle_degrees=1.5, confidence=0.9, transform=t, method="x")
    assert d.angle_degrees == 1.5
    assert d.transform is t
    w = DewarpResult(transform=t, confidence=0.5, method="y")
    assert w.transform is t
    ps = PageSideResult(
        side=PageSide.LEFT, gutter_edge="right", confidence=0.8, method="z"
    )
    assert ps.gutter_edge == "right"
    cr = CurvatureReport(
        flatness=0.1, recommended="deskew_only", per_line_residuals=None, method="q"
    )
    assert cr.recommended == "deskew_only"


# --- Task 4: registry ---

from pdomain_book_tools.geometry_correction import Deskew  # noqa: E402
from pdomain_book_tools.geometry_correction.registry import (  # noqa: E402
    available,
    get_deskew,
    register_deskew,
)


class _FakeDeskew:
    name = "fake"

    def estimate(
        self,
        image: np.ndarray,
        *,
        page_side: PageSide | None = None,
        text_lines: Sequence[BBox] | None = None,
    ) -> DeskewResult:
        return DeskewResult(
            0.0, 1.0, GeometryTransform.identity(image.shape[:2]), self.name
        )


def test_register_and_get_roundtrip() -> None:
    register_deskew("fake", _FakeDeskew)
    inst = get_deskew("fake")
    assert isinstance(inst, Deskew)  # satisfies the Protocol
    assert "fake" in available("deskew")


def test_get_unknown_raises() -> None:
    with pytest.raises(KeyError):
        get_deskew("nope-not-registered")


# --- Task 13: defaults ---


def test_builtin_backends_are_registered() -> None:
    from pdomain_book_tools.geometry_correction import registry

    registry.ensure_defaults()
    assert "projection" in registry.available("deskew")
    assert "sbrunner" in registry.available("deskew")
    assert "image_based" in registry.available("curvature")
    assert "supplied" in registry.available("page_side")
    assert "gutter_shadow" in registry.available("page_side")
    assert "uvdoc" in registry.available("dewarp")  # registered even if extra absent


def test_default_pipeline_builds_and_runs_on_flat_page() -> None:
    import cv2
    import numpy as np

    from pdomain_book_tools.geometry_correction.defaults import default_pipeline

    img = np.full((200, 300), 255, np.uint8)
    for y in range(30, 170, 14):
        cv2.rectangle(img, (40, y), (260, y + 4), 0, -1)
    res = default_pipeline().run(img)
    assert res.image.shape == img.shape  # flat page: deskew-only, shape preserved
