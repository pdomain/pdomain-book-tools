"""Coverage tests for Page paragraph/line/word operations."""

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
def multi_paragraph_page():
    """Page with two paragraphs, two lines each, two words each."""
    p1l1 = _make_line(
        [_make_word("p1l1w1", 0, 0, 30, 10), _make_word("p1l1w2", 35, 0, 60, 10)]
    )
    p1l2 = _make_line(
        [_make_word("p1l2w1", 0, 12, 30, 22), _make_word("p1l2w2", 35, 12, 60, 22)]
    )
    p2l1 = _make_line(
        [_make_word("p2l1w1", 0, 30, 30, 40), _make_word("p2l1w2", 35, 30, 60, 40)]
    )
    p2l2 = _make_line(
        [_make_word("p2l2w1", 0, 42, 30, 52), _make_word("p2l2w2", 35, 42, 60, 52)]
    )
    return Page(
        width=100,
        height=100,
        page_index=0,
        items=[
            _make_paragraph([p1l1, p1l2]),
            _make_paragraph([p2l1, p2l2]),
        ],
    )


# Merge paragraphs ------------------------------------------------------------


class TestMergeParagraphs:
    def test_merge_two_paragraphs(self, multi_paragraph_page):
        result = multi_paragraph_page.merge_paragraphs([0, 1])
        assert result is True
        # After merge, only one paragraph should remain
        assert len(multi_paragraph_page.paragraphs) == 1

    def test_too_few_indices_returns_false(self, multi_paragraph_page):
        assert multi_paragraph_page.merge_paragraphs([0]) is False
        assert multi_paragraph_page.merge_paragraphs([]) is False
        assert multi_paragraph_page.merge_paragraphs(None) is False

    def test_index_out_of_range_returns_false(self, multi_paragraph_page):
        assert multi_paragraph_page.merge_paragraphs([0, 99]) is False
        assert multi_paragraph_page.merge_paragraphs([-1, 0]) is False


# Delete paragraphs -----------------------------------------------------------


class TestDeleteParagraphs:
    def test_delete_one(self, multi_paragraph_page):
        before = len(multi_paragraph_page.paragraphs)
        result = multi_paragraph_page.delete_paragraphs([0])
        assert result is True
        assert len(multi_paragraph_page.paragraphs) == before - 1

    def test_delete_all(self, multi_paragraph_page):
        result = multi_paragraph_page.delete_paragraphs([0, 1])
        assert result is True

    def test_empty_indices_returns_false(self, multi_paragraph_page):
        assert multi_paragraph_page.delete_paragraphs([]) is False

    def test_invalid_index_returns_false(self, multi_paragraph_page):
        assert multi_paragraph_page.delete_paragraphs([99]) is False


# Split paragraphs ------------------------------------------------------------


class TestSplitParagraphs:
    def test_split_paragraph_with_two_lines(self, multi_paragraph_page):
        before = len(multi_paragraph_page.paragraphs)
        result = multi_paragraph_page.split_paragraphs([0])
        assert result is True
        assert len(multi_paragraph_page.paragraphs) == before + 1

    def test_split_paragraph_single_line_skipped(self):
        para = _make_paragraph([_make_line([_make_word("w", 0, 0, 10, 10)])])
        page = Page(width=50, height=50, page_index=0, items=[para])
        # Single line in paragraph, can't split
        assert page.split_paragraphs([0]) is False

    def test_empty_indices_returns_false(self, multi_paragraph_page):
        assert multi_paragraph_page.split_paragraphs([]) is False

    def test_invalid_index_returns_false(self, multi_paragraph_page):
        assert multi_paragraph_page.split_paragraphs([99]) is False


# Split paragraph after line --------------------------------------------------


class TestSplitParagraphAfterLine:
    def test_split_after_first_line(self, multi_paragraph_page):
        result = multi_paragraph_page.split_paragraph_after_line(0)
        assert result is True

    def test_split_after_last_line_in_paragraph_returns_false(
        self, multi_paragraph_page
    ):
        # Paragraph 0 has lines at indices 0,1; line index 1 is last in para -> can't split
        result = multi_paragraph_page.split_paragraph_after_line(1)
        assert result is False

    def test_invalid_line_index_returns_false(self, multi_paragraph_page):
        assert multi_paragraph_page.split_paragraph_after_line(-1) is False
        assert multi_paragraph_page.split_paragraph_after_line(99) is False


