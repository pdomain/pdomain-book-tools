"""Re-export of :class:`PGDPExport` and :class:`PGDPResults`, moved to ``pdomain-book-contracts``.

Both are pure-Python value types with no imaging-stack dependency, so they
now live in ``pdomain_book_contracts.sources.pgdp.rounds`` — renamed from
``pgdp_results.py`` there, since the module reads any PGDP round rather than
one thing called a result. This module keeps the old import path
(``pdomain_book_tools.pgdp.pgdp_results``) working for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.sources.pgdp.rounds import PGDPExport, PGDPResults

__all__ = ["PGDPExport", "PGDPResults"]
