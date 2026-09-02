"""Re-export of :class:`BlobStoreProtocol`, moved to ``pdomain-book-contracts``.

``BlobStoreProtocol`` is a pure-Python ``typing.Protocol`` with no
imaging-stack dependency, so it now lives in
``pdomain_book_contracts.ocr.blob_protocol``. This module keeps the old
import path (``pdomain_book_tools.ocr.blob_protocol``) working for
existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.ocr.blob_protocol import BlobStoreProtocol

__all__ = ["BlobStoreProtocol"]
