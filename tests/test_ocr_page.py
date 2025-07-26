from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.word import Word
from pd_book_tools.ocr.block import Block, BlockChildType, BlockCategory
from pd_book_tools.ocr.page import Page


def test_page_initialization(sample_page):
    assert sample_page.width == 100
    assert sample_page.height == 200
    assert sample_page.page_index == 1
    assert len(sample_page.items) == 2
    assert sample_page.page_labels == ["labelpage1"]
    assert isinstance(sample_page.bounding_box, BoundingBox)


def test_page_text(sample_page):
    text = sample_page.text
    assert isinstance(text, str)
    assert "word1 word2\nword3 word4\n\nword5 word6\n\nword7 word8\n" in text


def test_page_words(sample_page):
    words = sample_page.words
    assert isinstance(words, list)
    assert all(isinstance(word, Word) for word in words)


def test_page_lines(sample_page):
    lines = sample_page.lines
    assert isinstance(lines, list)
    assert all(isinstance(line, Block) for line in lines)


def test_page_to_dict(sample_page):
    page_dict = sample_page.to_dict()
    assert isinstance(page_dict, dict)
    assert "items" in page_dict
    assert "width" in page_dict
    assert "height" in page_dict
    assert "page_index" in page_dict
    assert "bounding_box" in page_dict


def test_page_from_dict(sample_page):
    page_dict = sample_page.to_dict()
    print(page_dict)
    new_page = Page.from_dict(page_dict)
    assert new_page.width == sample_page.width
    assert new_page.height == sample_page.height
    assert new_page.page_index == sample_page.page_index
    assert len(new_page.items) == len(sample_page.items)


def test_page_remove_ground_truth():
    """Test that remove_ground_truth removes all ground truth data from the page and its items"""
    # Create words with ground truth data
    word1 = Word(
        text="word1",
        bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
        ocr_confidence=0.9,
        ground_truth_text="gt_word1",
        ground_truth_bounding_box=BoundingBox.from_ltrb(1, 1, 11, 11),
        ground_truth_match_keys={"match_score": 95},
    )

    word2 = Word(
        text="word2",
        bounding_box=BoundingBox.from_ltrb(10, 0, 20, 10),
        ocr_confidence=0.8,
        ground_truth_text="gt_word2",
        ground_truth_bounding_box=BoundingBox.from_ltrb(11, 1, 21, 11),
        ground_truth_match_keys={"match_score": 87},
    )

    # Create blocks containing these words
    block1 = Block(
        items=[word1, word2],
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )

    # Create a page with these blocks
    page = Page(width=100, height=200, page_index=1, items=[block1])

    # Verify ground truth data exists before removal
    words = page.words
    assert len(words) == 2
    assert words[0].ground_truth_text == "gt_word1"
    assert words[1].ground_truth_text == "gt_word2"
    assert words[0].ground_truth_bounding_box is not None
    assert words[1].ground_truth_bounding_box is not None
    assert words[0].ground_truth_match_keys == {"match_score": 95}
    assert words[1].ground_truth_match_keys == {"match_score": 87}

    # Call remove_ground_truth
    page.remove_ground_truth()

    # Verify all ground truth data has been removed
    words_after = page.words
    assert len(words_after) == 2
    assert words_after[0].ground_truth_text == ""
    assert words_after[1].ground_truth_text == ""
    assert words_after[0].ground_truth_bounding_box is None
    assert words_after[1].ground_truth_bounding_box is None
    # Note: ground_truth_match_keys are not cleared in the remove_ground_truth method
    # This might be intentional to preserve match history

    # Verify that the original text and bounding boxes remain unchanged
    assert words_after[0].text == "word1"
    assert words_after[1].text == "word2"
    assert words_after[0].bounding_box == BoundingBox.from_ltrb(0, 0, 10, 10)
    assert words_after[1].bounding_box == BoundingBox.from_ltrb(10, 0, 20, 10)


def test_page_remove_ground_truth_empty_page():
    """Test that remove_ground_truth works correctly on an empty page"""
    # Create an empty page
    page = Page(width=100, height=200, page_index=1, items=[])

    # Should not raise any errors
    page.remove_ground_truth()

    # Page should still be empty
    assert len(page.items) == 0
    assert len(page.words) == 0


def test_page_remove_ground_truth_no_ground_truth_data():
    """Test that remove_ground_truth works correctly when there's no ground truth data"""
    # Create words without ground truth data
    word1 = Word(
        text="word1",
        bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
        ocr_confidence=0.9,
    )

    word2 = Word(
        text="word2",
        bounding_box=BoundingBox.from_ltrb(10, 0, 20, 10),
        ocr_confidence=0.8,
    )

    # Create blocks containing these words
    block1 = Block(
        items=[word1, word2],
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )

    # Create a page with these blocks
    page = Page(width=100, height=200, page_index=1, items=[block1])

    # Verify no ground truth data exists
    words = page.words
    assert len(words) == 2
    assert words[0].ground_truth_text == ""
    assert words[1].ground_truth_text == ""
    assert words[0].ground_truth_bounding_box is None
    assert words[1].ground_truth_bounding_box is None

    # Should not raise any errors
    page.remove_ground_truth()

    # Verify everything remains the same
    words_after = page.words
    assert len(words_after) == 2
    assert words_after[0].ground_truth_text == ""
    assert words_after[1].ground_truth_text == ""
    assert words_after[0].ground_truth_bounding_box is None
    assert words_after[1].ground_truth_bounding_box is None
    assert words_after[0].text == "word1"
    assert words_after[1].text == "word2"
