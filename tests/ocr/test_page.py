from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.word import Word
from pd_book_tools.ocr.block import Block, BlockChildType, BlockCategory
from pd_book_tools.ocr.page import Page
import numpy as np
import pytest


# ============================================================================
# Basic Page construction & serialization
# ============================================================================


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


    

# ============================================================================
# Ground truth removal (clearing gt text / boxes)
# ============================================================================


def test_page_remove_ground_truth():
    """remove_ground_truth clears gt text/bboxes but preserves match keys"""
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
    """remove_ground_truth on empty page is a no-op"""
    # Create an empty page
    page = Page(width=100, height=200, page_index=1, items=[])

    # Should not raise any errors
    page.remove_ground_truth()

    # Page should still be empty
    assert len(page.items) == 0
    assert len(page.words) == 0


def test_page_remove_ground_truth_no_ground_truth_data():
    """remove_ground_truth when no gt data present (idempotent)"""
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


# ============================================================================
# Helpers / factories
# ============================================================================


def _make_line(texts, y_top, height=10, x_start=0):
    words = []
    x = x_start
    for t in texts:
        w = len(t) * 5 or 5
        words.append(
            Word(
                text=t,
                bounding_box=BoundingBox.from_ltrb(x, y_top, x + w, y_top + height),
                ocr_confidence=0.9,
            )
        )
        x += w + 2
    return Block(
        items=words,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )


# ============================================================================
# Item management (add/remove/mutate)
# ============================================================================


def test_page_add_and_remove_item(sample_page, sample_block4):
    initial_count = len(sample_page.items)
    # Add new empty paragraph block (will have bbox None until recompute)
    new_block = Block(
        items=[_make_line(["x"], 90)],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
    )
    sample_page.add_item(new_block)
    assert len(sample_page.items) == initial_count + 1
    sample_page.remove_item(new_block)
    assert len(sample_page.items) == initial_count
    with pytest.raises(ValueError):
        sample_page.remove_item(new_block)


def test_page_items_setter_errors():
    # Non-collection
    with pytest.raises(TypeError):
        Page(width=10, height=10, page_index=0, items=None)  # type: ignore[arg-type]
    # Collection with non Block
    with pytest.raises(TypeError):
        Page(width=10, height=10, page_index=0, items=["notablock"])  # type: ignore[list-item]


def test_page_recompute_bounding_box_empty():
    p = Page(width=10, height=20, page_index=0, items=[])
    # Initially no bbox
    assert p.bounding_box is None
    # Add then remove to trigger recompute path
    line = _make_line(["a"], 0)
    block = Block(
        items=[line],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
    )
    p.add_item(block)
    assert p.bounding_box is not None
    p.remove_item(block)
    assert p.bounding_box is None


# ============================================================================
# Scaling & normalization
# ============================================================================


def test_page_scale_normalized():
    # Build normalized words
    w1 = Word(
        text="hello",
        bounding_box=BoundingBox.from_ltrb(0.1, 0.1, 0.2, 0.2, is_normalized=True),
        ocr_confidence=0.5,
    )
    line = Block(
        items=[w1],
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )
    para = Block(
        items=[line],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
    )
    page = Page(width=100, height=200, page_index=0, items=[para])
    scaled = page.scale(1000, 2000)
    assert scaled.width == 1000 and scaled.height == 2000
    assert not scaled.items[0].items[0].items[0].bounding_box.is_normalized


# ============================================================================
# Ground truth aggregation & exact match flag
# ============================================================================


def test_page_ground_truth_text_and_match():
    w1 = Word(
        text="abc",
        bounding_box=BoundingBox.from_ltrb(0, 0, 3, 3),
        ocr_confidence=0.9,
        ground_truth_text="abc",
    )
    w2 = Word(
        text="def",
        bounding_box=BoundingBox.from_ltrb(4, 0, 7, 3),
        ocr_confidence=0.9,
        ground_truth_text="def",
    )
    line = Block(
        items=[w1, w2],
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )
    para = Block(items=[line], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)
    page = Page(width=10, height=10, page_index=0, items=[para])
    assert page.ground_truth_text.strip() == "abc def"
    assert page.ground_truth_exact_match


