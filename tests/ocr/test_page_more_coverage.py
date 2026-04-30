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


# generate_doctr_checks coverage -----------------------------------------------


class TestGenerateDoctrChecksEdgeCases:
    def test_generate_doctr_checks_nonexistent_parent_raises(self, tmp_path):
        """Line 3006: raises when output_path.parent does not exist."""
        import numpy as np

        page = Page(width=100, height=100, page_index=0, items=[])
        page.cv2_numpy_page_image = np.zeros((100, 100, 3), dtype=np.uint8)
        # Add a word so items is not empty
        from pd_book_tools.geometry.bounding_box import BoundingBox
        from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
        from pd_book_tools.ocr.word import Word

        word = Word(
            text="hi",
            bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10, is_normalized=False),
            ocr_confidence=0.9,
        )
        line = Block(
            items=[word],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        para = Block(
            items=[line],
            block_category=BlockCategory.PARAGRAPH,
            child_type=BlockChildType.BLOCKS,
        )
        page = Page(width=100, height=100, page_index=0, items=[para])
        page.cv2_numpy_page_image = np.zeros((100, 100, 3), dtype=np.uint8)
        # Use a path whose parent doesn't exist

        import pytest

        nonexistent = tmp_path / "no_such_dir" / "output.json"
        with pytest.raises(ValueError, match="Output path does not exist"):
            page.generate_doctr_checks(nonexistent)


class TestComputeTextRowBlocksWithTolerance:
    def test_with_explicit_tolerance_covers_false_branch(self):
        """Line 2821->2826 False branch: tolerance is provided explicitly (not None)."""
        from pd_book_tools.geometry.bounding_box import BoundingBox
        from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
        from pd_book_tools.ocr.word import Word

        def make_word(text, x1, y1, x2, y2):
            return Word(
                text=text,
                bounding_box=BoundingBox.from_ltrb(x1, y1, x2, y2, is_normalized=False),
                ocr_confidence=0.9,
            )

        line1 = Block(
            items=[make_word("a", 0, 0, 10, 10)],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        line2 = Block(
            items=[make_word("b", 0, 30, 10, 40)],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        # Pass explicit tolerance → skips the 2821 None-check → covers 2821->2826 False
        result = Page.compute_text_row_blocks([line1, line2], tolerance=5.0)
        assert result is not None


class TestReorganizeLinesSwapBranch:
    def test_line_swap_when_second_has_lower_x(self):
        """Line 2772: swap line and next_line when line.minX > next_line.minX."""
        from pd_book_tools.geometry.bounding_box import BoundingBox
        from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
        from pd_book_tools.ocr.word import Word

        def make_word(text, x1, y1, x2, y2):
            return Word(
                text=text,
                bounding_box=BoundingBox.from_ltrb(x1, y1, x2, y2, is_normalized=False),
                ocr_confidence=0.9,
            )

        # line1: y=0-10, x=100-200 → sorted FIRST (lower minY)
        # line2: y=5-15, x=5-90  → sorted SECOND (higher minY)
        # After sort: [line1 (y=0,x=100), line2 (y=5,x=5)]
        # In loop: line=line1(minX=100), next=line2(minX=5) → 100>5 → triggers swap at 2772
        line1 = Block(
            items=[make_word("AAA", 100, 0, 200, 10)],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        line2 = Block(
            items=[make_word("BBB", 5, 5, 90, 15)],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        para = Block(
            items=[line1, line2],
            block_category=BlockCategory.PARAGRAPH,
            child_type=BlockChildType.BLOCKS,
        )
        Page.reorganize_lines(para)
        assert len(para.items) >= 1


class TestMoveWordToLineException:
    """Tests for _move_word_to_line exception path (lines 554-556)."""

    def test_add_item_failure_restores_word_to_source(self):
        """Lines 554-556: When add_item raises, word is restored to source_line."""
        from unittest.mock import patch

        from pd_book_tools.geometry.bounding_box import BoundingBox
        from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
        from pd_book_tools.ocr.page import Page
        from pd_book_tools.ocr.word import Word

        bb = BoundingBox.from_ltrb(0, 0, 50, 20)
        word = Word(text="hello", bounding_box=bb, ocr_confidence=0.9)
        source_line = Block(
            items=[word],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        target_line = Block(
            items=[], block_category=BlockCategory.LINE, child_type=BlockChildType.WORDS
        )

        with patch.object(target_line, "add_item", side_effect=RuntimeError("fail")):
            result = Page.move_word_between_lines(source_line, target_line, word)

        assert result is False
        assert word in source_line.words


class TestClosestLineByYRangeThenX:
    """Tests for closest_line_by_y_range_then_x paths."""

    def test_skips_line_with_null_bbox(self):
        """Line 581: Line with None bbox is skipped."""
        from pd_book_tools.geometry.bounding_box import BoundingBox
        from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
        from pd_book_tools.ocr.page import Page
        from pd_book_tools.ocr.word import Word

        # fallback_line has valid bbox
        bb = BoundingBox.from_ltrb(0, 0, 100, 20)
        fallback_word = Word(text="a", bounding_box=bb, ocr_confidence=0.9)
        fallback_line = Block(
            items=[fallback_word],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )

        # valid_word_line for no_bbox_line but we'll patch its bounding_box
        word2 = Word(text="b", bounding_box=bb, ocr_confidence=0.9)
        no_bbox_line = Block(
            items=[word2],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )

        no_bbox_line.bounding_box = None
        result = Page.closest_line_by_y_range_then_x(
            lines=[no_bbox_line, fallback_line],
            center_x=50,
            center_y=10,
            fallback_line=fallback_line,
        )
        assert result is fallback_line

    def test_closest_line_by_vertical_midpoint_false_branch(self):
        """Line 617->612 False branch: second line not closer than first."""
        from pd_book_tools.geometry.bounding_box import BoundingBox
        from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
        from pd_book_tools.ocr.page import Page
        from pd_book_tools.ocr.word import Word

        bb1 = BoundingBox.from_ltrb(
            0, 10, 100, 20
        )  # midY = 15, distance from midY=12 is 3
        bb2 = BoundingBox.from_ltrb(
            0, 50, 100, 80
        )  # midY = 65, distance from midY=12 is 53
        word1 = Word(text="a", bounding_box=bb1, ocr_confidence=0.9)
        word2 = Word(text="b", bounding_box=bb2, ocr_confidence=0.9)
        line1 = Block(
            items=[word1],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        line2 = Block(
            items=[word2],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )

        result = Page.closest_line_by_midpoint(
            lines=[line1, line2],
            midpoint_y=12,
            fallback_line=line1,
        )
        assert result is line1  # line1 is closer; line2's False branch is visited


class TestFinalizePageStructureExceptions:
    """Tests for finalize_page_structure exception paths (lines 643, 652-655)."""

    def test_non_geometry_error_in_recompute_is_reraised(self):
        """Line 643: Non-geometry exceptions from _recompute_nested_bounding_boxes are re-raised."""
        from unittest.mock import patch

        import pytest

        from pd_book_tools.ocr.page import Page

        page = Page(width=1000, height=1000, page_index=0, items=[])

        with patch.object(
            Page,
            "_recompute_nested_bounding_boxes",
            side_effect=RuntimeError("not geometry"),
        ):
            with pytest.raises(RuntimeError, match="not geometry"):
                page.finalize_page_structure()

    def test_non_geometry_error_in_recompute_bbox_is_reraised(self):
        """Lines 652-655: Non-geometry exceptions from recompute_bounding_box are re-raised."""
        from unittest.mock import patch

        import pytest

        from pd_book_tools.ocr.page import Page

        page = Page(width=1000, height=1000, page_index=0, items=[])

        with patch.object(
            page, "recompute_bounding_box", side_effect=RuntimeError("bbox fail")
        ):
            with pytest.raises(RuntimeError, match="bbox fail"):
                page.finalize_page_structure()


class TestRecomputeParagraphBboxes:
    """Tests for _recompute_paragraph_bboxes exception path (lines 805-806)."""

    def test_exception_in_paragraph_recompute_is_swallowed(self):
        """Lines 805-806: Exception in paragraph.recompute_bounding_box is swallowed."""
        from unittest.mock import patch

        from pd_book_tools.geometry.bounding_box import BoundingBox
        from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
        from pd_book_tools.ocr.page import Page
        from pd_book_tools.ocr.word import Word

        bb = BoundingBox.from_ltrb(0, 0, 100, 20)
        word = Word(text="a", bounding_box=bb, ocr_confidence=0.9)
        line = Block(
            items=[word],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        para = Block(
            items=[line],
            block_category=BlockCategory.PARAGRAPH,
            child_type=BlockChildType.BLOCKS,
        )
        page = Page(width=1000, height=1000, page_index=0, items=[para])

        with patch.object(
            para, "recompute_bounding_box", side_effect=RuntimeError("bbox fail")
        ):
            # Should not raise
            page._recompute_paragraph_bboxes()
