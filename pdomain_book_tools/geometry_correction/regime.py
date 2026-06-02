"""Regime detector: classify a single page into flat | flat_curl | oblique.

Signals (spec section 5): aggregate baseline curvature (mean |c2| of detected text
lines, scaled to a dimensionless page-sag) and page-edge convergence (angle between
line fits to the left/right content edges). The pipeline maps regime -> backend:
flat -> deskew-only, flat_curl -> textline_disparity, oblique -> UVDoc. Callers may
override the routing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import cv2
import numpy as np

from pdomain_book_tools.image_processing.cv2_processing import textline_dewarp as _td

Regime = Literal["flat", "flat_curl", "oblique"]


@dataclass(frozen=True)
class RegimeReport:
    """Regime classification result with supporting signal values."""

    regime: Regime
    baseline_sag: float  # dimensionless: mean |c2| * width^2 / height
    edge_convergence: float  # radians between left & right content-edge directions
    method: str


class RegimeDetector:
    """Classify a page image into flat / flat_curl / oblique."""

    name = "edge_curvature"

    def __init__(
        self, *, curl_sag: float = 0.04, oblique_radians: float = 0.10
    ) -> None:
        """Initialise with classification thresholds."""
        self.curl_sag = curl_sag
        self.oblique_radians = oblique_radians

    def _baseline_sag(self, page: np.ndarray, w: int, h: int) -> float:
        """Compute dimensionless baseline sag from mean |c2| of detected lines."""
        lines = _td.remove_short_lines(_td.detect_textlines(page, page_width=w))
        if len(lines) < 3:
            return 0.0
        coeffs = _td.fit_baselines(lines)
        return float(np.mean([abs(c.c2) for c in coeffs]) * (w**2) / h)

    def _edge_convergence(self, page: np.ndarray, w: int, h: int) -> float:
        """Compute angle between left and right content-edge directions."""
        gray = page if page.ndim == 2 else cv2.cvtColor(page, cv2.COLOR_BGR2GRAY)
        _, fg = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        rows, lefts, rights = [], [], []
        for r in range(0, h, max(1, h // 60)):
            cols = np.nonzero(fg[r])[0]
            if cols.size < 2:
                continue
            rows.append(r)
            lefts.append(cols[0])
            rights.append(cols[-1])
        if len(rows) < 5:
            return 0.0
        rows_a = np.array(rows, np.float64)
        sl = np.polyfit(rows_a, np.array(lefts, np.float64), 1)[0]  # dx/dy left edge
        sr = np.polyfit(rows_a, np.array(rights, np.float64), 1)[0]  # dx/dy right edge
        # parallel edges: sl == sr (same lean). Convergence: opposite signs / large gap.
        return float(abs(np.arctan(sl) - np.arctan(sr)))

    def classify(self, image: np.ndarray) -> RegimeReport:
        """Classify the page image into flat / flat_curl / oblique."""
        h, w = image.shape[:2]
        conv = self._edge_convergence(image, w, h)
        sag = self._baseline_sag(image, w, h)
        if conv >= self.oblique_radians:
            regime: Regime = "oblique"
        elif sag >= self.curl_sag:
            regime = "flat_curl"
        else:
            regime = "flat"
        return RegimeReport(
            regime=regime, baseline_sag=sag, edge_convergence=conv, method=self.name
        )


_REGIME_BACKEND: dict[Regime, str | None] = {
    "flat": None,
    "flat_curl": "textline_disparity",
    "oblique": "uvdoc",
}


def dewarp_for_regime(regime: Regime, *, override: str | None = None) -> str | None:
    """Map a regime to a dewarp backend name (caller override wins)."""
    if override is not None:
        return override
    return _REGIME_BACKEND[regime]
