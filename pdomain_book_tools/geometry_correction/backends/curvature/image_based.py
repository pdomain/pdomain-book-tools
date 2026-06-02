"""Image-based curvature gate: measures text-row bow to recommend dewarp vs deskew."""

from __future__ import annotations

from typing import TYPE_CHECKING

import cv2
import numpy as np

from pdomain_book_tools.geometry_correction.protocols import CurvatureReport

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pdomain_book_tools.geometry_correction.protocols import BBox


class ImageBasedCurvature:
    """Estimate page curl from how 'bowed' text rows are.

    For each detected text row we fit its dark-pixel y-position as a function of x;
    a flat row is a horizontal line, a curled row bows. The normalized mean of the
    per-row vertical spans is the flatness score (0 flat .. 1 strongly curled).
    """

    name = "image_based"

    def __init__(
        self, dewarp_threshold: float = 0.5, deskew_threshold: float = 0.12
    ) -> None:
        """Initialise with threshold values for recommendation decisions."""
        self.dewarp_threshold = dewarp_threshold
        self.deskew_threshold = deskew_threshold

    def score(
        self,
        image: np.ndarray,
        *,
        text_lines: Sequence[BBox] | None = None,
    ) -> CurvatureReport:
        """Score the page curvature and recommend a correction strategy."""
        gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        h, w = bw.shape
        # collapse into horizontal bands, then per band measure the vertical spread
        # of dark pixels across columns (a bowed row spreads vertically).
        residuals: list[float] = []
        band = max(8, h // 30)
        for top in range(0, h - band, band):
            strip = bw[top : top + band]
            ys, xs = np.nonzero(strip)
            if xs.size < w * 0.2:  # not a text band
                continue
            # centroid y per column bucket
            buckets = np.clip((xs / w * 10).astype(int), 0, 9)
            centers = [
                ys[buckets == b].mean() for b in range(10) if np.any(buckets == b)
            ]
            if len(centers) >= 5:
                residuals.append(float(np.max(centers) - np.min(centers)))
        if not residuals:
            return CurvatureReport(0.0, "deskew_only", [], self.name)
        flatness = float(np.clip(np.mean(residuals) / band, 0.0, 1.0))
        if flatness >= self.dewarp_threshold:
            rec = "dewarp"
        elif flatness >= self.deskew_threshold:
            rec = "deskew_only"
        else:
            rec = "none"
        return CurvatureReport(
            flatness=flatness,
            recommended=rec,
            per_line_residuals=residuals,
            method=self.name,
        )
