import numpy as np

from pdomain_book_tools.geometry_correction import (
    CurvatureReport,
    DeskewResult,
    DewarpResult,
    GeometryTransform,
    PageSide,
    PageSideResult,
)
from pdomain_book_tools.geometry_correction.pipeline import (
    GeometryPipeline,
    PipelineResult,
)


class _Side:
    name = "supplied"

    def detect(self, image, *, hint=None):
        return PageSideResult(hint or PageSide.UNKNOWN, "right", 1.0, self.name)


class _Curv:
    def __init__(self, rec):
        self.rec = rec
        self.name = "fake"

    def score(self, image, *, text_lines=None):
        return CurvatureReport(0.0, self.rec, None, self.name)


class _Dewarp:
    name = "fake"
    called = False

    def estimate(self, image, *, gutter_edge=None, text_lines=None):
        _Dewarp.called = True
        return DewarpResult(GeometryTransform.identity(image.shape[:2]), 1.0, self.name)


class _Deskew:
    name = "fake"

    def estimate(self, image, *, page_side=None, text_lines=None):
        return DeskewResult(
            0.0, 1.0, GeometryTransform.identity(image.shape[:2]), self.name
        )


def test_pipeline_skips_dewarp_when_curvature_says_flat():
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


def test_pipeline_runs_dewarp_when_curved():
    _Dewarp.called = False
    pipe = GeometryPipeline(
        page_side=_Side(),
        curvature=_Curv("dewarp"),
        dewarp=_Dewarp(),
        deskew=_Deskew(),
    )
    pipe.run(np.zeros((20, 20), np.uint8), page_side_hint=PageSide.LEFT)
    assert _Dewarp.called is True
