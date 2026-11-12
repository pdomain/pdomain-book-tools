from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pdomain_book_tools.geometry_correction import (
    CurvatureReport,
    DeskewResult,
    DewarpResult,
    GeometryTransform,
    PageSide,
    PageSideResult,
    TextlineDisparityDewarp,
)
from pdomain_book_tools.geometry_correction.pipeline import (
    GeometryPipeline,
    PipelineResult,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pdomain_book_tools.geometry_correction.protocols import (
        BBox,
        Dewarp,
        Recommended,
    )


class _Side:
    name = "supplied"

    def detect(
        self, image: np.ndarray, *, hint: PageSide | None = None
    ) -> PageSideResult:
        return PageSideResult(hint or PageSide.UNKNOWN, "right", 1.0, self.name)


class _Curv:
    def __init__(self, rec: Recommended) -> None:
        self.rec: Recommended = rec
        self.name = "fake"

    def score(
        self, image: np.ndarray, *, text_lines: Sequence[BBox] | None = None
    ) -> CurvatureReport:
        return CurvatureReport(0.0, self.rec, None, self.name)


class _Dewarp:
    name = "fake"
    called = False

    def estimate(
        self,
        image: np.ndarray,
        *,
        gutter_edge: str | None = None,
        text_lines: Sequence[BBox] | None = None,
    ) -> DewarpResult:
        _Dewarp.called = True
        return DewarpResult(GeometryTransform.identity(image.shape[:2]), 1.0, self.name)


class _Deskew:
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


def test_pipeline_skips_dewarp_when_curvature_says_flat() -> None:
    _Dewarp.called = False
    pipe = GeometryPipeline(
        page_side=_Side(),
        curvature=_Curv("deskew_only"),
        dewarp=_Dewarp(),
        deskew=_Deskew(),
    )
    img = np.zeros((20, 20), np.uint8)
    res = pipe.run(img, page_side_hint=PageSide.LEFT)
    assert isinstance(res, PipelineResult)
    assert _Dewarp.called is False
    assert res.page_side.side is PageSide.LEFT
    assert res.dewarp is None
    assert res.deskew is not None


def test_pipeline_runs_dewarp_when_curved() -> None:
    _Dewarp.called = False
    pipe = GeometryPipeline(
        page_side=_Side(),
        curvature=_Curv("dewarp"),
        dewarp=_Dewarp(),
        deskew=_Deskew(),
    )
    pipe.run(np.zeros((20, 20), np.uint8), page_side_hint=PageSide.LEFT)
    assert _Dewarp.called is True


class _GridDewarp:
    name = "fake_grid"

    def estimate(
        self,
        image: np.ndarray,
        *,
        gutter_edge: str | None = None,
        text_lines: Sequence[BBox] | None = None,
    ) -> DewarpResult:
        h, w = image.shape[:2]
        xs, ys = np.meshgrid(
            np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32)
        )
        return DewarpResult(
            GeometryTransform.grid(xs, ys + 1.0, (h, w)), 0.9, self.name
        )


def _run(rec: Recommended, dewarp: Dewarp | None) -> PipelineResult:
    pipe = GeometryPipeline(
        page_side=_Side(), curvature=_Curv(rec), dewarp=dewarp, deskew=_Deskew()
    )
    return pipe.run(np.zeros((20, 20), np.uint8))


def test_outcome_not_recommended_when_curvature_says_flat() -> None:
    assert _run("deskew_only", _Dewarp()).dewarp_outcome == "not_recommended"


def test_outcome_no_backend_when_dewarp_wanted_but_none_selected() -> None:
    res = _run("dewarp", None)
    assert res.dewarp is None
    assert res.dewarp_outcome == "no_backend"


def test_outcome_identity_no_op_when_backend_returns_identity() -> None:
    res = _run("dewarp", _Dewarp())
    assert res.dewarp is not None
    assert res.dewarp_outcome == "identity_no_op"


def test_outcome_identity_no_op_for_textline_backend_with_too_few_lines() -> None:
    res = _run("dewarp", TextlineDisparityDewarp())
    assert res.dewarp is not None
    assert res.dewarp.confidence == 0.0
    assert res.dewarp_outcome == "identity_no_op"


def test_outcome_applied_when_backend_returns_a_real_warp() -> None:
    assert _run("dewarp", _GridDewarp()).dewarp_outcome == "applied"
