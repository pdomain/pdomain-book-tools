"""Re-export of the round-JSON lexical readers, moved to ``pdomain-book-contracts``.

These are pure-Python pydantic contracts and functions with no imaging-stack
dependency, so they now live in ``pdomain_book_contracts.sources.pgdp.offsets``
— moved up out of ``f2/`` there, since the module contains no F2 markup
handling: it decodes generic JSON string bytes and tracks byte offsets into
the round-JSON container every PGDP round shares. This module keeps the old
import path (``pdomain_book_tools.pgdp.f2.offsets``) working for existing
callers.

``read_lexical_f2_index``, ``read_lexical_f2_page`` and ``read_lexical_f2_json``
are the pre-rename names. ``pdomain-source-data`` calls the first two of
these directly against P3 artifacts and must keep working unmodified, so
they stay exported here under their old names. ``read_lexical_index``,
``read_lexical_page`` and ``read_lexical_json`` are the renamed exports the
contracts package now canonically defines; both spellings resolve to the
same functions.
"""

from __future__ import annotations

from pdomain_book_contracts.sources.pgdp.offsets import (
    DecodedF2Character,
    LexicalF2Document,
    LexicalF2Index,
    LexicalF2Page,
    LexicalF2PageIndex,
    read_lexical_index,
    read_lexical_json,
    read_lexical_page,
)
from pdomain_book_contracts.sources.pgdp.offsets import (
    read_lexical_index as read_lexical_f2_index,
)
from pdomain_book_contracts.sources.pgdp.offsets import (
    read_lexical_json as read_lexical_f2_json,
)
from pdomain_book_contracts.sources.pgdp.offsets import (
    read_lexical_page as read_lexical_f2_page,
)

__all__ = [
    "DecodedF2Character",
    "LexicalF2Document",
    "LexicalF2Index",
    "LexicalF2Page",
    "LexicalF2PageIndex",
    "read_lexical_f2_index",
    "read_lexical_f2_json",
    "read_lexical_f2_page",
    "read_lexical_index",
    "read_lexical_json",
    "read_lexical_page",
]