# ============================================================================
# Line / paragraph reorganization heuristics
# ============================================================================


def test_page_reorganize_lines_merge():
    # Two lines that should merge (small x gap, same y range)
    line1 = _make_line(["hello"], 0, height=20)
    # shift start just after end of line1 with tiny gap
    last_x = line1.bounding_box.maxX
    line2_words = [
        Word(
            text="world",
            bounding_box=BoundingBox.from_ltrb(last_x + 2, 0, last_x + 2 + 48, 20),
            ocr_confidence=0.9,
        )
    ]
    line2 = Block(items=line2_words, child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE)
    para = Block(items=[line1, line2], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)
    Page.reorganize_lines(para)
    # Lines should merge into one
    assert len(para.items) == 1
    assert "helloworld" in para.text.replace(" ", "")


def test_page_compute_text_row_blocks():
    # Create three lines with a large vertical gap before third to force new block
    l1 = _make_line(["a"], 0)
    l2 = _make_line(["b"], 12)
    l3 = _make_line(["c"], 60)
    rb = Page.compute_text_row_blocks([l1, l2, l3])
    assert rb is not None
    # Should have at least 2 paragraph blocks inside
    assert len(rb.items) >= 2


def test_page_compute_text_paragraph_blocks():
    # First two lines narrow, third wide to trigger paragraph split
    l1 = _make_line(["short"], 0)
    l2 = _make_line(["short2"], 12)
    # Indent third line to start a new paragraph (large minX)
    l3 = _make_line(["indent"], 24, x_start=100)
    pb = Page.compute_text_paragraph_blocks([l1, l2, l3])
    assert pb is not None
    assert len(pb.items) >= 2  # paragraphs


def test_page_remove_line_if_exists_nested():
    # Build nested structure: page -> block(BLOCK) -> paragraph -> lines
    l1 = _make_line(["a"], 0)
    l2 = _make_line(["b"], 10)
    para = Block(items=[l1, l2], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)
    outer = Block(items=[para], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.BLOCK)
    page = Page(width=50, height=50, page_index=0, items=[outer])
    page.remove_line_if_exists(l2)
    assert l2 not in page.lines


def test_page_remove_empty_items():
    # Block with empty child after removing line
    l1 = _make_line(["a"], 0)
    para = Block(items=[l1], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)
    outer = Block(items=[para], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.BLOCK)
    page = Page(width=10, height=10, page_index=0, items=[outer])
    para.remove_item(l1)
    page.remove_empty_items()
    # Paragraph should be removed
    # Outer block should also be removed from page -> no items remain
    assert len(page.items) == 0


# ============================================================================
# Image refresh & drawing (page/blocks/words) + property setters
# ============================================================================


def test_page_refresh_page_images_and_setters(tmp_path):
    l1 = _make_line(["a"], 0)
    page = Page(width=20, height=20, page_index=0, items=[Block(items=[l1], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)])
    img = np.zeros((20, 20, 3), dtype=np.uint8)
    page.cv2_numpy_page_image = img
    assert page.cv2_numpy_page_image_page_with_bbox is not None
    assert page.cv2_numpy_page_image_blocks_with_bboxes is not None
    assert page.cv2_numpy_page_image_word_with_bboxes is not None
    # Type error path
    with pytest.raises(TypeError):
        page.cv2_numpy_page_image = 123  # type: ignore[assignment]


# ============================================================================
# DocTR dataset generation (detection / recognition)
# ============================================================================


def test_page_doctr_detection_training_set(tmp_path):
    l1 = _make_line(["abc"], 0)
    # Provide ground truth for recognition test later
    for w in l1.items:
        w.ground_truth_text = w.text
    page = Page(width=20, height=20, page_index=5, items=[Block(items=[l1], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)])
    page.cv2_numpy_page_image = np.zeros((20, 20, 3), dtype=np.uint8)
    out = tmp_path / "train"
    page.generate_doctr_detection_training_set(out, prefix="book")
    det_labels = out / "detection" / "labels.json"
    assert det_labels.exists()


