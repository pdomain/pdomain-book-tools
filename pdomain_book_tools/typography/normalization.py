"""Re-export of the text-normalization comparison views, moved to ``pdomain-book-contracts``.

These build the comparison views alignment consumes and are pure-Python
with no imaging-stack dependency, so they now live in
``pdomain_book_contracts.text.normalization`` — in the ``text`` package,
not ``typography``, since none of this is specific to typography or OCR
results (see the module layout spec). This module keeps the old import
path (``pdomain_book_tools.typography.normalization``) working for
existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.text.normalization import (
    ComparisonOperation,
    ComparisonOperationKind,
    ComparisonView,
    build_comparison_view,
    small_caps_ranges_from_spans,
)

__all__ = [
    "ComparisonOperation",
    "ComparisonOperationKind",
    "ComparisonView",
    "build_comparison_view",
    "small_caps_ranges_from_spans",
]
