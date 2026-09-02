"""Re-export of :class:`F2Parser`, moved to ``pdomain-book-contracts``.

This is pure-Python semantic parsing with no imaging-stack dependency, so it
now lives in ``pdomain_book_contracts.sources.pgdp.f2.parser``. This module
keeps the old import path (``pdomain_book_tools.pgdp.f2.parser``) working for
existing callers.

Patching a name here does not affect the moved module's own callers: a Python
function resolves global names from the module it was defined in, not from a
module that re-exports it. A test that patches these names to observe
:meth:`F2Parser.parse_page` must patch the defining module instead.
"""

from __future__ import annotations

from pdomain_book_contracts.sources.pgdp.f2.parser import F2Parser
from pdomain_book_contracts.sources.pgdp.f2.tokens import read_f2_json_page
from pdomain_book_contracts.sources.pgdp.offsets import (
    read_lexical_index as read_lexical_f2_index,
)

__all__ = ["F2Parser", "read_f2_json_page", "read_lexical_f2_index"]
