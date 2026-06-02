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
from pdomain_book_tools.geometry_correction.regime import (
    RegimeReport,
    dewarp_for_regime,
)


def test_dewarp_for_regime_routing_table():
    assert dewarp_for_regime("flat") is None
    assert dewarp_for_regime("flat_curl") == "textline_disparity"
    assert dewarp_for_regime("oblique") == "uvdoc"
    # caller override wins
    assert dewarp_for_regime("flat_curl", override="uvdoc") == "uvdoc"


class _Side:
    name = "supplied"

    def detect(self, image, *, hint=None):
        return PageSideResult(hint or PageSide.UNKNOWN, "right", 1.0, self.name)


class _Curv:
    name = "fake"

    def score(self, image, *, text_lines=None):
        return CurvatureReport(0.9, "dewarp", None, self.name)


class _Regime:
    def __init__(self, regime):
        self._r = regime

    def classify(self, image):
        return RegimeReport(self._r, 0.0, 0.0, "fake")


class _NamedDewarp:
    def __init__(self, name):
        self.name = name
        self.called = False

    def estimate(self, image, *, gutter_edge=None, text_lines=None):
        self.called = True
        return DewarpResult(GeometryTransform.identity(image.shape[:2]), 1.0, self.name)


class _Deskew:
    name = "fake"

    def estimate(self, image, *, page_side=None, text_lines=None):
        return DeskewResult(
            0.0, 1.0, GeometryTransform.identity(image.shape[:2]), self.name
        )


def test_pipeline_routes_flat_curl_to_textline_backend():
    textline = _NamedDewarp("textline_disparity")
    uvdoc = _NamedDewarp("uvdoc")
    pipe = GeometryPipeline(
        page_side=_Side(),
        curvature=_Curv(),
        deskew=_Deskew(),
        dewarp_backends={"textline_disparity": textline, "uvdoc": uvdoc},
        regime=_Regime("flat_curl"),
    )
    res = pipe.run(np.zeros((40, 40), np.uint8), page_side_hint=PageSide.LEFT)
    assert isinstance(res, PipelineResult)
    assert textline.called is True
    assert uvdoc.called is False
    assert res.regime == "flat_curl"


def test_pipeline_routes_oblique_to_uvdoc():
    textline = _NamedDewarp("textline_disparity")
    uvdoc = _NamedDewarp("uvdoc")
    pipe = GeometryPipeline(
        page_side=_Side(),
        curvature=_Curv(),
        deskew=_Deskew(),
        dewarp_backends={"textline_disparity": textline, "uvdoc": uvdoc},
        regime=_Regime("oblique"),
    )
    pipe.run(np.zeros((40, 40), np.uint8))
    assert uvdoc.called is True
    assert textline.called is False
