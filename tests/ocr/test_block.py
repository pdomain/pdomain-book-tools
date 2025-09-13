import numpy as np
import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.word import Word


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
    assert any(
        word.ground_truth_text != "" for word in sample_two_paragraph_block1.words
    )
    assert any(
        word.ground_truth_bounding_box is not None
        for word in sample_two_paragraph_block1.words
    )
    assert len(sample_two_paragraph_block1.unmatched_ground_truth_words) == 1

    # Call remove_ground_truth on the top-level block
    sample_two_paragraph_block1.remove_ground_truth()

    # Verify all ground truth data is removed recursively
    assert all(
        word.ground_truth_text == "" for word in sample_two_paragraph_block1.words
    )
    assert all(
        word.ground_truth_bounding_box is None
        for word in sample_two_paragraph_block1.words
    )
    assert len(sample_two_paragraph_block1.unmatched_ground_truth_words) == 0

    # Verify nested blocks also have their unmatched ground truth words cleared
    for paragraph in sample_two_paragraph_block1.items:
        assert len(paragraph.unmatched_ground_truth_words) == 0
        for line in paragraph.items:
            assert len(line.unmatched_ground_truth_words) == 0


def test_remove_ground_truth_empty_block():
    """Test remove_ground_truth method on an empty block"""
    from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType

    empty_block = Block(
        items=[],
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )
    empty_block.unmatched_ground_truth_words = [(0, "some_unmatched")]

    # Should not raise an error and should clear unmatched ground truth words
    empty_block.remove_ground_truth()
    assert len(empty_block.unmatched_ground_truth_words) == 0


# ---------------- Additional tests for uncovered branches ------------------


def test_block_items_sorted_and_copy(sample_block1, sample_block2):
    # Construct unsorted WORDS block (x order reversed)
    w1 = Word("a", BoundingBox.from_ltrb(10, 0, 20, 10), 0.5)
    w2 = Word("b", BoundingBox.from_ltrb(0, 0, 5, 10), 0.6)
    line = Block(
        [w1, w2], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE
    )
    assert [w.text for w in line.items] == ["b", "a"]  # sorted
    # Returned list is a copy
    items_copy = line.items
    items_copy.pop()
    assert len(line.items) == 2

    # BLOCKS sorting by y then x
    b1 = Block.from_dict(sample_block1.to_dict())
    b2 = Block.from_dict(sample_block2.to_dict())
    # shift coordinates to force ordering differences
    b1.bounding_box = BoundingBox.from_ltrb(0, 50, 10, 60)
    b2.bounding_box = BoundingBox.from_ltrb(0, 10, 10, 20)
    outer = Block(
        [b1, b2],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
    )
    assert outer.items[0] is b2
    assert outer.items[1] is b1


def test_block_items_uniform_coordinate_system_setter():
    # Mixed normalized / pixel should raise
    w_norm = Word(
        "n", BoundingBox.from_ltrb(0.1, 0.1, 0.2, 0.2, is_normalized=True), 0.5
    )
    w_px = Word("p", BoundingBox.from_ltrb(10, 10, 20, 20, is_normalized=False), 0.6)
    with pytest.raises(ValueError):
        Block(
            [w_norm, w_px],
            child_type=BlockChildType.WORDS,
            block_category=BlockCategory.LINE,
        )


def test_block_items_uniform_coordinate_system_add_item():
    # Start with normalized then attempt to add pixel word
    w_norm1 = Word(
        "a", BoundingBox.from_ltrb(0.1, 0.1, 0.2, 0.2, is_normalized=True), 0.5
    )
    w_norm2 = Word(
        "b", BoundingBox.from_ltrb(0.2, 0.1, 0.3, 0.2, is_normalized=True), 0.5
    )
    blk = Block(
        [w_norm1, w_norm2],
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )
    w_px = Word("c", BoundingBox.from_ltrb(10, 10, 20, 20, is_normalized=False), 0.5)
    with pytest.raises(ValueError):
        blk.add_item(w_px)


def test_block_remove_item_success_and_failure(sample_block1):
    w = sample_block1.items[0]
    original_bbox = sample_block1.bounding_box
    sample_block1.remove_item(w)
    assert w not in sample_block1.items
    # bbox recomputed (now just second word)
    assert sample_block1.bounding_box != original_bbox
    with pytest.raises(ValueError):
        sample_block1.remove_item(w)


