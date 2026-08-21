"""Canonical typography labels and grapheme-span contracts."""

from pdomain_book_tools.typography.annotations import TypographyAnnotations
from pdomain_book_tools.typography.labels import (
    ConfidenceTier,
    KnowledgeState,
    LabelSource,
    StyleLabel,
)
from pdomain_book_tools.typography.records import (
    AlignmentEvidence,
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
from pdomain_book_tools.typography.spans import (
    GRAPHEME_SEGMENTATION_VERSION,
    SourceSlice,
    StyleSpan,
    TypographySpans,
    split_graphemes,
)

__all__ = [
    "GRAPHEME_SEGMENTATION_VERSION",
    "AlignmentEvidence",
    "ArtifactRef",
    "ArtifactSource",
    "ConfidenceTier",
    "Grapheme",
    "KnowledgeState",
    "LabelSource",
    "OcrTokenRef",
    "ParserControlEvidence",
    "ParserControlKind",
    "ParserNormalizationEvidence",
    "ParserNormalizationKind",
    "ParserNoteEvidence",
    "ParserNoteStatus",
    "SourceCoordinateSpace",
    "SourceSlice",
    "StyleLabel",
    "StyleSpan",
    "TargetCoordinateSpace",
    "TextIdentity",
    "TypographyAnnotations",
    "TypographyPageRecord",
    "TypographySpans",
    "split_graphemes",
]
