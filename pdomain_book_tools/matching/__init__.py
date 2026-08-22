"""Public immutable contracts for source-neutral OCR-to-text matching."""

from __future__ import annotations

from pdomain_book_tools.matching.models import (
    ArtifactRange,
    MatchAlternative,
    MatchDocument,
    MatchGraph,
    MatchLine,
    MatchOperation,
    MatchOperationKind,
    MatchPage,
    MatchPolicy,
    MatchQuarantineReason,
    MatchRelation,
    MatchRelationKind,
    MatchToken,
)

__all__ = [
    "ArtifactRange",
    "MatchAlternative",
    "MatchDocument",
    "MatchGraph",
    "MatchLine",
    "MatchOperation",
    "MatchOperationKind",
    "MatchPage",
    "MatchPolicy",
    "MatchQuarantineReason",
    "MatchRelation",
    "MatchRelationKind",
    "MatchToken",
]