def test_page_doctr_recognition_training_set_error(tmp_path):
    l1 = _make_line(["abc"], 0)
    # Ensure ground_truth_text empty to trigger error
    for w in l1.items:
        w.ground_truth_text = ""
    page = Page(width=20, height=20, page_index=2, items=[Block(items=[l1], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)])
    page.cv2_numpy_page_image = np.zeros((20, 20, 3), dtype=np.uint8)
    out = tmp_path / "train2"
    with pytest.raises(ValueError):
        page.generate_doctr_recognition_training_set(out, prefix="p")


def test_page_convert_to_training_set(tmp_path):
    # Use normalized bbox so scaling inside recognition set succeeds
    w_norm = Word(
        text="abc",
        bounding_box=BoundingBox.from_ltrb(0.1, 0.1, 0.25, 0.2, is_normalized=True),
        ocr_confidence=0.9,
        ground_truth_text="abc",
    )
    line = Block(items=[w_norm], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE)
    para = Block(items=[line], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)
    page = Page(width=20, height=20, page_index=3, items=[para])
    page.cv2_numpy_page_image = np.zeros((40, 60, 3), dtype=np.uint8)
    out = tmp_path / "both"
    page.convert_to_training_set(out, prefix="set")
    assert (out / "detection" / "labels.json").exists()
    assert (out / "recognition" / "labels.json").exists()


def test_page_generate_doctr_checks_errors(tmp_path):
    p = Page(width=10, height=10, page_index=0, items=[])
    with pytest.raises(ValueError):
        p.generate_doctr_detection_training_set(tmp_path / "out")


def test_page_add_ground_truth_calls_refresh(sample_page):
    # Provide simple gt identical to text
    gt_text = sample_page.text
    # Should not raise
    sample_page.add_ground_truth(gt_text)
    # At least one word should now have ground_truth_text (cannot guarantee alignment details here)
    assert any(w.ground_truth_text for w in sample_page.words)


def test_page_add_rect_type_errors():
    img = np.zeros((5, 5, 3), dtype=np.uint8)
    # _add_ocr_text expects Word
    with pytest.raises(TypeError):
        Page._add_ocr_text(img, Block(items=[], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.LINE))
    with pytest.raises(TypeError):
        Page._add_gt_text(img, Block(items=[], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.LINE))


# ============================================================================
# Label overwrite / cleanup behaviors
# ============================================================================


def test_page_detection_labels_overwrite(tmp_path):
    # Existing labels file with a conflicting and a non-conflicting entry
    detection_dir = tmp_path / "detection"
    (detection_dir / "images").mkdir(parents=True, exist_ok=True)
    existing = {
        "oldprefix_5.png": {"img_dimensions": (10, 10), "img_hash": "abc", "polygons": []},
        "book_7.png": {"img_dimensions": (10, 10), "img_hash": "def", "polygons": []},
    }
    with open(detection_dir / "labels.json", "w") as f:
        import json
        json.dump(existing, f)
    # Build page with page_index=7 so one entry replaced, oldprefix remains
    w = Word(
        text="x",
        bounding_box=BoundingBox.from_ltrb(0.1, 0.1, 0.2, 0.2, is_normalized=True),
        ocr_confidence=0.9,
        ground_truth_text="x",
    )
    line = Block(items=[w], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE)
    para = Block(items=[line], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)
    page = Page(width=100, height=100, page_index=7, items=[para])
    page.cv2_numpy_page_image = np.zeros((50, 50, 3), dtype=np.uint8)
    page.generate_doctr_detection_training_set(tmp_path, prefix="book")
    with open(detection_dir / "labels.json") as f:
        data = json.load(f)
    assert "oldprefix_5.png" in data  # preserved
    assert f"book_{page.page_index}.png" in data  # new replaced
    # ensure conflicting key not duplicated
    assert len([k for k in data if k.startswith("book_7")]) == 1


