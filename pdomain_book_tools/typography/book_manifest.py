"""Re-export of the book labeling manifest, moved to ``pdomain-book-contracts``.

These are pure-Python pydantic contracts with no imaging-stack dependency,
so they now live in ``pdomain_book_contracts.typography.book_manifest``.
This module keeps the old import path
(``pdomain_book_tools.typography.book_manifest``) working for existing
callers.
"""

from __future__ import annotations

from pdomain_book_contracts.typography.book_manifest import (
    BookLabelingManifest,
    BookLabelingPage,
    BookMatchRelationReference,
)

__all__ = [
    "BookLabelingManifest",
    "BookLabelingPage",
    "BookMatchRelationReference",
]
