"""Reference pipeline: page-side -> curvature gate -> (dewarp) -> deskew (last)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

    import numpy as np

    from .protocols import (
        BBox,
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


@dataclass(frozen=True)
class PipelineResult:
    """Holds the fully corrected image and all intermediate results."""

    image: np.ndarray
    page_side: PageSideResult
    curvature: CurvatureReport
    dewarp: DewarpResult | None
    deskew: DeskewResult | None
    regime: str | None = None


class GeometryPipeline:
    """Reference sequence: page-side -> curvature gate -> (dewarp) -> deskew (last).

    Dewarp selection: if a ``regime`` detector + ``dewarp_backends`` map are given,
    the regime routes to a named backend (caller may force one via
    ``dewarp_override``). Otherwise the v1 single ``dewarp`` is used when the
    curvature gate recommends it.
    """

    def __init__(
        self,
        *,
        page_side: PageSideDetector,
        curvature: CurvatureDetector,
        deskew: Deskew,
        dewarp: Dewarp | None = None,
        dewarp_backends: dict[str, Any] | None = None,
        regime: Any | None = None,
        dewarp_override: str | None = None,
    ) -> None:
        """Initialise the pipeline with backend instances."""
        self.page_side = page_side
        self.curvature = curvature
        self.deskew = deskew
        self.dewarp = dewarp
        self.dewarp_backends: dict[str, Any] = dewarp_backends or {}
        self.regime = regime
        self.dewarp_override = dewarp_override

    def _select_dewarp(self, image: np.ndarray) -> tuple[Any | None, str | None]:
        """Return (backend_or_None, regime_or_None)."""
        if self.regime is not None and self.dewarp_backends:
            from .regime import dewarp_for_regime

            regime = self.regime.classify(image).regime
            name = dewarp_for_regime(regime, override=self.dewarp_override)
            return (self.dewarp_backends.get(name) if name else None), regime
        return self.dewarp, None

    def run(
        self,
        image: np.ndarray,
        *,
        page_side_hint: PageSide | None = None,
        text_lines: Sequence[BBox] | None = None,
    ) -> PipelineResult:
        """Run the full geometry-correction pipeline and return the result."""
        side = self.page_side.detect(image, hint=page_side_hint)
        curv = self.curvature.score(image, text_lines=text_lines)
        backend, regime = self._select_dewarp(image)
        current = image
        dewarp_res = None
        if curv.recommended == "dewarp" and backend is not None:
            dewarp_res = backend.estimate(
                current, gutter_edge=side.gutter_edge, text_lines=text_lines
            )
            current = dewarp_res.transform.apply(current)
        deskew_res = None
        if curv.recommended in ("deskew_only", "dewarp"):
            deskew_res = self.deskew.estimate(
                current, page_side=side.side, text_lines=text_lines
            )
            current = deskew_res.transform.apply(current)
        return PipelineResult(current, side, curv, dewarp_res, deskew_res, regime)
