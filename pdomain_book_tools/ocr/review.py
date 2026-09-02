"""Re-export of :class:`ReviewMetadata`, moved to ``pdomain-book-contracts``.

``ReviewMetadata`` is a pure-Python dataclass with no imaging-stack
dependency, so it now lives in ``pdomain_book_contracts.ocr.review``. This
module keeps the old import path (``pdomain_book_tools.ocr.review``)
working for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.ocr.review import ReviewMetadata

__all__ = ["ReviewMetadata"]
