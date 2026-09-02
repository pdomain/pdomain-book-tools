"""Re-export of the typography page record contracts, moved to ``pdomain-book-contracts``.

These are pure-Python pydantic contracts with no imaging-stack dependency,
so they now live in ``pdomain_book_contracts.typography.records``. This
module keeps the old import path (``pdomain_book_tools.typography.records``)
working for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.typography.records import (
    TYPOGRAPHY_PAGE_RECORD_EXTERNAL_F2_SCHEMA_VERSION,
    TYPOGRAPHY_PAGE_RECORD_LEGACY_SCHEMA_VERSION,
    AlignmentEvidence,
    AlignmentPathOperation,
    ArtifactRef,
    ArtifactSource,
    Grapheme,
    OcrTokenRef,
    ParserControlEvidence,
    ParserControlKind,
    ParserNormalizationEvidence,
    ParserNormalizationKind,
    ParserNoteEvidence,
    ParserNoteStatus,
    SourceCoordinateSpace,
    TargetCoordinateSpace,
    TextIdentity,
    TypographyPageRecord,
)

__all__ = [
    "TYPOGRAPHY_PAGE_RECORD_EXTERNAL_F2_SCHEMA_VERSION",
    "TYPOGRAPHY_PAGE_RECORD_LEGACY_SCHEMA_VERSION",
    "AlignmentEvidence",
    "AlignmentPathOperation",
    "ArtifactRef",
    "ArtifactSource",
    "Grapheme",
    "OcrTokenRef",
    "ParserControlEvidence",
    "ParserControlKind",
    "ParserNormalizationEvidence",
    "ParserNormalizationKind",
    "ParserNoteEvidence",
    "ParserNoteStatus",
    "SourceCoordinateSpace",
    "TargetCoordinateSpace",
    "TextIdentity",
    "TypographyPageRecord",
]
