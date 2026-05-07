"""L-23 regression-lock + deferral.

The bug claim: ``Block.items`` and ``Page.items`` re-sort on every read,
making N reads inside one operation O(N * n log n).

Audit result:
- ``Block.items`` (block.py:316-318) — STALE. The getter just returns
  ``self._items.copy()``; no sort happens on read. The reviewer cited
  lines 309-312 which are sort-key lambdas inside ``_sort_items`` itself,
  not the items getter. Pinned here so a future refactor can't quietly
  re-add a sort to the getter and reintroduce the perf cliff.
- ``Page.items`` (page.py:236-240) — REAL. The getter does call
  ``self._sort_items()`` on every read. A correct fix would add a
  ``_dirty`` flag wired through every mutation site (``add_item``,
  ``remove_item``, ``items.setter``, ``remove_empty_items``,
  ``_remove_empty_items_safely``, the layout-aware reorganization
  helpers that do raw ``container._items = ...`` assignment at
  page.py:846 and 889, and ``self.items = items`` in ``__init__``).
  That's a non-trivial mutation surface with cross-cutting risk
  (silently dropping the dirty flag at any one site means stale sort
  order under non-trivial layout work). Deferred to a focused refactor
  rather than rammed through here.

This module pins both the stale and real findings so the deferral is
visible in the test suite, not just the review doc.
"""

from unittest.mock import patch

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.word import Word


def _make_word(x: float, text: str) -> Word:
    bbox = BoundingBox(
        Point(x, 0.1, is_normalized=True),
        Point(x + 0.05, 0.2, is_normalized=True),
        is_normalized=True,
    )
    return Word(text=text, bounding_box=bbox, ocr_confidence=1.0)


def _make_block(words: list[Word]) -> Block:
    return Block(
        items=words,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )


def test_block_items_getter_does_not_resort_on_each_read():
    """L-23 stale-claim lock: Block.items does NOT call _sort_items on
    read. If a future refactor adds one, this test fails so the perf
    cliff is caught."""
    block = _make_block([_make_word(0.1, "a"), _make_word(0.3, "b")])

    with patch.object(Block, "_sort_items", autospec=True) as mock_sort:
        for _ in range(5):
            _ = block.items
        assert mock_sort.call_count == 0


def test_page_items_getter_currently_resorts_on_each_read_deferred_fix():
    """L-23 real-bug lock: Page.items DOES call _sort_items on every
    read today. Test pins the current (deferred-fix) behavior so the
    eventual dirty-flag refactor will need to update this assertion in
    the same commit that lands the optimization — the change cannot
    silently regress sort-order correctness."""
    word = _make_word(0.1, "a")
    line_block = _make_block([word])
    para_block = Block(
        items=[line_block],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
    )
    outer_block = Block(
        items=[para_block],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.BLOCK,
    )
    page = Page(width=100, height=100, page_index=0, blocks=[outer_block])

    with patch.object(Page, "_sort_items", autospec=True) as mock_sort:
        for _ in range(3):
            _ = page.items
        # Today's behavior: one sort call per read.
        assert mock_sort.call_count == 3, (
            "If you fixed L-23 by adding a dirty-flag (sort-on-mutate "
            "instead of sort-on-read), update this assertion AND audit "
            "every Page._items mutation site (add_item, remove_item, "
            "items.setter, remove_empty_items, _remove_empty_items_safely, "
            "and the raw container._items = ... assignments in the "
            "layout-aware helpers around page.py:846 and 889) to set the "
            "dirty flag — otherwise sort order will silently go stale."
        )
