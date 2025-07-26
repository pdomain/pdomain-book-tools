import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.block import BlockChildType, BlockCategory


def test_block_initialization(sample_block1):
    assert sample_block1.bounding_box == BoundingBox.from_ltrb(0, 0, 20, 10)
    assert sample_block1.child_type == BlockChildType.WORDS
    assert sample_block1.block_category == BlockCategory.LINE
    assert sample_block1.block_labels == ["labelline1"]
    assert len(sample_block1.items) == 2
    assert sample_block1.items[0].text == "word1"
    assert sample_block1.items[1].text == "word2"


def test_block_methods(sample_block1):
    assert sample_block1.text == "word1 word2"
    assert sample_block1.words == sample_block1.items
    assert sample_block1.lines == [sample_block1]


def test_block_scores(sample_block1):
    assert sample_block1.ocr_confidence_scores() == pytest.approx([0.9, 0.8])
    assert sample_block1.mean_ocr_confidence() == pytest.approx(0.85)


def test_block_to_dict(sample_block1, sample_line1, sample_two_paragraph_block1):
    block_dict = sample_block1.to_dict()
    assert block_dict["bounding_box"] == sample_block1.bounding_box.to_dict()
    assert block_dict["child_type"] == BlockChildType.WORDS.value
    assert block_dict["block_category"] == BlockCategory.LINE.value
    assert block_dict["block_labels"] == ["labelline1"]
    assert len(block_dict["items"]) == 2
    assert block_dict["items"][0] == sample_line1[0].to_dict()
    assert block_dict["items"][1] == sample_line1[1].to_dict()
    twoP = sample_two_paragraph_block1.to_dict()
    assert twoP["child_type"] == BlockChildType.BLOCKS.value
    assert twoP["block_category"] == BlockCategory.BLOCK.value
    assert len(twoP["items"]) == 2
    assert len(twoP["items"][0]["items"]) == 2
    assert len(twoP["items"][1]["items"]) == 1


def test_paragraph(
    sample_paragraph_block1,
    sample_line1,
    sample_line2,
    sample_line3,
    sample_block1,
    sample_block2,
    sample_block3,
):
    assert sample_paragraph_block1.text == "word1 word2\nword3 word4\nword5 word6"
    assert sample_paragraph_block1.words == [
        *sample_line1,
        *sample_line2,
        *sample_line3,
    ]
    assert sample_paragraph_block1.lines == [
        sample_block1,
        sample_block2,
        sample_block3,
    ]
    assert sample_paragraph_block1.items == [
        sample_block1,
        sample_block2,
        sample_block3,
    ]
    assert sample_paragraph_block1.mean_ocr_confidence() == pytest.approx(0.85)
    assert sample_paragraph_block1.ocr_confidence_scores() == pytest.approx(
        [0.9, 0.8, 0.9, 0.8, 0.9, 0.8]
    )
    assert sample_paragraph_block1.bounding_box == BoundingBox.from_ltrb(0, 0, 20, 30)
    assert sample_paragraph_block1.child_type == BlockChildType.BLOCKS
    assert sample_paragraph_block1.block_category == BlockCategory.PARAGRAPH
    assert sample_paragraph_block1.block_labels == ["labelparagraph1"]
    assert len(sample_paragraph_block1.items) == 3
    assert sample_paragraph_block1.items[0] == sample_block1
    assert sample_paragraph_block1.items[1] == sample_block2
    assert sample_paragraph_block1.items[2] == sample_block3


def test_two_paragraph_block(
    sample_two_paragraph_block1,
    sample_line1,
    sample_line2,
    sample_line3,
    sample_block1,
    sample_block2,
    sample_block3,
):
    assert sample_two_paragraph_block1.text == "word1 word2\nword3 word4\n\nword5 word6"
    assert sample_two_paragraph_block1.words == [
        *sample_line1,
        *sample_line2,
        *sample_line3,
    ]
    assert sample_two_paragraph_block1.lines == [
        sample_block1,
        sample_block2,
        sample_block3,
    ]
    assert len(sample_two_paragraph_block1.items) == 2
    assert len(sample_two_paragraph_block1.items[0].items) == 2
    assert len(sample_two_paragraph_block1.items[1].items) == 1
    assert sample_two_paragraph_block1.items[0].items == [
        sample_block1,
        sample_block2,
    ]
    assert sample_two_paragraph_block1.items[1].items == [sample_block3]
    assert sample_two_paragraph_block1.mean_ocr_confidence() == pytest.approx(0.85)
    assert sample_two_paragraph_block1.ocr_confidence_scores() == pytest.approx(
        [0.9, 0.8, 0.9, 0.8, 0.9, 0.8]
    )
    assert sample_two_paragraph_block1.bounding_box == BoundingBox.from_ltrb(
        0, 0, 20, 30
    )
    assert sample_two_paragraph_block1.child_type == BlockChildType.BLOCKS
    assert sample_two_paragraph_block1.block_category == BlockCategory.BLOCK
    assert sample_two_paragraph_block1.block_labels == ["labelparagraph2"]
    assert len(sample_two_paragraph_block1.items) == 2
    assert sample_two_paragraph_block1.items[0].items == [sample_block1, sample_block2]
    assert sample_two_paragraph_block1.items[1].items == [sample_block3]


