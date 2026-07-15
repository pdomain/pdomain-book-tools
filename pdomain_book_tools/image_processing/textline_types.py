"""Device-agnostic containers shared by the cv2 / cupy textline-dewarp modules.

These hold plain arrays (numpy *or* cupy) and floats — no device-specific code —
so both ``cv2_processing`` and ``cupy_processing`` (and the geometry_correction
detector seam above them) can import them without a layering cycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt


@dataclass(frozen=True)
class LineSamples:
    """Per-column vertical centroids of one detected text line.

    ``xs`` are sorted, unique column positions; ``ys`` are the weighted-centroid
    row at each column. Arrays may be numpy or cupy (cupy's stub subclasses
    ``numpy.ndarray`` for typing purposes, see ``typings/cupy/__init__.pyi``).
    """

    xs: npt.NDArray[np.float64]
    ys: npt.NDArray[np.float64]

    @property
    def left(self) -> float:
        """Left-most column position (minimum of xs)."""
        return float(self.xs.min())

    @property
    def right(self) -> float:
        """Right-most column position (maximum of xs)."""
        return float(self.xs.max())

    @property
    def width(self) -> float:
        """Horizontal span from left to right."""
        return self.right - self.left


@dataclass(frozen=True)
class QuadCoeffs:
    """Order-2 baseline polynomial y(x) = c2*x^2 + c1*x + c0 (Leptonica ptaGetQuadraticLSF)."""

    c2: float
    c1: float
    c0: float

    def eval(self, x: Any) -> Any:
        """Evaluate the polynomial at x (scalar or array)."""
        return self.c2 * x * x + self.c1 * x + self.c0