def test_remove_line_if_exists_direct_and_nested(
    sample_paragraph_block1, sample_block1
):
    # Direct removal
    paragraph = sample_paragraph_block1
    assert sample_block1 in paragraph.items
    paragraph.remove_line_if_exists(sample_block1)
    assert sample_block1 not in paragraph.items
    # Nested removal (add paragraph inside a block)
    outer = Block(
        [paragraph],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.BLOCK,
    )
    # Create new line to remove nested
    new_line = Word("x", BoundingBox.from_ltrb(30, 0, 40, 10), 0.9)
    nested_line_block = Block(
        [new_line], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE
    )
    paragraph.add_item(nested_line_block)
    assert nested_line_block in paragraph.items
    outer.remove_line_if_exists(nested_line_block)
    assert nested_line_block not in paragraph.items


def test_remove_line_if_exists_not_found_logs(sample_block1):
    other_line = Block(
        [], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE
    )
    # Should simply log and not raise
    sample_block1.remove_line_if_exists(other_line)

    # Removed unreachable TypeError branch test (malformed structure causes earlier AttributeError)


def test_block_text_variants(
    sample_block1, sample_paragraph_block1, sample_two_paragraph_block1
):
    assert sample_block1.text == "word1 word2"  # WORDS case
    assert sample_paragraph_block1.text.count("\n") == 2  # PARAGRAPH single newlines
    assert (
        sample_two_paragraph_block1.text.count("\n\n") == 1
    )  # BLOCK double newline between paragraphs
    empty_line = Block(
        [], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE
    )
    assert empty_line.text == ""


def test_ground_truth_text_only_ocr(sample_block1):
    w1, w2 = sample_block1.items
    w1.ground_truth_text = "gt1"
    w2.ground_truth_text = "gt2"
    assert sample_block1.ground_truth_text_only_ocr == "gt1 gt2"
    # Make second word have no OCR text => exclude
    w2.text = ""
    assert sample_block1.ground_truth_text_only_ocr == "gt1"


def test_ground_truth_exact_match(sample_block1):
    w1, w2 = sample_block1.items
    w1.ground_truth_text = w1.text
    w2.ground_truth_text = w2.text
    assert sample_block1.ground_truth_exact_match is True
    w2.ground_truth_text = "different"
    assert sample_block1.ground_truth_exact_match is False


def test_split_word_happy_path(sample_block1):
    # word1 -> split into 'wo' + 'rd1'
    sample_block1.split_word(0, bbox_split_offset=2, character_split_index=2)
    texts = [w.text for w in sample_block1.items]
    assert "wo" in texts and "rd1" in texts
    assert any(t == "word2" for t in texts)


def test_split_word_errors(sample_paragraph_block1):
    with pytest.raises(ValueError):
        sample_paragraph_block1.split_word(0, 1, 1)  # not a WORDS block
    line_block = sample_paragraph_block1.items[0]
    with pytest.raises(IndexError):
        line_block.split_word(99, 1, 1)
    # Inject non-Word into WORDS block to trigger TypeError
    bogus_block = Block(
        [], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE
    )
    line_block._items.insert(0, bogus_block)  # bypass setter
    with pytest.raises(TypeError):
        line_block.split_word(0, 1, 1)


def test_merge_blocks(sample_block1, sample_block2):
    b1 = Block.from_dict(sample_block1.to_dict())
    b2 = Block.from_dict(sample_block2.to_dict())
    b1.unmatched_ground_truth_words = [(0, "x")]
    b2.unmatched_ground_truth_words = [(1, "y")]
    b1.merge(b2)
    assert len(b1.items) == 4
    assert sorted(b1.block_labels) == sorted(["labelline1", "labelline2"])
    assert len(b1.unmatched_ground_truth_words) == 2


def test_merge_blocks_mismatches(sample_block1, sample_paragraph_block1):
    with pytest.raises(ValueError):
        sample_paragraph_block1.merge(sample_block1)  # child_type mismatch
    # Category mismatch
    paragraph_copy = Block.from_dict(sample_paragraph_block1.to_dict())
    paragraph_copy.block_category = BlockCategory.BLOCK
    with pytest.raises(ValueError):
        sample_paragraph_block1.merge(paragraph_copy)


