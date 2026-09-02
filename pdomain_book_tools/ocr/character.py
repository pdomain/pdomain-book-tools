"""Re-export of :class:`Character`, moved to ``pdomain-book-contracts``.

``Character`` is a pure-Python dataclass with no imaging-stack dependency,
so it now lives in ``pdomain_book_contracts.ocr.character``. This module
keeps the old import path (``pdomain_book_tools.ocr.character``) working
for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.ocr.character import Character

__all__ = ["Character"]
