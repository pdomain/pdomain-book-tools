"""Projection-profile variance deskew (Postl's method)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import cv2
import numpy as np

from pdomain_book_tools.geometry_correction.protocols import DeskewResult
from pdomain_book_tools.geometry_correction.transforms import GeometryTransform

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pdomain_book_tools.geometry_correction.protocols import BBox, PageSide


class ProjectionDeskew:
    """Projection-profile variance maximization (Postl's method).

    Sweeps candidate angles, rotates a binarized copy, and picks the angle whose
    horizontal pixel-sum profile has maximum variance (text rows aligned).
    """

    name = "projection"

    def __init__(
        self, limit: float = 15.0, coarse: float = 1.0, fine: float = 0.1
    ) -> None:
        """Initialise with search parameters."""
        self.limit, self.coarse, self.fine = limit, coarse, fine

    def _binary(self, image: np.ndarray) -> np.ndarray:
        gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        return bw

    def _score(self, bw: np.ndarray, angle: float) -> float:
        h, w = bw.shape
        m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        rot = cv2.warpAffine(bw, m, (w, h), flags=cv2.INTER_NEAREST, borderValue=0)
        profile = np.sum(rot, axis=1, dtype=np.float64)
        return float(np.var(profile))

    def _search(self, bw: np.ndarray, lo: float, hi: float, step: float) -> float:
        angles = np.arange(lo, hi + step, step)
        scores = [self._score(bw, a) for a in angles]
        return float(angles[int(np.argmax(scores))])

    def estimate(
        self,
        image: np.ndarray,
        *,
        page_side: PageSide | None = None,
        text_lines: Sequence[BBox] | None = None,
    ) -> DeskewResult:
        """Estimate the skew angle via projection-profile variance and return a corrective transform."""
        bw = self._binary(image)
        coarse = self._search(bw, -self.limit, self.limit, self.coarse)
        correction = self._search(
            bw, coarse - self.coarse, coarse + self.coarse, self.fine
        )
        # correction is the angle to rotate the image to align text rows.
        # The skew angle (tilt of the page) is the negative of the correction.
        skew_angle = -correction
        h, w = image.shape[:2]
        m = cv2.getRotationMatrix2D((w / 2, h / 2), correction, 1.0)
        return DeskewResult(
            angle_degrees=skew_angle,
            confidence=1.0,
            transform=GeometryTransform.affine(m, (h, w)),
            method=self.name,
        )