def test_merge_block_labels_none(sample_block1, sample_block2):
    b1 = Block.from_dict(sample_block1.to_dict())
    b1.block_labels = None
    b1.merge(sample_block2)
    assert b1.block_labels == ["labelline2"]


def test_merge_other_labels_none(sample_block1, sample_block2):
    b2 = Block.from_dict(sample_block2.to_dict())
    b2.block_labels = None
    original_labels = list(sample_block1.block_labels)
    sample_block1.merge(b2)
    assert sample_block1.block_labels == original_labels  # unchanged


def test_ocr_confidence_scores_and_mean_nested(sample_two_paragraph_block1):
    scores = sample_two_paragraph_block1.ocr_confidence_scores()
    assert len(scores) == 6
    assert sample_two_paragraph_block1.mean_ocr_confidence() == pytest.approx(
        sum(scores) / len(scores)
    )
    empty = Block(
        [], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE
    )
    assert empty.ocr_confidence_scores() == []
    assert empty.mean_ocr_confidence() == 0.0


def test_block_scale_normalized():
    # Build a normalized block
    w1 = Word("a", BoundingBox.from_ltrb(0.1, 0.1, 0.2, 0.2), 0.5)
    w2 = Word("b", BoundingBox.from_ltrb(0.2, 0.1, 0.3, 0.2), 0.6)
    line = Block(
        [w1, w2], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE
    )
    scaled = line.scale(100, 200)
    assert scaled.bounding_box.minX == 10
    assert not scaled.bounding_box.is_normalized
    # Original unchanged
    assert w1.bounding_box.is_normalized and w2.bounding_box.is_normalized


def test_block_scale_pixels_deepcopy(sample_block1):
    # sample_block1 already pixel space; scaling should raise for bbox.scale call if attempted.
    # The Block.scale method assumes bounding_box.scale is valid; ensure we pass a normalized bbox to avoid exception.
    # Create a normalized wrapper instead.
    w_norm = Word("n", BoundingBox.from_ltrb(0.0, 0.0, 0.1, 0.1), 0.5)
    block_norm = Block(
        [w_norm], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE
    )
    scaled = block_norm.scale(50, 100)
    assert scaled.items[0].bounding_box.width == 5
    assert scaled.items[0] is not w_norm  # deep copy


def test_fuzz_score_against(sample_block1):
    score_same = sample_block1.fuzz_score_against(sample_block1.text)
    assert score_same >= 99
    score_diff = sample_block1.fuzz_score_against("completely different")
    assert score_diff < score_same


def test_block_serialization_round_trip(sample_paragraph_block1):
    d = sample_paragraph_block1.to_dict()
    rt = Block.from_dict(d)
    assert rt.to_dict() == d


def test_block_to_dict_empty_additional_attrs():
    empty = Block(
        [], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE
    )
    data = empty.to_dict()
    assert data["bounding_box"] is None
    assert data["unmatched_ground_truth_words"] == []
    assert data["additional_block_attributes"] == {}


def test_block_from_dict_defaults(sample_block1):
    d = sample_block1.to_dict()
    # Remove child_type to test default WORDS
    d.pop("child_type")
    rt = Block.from_dict(d)
    assert rt.child_type == BlockChildType.WORDS


def test_refine_bounding_boxes_empty():
    empty = Block(
        [], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE
    )
    empty.refine_bounding_boxes(image=None)
    assert empty.bounding_box is None


def test_refine_bounding_boxes_words_none_image(monkeypatch):
    w = Word("a", BoundingBox.from_ltrb(0, 0, 5, 5), 0.5)
    b = Block([w], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE)
    before = w.bounding_box.to_dict()
    b.refine_bounding_boxes(image=None)
    assert w.bounding_box.to_dict() == before