def test_remove_ground_truth_words_block(sample_block1):
    """Test remove_ground_truth method for a block containing words"""
    # Setup: Add ground truth data to words
    word1, word2 = sample_block1.items
    word1.ground_truth_text = "truth1"
    word1.ground_truth_bounding_box = BoundingBox.from_ltrb(0, 0, 10, 10)
    word2.ground_truth_text = "truth2"
    word2.ground_truth_bounding_box = BoundingBox.from_ltrb(10, 0, 20, 10)
    
    # Add unmatched ground truth words to the block
    sample_block1.unmatched_ground_truth_words = [(0, "unmatched1"), (2, "unmatched2")]
    
    # Verify ground truth data is present before removal
    assert word1.ground_truth_text == "truth1"
    assert word1.ground_truth_bounding_box is not None
    assert word2.ground_truth_text == "truth2"
    assert word2.ground_truth_bounding_box is not None
    assert len(sample_block1.unmatched_ground_truth_words) == 2
    
    # Call remove_ground_truth
    sample_block1.remove_ground_truth()
    
    # Verify ground truth data is removed
    assert word1.ground_truth_text == ""
    assert word1.ground_truth_bounding_box is None
    assert word2.ground_truth_text == ""
    assert word2.ground_truth_bounding_box is None
    assert len(sample_block1.unmatched_ground_truth_words) == 0


def test_remove_ground_truth_nested_blocks(sample_two_paragraph_block1):
    """Test remove_ground_truth method for a block containing nested blocks"""
    # Setup: Add ground truth data to nested words
    for paragraph in sample_two_paragraph_block1.items:
        for line in paragraph.items:
            for word in line.items:
                word.ground_truth_text = f"gt_{word.text}"
                word.ground_truth_bounding_box = word.bounding_box
    
    # Add unmatched ground truth words to various levels
    sample_two_paragraph_block1.unmatched_ground_truth_words = [(0, "top_unmatched")]
    for paragraph in sample_two_paragraph_block1.items:
        paragraph.unmatched_ground_truth_words = [(1, "para_unmatched")]
        for line in paragraph.items:
            line.unmatched_ground_truth_words = [(0, "line_unmatched")]
    
    # Verify ground truth data is present before removal
    assert any(word.ground_truth_text != "" for word in sample_two_paragraph_block1.words)
    assert any(word.ground_truth_bounding_box is not None for word in sample_two_paragraph_block1.words)
    assert len(sample_two_paragraph_block1.unmatched_ground_truth_words) == 1
    
    # Call remove_ground_truth on the top-level block
    sample_two_paragraph_block1.remove_ground_truth()
    
    # Verify all ground truth data is removed recursively
    assert all(word.ground_truth_text == "" for word in sample_two_paragraph_block1.words)
    assert all(word.ground_truth_bounding_box is None for word in sample_two_paragraph_block1.words)
    assert len(sample_two_paragraph_block1.unmatched_ground_truth_words) == 0
    
    # Verify nested blocks also have their unmatched ground truth words cleared
    for paragraph in sample_two_paragraph_block1.items:
        assert len(paragraph.unmatched_ground_truth_words) == 0
        for line in paragraph.items:
            assert len(line.unmatched_ground_truth_words) == 0


def test_remove_ground_truth_empty_block():
    """Test remove_ground_truth method on an empty block"""
    from pd_book_tools.ocr.block import Block, BlockChildType, BlockCategory
    
    empty_block = Block(
        items=[],
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )
    empty_block.unmatched_ground_truth_words = [(0, "some_unmatched")]
    
    # Should not raise an error and should clear unmatched ground truth words
    empty_block.remove_ground_truth()
    assert len(empty_block.unmatched_ground_truth_words) == 0
