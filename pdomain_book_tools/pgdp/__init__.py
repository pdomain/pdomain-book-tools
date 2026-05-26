"""PGDP (Distributed Proofreaders) result loaders.

Re-exports :class:`PGDPResults` and :class:`PGDPExport`, which are
also available from the top-level :mod:`pdomain_book_tools` package.
"""

from pdomain_book_tools.pgdp.pgdp_results import PGDPExport, PGDPResults

__all__ = ["PGDPExport", "PGDPResults"]
