"""Re-export of the glyph-annotation types, moved to ``pdomain-book-contracts``.

``GlyphAnnotations``, ``LigatureKind``, ``LigatureMark``, and ``GlyphSource``
are pure-Python value types with no imaging-stack dependency, so they now
live in ``pdomain_book_contracts.ocr.glyph_annotations``. This module keeps
the old import path (``pdomain_book_tools.ocr.glyph_annotations``) working
for existing callers.

``GlyphAnnotations.validate()`` no longer type-hints its ``word`` parameter
as ``pdomain_book_tools.ocr.word.Word`` directly — the contracts package
cannot import that class (see the module layout spec's "What this layout
does not solve"). It accepts a module-private structural Protocol there
instead, which ``Word`` satisfies structurally; every existing caller here
still passes a real ``Word`` and the call behaves identically.
"""

from __future__ import annotations

from pdomain_book_contracts.ocr.glyph_annotations import (
    GlyphAnnotations,
    GlyphSource,
    LigatureKind,
    LigatureMark,
)

__all__ = ["GlyphAnnotations", "GlyphSource", "LigatureKind", "LigatureMark"]
