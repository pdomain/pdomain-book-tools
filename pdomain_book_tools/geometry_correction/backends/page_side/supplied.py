"""Supplied (hint passthrough) page-side backend."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pdomain_book_tools.geometry_correction.protocols import (
    GutterEdge,
    PageSide,
    PageSideResult,
)

if TYPE_CHECKING:
    import numpy as np

_GUTTER: dict[PageSide, GutterEdge] = {
    PageSide.LEFT: "right",
    PageSide.RIGHT: "left",
}


class SuppliedPageSide:
    """Trust a caller-supplied side hint (from page-sequence parity / split stage)."""

    name = "supplied"

    def detect(
        self, image: np.ndarray, *, hint: PageSide | None = None
    ) -> PageSideResult:
        """Return a page-side result based on the supplied hint."""
        if hint in _GUTTER:
            return PageSideResult(hint, _GUTTER[hint], 1.0, self.name)
        if hint is PageSide.SINGLE:
            return PageSideResult(PageSide.SINGLE, "none", 1.0, self.name)
        return PageSideResult(PageSide.UNKNOWN, "none", 0.0, self.name)
