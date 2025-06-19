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
