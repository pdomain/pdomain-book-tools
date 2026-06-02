from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Sequence

    import numpy as np

    from .transforms import GeometryTransform

GutterEdge = Literal["left", "right", "none"]
Recommended = Literal["none", "deskew_only", "dewarp"]
BBox = tuple[int, int, int, int]


class PageSide(Enum):
    """Which side of a two-page spread this page occupies."""

    LEFT = "left"
    RIGHT = "right"
    SINGLE = "single"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DeskewResult:
    """Result from a deskew backend."""

    angle_degrees: float
    confidence: float
    transform: GeometryTransform
    method: str


@dataclass(frozen=True)
class DewarpResult:
    """Result from a dewarp backend."""

    transform: GeometryTransform
    confidence: float
    method: str


@dataclass(frozen=True)
class PageSideResult:
    """Result from a page-side detector."""

    side: PageSide
    gutter_edge: GutterEdge
    confidence: float
    method: str


@dataclass(frozen=True)
class CurvatureReport:
    """Curvature score and dewarp recommendation from a curvature detector."""

    flatness: float
    recommended: Recommended
    per_line_residuals: list[float] | None
    method: str


@runtime_checkable
class Deskew(Protocol):
    """Protocol for deskew backends."""

    name: str

    def estimate(
        self,
        image: np.ndarray,
        *,
        page_side: PageSide | None = None,
        text_lines: Sequence[BBox] | None = None,
    ) -> DeskewResult:
        """Estimate the skew angle and return a corrective transform."""
        ...


@runtime_checkable
class Dewarp(Protocol):
    """Protocol for dewarp backends."""

    name: str

    def estimate(
        self,
        image: np.ndarray,
        *,
        gutter_edge: GutterEdge | None = None,
        text_lines: Sequence[BBox] | None = None,
    ) -> DewarpResult:
        """Estimate a dewarp correction grid and return a corrective transform."""
        ...


@runtime_checkable
class PageSideDetector(Protocol):
    """Protocol for page-side detector backends."""

    name: str

    def detect(
        self, image: np.ndarray, *, hint: PageSide | None = None
    ) -> PageSideResult:
        """Detect which side of the spread this page is on."""
        ...


@runtime_checkable
class CurvatureDetector(Protocol):
    """Protocol for curvature detector backends."""

    name: str

    def score(
        self,
        image: np.ndarray,
        *,
        text_lines: Sequence[BBox] | None = None,
    ) -> CurvatureReport:
        """Score the page curvature and recommend a correction strategy."""
        ...
