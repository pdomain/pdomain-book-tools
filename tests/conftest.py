import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.word import Word
from pd_book_tools.ocr.block import Block, BlockChildType, BlockCategory
from pd_book_tools.ocr.page import Page

@pytest.fixture
def sample_word1():
    return Word(
        text="word1",
        bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
        ocr_confidence=0.9,
    )


@pytest.fixture
def sample_word2():
    return Word(
        text="word2",
        bounding_box=BoundingBox.from_ltrb(10, 0, 20, 10),
        ocr_confidence=0.8,
        word_labels=["label_word2"],
    )


@pytest.fixture
def sample_line1(sample_word1, sample_word2):
    return [
        sample_word1,
        sample_word2,
    ]


@pytest.fixture
def sample_line2():
    return [
        Word(
            text="word3",
            bounding_box=BoundingBox.from_ltrb(0, 10, 10, 20),
            ocr_confidence=0.9,
        ),
        Word(
            text="word4",
            bounding_box=BoundingBox.from_ltrb(10, 10, 20, 20),
            ocr_confidence=0.8,
        ),
    ]


@pytest.fixture
def sample_line3():
    return [
        Word(
            text="word5",
            bounding_box=BoundingBox.from_ltrb(0, 20, 10, 30),
            ocr_confidence=0.9,
        ),
        Word(
            text="word6",
            bounding_box=BoundingBox.from_ltrb(0, 20, 20, 30),
            ocr_confidence=0.8,
        ),
    ]


@pytest.fixture
def sample_line4():
    return [
        Word(
            text="word7",
            bounding_box=BoundingBox.from_ltrb(0, 30, 10, 40),
            ocr_confidence=0.9,
        ),
        Word(
            text="word8",
            bounding_box=BoundingBox.from_ltrb(0, 30, 20, 40),
            ocr_confidence=0.8,
        ),
    ]


@pytest.fixture
def sample_block1(sample_line1):
    return Block(
        items=sample_line1,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
        block_labels=["labelline1"],
    )


@pytest.fixture
def sample_block2(sample_line2):
    return Block(
        items=sample_line2,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
        block_labels=["labelline2"],
    )


@pytest.fixture
def sample_block3(sample_line3):
    return Block(
        items=sample_line3,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
        block_labels=["labelline3"],
    )


@pytest.fixture
def sample_block4(sample_line4):
    return Block(
        items=sample_line4,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
        block_labels=["labelline4"],
    )


@pytest.fixture
def sample_paragraph_block1(sample_block1, sample_block2, sample_block3):
    # initialize with out-of-order list to test sorting
    return Block(
        items=[sample_block1, sample_block3, sample_block2],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
        block_labels=["labelparagraph1"],
    )


@pytest.fixture
def sample_two_paragraph_block1(sample_block1, sample_block2, sample_block3):
    block1 = Block(
        items=[sample_block2, sample_block1],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
        block_labels=["labelparagraph1-1"],
    )
    block2 = Block(
        items=[sample_block3],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
        block_labels=["labelparagraph1-2"],
    )
    return Block(
        items=[block2, block1],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.BLOCK,
        block_labels=["labelparagraph2"],
    )


@pytest.fixture
def sample_page(sample_two_paragraph_block1, sample_block4):
    return Page(
        width=100,
        height=200,
        page_index=1,
        items=[sample_two_paragraph_block1, sample_block4],
        page_labels=["labelpage1"],
    )
