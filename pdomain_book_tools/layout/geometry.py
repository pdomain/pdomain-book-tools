"""Re-export of the region-adjacency helpers, moved to
``pdomain-book-contracts``.

These are pure-Python functions with no imaging-stack dependency, so they
now live in ``pdomain_book_contracts.layout.regions`` — renamed from
``geometry`` there, since that name already means the spatial value types
one level up in that package (``pdomain_book_contracts.geometry``). This
module keeps the old import path
(``pdomain_book_tools.layout.geometry``) working for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.layout.regions import (
    caption_for_figure,
    contains,
    horizontal_overlap_ratio,
    iou,
    region_reading_order,
)

__all__ = [
    "caption_for_figure",
    "contains",
    "horizontal_overlap_ratio",
    "iou",
    "region_reading_order",
]
