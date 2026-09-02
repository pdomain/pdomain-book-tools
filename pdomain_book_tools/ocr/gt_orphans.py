"""Re-export of :class:`GtOrphans`, moved to ``pdomain-book-contracts``.

``GtOrphans`` is a pure-Python dataclass with no imaging-stack dependency,
so it now lives in ``pdomain_book_contracts.ocr.gt_orphans``. This module
keeps the old import path (``pdomain_book_tools.ocr.gt_orphans``) working
for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.ocr.gt_orphans import GtOrphans

__all__ = ["GtOrphans"]