def test_refine_bounding_boxes_nested(monkeypatch):
    # Monkeypatch BoundingBox.refine to shrink box deterministically
    def fake_refine(self, image, padding_px=0, expand_beyond_original=False):
        return BoundingBox.from_ltrb(self.minX, self.minY, self.maxX - 1, self.maxY - 1)

    monkeypatch.setattr(BoundingBox, "refine", fake_refine, raising=True)
    img = np.ones((100, 100), dtype=np.uint8) * 255
    w1 = Word("a", BoundingBox.from_ltrb(0, 0, 10, 10), 0.5)
    w2 = Word("b", BoundingBox.from_ltrb(10, 0, 20, 10), 0.5)
    line1 = Block(
        [w1, w2], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE
    )
    para = Block(
        [line1],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
    )
    before_union_right = para.bounding_box.maxX
    para.refine_bounding_boxes(img)
    # Each word reduced by 1 pixel on right & bottom; parent union should shrink
    assert para.bounding_box.maxX == before_union_right - 1


def test_refine_bounding_boxes_not_implemented():
    # Insert a stub object lacking refine_bounding_box into a WORDS block post-construction
    class Stub:
        def __init__(self, bbox):
            self.bounding_box = bbox
            # no refine_bounding_box method

    w = Word("a", BoundingBox.from_ltrb(0, 0, 5, 5), 0.5)
    line = Block(
        [w], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE
    )
    stub = Stub(BoundingBox.from_ltrb(10, 0, 15, 5))
    line._items.append(stub)  # bypass validation intentionally
    with pytest.raises(NotImplementedError):
        line.refine_bounding_boxes(image=np.ones((10, 10), dtype=np.uint8))


# ---------------- Additional targeted coverage tests -----------------------


def test_items_setter_non_collection(sample_word1):
    with pytest.raises(TypeError):
        Block(
            sample_word1,
            child_type=BlockChildType.WORDS,
            block_category=BlockCategory.LINE,
        )  # type: ignore[arg-type]


def test_items_setter_missing_bbox_attribute():
    class NoBBox:
        def __init__(self):
            self.text = "x"

    with pytest.raises(TypeError):
        Block(
            [NoBBox()],
            child_type=BlockChildType.WORDS,
            block_category=BlockCategory.LINE,
        )


def test_items_setter_bbox_wrong_type():
    class BadBBox:
        def __init__(self):
            self.bounding_box = 123  # not a BoundingBox

    with pytest.raises(TypeError):
        Block(
            [BadBBox()],
            child_type=BlockChildType.WORDS,
            block_category=BlockCategory.LINE,
        )


def test_items_setter_invalid_item_type():
    class HasBBox:
        def __init__(self):
            self.bounding_box = BoundingBox.from_ltrb(0, 0, 1, 1)

    with pytest.raises(TypeError):
        Block(
            [HasBBox()],
            child_type=BlockChildType.WORDS,
            block_category=BlockCategory.LINE,
        )


def test_paragraph_ground_truth_text_only_ocr(sample_paragraph_block1):
    # Assign ground truth to all words
    for line in sample_paragraph_block1.items:
        for w in line.items:
            w.ground_truth_text = w.text.upper()
    # Blank out OCR text of one word to test filtering
    sample_paragraph_block1.items[1].items[0].text = ""
    gt = sample_paragraph_block1.ground_truth_text_only_ocr
    # Ensure newline separation and exclusion of blank OCR word
    assert "\n" in gt
    assert "WORD3" not in gt  # filtered due to OCR text removed


def test_block_ground_truth_text_only_ocr(sample_two_paragraph_block1):
    # Provide ground truth everywhere
    for paragraph in sample_two_paragraph_block1.items:
        for line in paragraph.items:
            for w in line.items:
                w.ground_truth_text = w.text
    gt_block = sample_two_paragraph_block1.ground_truth_text_only_ocr
    # Double newline between paragraphs
    assert "\n\n" in gt_block


def test_nested_ground_truth_exact_match(sample_two_paragraph_block1):
    # Exact matches
    for word in sample_two_paragraph_block1.words:
        word.ground_truth_text = word.text
    assert sample_two_paragraph_block1.ground_truth_exact_match is True
    # Introduce mismatch
    sample_two_paragraph_block1.words[0].ground_truth_text = "DIFF"
    assert sample_two_paragraph_block1.ground_truth_exact_match is False


