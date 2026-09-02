"""Re-export of PGDP F2 project rules, moved to ``pdomain-book-contracts``.

This is pure-Python evidence-bound configuration with no imaging-stack
dependency, so it now lives in
``pdomain_book_contracts.sources.pgdp.f2.project_rules``. This module keeps
the old import path (``pdomain_book_tools.pgdp.f2.project_rules``) working
for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.sources.pgdp.f2.project_rules import (
    ProjectRule,
    ProjectRuleRegistry,
)

__all__ = ["ProjectRule", "ProjectRuleRegistry"]
