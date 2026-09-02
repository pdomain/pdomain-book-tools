"""Re-export of the matching contracts, moved to ``pdomain-book-contracts``.

These are immutable, source-neutral pydantic contracts with no imaging-stack
dependency, so they now live in ``pdomain_book_contracts.matching.models``.
This module keeps the old import path (``pdomain_book_tools.matching.models``)
working for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.matching.models import (
    ArtifactRange,
    MatchAlternative,
    MatchComparisonNormalization,
    MatchContinuationReference,
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
    MatchSearchEvidence,
    MatchSearchPathEvidence,
    MatchTieBreakRule,
    MatchToken,
    canonical_relation_path_bytes,
    continuation_reference_matches_document_side,
)

__all__ = [
    "ArtifactRange",
    "MatchAlternative",
    "MatchComparisonNormalization",
    "MatchContinuationReference",
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
    "MatchSearchEvidence",
    "MatchSearchPathEvidence",
    "MatchTieBreakRule",
    "MatchToken",
    "canonical_relation_path_bytes",
    "continuation_reference_matches_document_side",
]
