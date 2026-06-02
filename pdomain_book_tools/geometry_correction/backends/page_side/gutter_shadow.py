"""Gutter-shadow page-side detector: infers binding edge from dark vertical band."""

from __future__ import annotations

from typing import TYPE_CHECKING

import cv2

from pdomain_book_tools.geometry_correction.protocols import PageSide, PageSideResult

if TYPE_CHECKING:
    import numpy as np

_SIDE_FOR_GUTTER: dict[str, PageSide] = {
    "right": PageSide.LEFT,
    "left": PageSide.RIGHT,
}


class GutterShadowPageSide:
    """Infer the gutter (binding) edge from a dark vertical band near a left/right edge.

    The gutter casts the darkest near-edge column band. We compare mean intensity of
    a thin strip on each side; the markedly darker side is the gutter. A caller hint,
    when given, overrides weak detections.
    """

    name = "gutter_shadow"

    def __init__(self, strip_frac: float = 0.06, min_contrast: float = 20.0) -> None:
        """Initialise with detection parameters."""
        self.strip_frac, self.min_contrast = strip_frac, min_contrast

    def detect(
        self, image: np.ndarray, *, hint: PageSide | None = None
    ) -> PageSideResult:
        """Detect which page side this is by looking for a dark binding-shadow band."""
        gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _h, w = gray.shape
        s = max(2, int(w * self.strip_frac))
        left_mean = float(gray[:, :s].mean())
        right_mean = float(gray[:, -s:].mean())
        contrast = abs(left_mean - right_mean)
        if contrast >= self.min_contrast:
            gutter: str = "left" if left_mean < right_mean else "right"
            conf = float(min(1.0, contrast / 128.0))
            return PageSideResult(_SIDE_FOR_GUTTER[gutter], gutter, conf, self.name)  # type: ignore[arg-type]
        # weak/no detection: fall back to hint
        if hint in (PageSide.LEFT, PageSide.RIGHT):
            gutter = "right" if hint is PageSide.LEFT else "left"
            return PageSideResult(hint, gutter, 0.3, self.name)  # type: ignore[arg-type]
        return PageSideResult(PageSide.UNKNOWN, "none", 0.0, self.name)
