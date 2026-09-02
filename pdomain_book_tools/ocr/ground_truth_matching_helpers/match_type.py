"""Re-export of :class:`MatchType`, moved to ``pdomain-book-contracts``.

``MatchType`` is matching vocabulary, not an OCR result, so it now lives in
``pdomain_book_contracts.matching.match_type`` beside the rest of the
matching contracts. This module keeps the old import path
(``pdomain_book_tools.ocr.ground_truth_matching_helpers.match_type``)
working for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.matching.match_type import MatchType

__all__ = ["MatchType"]