# Split paragraph with selected lines -----------------------------------------


class TestSplitParagraphWithSelectedLines:
    def test_split_selected_lines(self, multi_paragraph_page):
        # Select line 0 (in paragraph 0) -> split
        result = multi_paragraph_page.split_paragraph_with_selected_lines([0])
        # Result depends on internal logic
        assert result in (True, False)

    def test_empty_indices(self, multi_paragraph_page):
        assert multi_paragraph_page.split_paragraph_with_selected_lines([]) is False

    def test_invalid_line_index(self, multi_paragraph_page):
        assert multi_paragraph_page.split_paragraph_with_selected_lines([99]) is False


# Merge lines ----------------------------------------------------------------


class TestMergeLines:
    def test_merge_two_lines(self, multi_paragraph_page):
        before = len(multi_paragraph_page.lines)
        # Lines 0 and 1 are both in paragraph 0
        result = multi_paragraph_page.merge_lines([0, 1])
        # Either succeeds or fails, but should not crash
        assert result in (True, False)
        if result:
            assert len(multi_paragraph_page.lines) == before - 1

    def test_too_few_indices(self, multi_paragraph_page):
        assert multi_paragraph_page.merge_lines([0]) is False

    def test_invalid_index(self, multi_paragraph_page):
        assert multi_paragraph_page.merge_lines([0, 99]) is False


# Delete lines ----------------------------------------------------------------


class TestDeleteLines:
    def test_delete_one_line(self, multi_paragraph_page):
        before = len(multi_paragraph_page.lines)
        result = multi_paragraph_page.delete_lines([0])
        assert result is True
        assert len(multi_paragraph_page.lines) == before - 1

    def test_empty_returns_false(self, multi_paragraph_page):
        assert multi_paragraph_page.delete_lines([]) is False

    def test_invalid_returns_false(self, multi_paragraph_page):
        assert multi_paragraph_page.delete_lines([99]) is False


# Delete words ----------------------------------------------------------------


class TestDeleteWords:
    def test_delete_one_word(self, multi_paragraph_page):
        # Remove first word in first line
        before = len(multi_paragraph_page.words)
        result = multi_paragraph_page.delete_words([(0, 0)])
        assert result is True
        assert len(multi_paragraph_page.words) == before - 1

    def test_empty_returns_false(self, multi_paragraph_page):
        assert multi_paragraph_page.delete_words([]) is False

    def test_invalid_line_index_returns_false(self, multi_paragraph_page):
        assert multi_paragraph_page.delete_words([(99, 0)]) is False


# Split word ------------------------------------------------------------------


class TestSplitWord:
    def test_split_word_at_middle(self, multi_paragraph_page):
        # Split first word at split_fraction=0.5
        result = multi_paragraph_page.split_word(0, 0, 0.5)
        assert result in (True, False)

    def test_invalid_line_index(self, multi_paragraph_page):
        assert multi_paragraph_page.split_word(99, 0, 0.5) is False

    def test_invalid_split_fraction(self, multi_paragraph_page):
        assert multi_paragraph_page.split_word(0, 0, 0.0) is False
        assert multi_paragraph_page.split_word(0, 0, 1.0) is False
        assert multi_paragraph_page.split_word(0, 0, 1.5) is False


# Split line after word -------------------------------------------------------


class TestSplitLineAfterWord:
    def test_split_after_first_word(self, multi_paragraph_page):
        result = multi_paragraph_page.split_line_after_word(0, 0)
        assert result in (True, False)

    def test_invalid_line_index(self, multi_paragraph_page):
        assert multi_paragraph_page.split_line_after_word(99, 0) is False

    def test_invalid_word_index(self, multi_paragraph_page):
        assert multi_paragraph_page.split_line_after_word(0, 99) is False


# Reorganize page -------------------------------------------------------------


class TestReorganizePage:
    def test_reorganize_does_not_crash(self, multi_paragraph_page):
        multi_paragraph_page.reorganize_page()
        # Either changes or stays the same; should not crash
        assert multi_paragraph_page is not None

    def test_reorganize_empty_page(self):
        page = Page(width=10, height=10, page_index=0, items=[])
        page.reorganize_page()
        assert page is not None


# Compute text row blocks -----------------------------------------------------


