"""OCR helpers for pdomain-book-tools."""

from pdomain_book_tools.ocr.text_normalize import (
    apply_text_normalizations,
    normalize_curly_quotes,
    normalize_em_dash,
)

__all__ = [
    "apply_text_normalizations",
    "normalize_curly_quotes",
    "normalize_em_dash",
]
