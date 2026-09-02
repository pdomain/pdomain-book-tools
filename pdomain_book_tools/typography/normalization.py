"""Re-export of the typography-normalization comparison views, moved to ``pdomain-book-contracts``.

These build the comparison views alignment consumes and are pure-Python
with no imaging-stack dependency, so they now live in
``pdomain_book_contracts.typography.normalization``. They moved to
``pdomain_book_contracts.text.normalization`` briefly, but that module
needs ``typography.labels`` and ``typography.spans`` for its own
vocabulary, which produced a real import cycle with
``typography/records.py`` — see ``pdomain-book-contracts``'s history for
the fix. This module keeps the old import path
(``pdomain_book_tools.typography.normalization``) working for existing
callers.
"""

from __future__ import annotations

from pdomain_book_contracts.typography.normalization import (
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
