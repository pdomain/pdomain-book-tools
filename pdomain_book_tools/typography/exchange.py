"""Re-export of the typography exchange contracts, moved to ``pdomain-book-contracts``.

These are pure-Python pydantic contracts with no imaging-stack dependency,
so they now live in ``pdomain_book_contracts.typography.exchange``. This
module keeps the old import path (``pdomain_book_tools.typography.exchange``)
working for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.typography.exchange import (
    ArtifactReference,
    CoordinateTransform,
    CoordinateTransformStage,
    CorrectionBundle,
    Evidence,
    LabelingBundle,
    ModelRun,
    ModelRunPurpose,
    PageGeometry,
    ReplacementArtifact,
    SourceOrientation,
    WordGeometry,
)

__all__ = [
    "ArtifactReference",
    "CoordinateTransform",
    "CoordinateTransformStage",
    "CorrectionBundle",
    "Evidence",
    "LabelingBundle",
    "ModelRun",
    "ModelRunPurpose",
    "PageGeometry",
    "ReplacementArtifact",
    "SourceOrientation",
    "WordGeometry",
]
