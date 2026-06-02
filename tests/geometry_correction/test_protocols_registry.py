from pdomain_book_tools.geometry_correction.protocols import (
    CurvatureReport,
    DeskewResult,
    DewarpResult,
    PageSide,
    PageSideResult,
)
from pdomain_book_tools.geometry_correction.transforms import GeometryTransform


def test_pageside_enum_members():
    assert {m.name for m in PageSide} == {"LEFT", "RIGHT", "SINGLE", "UNKNOWN"}


def test_result_dataclasses_hold_transform():
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
