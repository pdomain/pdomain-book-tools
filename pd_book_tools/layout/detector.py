"""Detector Protocol + the no-model adapters.

The contract is intentionally tiny: ``detect(source) -> PageLayout``. Source
may be a file path or a numpy BGR image (the contour adapter accepts both;
the model adapter loads from a path via PIL but will accept an array too).

``NullDetector`` is the default — returns an empty layout. ``ContourDetector``
is a rule-based heuristic for "find rectangles that look like illustrations"
without any ML dep; it's the stepping-stone the pd-prep-for-pgdp spec 05
originally drafted.
"""

from __future__ import annotations

from logging import getLogger
from pathlib import Path
from typing import Protocol, runtime_checkable

import cv2
import numpy as np

from pd_book_tools.layout.types import LayoutRegion, PageLayout, RegionType

logger = getLogger(__name__)

# Runtime alias (not a forward-reference) — Python 3.10+ supports PEP 604
# ``X | Y`` at module top-level, so this evaluates to a ``types.UnionType``
# usable with isinstance() in callers.
ImageSource = str | Path | np.ndarray


def _load_image(source: ImageSource) -> np.ndarray:
    """Return a BGR image from either a path-like or an existing array."""
    if isinstance(source, np.ndarray):
        return source
    img = cv2.imread(str(source), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {source}")
    return img


@runtime_checkable
class LayoutDetector(Protocol):
    """All adapters implement this single method.

    Implementations should be safe to call repeatedly on the same instance —
    the registry memoises adapters and reuses them across pages.
    """

    def detect(self, source: ImageSource) -> PageLayout: ...


class NullDetector:
    """No-op adapter — always returns an empty :class:`PageLayout`.

    Useful when ``--layout-aware`` is not requested but downstream code wants
    a non-None layout to simplify branching.
    """

    KEY = "none"

    def detect(self, source: ImageSource) -> PageLayout:
        img = _load_image(source)
        h, w = img.shape[:2]
        return PageLayout(
            regions=[],
            image_width=int(w),
            image_height=int(h),
            detector=self.KEY,
            inference_ms=0,
        )


class ContourDetector:
    """Rule-based fallback: find dark rectangular regions that look like
    illustrations or decorations.

    Algorithm:
      1. grayscale + Otsu binarise (inverted — text/ink → white).
      2. close small gaps so an engraving connects into a single blob.
      3. find external contours; bounding rect each.
      4. filter by area (>= ``min_area_frac`` of the page) and aspect ratio.

    All output regions are tagged :attr:`RegionType.figure`. The downstream
    illustration extractor in pd-prep-for-pgdp may post-classify some as
    ``decoration`` based on size/position — see the
    "Decoration-vs-figure post-classification" item in
    ``pd-book-tools/docs/ROADMAP.md``.
    """

    KEY = "contour"

    def __init__(
        self,
        min_area_frac: float = 0.005,
        max_area_frac: float = 0.6,
        min_aspect: float = 0.1,
        max_aspect: float = 10.0,
        close_kernel_px: int = 9,
    ):
        self.min_area_frac = min_area_frac
        self.max_area_frac = max_area_frac
        self.min_aspect = min_aspect
        self.max_aspect = max_aspect
        self.close_kernel_px = close_kernel_px

    def detect(self, source: ImageSource) -> PageLayout:
        img = _load_image(source)
        h, w = img.shape[:2]
        page_area = float(h * w)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binarised = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (self.close_kernel_px, self.close_kernel_px)
        )
        closed = cv2.morphologyEx(binarised, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(
            closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        regions: list[LayoutRegion] = []
        for c in contours:
            x, y, cw, ch = cv2.boundingRect(c)
            if cw <= 0 or ch <= 0:
                continue
            area = float(cw * ch)
            frac = area / page_area if page_area else 0.0
            if frac < self.min_area_frac or frac > self.max_area_frac:
                continue
            aspect = cw / float(ch)
            if aspect < self.min_aspect or aspect > self.max_aspect:
                continue
            regions.append(
                LayoutRegion(
                    type=RegionType.figure,
                    L=int(x),
                    R=int(x + cw),
                    T=int(y),
                    B=int(y + ch),
                    confidence=1.0,
                    raw_label="contour",
                )
            )

        return PageLayout(
            regions=regions,
            image_width=int(w),
            image_height=int(h),
            detector=self.KEY,
            inference_ms=0,
        )
