"""Re-export of the legacy projection adapter, moved to ``pdomain-book-contracts``.

This module projects immutable match graphs onto mutable OCR pages. The
adapter itself is pure-Python and only reads or mutates the ``Block``,
``Page``, and ``Word`` surface it needs (through structural Protocols), so
it now lives in ``pdomain_book_contracts.matching.legacy_projection``. This
module keeps the old import path
(``pdomain_book_tools.matching.legacy_projection``) working for existing
callers.
"""

from __future__ import annotations

from pdomain_book_contracts.matching.legacy_projection import (
    LegacyDocumentSide,
    LegacyMatchEvidence,
    LegacyProjectionMutation,
    LegacyProjectionResult,
    legacy_page_to_match_document,
    project_match_graph_onto_page,
)

__all__ = [
    "LegacyDocumentSide",
    "LegacyMatchEvidence",
    "LegacyProjectionMutation",
    "LegacyProjectionResult",
    "legacy_page_to_match_document",
    "project_match_graph_onto_page",
]
