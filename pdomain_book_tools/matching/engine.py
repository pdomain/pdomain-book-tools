"""Re-export of the matching engine, moved to ``pdomain-book-contracts``.

The bounded deterministic matcher is pure-Python and source-neutral, so it
now lives in ``pdomain_book_contracts.matching.engine``. This module keeps
the old import path (``pdomain_book_tools.matching.engine``) working for
existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.matching.engine import match_documents

__all__ = ["match_documents"]
