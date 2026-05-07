"""Regression tests for ``reconcile_dropped_words`` (M-13).

The historical implementation hardcoded a 3-level traversal
``outer.items -> paragraph.items -> line.words`` (with a ``hasattr(line,
"words")`` fallback) when computing ``post_words``. Any tree shape that
did not happen to be ``BLOCK -> PARAGRAPH -> LINE -> WORDS`` could
slip through that walk — including the simple ``BLOCK -> LINE ->
WORDS`` shape produced when a recovered/floated branch skips the
PARAGRAPH wrapper. In that case ``line`` ended up being a ``Word``,
``hasattr(Word, "words")`` is ``False``, and the comprehension
silently treated every word as missing, raising a *false-positive*
"dropped word" error.

The fix is to use the page's own recursive ``Page.words`` accessor
(itself backed by ``Block.words``, which recurses through nested
BLOCKS / PARAGRAPHs / LINEs of arbitrary depth). To get a meaningful
``post_words``, the tests temporarily install the candidate
``final_blocks`` on the Page so the recursive walker sees them.

Two tests:

1. **False-positive regression** — words live under
   ``BLOCK -> LINE -> WORDS`` (no PARAGRAPH layer). Pre-fix this
   shape triggered a spurious dropped-word error in strict mode.
   Post-fix it must succeed silently.
2. **True-positive preservation** — a word genuinely missing from
   ``final_blocks`` must still raise. This locks the safety net so
   any future "fix" that ignores real drops fails this test.
"""

from __future__ import annotations

import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.reorganize_page_utils import (
    ReorganizeDroppedWordsError,
    reconcile_dropped_words,
)
from pd_book_tools.ocr.word import Word


def _w(text: str, x0: float, y0: float, w: float = 0.05, h: float = 0.02) -> Word:
    return Word(
        text=text,
        bounding_box=BoundingBox.from_ltrb(x0, y0, x0 + w, y0 + h),
        ocr_confidence=1.0,
    )


def _make_block_line_words_page(words: list[Word]) -> tuple[Page, list[Block]]:
    """Build a Page whose word tree skips the PARAGRAPH layer.

    Layout: ``Page -> BLOCK -> LINE -> Word``. ``Block.words`` recurses
    through this just fine (it terminates at ``child_type == WORDS``),
    so ``page.words`` returns every word — but the legacy 3-level
    comprehension in ``reconcile_dropped_words`` would walk
    ``outer.items`` (LINE), then ``paragraph.items`` (the Words
    themselves), and arrive at a Word in the place ``line`` was
    expected. ``hasattr(Word, "words")`` is False, so the fallback
    yielded an empty list and the function reported every word as
    dropped.
    """
    line = Block(
        items=list(words),
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )
    outer = Block(
        items=[line],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.BLOCK,
    )
    page = Page(width=1000, height=1000, page_index=0, blocks=[outer])
    return page, [outer]


def test_block_line_words_shape_does_not_false_positive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No PARAGRAPH layer → pre-fix, strict mode raised; post-fix silent."""
    monkeypatch.setenv("PD_OCR_REORGANIZE_STRICT", "1")

    pre_words = [
        _w("hello", x0=0.10, y0=0.10),
        _w("world", x0=0.20, y0=0.10),
        _w("again", x0=0.30, y0=0.10),
    ]
    page, final_blocks = _make_block_line_words_page(pre_words)

    # Sanity: the recursive accessor sees every word.
    assert {w.text for w in page.words} == {w.text for w in pre_words}

    # Post-fix: no dropped-word error is raised even though the tree
    # skips the PARAGRAPH layer the legacy 3-level walk assumed.
    result = reconcile_dropped_words(page, pre_words, final_blocks)
    assert result is final_blocks


def test_genuine_drop_still_raises_in_strict_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Safety net: a word truly missing from ``final_blocks`` must raise.

    Builds the same BLOCK -> LINE -> WORDS shape as the false-positive
    test but with one of the ``pre_words`` deliberately *not* placed
    into the final block tree. ``Page.words`` will report the
    surviving words only; ``validate_word_preservation`` must spot
    the missing word and ``reconcile_dropped_words`` must surface it
    (raise in strict mode).

    This guards against a regression in which a "use page.words"
    refactor is applied so loosely that real drops also slip
    through.
    """
    monkeypatch.setenv("PD_OCR_REORGANIZE_STRICT", "1")

    kept = [
        _w("alpha", x0=0.10, y0=0.10),
        _w("beta", x0=0.20, y0=0.10),
    ]
    dropped_word = _w("gamma", x0=0.30, y0=0.10)
    pre_words = [*kept, dropped_word]

    # Final block tree contains only the kept words. ``gamma`` is
    # genuinely missing from the post-reorg structure.
    page, final_blocks = _make_block_line_words_page(kept)

    with pytest.raises(ReorganizeDroppedWordsError) as excinfo:
        reconcile_dropped_words(page, pre_words, final_blocks)
    assert any("gamma" in msg for msg in excinfo.value.errors), excinfo.value.errors
    assert any(w.text == "gamma" for w in excinfo.value.dropped)
