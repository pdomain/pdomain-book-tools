"""Coverage tests for page.py rendering/editing helpers (lines 2068-2415)."""

from unittest.mock import PropertyMock, patch

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


class TestReboxWordExceptionHandling:
    """Test exception handling and error logging in rebox_word."""

    @pytest.fixture
    def simple_page(self):
        line = _make_line([_make_word("hello", 0, 0, 50, 20)])
        para = _make_paragraph([line])
        return Page(width=1000, height=1000, page_index=0, blocks=[para])

    def test_rebox_word_catches_generic_exception(self, simple_page):
        """rebox_word catches exceptions and returns False (lines 2123-2130)."""
        # Mock validated_line_words to raise an exception
        with patch.object(
            simple_page,
            "validated_line_words",
            side_effect=RuntimeError("Simulated error"),
        ):
            result = simple_page.rebox_word(0, 0, 10, 10, 40, 20)
            assert result is False


class TestAddWordToPageExceptionHandling:
    """Test exception handling and error logging in add_word_to_page."""

    @pytest.fixture
    def simple_page(self):
        line = _make_line([_make_word("hello", 0, 0, 50, 20)])
        para = _make_paragraph([line])
        return Page(width=1000, height=1000, page_index=0, blocks=[para])

    def test_add_word_catches_generic_exception(self, simple_page):
        """add_word_to_page catches exceptions and returns False (lines 2213-2215)."""
        # Mock lines property to raise an exception
        with patch.object(
            type(simple_page),
            "lines",
            new_callable=PropertyMock,
            side_effect=RuntimeError("Simulated error"),
        ):
            result = simple_page.add_word_to_page(10, 10, 40, 20, text="new")
            assert result is False


class TestSplitLineWithSelectedWordsEdgeCases:
    """Test edge cases and error paths in split_line_with_selected_words."""

    @pytest.fixture
    def multi_line_page(self):
        line1 = _make_line(
            [
                _make_word("word1", 0, 0, 20, 10),
                _make_word("word2", 25, 0, 45, 10),
            ]
        )
        line2 = _make_line(
            [
                _make_word("word3", 0, 15, 20, 25),
                _make_word("word4", 25, 15, 45, 25),
            ]
        )
        line3 = _make_line(
            [
                _make_word("word5", 0, 30, 20, 40),
                _make_word("word6", 25, 30, 45, 40),
            ]
        )
        para = _make_paragraph([line1, line2, line3])
        return Page(width=100, height=100, page_index=0, blocks=[para])

    def test_split_exception_in_main_try_block(self, multi_line_page):
        """split_line_with_selected_words exception handling (2427-2433)."""
        # Cause an exception by mocking paragraphs to raise
        with patch.object(
            type(multi_line_page),
            "paragraphs",
            new_callable=PropertyMock,
            side_effect=RuntimeError("Test error"),
        ):
            result = multi_line_page.split_line_with_selected_words([(0, 0)])
            assert result is False

    def test_split_unique_paragraphs_deduplication(self, multi_line_page):
        """split_line_with_selected_words deduplicates paragraphs (2381-2384)."""
        # If we select words across multiple lines in the same paragraph,
        # the unique_paragraphs list should have the paragraph just once.
        # Select words from line 0 and line 1 (same paragraph)
        result = multi_line_page.split_line_with_selected_words([(0, 0), (1, 0)])
        assert result is True
        assert len(multi_line_page.paragraphs) >= 1

    def test_split_single_paragraph_same_paragraph(self, multi_line_page):
        """split_line_with_selected_words path when selections from single para (2386-2408)."""
        # All selections are from the same paragraph -> len(unique_paragraphs) == 1
        # Words should be added to the existing paragraph (2404-2407)
        result = multi_line_page.split_line_with_selected_words([(0, 0), (1, 1)])
        assert result is True

    def test_split_multiple_paragraphs_creates_new_para(self):
        """split_line_with_selected_words creates new para for cross-para selections (2409-2419)."""
        # Create a page with two separate paragraphs
        line1 = _make_line(
            [
                _make_word("word1", 0, 0, 20, 10),
                _make_word("word2", 25, 0, 45, 10),
            ]
        )
        line2 = _make_line(
            [
                _make_word("word3", 0, 15, 20, 25),
                _make_word("word4", 25, 15, 45, 25),
            ]
        )
        para1 = _make_paragraph([line1])
        para2 = _make_paragraph([line2])
        page = Page(width=100, height=100, page_index=0, blocks=[para1, para2])

        # Select from both paragraphs
        paras_before = len(page.paragraphs)
        result = page.split_line_with_selected_words([(0, 0), (1, 1)])
        assert result is True
        assert len(page.paragraphs) >= paras_before


class TestSplitLinesIntoSelectedAndUnselectedWordsEdgeCases:
    """Test edge cases in split_lines_into_selected_and_unselected_words."""

    @pytest.fixture
    def multi_line_page(self):
        line1 = _make_line(
            [
                _make_word("word1", 0, 0, 20, 10),
                _make_word("word2", 25, 0, 45, 10),
            ]
        )
        line2 = _make_line(
            [
                _make_word("word3", 0, 15, 20, 25),
                _make_word("word4", 25, 15, 45, 25),
            ]
        )
        line3 = _make_line(
            [
                _make_word("word5", 0, 30, 20, 40),
                _make_word("word6", 25, 30, 45, 40),
            ]
        )
        para = _make_paragraph([line1, line2, line3])
        return Page(width=100, height=100, page_index=0, blocks=[para])

    def test_split_with_valid_selection(self, multi_line_page):
        """split_lines_into_selected_and_unselected successfully splits lines."""
        result = multi_line_page.split_lines_into_selected_and_unselected_words(
            [(0, 0)]
        )
        assert result is True
        assert len(multi_line_page.paragraphs) >= 1


class TestRenderingHelpersIntegration:
    """Integration tests for rendering helpers working together."""

    def test_rebox_then_split(self):
        """Test reboxing a word then splitting its line."""
        line = _make_line(
            [
                _make_word("word1", 0, 0, 20, 10),
                _make_word("word2", 25, 0, 45, 10),
            ]
        )
        para = _make_paragraph([line])
        page = Page(width=100, height=100, page_index=0, blocks=[para])

        result = page.rebox_word(0, 0, 5, 5, 25, 15, refine_after=False)
        assert result is True

        result = page.split_line_with_selected_words([(0, 0)])
        assert result is True

    def test_add_word_then_split(self):
        """Test adding a word then splitting its line."""
        line = _make_line(
            [
                _make_word("word1", 0, 0, 20, 10),
                _make_word("word2", 25, 0, 45, 10),
            ]
        )
        para = _make_paragraph([line])
        page = Page(width=100, height=100, page_index=0, blocks=[para])

        result = page.add_word_to_page(50, 0, 70, 10, text="new")
        assert result is True

        result = page.split_line_with_selected_words([(0, 2)])
        assert result is True