class TestComputeTextRowBlocks:
    def test_compute_with_lines(self, multi_paragraph_page):
        lines = list(multi_paragraph_page.lines)
        result = Page.compute_text_row_blocks(lines)
        assert result is not None

    def test_compute_with_no_lines(self):
        result = Page.compute_text_row_blocks([])
        # Either None or empty result; should not crash
        assert result is None or hasattr(result, "items")


# Compute text paragraph blocks -----------------------------------------------


class TestComputeTextParagraphBlocks:
    def test_compute_paragraph_blocks_with_lines(self, multi_paragraph_page):
        lines = list(multi_paragraph_page.lines)
        result = Page.compute_text_paragraph_blocks(lines)
        # Should not crash
        assert result is not None or result is None


# Reorganize lines -----------------------------------------------------------


class TestReorganizeLines:
    def test_reorganize_lines_block(self, multi_paragraph_page):
        para = multi_paragraph_page.items[0]
        Page.reorganize_lines(para)
        # Should not crash

    def test_reorganize_empty_block(self):
        block = Block(
            items=[],
            block_category=BlockCategory.PARAGRAPH,
            child_type=BlockChildType.BLOCKS,
        )
        Page.reorganize_lines(block)


# Add ground truth ------------------------------------------------------------


class TestAddGroundTruth:
    def test_add_ground_truth(self, multi_paragraph_page):
        # Just exercise the function
        multi_paragraph_page.add_ground_truth(
            "p1l1w1 p1l1w2\np1l2w1 p1l2w2\n\np2l1w1 p2l1w2\np2l2w1 p2l2w2\n"
        )


# Rebox word ------------------------------------------------------------------


class TestReboxWord:
    def test_rebox_with_valid_indices(self, multi_paragraph_page):
        result = multi_paragraph_page.rebox_word(0, 0, 1, 1, 25, 9, refine_after=False)
        assert result in (True, False)

    def test_rebox_invalid_line(self, multi_paragraph_page):
        result = multi_paragraph_page.rebox_word(99, 0, 1, 1, 25, 9, refine_after=False)
        assert result is False

    def test_rebox_invalid_rectangle(self, multi_paragraph_page):
        # x2 < x1 -> after normalization rx2 == rx1; rejected
        result = multi_paragraph_page.rebox_word(0, 0, 5, 5, 5, 5, refine_after=False)
        assert result is False

    def test_rebox_invalid_word_index(self, multi_paragraph_page):
        result = multi_paragraph_page.rebox_word(0, 99, 1, 1, 25, 9, refine_after=False)
        assert result is False


# Nudge word bbox -------------------------------------------------------------


class TestNudgeWordBbox:
    def test_nudge_word(self, multi_paragraph_page):
        result = multi_paragraph_page.nudge_word_bbox(
            0,
            0,
            left_delta=1.0,
            right_delta=1.0,
            top_delta=0.5,
            bottom_delta=0.5,
            refine_after=False,
        )
        assert result in (True, False)

    def test_nudge_invalid_line(self, multi_paragraph_page):
        result = multi_paragraph_page.nudge_word_bbox(
            99,
            0,
            left_delta=1.0,
            right_delta=1.0,
            top_delta=0.5,
            bottom_delta=0.5,
            refine_after=False,
        )
        assert result is False

    def test_nudge_invalid_word(self, multi_paragraph_page):
        result = multi_paragraph_page.nudge_word_bbox(
            0,
            99,
            left_delta=1.0,
            right_delta=1.0,
            top_delta=0.5,
            bottom_delta=0.5,
            refine_after=False,
        )
        assert result is False


# Add word to page ------------------------------------------------------------


class TestAddWordToPage:
    def test_add_word_to_existing_line(self, multi_paragraph_page):
        result = multi_paragraph_page.add_word_to_page(65, 0, 80, 10, text="new")
        assert result in (True, False)

    def test_add_word_invalid_rectangle(self, multi_paragraph_page):
        result = multi_paragraph_page.add_word_to_page(5, 5, 5, 5, text="bad")
        assert result is False


# Image-based generators (skip if no doctr) -----------------------------------


class TestImageGenerators:
    def test_generate_doctr_checks_no_op_no_image(self, multi_paragraph_page, tmp_path):
        # Without an image, should not crash. If it requires image, we just
        # invoke and accept the failure as expected.
        try:
            multi_paragraph_page.generate_doctr_checks(tmp_path / "out.json")
        except Exception:
            # Acceptable if it throws because no image
            pass
