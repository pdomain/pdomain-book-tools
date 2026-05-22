"""Document-layout detection — region-typed page understanding.

Public surface:

- :class:`RegionType` — enum of region categories the rest of the pipeline
  cares about (``text``, ``figure``, ``caption``, ``header``, etc.).
- :class:`LayoutRegion` — a single typed bounding box with confidence and
  the original model label.
- :class:`PageLayout` — a list of regions plus image dimensions and
  detector metadata.
- :class:`LayoutRegionDict` / :class:`PageLayoutDict` — TypedDict types
  for the serialised forms returned by ``to_dict()``.
- :class:`LayoutDetector` — Protocol all adapters implement.
- :func:`get_detector` — registry: returns a memoised adapter for the given
  key. Keys: ``"none"`` (no-op), ``"contour"`` (rule-based heuristic),
  ``"pp-doclayout-plus-l"`` (RT-DETR via ``transformers``).
- :func:`clear_detector_cache` — drop the memoised adapters (mostly for
  tests / hot-swap workflows).
- :func:`draw_layout_overlay` — render a per-region overlay PNG.
- Region-geometry helpers: :func:`iou`, :func:`contains`,
  :func:`horizontal_overlap_ratio`, :func:`caption_for_figure`,
  :func:`region_reading_order`.
"""

from pd_book_tools.layout.detector import (
    ContourDetector,
    LayoutDetector,
    NullDetector,
)
from pd_book_tools.layout.geometry import (
    caption_for_figure,
    contains,
    horizontal_overlap_ratio,
    iou,
    region_reading_order,
)
from pd_book_tools.layout.registry import clear_detector_cache, get_detector
from pd_book_tools.layout.types import (
    LayoutRegion,
    LayoutRegionDict,
    PageLayout,
    PageLayoutDict,
    RegionType,
)
from pd_book_tools.layout.visualize import draw_layout_overlay

__all__ = [
    "ContourDetector",
    "LayoutDetector",
    "LayoutRegion",
    "LayoutRegionDict",
    "NullDetector",
    "PageLayout",
    "PageLayoutDict",
    "RegionType",
    "caption_for_figure",
    "clear_detector_cache",
    "contains",
    "draw_layout_overlay",
    "get_detector",
    "horizontal_overlap_ratio",
    "iou",
    "region_reading_order",
]
