"""Tests for ground truth matching functionality."""

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.ground_truth_matching import (
    update_line_with_ground_truth_replace_words,
    WordDiffOpCodes,
)
from pd_book_tools.ocr.word import Word


class TestGroundTruthMatching:
    """Test ground truth matching functions."""

    def test_update_line_with_ground_truth_replace_words_preserves_existing_unmatched(
        self,
    ):
        """Test that replace words operation preserves existing unmatched ground truth words."""
        # Create a line with some OCR words
        words = [
            Word(
                text="hello",
                bounding_box=BoundingBox.from_ltrb(0, 0, 50, 20, is_normalized=False),
            ),
            Word(
                text="world",
                bounding_box=BoundingBox.from_ltrb(60, 0, 110, 20, is_normalized=False),
            ),
        ]

        line = Block(
            items=words,
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )

        # Pre-populate the line with some unmatched ground truth words
        # (as would happen from previous "insert" operations)
        line.unmatched_ground_truth_words = [
            (0, "previous"),
            (1, "unmatched"),
        ]

        # Create a replace operation
        op = WordDiffOpCodes(
            word_tag="replace",
            ocr_word_1=0,
            ocr_word_2=2,
            gt_word_1=0,
            gt_word_2=3,  # More GT words than OCR words
        )

        ocr_line_tuple = ("hello", "world")
        ground_truth_tuple = ("hi", "there", "extra")

        # Call the function
        combined_ocr_word_nbrs, new_combined_words = (
            update_line_with_ground_truth_replace_words(
                line=line,
                op=op,
                ocr_line_tuple=ocr_line_tuple,
                ground_truth_tuple=ground_truth_tuple,
                auto_combine=False,  # Disable auto combine for predictable behavior
            )
        )

        # The function should preserve existing unmatched words
        # and add new unmatched words from the current operation
        assert line.unmatched_ground_truth_words is not None

        # Should contain the original unmatched words plus the new one
        unmatched_texts = [word[1] for word in line.unmatched_ground_truth_words]
        assert "previous" in unmatched_texts
        assert "unmatched" in unmatched_texts
        assert "extra" in unmatched_texts

        # Should have 3 total unmatched words
        assert len(line.unmatched_ground_truth_words) == 3

    def test_update_line_with_ground_truth_multiple_replace_operations(self):
        """Test that multiple replace operations preserve all unmatched ground truth words."""
        # Create a line with OCR words
        words = [
            Word(
                text="hello",
                bounding_box=BoundingBox.from_ltrb(0, 0, 50, 20, is_normalized=False),
            ),
        ]

        line = Block(
            items=words,
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )

        # First, simulate an insert operation that adds unmatched words
        line.unmatched_ground_truth_words = [(0, "inserted_word")]

        # Then call a replace operation that should preserve the existing unmatched words
        op = WordDiffOpCodes(
            word_tag="replace",
            ocr_word_1=0,
            ocr_word_2=1,
            gt_word_1=0,
            gt_word_2=2,  # More GT words than OCR words
        )

        ocr_line_tuple = ("hello",)
        ground_truth_tuple = ("hi", "extra_from_replace")

        # Call the function - this should preserve the inserted_word and add extra_from_replace
        combined_ocr_word_nbrs, new_combined_words = (
            update_line_with_ground_truth_replace_words(
                line=line,
                op=op,
                ocr_line_tuple=ocr_line_tuple,
                ground_truth_tuple=ground_truth_tuple,
                auto_combine=False,
            )
        )

        # Should have both the original and new unmatched words
        assert line.unmatched_ground_truth_words is not None
        unmatched_texts = [word[1] for word in line.unmatched_ground_truth_words]

        # Should contain both the original inserted word and the new extra word
        assert "inserted_word" in unmatched_texts, (
            "Original unmatched word should be preserved"
        )
        assert "extra_from_replace" in unmatched_texts, (
            "New unmatched word should be added"
        )
        assert len(line.unmatched_ground_truth_words) == 2, (
            "Should have exactly 2 unmatched words"
        )

    def test_update_line_with_ground_truth_replace_words_empty_initial_list(self):
        """Test that function works correctly when starting with empty unmatched list."""
        words = [
            Word(
                text="hello",
                bounding_box=BoundingBox.from_ltrb(0, 0, 50, 20, is_normalized=False),
            ),
        ]

        line = Block(
            items=words,
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )

        # Start with empty list (this is the normal case)
        line.unmatched_ground_truth_words = []

        op = WordDiffOpCodes(
            word_tag="replace",
            ocr_word_1=0,
            ocr_word_2=1,
            gt_word_1=0,
            gt_word_2=2,  # More GT words than OCR words
        )

        ocr_line_tuple = ("hello",)
        ground_truth_tuple = ("hi", "extra")

        combined_ocr_word_nbrs, new_combined_words = (
            update_line_with_ground_truth_replace_words(
                line=line,
                op=op,
                ocr_line_tuple=ocr_line_tuple,
                ground_truth_tuple=ground_truth_tuple,
                auto_combine=False,
            )
        )

        # Should have one unmatched word
        assert line.unmatched_ground_truth_words is not None
        assert len(line.unmatched_ground_truth_words) == 1
        assert line.unmatched_ground_truth_words[0][1] == "extra"
