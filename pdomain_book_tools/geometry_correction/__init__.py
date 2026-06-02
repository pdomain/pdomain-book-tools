"""Geometry correction package: deskew, dewarp, curvature gate, page-side detection."""

from .backends.dewarp.textline import TextlineDisparityDewarp
from .detectors.textline import MorphCentroidDetector, TextlineDetector
from .protocols import (
    CurvatureDetector,
    CurvatureReport,
    Deskew,
    DeskewResult,
    Dewarp,
    DewarpResult,
    PageSide,
    PageSideDetector,
    PageSideResult,
)
from .regime import RegimeDetector, RegimeReport, dewarp_for_regime
from .transforms import GeometryTransform

__all__ = [
    "CurvatureDetector",
    "CurvatureReport",
    "Deskew",
    "DeskewResult",
    "Dewarp",
    "DewarpResult",
    "GeometryTransform",
    "MorphCentroidDetector",
    "PageSide",
    "PageSideDetector",
    "PageSideResult",
    "RegimeDetector",
    "RegimeReport",
    "TextlineDetector",
    "TextlineDisparityDewarp",
    "dewarp_for_regime",
]
