"""Re-export of :class:`F2Parser`, moved to ``pdomain-book-contracts``.

This is pure-Python semantic parsing with no imaging-stack dependency, so it
now lives in ``pdomain_book_contracts.sources.pgdp.f2.parser``. This module
keeps the old import path (``pdomain_book_tools.pgdp.f2.parser``) working
for existing callers.

Unlike the other shims in this package, this module also replaces its own
entry in ``sys.modules`` with the real module object, rather than only
re-exporting names. ``tests/pgdp/f2/test_parser.py`` imports this module as
an object (``import pdomain_book_tools.pgdp.f2.parser as parser_module``)
and monkeypatches ``parser_module.read_lexical_f2_index`` /
``.read_f2_json_page`` to count calls made during
:meth:`F2Parser.parse_page`. A plain name re-export would let that
monkeypatch patch a copy those calls never read: a Python function resolves
global names from the module it was *defined* in, not from whatever module a
caller imported it through (verified empirically — patching a re-exporting
shim's copy of a name has no effect on the defining module's own callers).
Making this module *be* the real module, via the ``sys.modules``
substitution below, is what keeps those pre-existing tests meaningful
without editing them. The named imports above the substitution are kept too,
so static type checkers that analyse this file's own source (rather than
following the runtime substitution) still resolve ``F2Parser`` and friends
normally.
"""

from __future__ import annotations

import sys

from pdomain_book_contracts.sources.pgdp.f2 import parser as _parser
from pdomain_book_contracts.sources.pgdp.f2.parser import F2Parser
from pdomain_book_contracts.sources.pgdp.f2.tokens import read_f2_json_page
from pdomain_book_contracts.sources.pgdp.offsets import (
    read_lexical_index as read_lexical_f2_index,
)

__all__ = ["F2Parser", "read_f2_json_page", "read_lexical_f2_index"]

sys.modules[__name__] = _parser
