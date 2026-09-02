"""Re-export of PGDP F2 parse warnings, moved to ``pdomain-book-contracts``.

This is a pure-Python enum and predicate with no imaging-stack dependency,
so it now lives in ``pdomain_book_contracts.sources.pgdp.f2.warnings``. This
module keeps the old import path (``pdomain_book_tools.pgdp.f2.warnings``)
working for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.sources.pgdp.f2.warnings import (
    F2ParseWarning,
    warning_blocks_training,
)

__all__ = ["F2ParseWarning", "warning_blocks_training"]
