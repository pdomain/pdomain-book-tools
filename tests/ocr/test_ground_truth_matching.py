"""Tests for ground truth matching functionality."""

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.ground_truth_matching import (
    try_matching_combined_words,
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

    def test_no_combined_words_found_with_misspelled_ocr(self):
        """Test that no combined words are found when OCR has misspellings that don't combine well."""
        # Create OCR words with misspellings: ['tbe', 'Jounding','of','tbe', 'Gopernment']
        words = [
            Word(
                text="tbe",
                bounding_box=BoundingBox.from_ltrb(0, 0, 30, 20, is_normalized=False),
            ),
            Word(
                text="Jounding",
                bounding_box=BoundingBox.from_ltrb(35, 0, 100, 20, is_normalized=False),
            ),
            Word(
                text="of",
                bounding_box=BoundingBox.from_ltrb(
                    105, 0, 125, 20, is_normalized=False
                ),
            ),
            Word(
                text="tbe",
                bounding_box=BoundingBox.from_ltrb(
                    130, 0, 160, 20, is_normalized=False
                ),
            ),
            Word(
                text="Gopernment",
                bounding_box=BoundingBox.from_ltrb(
                    165, 0, 245, 20, is_normalized=False
                ),
            ),
        ]

        line = Block(
            items=words,
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )

        # Ground truth: 'The Founding of the Government'
        ocr_line_tuple = ("tbe", "Jounding", "of", "tbe", "Gopernment")
        ground_truth_tuple = ("The", "Founding", "of", "the", "Government")

        # Call the function to update the line with ground truth
        from pd_book_tools.ocr.ground_truth_matching import (
            update_line_with_ground_truth,
        )

        update_line_with_ground_truth(
            line=line,
            ocr_line_tuple=ocr_line_tuple,
            ground_truth_tuple=ground_truth_tuple,
            auto_combine=True,  # Enable auto combine to test that no combinations are found
        )

        # Verify no words were combined (all words should still exist as separate entities)
        assert len(line.words) == 5, "Should still have 5 separate words"

        # Check that each word has ground truth text assigned (from the replace operations)
        expected_gt_texts = ["The", "Founding", "of", "the", "Government"]
        for i, word in enumerate(line.words):
            assert word.ground_truth_text == expected_gt_texts[i], (
                f"Word {i} should have ground truth '{expected_gt_texts[i]}', "
                f"but got '{word.ground_truth_text}'"
            )

        # Verify that no words have been marked as combined
        for word in line.words:
            # Check that no word has been marked as the result of a combination
            assert (
                word.ground_truth_match_keys.get("match_type")
                != "difflib-line-replace-word-replace-combined"
            ), f"Word '{word.text}' should not be marked as combined"

    def test_try_matching_combined_words_individual_scores_higher(self):
        """Test case where individual word matches better than combined."""

        # Helper to create a Word object for testing
        def create_test_word(text, x=0, y=0, width=10, height=10):
            top_left = Point(x=x, y=y)
            bottom_right = Point(x=x + width, y=y + height)
            bbox = BoundingBox(top_left=top_left, bottom_right=bottom_right)
            return Word(text=text, bounding_box=bbox, ocr_confidence=0.9)

        # Create OCR words: "hello" and "world"
        ocr_words = [create_test_word("hello", 0, 0), create_test_word("world", 20, 0)]

        # OCR tuple matches the words
        ocr_tuple = ("hello", "world")

        # Ground truth has perfect matches for individual words
        gt_tuple = ("hello", "world")

        # Call the function
        result = try_matching_combined_words(ocr_words, ocr_tuple, gt_tuple)

        # Should return empty list since individual words score 100% each
        # and combining them would score lower
        assert len(result) == 0, (
            "Should not combine when individual words score perfectly"
        )

    def test_try_matching_combined_words_combination_scores_higher(self):
        """Test case where combination matches better than individuals."""

        # Helper to create a Word object for testing
        def create_test_word(text, x=0, y=0, width=10, height=10):
            top_left = Point(x=x, y=y)
            bottom_right = Point(x=x + width, y=y + height)
            bbox = BoundingBox(top_left=top_left, bottom_right=bottom_right)
            return Word(text=text, bounding_box=bbox, ocr_confidence=0.9)

        # Create OCR words that when combined match GT better
        ocr_words = [create_test_word("hel", 0, 0), create_test_word("lo", 15, 0)]

        ocr_tuple = ("hel", "lo")

        # Ground truth has a single word that matches the combination
        gt_tuple = ("hello",)

        result = try_matching_combined_words(ocr_words, ocr_tuple, gt_tuple)

        # Should combine since "hel" + "lo" = "hello" matches GT better than individual words
        assert len(result) > 0, "Should combine when combination scores higher"
        if result:
            combined_word = result[0][3]  # The combined Word object
            assert combined_word.text == "hello", (
                f"Expected combined text 'hello', got '{combined_word.text}'"
            )
            assert combined_word.ground_truth_text == "hello", (
                f"Expected GT text 'hello', got '{combined_word.ground_truth_text}'"
            )