def test_page_recognition_labels_overwrite_and_cleanup(tmp_path):
    rec_dir = tmp_path / "recognition" / "images"
    rec_dir.mkdir(parents=True, exist_ok=True)
    # Pre-create an old cropped image file for same prefix/page index to ensure it's deleted
    old_img = rec_dir / "pref_9_0_10_0_10.png"
    old_img.write_bytes(b"old")
    labels_path = tmp_path / "recognition" / "labels.json"
    with open(labels_path, "w") as f:
        import json
        json.dump({"pref_9_0_10_0_10.png": "OLD"}, f)
    w = Word(
        text="word",
        bounding_box=BoundingBox.from_ltrb(0.05, 0.05, 0.2, 0.15, is_normalized=True),
        ocr_confidence=0.8,
        ground_truth_text="word",
    )
    line = Block(items=[w], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE)
    para = Block(items=[line], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)
    page = Page(width=100, height=100, page_index=9, items=[para])
    page.cv2_numpy_page_image = np.zeros((60, 80, 3), dtype=np.uint8)
    page.generate_doctr_recognition_training_set(tmp_path, prefix="pref")
    # Old image removed
    assert not old_img.exists()
    # labels replaced with new single label
    with open(labels_path) as f:
        import json
        labels = json.load(f)
    assert len(labels) == 1
    assert list(labels.values())[0] == "word"


# ============================================================================
# Match score coloring (visual QA overlays)
# ============================================================================


def test_page_refresh_page_images_match_score_coloring():
    # Create several words with different match score conditions
    def mw(x1, x2, score, gt_text="w"):
        w = Word(
            text="w",
            bounding_box=BoundingBox.from_ltrb(x1, 0, x2, 10),
            ocr_confidence=0.9,
            ground_truth_text=gt_text if score is not None else "",
            ground_truth_match_keys={"match_score": score} if score is not None else {},
        )
        return w
    words = [
        mw(0, 5, 100),  # skipped drawing
        mw(6, 11, 95),  # dark_green
        mw(12, 17, 75),  # dark_green branch second
        mw(18, 23, 50),  # magenta
        mw(24, 29, None),  # no gt => red branch
    ]
    line = Block(items=words, child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE)
    para = Block(items=[line], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)
    page = Page(width=300, height=100, page_index=0, items=[para])
    page.cv2_numpy_page_image = np.zeros((20, 40, 3), dtype=np.uint8)
    img = page.cv2_numpy_page_image_matched_word_with_colors
    # First word region should remain all zeros, others should have some non-zero pixels
    first_region = img[0:10, 0:5]
    second_region = img[0:10, 6:11]
    assert np.count_nonzero(first_region) == 0
    assert np.count_nonzero(second_region) > 0


def test_page_reorganize_lines_edge_branches():
    # single line -> early return
    single = Block(items=[_make_line(["solo"], 0)], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)
    Page.reorganize_lines(single)
    assert len(single.items) == 1
    # lines with large height diff -> skip merge
    l1 = _make_line(["AAA"], 0, height=10)
    l2 = _make_line(["BBB"], 0, height=30)
    para = Block(items=[l1, l2], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)
    Page.reorganize_lines(para)
    assert len(para.items) == 2
    # overlapping x too much (second starts inside first) => no merge
    a1 = _make_line(["abc"], 0)
    # create second starting before end of first to produce overlap_x_amount large
    overlap_word = Word(text="xyz", bounding_box=BoundingBox.from_ltrb(a1.bounding_box.minX + 2, 0, a1.bounding_box.minX + 20, 10), ocr_confidence=0.5)
    a2 = Block(items=[overlap_word], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE)
    para2 = Block(items=[a1, a2], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)
    Page.reorganize_lines(para2)
    assert len(para2.items) == 2


def test_page_compute_text_row_blocks_empty():
    assert Page.compute_text_row_blocks([]) is None


# ============================================================================
# Error handling & edge cases
# ============================================================================


def test_page_constructor_cv2_type_error():
    w = Word(text="a", bounding_box=BoundingBox.from_ltrb(0, 0, 1, 1), ocr_confidence=0.1)
    line = Block(items=[w], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE)
    para = Block(items=[line], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)
    with pytest.raises(TypeError):
        Page(width=10, height=10, page_index=0, items=[para], cv2_numpy_page_image="bad")  # type: ignore[arg-type]


def test_page_scale_no_bounding_box():
    # empty page -> bounding_box None path
    p = Page(width=10, height=20, page_index=1, items=[])
    scaled = p.scale(100, 200)
    assert scaled.bounding_box is None


# ============================================================================
# Additional incremental coverage for remaining branches
# ============================================================================


