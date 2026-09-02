"""Re-export of the OCR provenance types, moved to ``pdomain-book-contracts``.

``OCRModelProvenance``, ``OCRProvenance``, and ``UNKNOWN_METADATA_VALUE``
are pure-Python, frozen dataclasses and a constant with no imaging-stack
dependency, so they now live in ``pdomain_book_contracts.ocr.provenance``.
This module keeps the old import path
(``pdomain_book_tools.ocr.provenance``) working for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.ocr.provenance import (
    UNKNOWN_METADATA_VALUE,
    OCRModelProvenance,
    OCRProvenance,
)

__all__ = ["UNKNOWN_METADATA_VALUE", "OCRModelProvenance", "OCRProvenance"]
