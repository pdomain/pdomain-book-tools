"""Hough-transform skew estimation via the ``deskew`` PyPI package (scikit-image)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import cv2
from deskew import determine_skew

from pdomain_book_tools.geometry_correction.protocols import DeskewResult
from pdomain_book_tools.geometry_correction.transforms import GeometryTransform

if TYPE_CHECKING:
    from collections.abc import Sequence

    import numpy as np

    from pdomain_book_tools.geometry_correction.protocols import BBox, PageSide


class SbrunnerDeskew:
    """Hough-transform skew estimate via the ``deskew`` PyPI package (scikit-image)."""

    name = "sbrunner"

    def estimate(
        self,
        image: np.ndarray,
        *,
        page_side: PageSide | None = None,
        text_lines: Sequence[BBox] | None = None,
    ) -> DeskewResult:
        """Estimate the skew angle using Hough-transform-based line detection."""
        gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        raw = determine_skew(gray)  # degrees; may be None on blank input
        # determine_skew returns the correction angle (negative of the skew).
        # We report the skew angle (positive = counter-clockwise tilt).
        correction = 0.0 if raw is None else float(raw)
        skew_angle = -correction
        h, w = image.shape[:2]
        m = cv2.getRotationMatrix2D((w / 2, h / 2), correction, 1.0)
        return DeskewResult(
            angle_degrees=skew_angle,
            confidence=1.0,
            transform=GeometryTransform.affine(m, (h, w)),
            method=self.name,
        )
