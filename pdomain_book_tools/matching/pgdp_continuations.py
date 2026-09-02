"""Re-export of the PGDP continuation decoder, moved to ``pdomain-book-contracts``.

Lossless decoding of PGDP ``*`` physical-continuation controls is
pure-Python and source-neutral, so it now lives in
``pdomain_book_contracts.matching.pgdp_continuations``. This module keeps
the old import path (``pdomain_book_tools.matching.pgdp_continuations``)
working for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.matching.pgdp_continuations import (
    PgdpContinuation,
    PgdpContinuationBoundary,
    PgdpContinuationDecision,
    PgdpContinuationDecode,
    PgdpContinuationQuarantineReason,
    PgdpLogicalCandidate,
    PgdpMarkerEvidence,
    PgdpPhysicalFragment,
    PgdpQuarantinedMarker,
    PgdpRound,
    PgdpRoundContinuationEvidence,
    PgdpUnmappedMarkerEvidence,
    build_pgdp_surface_document,
    decode_pgdp_continuations,
)

__all__ = [
    "PgdpContinuation",
    "PgdpContinuationBoundary",
    "PgdpContinuationDecision",
    "PgdpContinuationDecode",
    "PgdpContinuationQuarantineReason",
    "PgdpLogicalCandidate",
    "PgdpMarkerEvidence",
    "PgdpPhysicalFragment",
    "PgdpQuarantinedMarker",
    "PgdpRound",
    "PgdpRoundContinuationEvidence",
    "PgdpUnmappedMarkerEvidence",
    "build_pgdp_surface_document",
    "decode_pgdp_continuations",
]
