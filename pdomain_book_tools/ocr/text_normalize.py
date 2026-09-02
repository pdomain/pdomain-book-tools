"""Re-export of the text-normalization helpers, moved to
``pdomain-book-contracts``.

These functions import nothing but the standard library, so they now live
in ``pdomain_book_contracts.text.text_normalize`` — the package the module
layout spec keeps genuinely dependency-free. This module keeps the old
import path (``pdomain_book_tools.ocr.text_normalize``) working for
existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.text.text_normalize import (
    apply_text_normalizations,
    normalize_curly_quotes,
    normalize_em_dash,
)

__all__ = [
    "apply_text_normalizations",
    "normalize_curly_quotes",
    "normalize_em_dash",
]
