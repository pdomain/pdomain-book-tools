"""Re-export of :class:`Point`, moved to ``pdomain-book-contracts``.

``Point`` is a pure-Python value type with no imaging-stack dependency, so
it now lives in ``pdomain_book_contracts.geometry.point``. This module keeps
the old import path (``pdomain_book_tools.geometry.point``) working for
existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.geometry.point import Point

__all__ = ["Point"]
