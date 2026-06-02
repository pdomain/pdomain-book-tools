"""Geometry correction package: deskew, dewarp, curvature gate, page-side detection."""

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
from .transforms import GeometryTransform

__all__ = [
    "CurvatureDetector",
    "CurvatureReport",
    "Deskew",
    "DeskewResult",
    "Dewarp",
    "DewarpResult",
    "GeometryTransform",
    "PageSide",
    "PageSideDetector",
    "PageSideResult",
]
