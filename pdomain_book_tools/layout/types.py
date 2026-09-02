"""Re-export of the layout value types, moved to ``pdomain-book-contracts``.

``RegionType``, ``LayoutRegion``, ``PageLayout``, ``LayoutRegionDict``, and
``PageLayoutDict`` are pure-Python value types with no imaging-stack
dependency, so they now live in ``pdomain_book_contracts.layout.types``.
This module keeps the old import path
(``pdomain_book_tools.layout.types``) working for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.layout.types import (
    LayoutRegion,
    LayoutRegionDict,
    PageLayout,
    PageLayoutDict,
    RegionType,
)

__all__ = [
    "LayoutRegion",
    "LayoutRegionDict",
    "PageLayout",
    "PageLayoutDict",
    "RegionType",
]
