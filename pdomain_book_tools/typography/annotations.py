"""Re-export of :class:`TypographyAnnotations`, moved to ``pdomain-book-contracts``.

``TypographyAnnotations`` is a pure-Python pydantic contract with no
imaging-stack dependency, so it now lives in
``pdomain_book_contracts.typography.annotations``. This module keeps the
old import path (``pdomain_book_tools.typography.annotations``) working for
existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.typography.annotations import TypographyAnnotations

__all__ = ["TypographyAnnotations"]
