"""Re-export of the F2 tokenizer, moved to ``pdomain-book-contracts``.

This is pure-Python byte-preserving tokenization with no imaging-stack
dependency, so it now lives in
``pdomain_book_contracts.sources.pgdp.f2.tokens``. This module keeps the old
import path (``pdomain_book_tools.pgdp.f2.tokens``) working for existing
callers.
"""

from __future__ import annotations

from pdomain_book_contracts.sources.pgdp.f2.tokens import (
    F2JsonDocument,
    F2JsonPage,
    F2NormalizationKind,
    F2NormalizationOperation,
    F2PageTokens,
    F2Token,
    F2TokenKind,
    F2Warning,
    read_f2_json,
    read_f2_json_page,
    tokenize_f2,
)

__all__ = [
    "F2JsonDocument",
    "F2JsonPage",
    "F2NormalizationKind",
    "F2NormalizationOperation",
    "F2PageTokens",
    "F2Token",
    "F2TokenKind",
    "F2Warning",
    "read_f2_json",
    "read_f2_json_page",
    "tokenize_f2",
]
