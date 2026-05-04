"""Document-layout detection — region-typed page understanding.

Public surface:

- :class:`RegionType` — enum of region categories the rest of the pipeline
  cares about (``text``, ``figure``, ``caption``, ``header``, etc.).
- :class:`LayoutRegion` — a single typed bounding box with confidence and
  the original model label.
- :class:`PageLayout` — a list of regions plus image dimensions and
  detector metadata.
- :class:`LayoutDetector` — Protocol all adapters implement.
- :func:`get_detector` — registry: returns a memoised adapter for the given
  key. Keys: ``"none"`` (no-op), ``"contour"`` (rule-based heuristic),
  ``"pp-doclayout-plus-l"`` (RT-DETR via ``transformers``).
"""

from pd_book_tools.layout.detector import (
    ContourDetector,
    LayoutDetector,
    NullDetector,
)
from pd_book_tools.layout.registry import get_detector
from pd_book_tools.layout.types import LayoutRegion, PageLayout, RegionType

__all__ = [
    "ContourDetector",
    "LayoutDetector",
    "LayoutRegion",
    "NullDetector",
    "PageLayout",
    "RegionType",
    "get_detector",
]
