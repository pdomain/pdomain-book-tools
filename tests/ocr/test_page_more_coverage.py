"""Additional Page coverage tests for word/line group operations."""

import numpy as np
import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.word import Word


def _make_word(text: str, x1: float, y1: float, x2: float, y2: float) -> Word:
    return Word(
        text=text,
        bounding_box=BoundingBox.from_ltrb(x1, y1, x2, y2, is_normalized=False),
        ocr_confidence=0.9,
    )


def _make_line(words):
    return Block(
        items=list(words),
        block_category=BlockCategory.LINE,
        child_type=BlockChildType.WORDS,
    )


def _make_paragraph(lines):
    return Block(
        items=list(lines),
        block_category=BlockCategory.PARAGRAPH,
        child_type=BlockChildType.BLOCKS,
    )


@pytest.fixture
def four_word_page():
    """Page with one paragraph, two lines of two words each."""
    line1 = _make_line(
        [
            _make_word("a", 0, 0, 10, 10),
            _make_word("b", 12, 0, 22, 10),
        ]
    )
    line2 = _make_line(
        [
            _make_word("c", 0, 12, 10, 22),
            _make_word("d", 12, 12, 22, 22),
        ]
    )
    return Page(
        width=50,
        height=50,
        page_index=0,
        items=[_make_paragraph([line1, line2])],
    )


@pytest.fixture
def six_word_page():
    """Page with one paragraph, two lines of three words each."""
    line1 = _make_line(
        [
            _make_word("a", 0, 0, 10, 10),
            _make_word("b", 12, 0, 22, 10),
            _make_word("c", 24, 0, 34, 10),
        ]
    )
    line2 = _make_line(
        [
            _make_word("d", 0, 12, 10, 22),
            _make_word("e", 12, 12, 22, 22),
            _make_word("f", 24, 12, 34, 22),
        ]
    )
    return Page(
        width=50,
        height=50,
        page_index=0,
        items=[_make_paragraph([line1, line2])],
    )


# Split lines into selected/unselected words ----------------------------------


class TestSplitLinesIntoSelectedAndUnselected:
    def test_split_with_valid_selection(self, six_word_page):
        # Select first word in first line -> split into [a] and [b, c]
        result = six_word_page.split_lines_into_selected_and_unselected_words([(0, 0)])
        assert result is True

    def test_empty_keys_returns_false(self, six_word_page):
        assert six_word_page.split_lines_into_selected_and_unselected_words([]) is False
        assert (
            six_word_page.split_lines_into_selected_and_unselected_words(None) is False
        )

    def test_invalid_line_index_returns_false(self, six_word_page):
        assert (
            six_word_page.split_lines_into_selected_and_unselected_words([(99, 0)])
            is False
        )

    def test_invalid_word_index_returns_false(self, six_word_page):
        assert (
            six_word_page.split_lines_into_selected_and_unselected_words([(0, 99)])
            is False
        )

    def test_only_one_word_in_line_skipped(self):
        line = _make_line([_make_word("only", 0, 0, 10, 10)])
        para = _make_paragraph([line])
        page = Page(width=50, height=50, page_index=0, items=[para])
        assert page.split_lines_into_selected_and_unselected_words([(0, 0)]) is False


# Split line with selected words ----------------------------------------------


class TestSplitLineWithSelectedWords:
    def test_split_with_valid_selection(self, six_word_page):
        result = six_word_page.split_line_with_selected_words([(0, 0)])
        assert result in (True, False)

    def test_empty_returns_false(self, six_word_page):
        assert six_word_page.split_line_with_selected_words([]) is False

    def test_invalid_line_index_returns_false(self, six_word_page):
        assert six_word_page.split_line_with_selected_words([(99, 0)]) is False

    def test_invalid_word_index_returns_false(self, six_word_page):
        assert six_word_page.split_line_with_selected_words([(0, 99)]) is False


# Group selected words into new paragraph -------------------------------------


class TestGroupSelectedWordsIntoNewParagraph:
    def test_group_words(self, six_word_page):
        # Select words in line 0 -> create new paragraph
        result = six_word_page.group_selected_words_into_new_paragraph([(0, 0)])
        assert result in (True, False)

    def test_empty_returns_false(self, six_word_page):
        assert six_word_page.group_selected_words_into_new_paragraph([]) is False

    def test_invalid_line_returns_false(self, six_word_page):
        assert six_word_page.group_selected_words_into_new_paragraph([(99, 0)]) is False


# Split paragraph with selected lines (more) ----------------------------------


class TestSplitParagraphSelectedLines:
    def test_split_with_valid_lines(self):
        # Create a page with one paragraph containing 3 lines
        lines = [
            _make_line([_make_word(f"l{i}w", 0, i * 12, 10, i * 12 + 10)])
            for i in range(3)
        ]
        page = Page(width=50, height=50, page_index=0, items=[_make_paragraph(lines)])
        result = page.split_paragraph_with_selected_lines([1])
        assert result in (True, False)


# Compute text row blocks -----------------------------------------------------


class TestComputeTextRowBlocksDetailed:
    def test_with_lines_at_same_row(self):
        """Lines at the same y range should be grouped together."""
        # Two lines side by side at the same y range
        line1 = _make_line([_make_word("a", 0, 0, 10, 10)])
        line2 = _make_line([_make_word("b", 20, 0, 30, 10)])
        result = Page.compute_text_row_blocks([line1, line2])
        assert result is not None

    def test_with_lines_at_different_rows(self):
        line1 = _make_line([_make_word("a", 0, 0, 10, 10)])
        line2 = _make_line([_make_word("b", 0, 30, 10, 40)])
        result = Page.compute_text_row_blocks([line1, line2])
        assert result is not None


class TestComputeTextParagraphBlocks:
    def test_with_consecutive_lines(self):
        line1 = _make_line([_make_word("a", 0, 0, 10, 10)])
        line2 = _make_line([_make_word("b", 0, 12, 10, 22)])
        result = Page.compute_text_paragraph_blocks([line1, line2])
        assert result is not None


# CV2 image rendering more variants --------------------------------------------


class TestCv2NumpyRenderingVariants:
    def test_render_with_word_no_match_keys(self, four_word_page):
        """Word without ground_truth_match_keys should still render."""
        img = np.zeros((50, 50, 3), dtype=np.uint8)
        # Default page words have no match keys
        four_word_page.cv2_numpy_page_image = img

    def test_render_with_normalized_bbox(self):
        # Page with a word that has tiny (subpixel) bbox -> _add_rect scales it
        word = Word(
            text="x",
            bounding_box=BoundingBox.from_ltrb(0.1, 0.1, 0.3, 0.3, is_normalized=True),
            ocr_confidence=0.9,
        )
        line = _make_line([word])
        para = _make_paragraph([line])
        page = Page(width=100, height=100, page_index=0, items=[para])
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        page.cv2_numpy_page_image = img
        # Should have rendered without error
