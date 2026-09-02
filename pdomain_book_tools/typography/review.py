"""Re-export of the typography review contracts, moved to ``pdomain-book-contracts``.

These are pure-Python pydantic contracts with no imaging-stack dependency,
so they now live in ``pdomain_book_contracts.typography.review``. This
module keeps the old import path (``pdomain_book_tools.typography.review``)
working for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.typography.review import (
    REVIEW_CONTRACT_VERSION,
    WORD_ID_NAMESPACE,
    CorrectionDecision,
    LabelState,
    ReviewDecision,
    ReviewState,
    TypographyCorrection,
    TypographyReviewMetadata,
    TypographySpan,
    TypographyTaxonomy,
    TypographyTaxonomyLabel,
    WordTypography,
    canonical_json_bytes,
    make_merged_word_id,
    make_split_word_id,
    make_word_id,
    validate_sha256,
)

__all__ = [
    "REVIEW_CONTRACT_VERSION",
    "WORD_ID_NAMESPACE",
    "CorrectionDecision",
    "LabelState",
    "ReviewDecision",
    "ReviewState",
    "TypographyCorrection",
    "TypographyReviewMetadata",
    "TypographySpan",
    "TypographyTaxonomy",
    "TypographyTaxonomyLabel",
    "WordTypography",
    "canonical_json_bytes",
    "make_merged_word_id",
    "make_split_word_id",
    "make_word_id",
    "validate_sha256",
]
