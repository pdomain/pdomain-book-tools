"""TextlineDisparityDewarp — the scanned-page Dewarp backend (clean-room Leptonica).

Orchestrates: detect text lines (via a TextlineDetector seam) -> cull short lines ->
order-2 baseline fit -> dense vertical + horizontal disparity maps -> grid
GeometryTransform. Fewer than ``min_textlines`` survivors => identity + confidence 0
(the regime gate / caller then defers to UVDoc or skips dewarp).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pdomain_book_tools.geometry_correction.detectors.textline import (
    MorphCentroidDetector,
    TextlineDetector,
)
from pdomain_book_tools.geometry_correction.protocols import DewarpResult, GutterEdge
from pdomain_book_tools.geometry_correction.transforms import GeometryTransform

if TYPE_CHECKING:
    import numpy as np

DEFAULT_MIN_TEXTLINES = 15  # Leptonica DefaultMinLines (dewarp1.c:426)


class TextlineDisparityDewarp:
    """Scanned-page dewarp: Leptonica-faithful morph-centroid textline disparity."""

    name = "textline_disparity"

    def __init__(
        self,
        *,
        detector: TextlineDetector | None = None,
        min_textlines: int = DEFAULT_MIN_TEXTLINES,
        prefer_gpu: bool = False,
        binarization: str = "otsu",
        binarization_params: dict[str, Any] | None = None,
    ) -> None:
        """Initialise the backend with an optional custom detector.

        When ``detector`` is ``None``, a :class:`MorphCentroidDetector` is
        constructed using ``prefer_gpu``, ``binarization``, and
        ``binarization_params``. When an explicit ``detector`` is provided it
        is used as-is and the binarization arguments are ignored.
        """
        self.detector = detector or MorphCentroidDetector(
            prefer_gpu=prefer_gpu,
            binarization=binarization,
            binarization_params=binarization_params,
        )
        self.min_textlines = min_textlines
        self.prefer_gpu = prefer_gpu
        self.binarization = binarization
        self.binarization_params = binarization_params

    def _module(self) -> Any:
        """Return the appropriate textline_dewarp module (cv2 or cupy)."""
        if self.prefer_gpu:
            from pdomain_book_tools.image_processing.cupy_processing._cupy_compat import (
                cupy_available,
            )

            if cupy_available():
                import importlib

                return importlib.import_module(
                    "pdomain_book_tools.image_processing.cupy_processing.textline_dewarp"
                )
        from pdomain_book_tools.image_processing.cv2_processing import (
            textline_dewarp as ctd,
        )

        return ctd

    def estimate(
        self,
        image: np.ndarray,
        *,
        gutter_edge: GutterEdge | None = None,
        text_lines: Any = None,
    ) -> DewarpResult:
        """Estimate a dewarp correction grid from detected textline baselines."""
        h, w = image.shape[:2]
        mod = self._module()
        lines = mod.remove_short_lines(self.detector.detect(image, page_width=w))
        if len(lines) < self.min_textlines:
            return DewarpResult(
                transform=GeometryTransform.identity((h, w)),
                confidence=0.0,
                method=self.name,
            )
        coeffs = mod.fit_baselines(lines)
        map_x, map_y = mod.build_disparity_maps(
            lines, coeffs, (h, w), gutter_edge=gutter_edge or "none"
        )
        confidence = float(min(1.0, len(lines) / max(self.min_textlines, 1)))
        return DewarpResult(
            transform=GeometryTransform.grid(map_x, map_y, (h, w)),
            confidence=confidence,
            method=self.name,
        )
