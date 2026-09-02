"""Re-export of the label-normalization helpers, moved to
``pdomain-book-contracts``.

These functions and constants import nothing but the standard library, so
they now live in ``pdomain_book_contracts.text.label_normalization`` — the
package the module layout spec keeps genuinely dependency-free. This
module keeps the old import path
(``pdomain_book_tools.ocr.label_normalization``) working for existing
callers.
"""

from __future__ import annotations

from pdomain_book_contracts.text.label_normalization import (
    ALLOWED_COMPONENTS,
    ALLOWED_TEXT_STYLE_LABEL_SCOPES,
    ALLOWED_TEXT_STYLE_LABELS,
    normalize_character_components,
    normalize_text_style_label,
    normalize_text_style_label_scope,
    normalize_text_style_label_scopes,
    normalize_text_style_labels,
    normalize_word_component,
    normalize_word_components,
)

__all__ = [
    "ALLOWED_COMPONENTS",
    "ALLOWED_TEXT_STYLE_LABELS",
    "ALLOWED_TEXT_STYLE_LABEL_SCOPES",
    "normalize_character_components",
    "normalize_text_style_label",
    "normalize_text_style_label_scope",
    "normalize_text_style_label_scopes",
    "normalize_text_style_labels",
    "normalize_word_component",
    "normalize_word_components",
]