def test_word_list_flatten(sample_two_paragraph_block1):
    wl = sample_two_paragraph_block1.word_list
    assert len(wl) == len(sample_two_paragraph_block1.words)
    # Order matches words order
    assert wl[0] == sample_two_paragraph_block1.words[0].text


def test_paragraphs_property(sample_two_paragraph_block1, sample_paragraph_block1):
    # Paragraph returns itself
    assert sample_paragraph_block1.paragraphs == [sample_paragraph_block1]
    # Higher level block flattens
    assert len(sample_two_paragraph_block1.paragraphs) == 2


# ---------------- Remaining uncovered line targets -----------------------


def test_block_ctor_unmatched_and_additional_attrs(sample_line1):
    attrs = {"foo": 1}
    unmatched = [(0, "INS"), (1, "ADD")]
    blk = Block(
        items=sample_line1,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
        unmatched_ground_truth_words=unmatched,
        additional_block_attributes=attrs,
    )
    assert blk.unmatched_ground_truth_words == unmatched  # line 91
    assert blk.additional_block_attributes == attrs  # line 99


def test_add_item_type_errors():
    # WORDS block adding non-Word
    wblock = Block(
        [], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE
    )
    with pytest.raises(TypeError):
        wblock.add_item(
            Block(
                [], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE
            )
        )  # line 161
    # BLOCKS block adding non-Block
    bblock = Block(
        [], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH
    )
    with pytest.raises(TypeError):
        bblock.add_item(Word("w", BoundingBox.from_ltrb(0, 0, 1, 1), 0.5))  # line 164


def test_remove_line_if_exists_not_found_blocks(sample_paragraph_block1):
    # Create a new line block not present
    new_line = Block(
        [], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE
    )
    sample_paragraph_block1.remove_line_if_exists(new_line)  # should hit line 207 path


def test_remove_empty_items_empty_return():
    empty_blocks_parent = Block(
        [], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.BLOCK
    )
    empty_blocks_parent.remove_empty_items()  # lines 211-212
    assert empty_blocks_parent.items == []


def test_remove_empty_items_nested_removal(sample_block1):
    # Build an initially non-empty line so validation passes, then clear items manually
    # Use pixel coordinates (not normalized) to match sample_block1 pixel space
    temp_word = Word("tmp", BoundingBox.from_ltrb(0, 0, 1, 1, is_normalized=False), 0.1)
    empty_line = Block(
        [temp_word], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE
    )
    empty_line._items.clear()  # force empty while keeping prior bbox
    parent = Block(
        [empty_line, sample_block1],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
    )
    parent.remove_empty_items()  # lines 215-219
    assert empty_line not in parent.items
    assert sample_block1 in parent.items


def test_ground_truth_text_unmatched_insertion(sample_block1):
    # words: word1 word2; insert unmatched after index positions
    sample_block1.unmatched_ground_truth_words = [(0, "X"), (1, "Y")]
    # Provide ground truth text for each existing word
    for w in sample_block1.items:
        w.ground_truth_text = w.text
    gt = sample_block1.ground_truth_text  # lines 260-278
    # expected order: word1 X word2 Y (due to reversed insertion logic placing at index+1)
    assert gt.split() == ["word1", "X", "word2", "Y"]


def test_ground_truth_text_paragraph_and_block(
    sample_paragraph_block1, sample_two_paragraph_block1
):
    # Set ground truth text for nested words
    for blk in [sample_paragraph_block1, sample_two_paragraph_block1]:
        for w in blk.words:
            w.ground_truth_text = w.text
    # Paragraph branch lines 279-280
    para_gt = sample_paragraph_block1.ground_truth_text
    assert para_gt.count("\n") == 2
    # Block branch lines 281-282
    top_gt = sample_two_paragraph_block1.ground_truth_text
    assert "\n\n" in top_gt


def test_merge_sets_bbox_when_missing(sample_block1):
    # empty block no bbox merges with populated line -> line 411
    empty = Block(
        [], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE
    )
    assert empty.bounding_box is None
    empty.merge(sample_block1)
    assert empty.bounding_box == sample_block1.bounding_box


# NOTE: Line 203 (TypeError in remove_line_if_exists loop) is practically unreachable due to earlier AttributeError
# when a Word lacks 'lines' attribute; exercising it would require code modification, so it's excluded intentionally.
