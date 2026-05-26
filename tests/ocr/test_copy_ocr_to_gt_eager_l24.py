"""L-24 regression: ``Block.copy_ocr_to_ground_truth`` /
``copy_ground_truth_to_ocr`` / ``clear_ground_truth`` (and their
``Page`` siblings) must process every word — they previously used
``any([list comp])``, which works because list construction is eager but
reads as if short-circuit was intended. The fix split the comprehension
out so the eager intent is explicit; this test pins that the eager
contract holds at the behavioral level (every word is mutated, even
when the first word's call already returns True).
"""

from unittest.mock import patch

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.geometry.point import Point
from pdomain_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pdomain_book_tools.ocr.page import Page
from pdomain_book_tools.ocr.word import Word


def _make_word(x: float, text: str, gt: str | None = None) -> Word:
    bbox = BoundingBox(
        Point(x, 0.1, is_normalized=True),
        Point(x + 0.05, 0.2, is_normalized=True),
        is_normalized=True,
    )
    w = Word(text=text, bounding_box=bbox, ocr_confidence=1.0)
    if gt is not None:
        w.ground_truth_text = gt
    return w


def _make_line(words: list[Word]) -> Block:
    return Block(
        items=words,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )


def _make_page(line: Block) -> Page:
    para = Block(
        items=[line],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
    )
    outer = Block(
        items=[para],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.BLOCK,
    )
    return Page(width=100, height=100, page_index=0, blocks=[outer])


def test_block_copy_ocr_to_gt_processes_every_word():
    """Even when word #0 returns True (mutation happened), word #1 must
    still be visited and mutated. The any([...]) -> any(results) refactor
    must not introduce short-circuiting."""
    words = [_make_word(0.1, "alpha"), _make_word(0.3, "beta")]
    line = _make_line(words)

    with patch.object(Word, "copy_ocr_to_ground_truth", autospec=True) as m:
        m.return_value = True  # first call's truthy result must NOT short-circuit
        result = line.copy_ocr_to_ground_truth()
    assert result is True
    assert m.call_count == 2


def test_block_copy_gt_to_ocr_processes_every_word():
    words = [_make_word(0.1, "a", gt="A"), _make_word(0.3, "b", gt="B")]
    line = _make_line(words)
    with patch.object(Word, "copy_ground_truth_to_ocr", autospec=True) as m:
        m.return_value = True
        result = line.copy_ground_truth_to_ocr()
    assert result is True
    assert m.call_count == 2


def test_block_clear_ground_truth_processes_every_word():
    words = [_make_word(0.1, "a", gt="A"), _make_word(0.3, "b", gt="B")]
    line = _make_line(words)
    with patch.object(Word, "clear_ground_truth", autospec=True) as m:
        m.return_value = True
        result = line.clear_ground_truth()
    assert result is True
    assert m.call_count == 2


def test_page_copy_ocr_to_gt_processes_every_word():
    words = [_make_word(0.1, "alpha"), _make_word(0.3, "beta")]
    page = _make_page(_make_line(words))
    with patch.object(Word, "copy_ocr_to_ground_truth", autospec=True) as m:
        m.return_value = True
        result = page.copy_ocr_to_ground_truth()
    assert result is True
    assert m.call_count == 2


def test_page_copy_gt_to_ocr_processes_every_word():
    words = [_make_word(0.1, "a", gt="A"), _make_word(0.3, "b", gt="B")]
    page = _make_page(_make_line(words))
    with patch.object(Word, "copy_ground_truth_to_ocr", autospec=True) as m:
        m.return_value = True
        result = page.copy_ground_truth_to_ocr()
    assert result is True
    assert m.call_count == 2


def test_page_clear_ground_truth_processes_every_word():
    words = [_make_word(0.1, "a", gt="A"), _make_word(0.3, "b", gt="B")]
    page = _make_page(_make_line(words))
    with patch.object(Word, "clear_ground_truth", autospec=True) as m:
        m.return_value = True
        result = page.clear_ground_truth()
    assert result is True
    assert m.call_count == 2


def test_block_copy_ocr_to_gt_returns_false_when_no_words_mutated():
    """The any() over results still reports False when nothing was
    actually copied — the eager reform must not flip the return value."""
    words = [_make_word(0.1, "a"), _make_word(0.3, "b")]
    line = _make_line(words)
    with patch.object(Word, "copy_ocr_to_ground_truth", autospec=True) as m:
        m.return_value = False
        result = line.copy_ocr_to_ground_truth()
    assert result is False
    assert m.call_count == 2
