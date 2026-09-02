"""Re-export of :class:`CharacterGroups`, moved to ``pdomain-book-contracts``.

``CharacterGroups`` is matching vocabulary, not an OCR result, so it now
lives in ``pdomain_book_contracts.matching.character_groups`` beside the
rest of the matching contracts. This module keeps the old import path
(``pdomain_book_tools.ocr.ground_truth_matching_helpers.character_groups``)
working for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.matching.character_groups import CharacterGroups

__all__ = ["CharacterGroups"]
