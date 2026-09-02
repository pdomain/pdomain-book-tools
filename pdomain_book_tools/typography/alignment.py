"""Re-export of the token alignment contracts, moved to ``pdomain-book-contracts``.

Alignment is pure-Python and source-neutral, so it now lives in
``pdomain_book_contracts.matching.alignment`` — beside the matching engine,
since aligning two texts is what ``matching/`` is for; it moved out of
``typography/`` on the same trip. This module keeps the old import path
(``pdomain_book_tools.typography.alignment``) working for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.matching.alignment import (
    AlignmentConfig,
    AlignmentEdit,
    AlignmentEditKind,
    ProjectedBoundingBox,
    ProjectedStyleSpan,
    TokenAlignmentResult,
    align_tokens,
    project_style_span,
    project_token_ranges,
)

__all__ = [
    "AlignmentConfig",
    "AlignmentEdit",
    "AlignmentEditKind",
    "ProjectedBoundingBox",
    "ProjectedStyleSpan",
    "TokenAlignmentResult",
    "align_tokens",
    "project_style_span",
    "project_token_ranges",
]