def test_page_init_with_explicit_bounding_box():
    # Provide explicit bbox different from union to ensure it's used
    w = Word(
        text="a",
        bounding_box=BoundingBox.from_ltrb(10, 10, 20, 20),
        ocr_confidence=0.5,
    )
    line = Block(items=[w], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE)
    para = Block(items=[line], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)
    explicit = BoundingBox.from_ltrb(0, 0, 50, 50)
    page = Page(width=60, height=60, page_index=2, items=[para], bounding_box=explicit)
    # Should retain explicit bbox not shrink to union
    assert page.bounding_box.to_ltrb() == explicit.to_ltrb()


def test_page_init_with_unmatched_ground_truth_lines():
    w = Word(
        text="hello",
        bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
        ocr_confidence=0.9,
    )
    line = Block(items=[w], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE)
    para = Block(items=[line], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)
    page = Page(
        width=20,
        height=20,
        page_index=0,
        items=[para],
        unmatched_ground_truth_lines=[(0, "UNMATCHED")],
    )
    assert page.unmatched_ground_truth_lines == [(0, "UNMATCHED")]


def test_page_add_rect_with_normalized_block():
    # Normalized coordinates trigger scaling path (width<1)
    w = Word(
        text="n",
        bounding_box=BoundingBox.from_ltrb(0.1, 0.1, 0.15, 0.2, is_normalized=True),
        ocr_confidence=0.4,
    )
    line = Block(items=[w], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE)
    block_block = Block(items=[line], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.BLOCK)
    page = Page(width=100, height=100, page_index=0, items=[block_block])
    img = np.zeros((50, 50, 3), dtype=np.uint8)
    Page._add_rect(img, page)  # page color branch
    Page._add_rect(img, block_block)  # block color branch
    Page._add_rect(img, line)  # line color branch
    Page._add_rect(img, w)  # word color branch (scaling for normalized width)
    # At least some non-zero pixels now
    assert np.count_nonzero(img) > 0



def test_page_reorganize_page_flow():
    # Two lines close enough to merge; ensure reorganize_page rewrites structure
    l1 = _make_line(["alpha"], 0)
    # create second line with small gap so they merge inside reorganize_lines
    last_x = l1.bounding_box.maxX
    l2_word = Word(text="beta", bounding_box=BoundingBox.from_ltrb(last_x + 1, 0, last_x + 1 + 20, 10), ocr_confidence=0.8)
    l2 = Block(items=[l2_word], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE)
    para = Block(items=[l1, l2], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)
    top_block = Block(items=[para], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.BLOCK)
    page = Page(width=100, height=100, page_index=0, items=[top_block])
    page.reorganize_page()
    # After reorganize, items should be paragraph blocks only; merged line content present
    # After reorganize, top-level items should be paragraph blocks; search their text for merged token
    assert any("alphabeta" in blk.text.replace(" ", "") for blk in page.items)


def test_page_convert_to_training_set_missing_image(tmp_path):
    w = Word(text="a", bounding_box=BoundingBox.from_ltrb(0.1, 0.1, 0.2, 0.2, is_normalized=True), ocr_confidence=0.5, ground_truth_text="a")
    line = Block(items=[w], child_type=BlockChildType.WORDS, block_category=BlockCategory.LINE)
    para = Block(items=[line], child_type=BlockChildType.BLOCKS, block_category=BlockCategory.PARAGRAPH)
    page = Page(width=10, height=10, page_index=1, items=[para])
    with pytest.raises(ValueError):
        page.convert_to_training_set(tmp_path / "out", prefix="x")


def test_page_detection_on_empty_items(tmp_path):
    # Page with no items but with an image exercises early return in checks
    page = Page(width=50, height=50, page_index=4, items=[])
    page.cv2_numpy_page_image = np.zeros((30, 30, 3), dtype=np.uint8)
    page.generate_doctr_detection_training_set(tmp_path / "set", prefix="emp")
    # labels.json should exist with one entry (no polygons) since method proceeds
    labels_path = tmp_path / "set" / "detection" / "labels.json"
    assert labels_path.exists()
    import json
    data = json.loads(labels_path.read_text())
    assert len(data) == 1
    assert list(data.values())[0]["polygons"] == []

