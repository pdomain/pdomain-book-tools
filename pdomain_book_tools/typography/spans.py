"""Re-export of the typography span contracts, moved to ``pdomain-book-contracts``.

These are pure-Python pydantic contracts with no imaging-stack dependency,
so they now live in ``pdomain_book_contracts.typography.spans``. This
module keeps the old import path (``pdomain_book_tools.typography.spans``)
working for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.typography.spans import (
    GRAPHEME_SEGMENTATION_VERSION,
    CanonicalModel,
    SourceSlice,
    StyleSpan,
    TypographySpans,
    split_graphemes,
)

__all__ = [
    "GRAPHEME_SEGMENTATION_VERSION",
    "CanonicalModel",
    "SourceSlice",
    "StyleSpan",
    "TypographySpans",
    "split_graphemes",
]
