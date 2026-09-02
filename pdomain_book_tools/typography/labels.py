"""Re-export of the typography label vocabulary, moved to ``pdomain-book-contracts``.

These are plain ``StrEnum`` types with no imaging-stack dependency, so they
now live in ``pdomain_book_contracts.typography.labels``. This module keeps
the old import path (``pdomain_book_tools.typography.labels``) working for
existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.typography.labels import (
    ConfidenceTier,
    KnowledgeState,
    LabelSource,
    StyleLabel,
)

__all__ = [
    "ConfidenceTier",
    "KnowledgeState",
    "LabelSource",
    "StyleLabel",
]
