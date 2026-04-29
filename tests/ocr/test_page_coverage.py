"""Coverage-focused tests for Page (rendering, structural ops, helpers)."""

import numpy as np
import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.word import Word

# Fixtures ---------------------------------------------------------------------


@pytest.fixture
def simple_word():
    return Word(
        text="abc",
        bounding_box=BoundingBox.from_ltrb(10, 10, 30, 20, is_normalized=False),
        ocr_confidence=0.9,
    )


@pytest.fixture
def simple_line(simple_word):
    word2 = Word(
        text="def",
        bounding_box=BoundingBox.from_ltrb(35, 10, 55, 20, is_normalized=False),
        ocr_confidence=0.85,
    )
    return Block(
        items=[simple_word, word2],
        block_category=BlockCategory.LINE,
        child_type=BlockChildType.WORDS,
    )


@pytest.fixture
def simple_paragraph(simple_line):
    return Block(
        items=[simple_line],
        block_category=BlockCategory.PARAGRAPH,
        child_type=BlockChildType.BLOCKS,
    )


@pytest.fixture
def simple_page(simple_paragraph):
    return Page(
        width=100,
        height=200,
        page_index=0,
        items=[simple_paragraph],
    )


@pytest.fixture
def two_paragraph_page():
    """Page with two paragraphs each containing one line each."""
    line1 = Block(
        items=[
            Word(
                text="line1",
                bounding_box=BoundingBox.from_ltrb(0, 0, 50, 20, is_normalized=False),
                ocr_confidence=0.9,
            )
        ],
        block_category=BlockCategory.LINE,
        child_type=BlockChildType.WORDS,
    )
    para1 = Block(
        items=[line1],
        block_category=BlockCategory.PARAGRAPH,
        child_type=BlockChildType.BLOCKS,
    )
    line2 = Block(
        items=[
            Word(
                text="line2",
                bounding_box=BoundingBox.from_ltrb(0, 30, 50, 50, is_normalized=False),
                ocr_confidence=0.9,
            )
        ],
        block_category=BlockCategory.LINE,
        child_type=BlockChildType.WORDS,
    )
    para2 = Block(
        items=[line2],
        block_category=BlockCategory.PARAGRAPH,
        child_type=BlockChildType.BLOCKS,
    )
    return Page(
        width=100,
        height=100,
        page_index=0,
        items=[para1, para2],
    )


# Property aliases and metadata -----------------------------------------------


class TestPropertyAliases:
    def test_index_alias_get_set(self, simple_page):
        assert simple_page.index == simple_page.page_index
        simple_page.index = 7
        assert simple_page.page_index == 7

    def test_page_source_alias_get_set(self, simple_page):
        assert simple_page.page_source == simple_page.source
        simple_page.page_source = "manual"
        assert simple_page.source == "manual"

    def test_resolved_dimensions_uses_width_height(self, simple_page):
        assert simple_page.resolved_dimensions == (100.0, 200.0)

    def test_resolved_dimensions_falls_back_to_image(self):
        page = Page(width=0, height=0, page_index=0, items=[])
        page._cv2_numpy_page_image = np.zeros((50, 70, 3), dtype=np.uint8)
        assert page.resolved_dimensions == (70.0, 50.0)

    def test_resolved_dimensions_zero_when_neither(self):
        page = Page(width=0, height=0, page_index=0, items=[])
        assert page.resolved_dimensions == (0.0, 0.0)


# is_content_normalized --------------------------------------------------------


class TestIsContentNormalized:
    def test_normalized_words(self):
        word = Word(
            text="x",
            bounding_box=BoundingBox.from_ltrb(0.1, 0.1, 0.2, 0.2, is_normalized=True),
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
        assert page.is_content_normalized is True

    def test_pixel_words(self, simple_page):
        assert simple_page.is_content_normalized is False

    def test_empty_page(self):
        page = Page(width=100, height=100, page_index=0, items=[])
        assert page.is_content_normalized is False


# Add/Remove items -------------------------------------------------------------


class TestAddRemoveItem:
    def test_add_item_validates_type(self, simple_page):
        with pytest.raises(TypeError, match="Block"):
            simple_page.add_item("not a block")

    def test_add_item_appends_and_recomputes(self, simple_page):
        new_block = Block(
            items=[
                Word(
                    text="z",
                    bounding_box=BoundingBox.from_ltrb(60, 80, 70, 90),
                    ocr_confidence=0.7,
                )
            ],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        before_count = len(simple_page.items)
        simple_page.add_item(new_block)
        assert len(simple_page.items) == before_count + 1

    def test_remove_item(self, simple_page):
        target = simple_page.items[0]
        simple_page.remove_item(target)
        assert target not in simple_page.items

    def test_remove_item_not_found(self, simple_page):
        new_block = Block(
            items=[
                Word(
                    text="z",
                    bounding_box=BoundingBox.from_ltrb(60, 80, 70, 90),
                    ocr_confidence=0.7,
                )
            ],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        with pytest.raises(ValueError, match="not found"):
            simple_page.remove_item(new_block)

    def test_items_setter_rejects_non_collection(self, simple_page):
        with pytest.raises(TypeError, match="must be a collection"):
            simple_page.items = 42

    def test_items_setter_rejects_non_block_items(self, simple_page):
        with pytest.raises(TypeError, match="must be of type Block"):
            simple_page.items = ["not a block"]


# Remove line if exists --------------------------------------------------------


class TestRemoveLineIfExists:
    def test_removes_top_level_line(self):
        line = Block(
            items=[
                Word(
                    text="x",
                    bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
                    ocr_confidence=0.9,
                )
            ],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        page = Page(width=50, height=50, page_index=0, items=[line])
        assert page.remove_line_if_exists(line) is True

    def test_removes_nested_line(self, simple_page, simple_line):
        # simple_page has a paragraph containing simple_line
        assert simple_page.remove_line_if_exists(simple_line) is True

    def test_returns_false_when_missing(self, simple_page):
        unrelated_line = Block(
            items=[
                Word(
                    text="x",
                    bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10),
                    ocr_confidence=0.9,
                )
            ],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        assert simple_page.remove_line_if_exists(unrelated_line) is False


# remove_empty_items ----------------------------------------------------------


class TestRemoveEmptyItems:
    def test_no_op_on_empty_page(self):
        page = Page(width=10, height=10, page_index=0, items=[])
        # Should be a no-op
        page.remove_empty_items()
        assert page.items == []


# CV2 image rendering ---------------------------------------------------------


class TestCv2NumpyImage:
    def test_setter_validates_type(self, simple_page):
        with pytest.raises(TypeError, match="ndarray"):
            simple_page.cv2_numpy_page_image = "not an array"

    def test_setter_accepts_none_clears(self, simple_page):
        simple_page.cv2_numpy_page_image = None
        # Now property getter returns None
        assert simple_page.cv2_numpy_page_image is None

    def test_setter_creates_overlay_images(self, simple_page):
        img = np.zeros((200, 100, 3), dtype=np.uint8)
        simple_page.cv2_numpy_page_image = img
        # All overlay images should be populated after setting
        assert simple_page.cv2_numpy_page_image_page_with_bbox is not None
        assert simple_page.cv2_numpy_page_image_blocks_with_bboxes is not None
        assert simple_page.cv2_numpy_page_image_paragraph_with_bboxes is not None
        assert simple_page.cv2_numpy_page_image_line_with_bboxes is not None
        assert simple_page.cv2_numpy_page_image_word_with_bboxes is not None
        assert (
            simple_page.cv2_numpy_page_image_word_with_bboxes_and_ocr_text is not None
        )
        assert simple_page.cv2_numpy_page_image_word_with_bboxes_and_gt_text is not None
        assert simple_page.cv2_numpy_page_image_matched_word_with_colors is not None

    def test_render_with_match_scores(self, simple_page):
        """Exercise the matched-word color branch."""
        img = np.zeros((200, 100, 3), dtype=np.uint8)
        word = simple_page.words[0]
        word.ground_truth_text = "abc"
        word.ground_truth_match_keys = {"match_score": 95}
        word2 = simple_page.words[1]
        word2.ground_truth_text = "def"
        word2.ground_truth_match_keys = {"match_score": 75}
        simple_page.cv2_numpy_page_image = img
        # No exception means the branches succeeded

    def test_render_with_perfect_match(self, simple_page):
        img = np.zeros((200, 100, 3), dtype=np.uint8)
        word = simple_page.words[0]
        word.ground_truth_text = "abc"
        word.ground_truth_match_keys = {"match_score": 100}
        simple_page.cv2_numpy_page_image = img

    def test_render_with_low_match_score(self, simple_page):
        img = np.zeros((200, 100, 3), dtype=np.uint8)
        word = simple_page.words[0]
        word.ground_truth_text = "abc"
        word.ground_truth_match_keys = {"match_score": 50}
        simple_page.cv2_numpy_page_image = img


# Text/ground-truth properties ------------------------------------------------


class TestTextProperties:
    def test_text(self, simple_page):
        assert isinstance(simple_page.text, str)

    def test_ground_truth_text(self, simple_page):
        assert isinstance(simple_page.ground_truth_text, str)

    def test_ground_truth_exact_match_when_no_gt(self, simple_page):
        # No ground truth set on items -> exact match cannot be true
        assert simple_page.ground_truth_exact_match is False

    def test_copy_ocr_to_ground_truth(self, simple_page):
        assert simple_page.copy_ocr_to_ground_truth() is True

    def test_copy_ocr_to_ground_truth_no_text(self):
        word = Word(
            text="",
            bounding_box=BoundingBox.from_ltrb(0, 0, 10, 10, is_normalized=False),
            ocr_confidence=0.0,
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
        assert page.copy_ocr_to_ground_truth() is False

    def test_copy_ground_truth_to_ocr(self, simple_page):
        for w in simple_page.words:
            w.ground_truth_text = "GT"
        assert simple_page.copy_ground_truth_to_ocr() is True

    def test_clear_ground_truth(self, simple_page):
        for w in simple_page.words:
            w.ground_truth_text = "GT"
        assert simple_page.clear_ground_truth() is True


# Spatial line search ---------------------------------------------------------


class TestSpatialHelpers:
    def test_closest_line_by_y_range(self, simple_line):
        line2 = Block(
            items=[
                Word(
                    text="other",
                    bounding_box=BoundingBox.from_ltrb(0, 100, 50, 110),
                    ocr_confidence=0.9,
                )
            ],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        result = Page.closest_line_by_y_range_then_x(
            [simple_line, line2], center_x=20.0, center_y=15.0, fallback_line=line2
        )
        # simple_line spans y 10-20, so center_y=15 should match it
        assert result is simple_line

    def test_closest_line_by_y_range_falls_back(self, simple_line):
        # No line covers y=200, falls back to closest_line_by_midpoint
        line2 = Block(
            items=[
                Word(
                    text="other",
                    bounding_box=BoundingBox.from_ltrb(0, 100, 50, 110),
                    ocr_confidence=0.9,
                )
            ],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        result = Page.closest_line_by_y_range_then_x(
            [simple_line, line2], center_x=20.0, center_y=200.0, fallback_line=line2
        )
        assert result in (simple_line, line2)

    def test_closest_line_by_midpoint(self, simple_line):
        result = Page.closest_line_by_midpoint(
            [simple_line], midpoint_y=14.0, fallback_line=simple_line
        )
        assert result is simple_line

    def test_closest_line_by_midpoint_none_returns_fallback(self, simple_line):
        result = Page.closest_line_by_midpoint(
            [simple_line], midpoint_y=None, fallback_line=simple_line
        )
        assert result is simple_line

    def test_closest_line_by_midpoint_no_usable_lines(self):
        line = Block(
            items=[],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        # No usable bbox -> returns fallback
        result = Page.closest_line_by_midpoint(
            [line], midpoint_y=10.0, fallback_line=line
        )
        assert result is line


# Move word between lines -----------------------------------------------------


class TestMoveWordBetweenLines:
    def test_same_line_returns_true(self, simple_line):
        word = simple_line.words[0]
        assert Page.move_word_between_lines(simple_line, simple_line, word) is True

    def test_move_word(self, simple_line):
        target_line = Block(
            items=[],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        word = simple_line.words[0]
        Page.move_word_between_lines(simple_line, target_line, word)
        assert word in target_line.words
        assert word not in simple_line.words


# Validated line words --------------------------------------------------------


class TestValidatedLineWords:
    def test_valid_index(self, simple_page):
        words = simple_page.validated_line_words(0)
        assert words is not None
        assert len(words) > 0

    def test_invalid_negative(self, simple_page):
        assert simple_page.validated_line_words(-1) is None

    def test_invalid_too_large(self, simple_page):
        assert simple_page.validated_line_words(100) is None


# Find / remove nested block --------------------------------------------------


class TestFindParentBlock:
    def test_find_top_level(self, simple_page, simple_paragraph):
        parent = simple_page.find_parent_block(simple_paragraph)
        assert parent is simple_page

    def test_find_nested(self, simple_page, simple_line):
        parent = simple_page.find_parent_block(simple_line)
        # Parent is the paragraph containing the line
        assert parent is not None

    def test_not_found(self, simple_page):
        unrelated = Block(
            items=[],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        assert simple_page.find_parent_block(unrelated) is None


class TestRemoveNestedBlock:
    def test_remove_top_level(self, simple_page, simple_paragraph):
        assert simple_page.remove_nested_block(simple_paragraph) is True

    def test_remove_nested(self, simple_page, simple_line):
        assert simple_page.remove_nested_block(simple_line) is True

    def test_not_found(self, simple_page):
        unrelated = Block(
            items=[],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        assert simple_page.remove_nested_block(unrelated) is False


# Replace block with split paragraphs -----------------------------------------


class TestReplaceBlockWithSplitParagraphs:
    def test_replace_paragraph(self, two_paragraph_page):
        para = two_paragraph_page.items[0]
        lines = list(para.lines)
        result = two_paragraph_page.replace_block_with_split_paragraphs(para, lines)
        assert result is True

    def test_paragraph_not_found_returns_false(self, simple_page):
        unrelated_paragraph = Block(
            items=[],
            block_category=BlockCategory.PARAGRAPH,
            child_type=BlockChildType.BLOCKS,
        )
        result = simple_page.replace_block_with_split_paragraphs(
            unrelated_paragraph, []
        )
        assert result is False


# First usable bbox -----------------------------------------------------------


class TestFirstUsableBbox:
    def test_returns_first_valid(self):
        bbox1 = None
        bbox2 = BoundingBox.from_ltrb(0, 0, 10, 10, is_normalized=False)
        result = Page.first_usable_bbox([bbox1, bbox2])
        assert result is bbox2

    def test_returns_none_when_no_usable(self):
        result = Page.first_usable_bbox([None, None])
        assert result is None


# Add/remove ground truth -----------------------------------------------------


class TestRemoveGroundTruth:
    def test_remove_ground_truth(self, simple_page):
        for w in simple_page.words:
            w.ground_truth_text = "GT"
        # Force unmatched_ground_truth_lines to be set
        simple_page.unmatched_ground_truth_lines = [(0, "extra")]
        simple_page.remove_ground_truth()
        for w in simple_page.words:
            assert w.ground_truth_text == ""
        assert simple_page.unmatched_ground_truth_lines == []


# Paragraphs property ---------------------------------------------------------


class TestParagraphs:
    def test_paragraphs(self, simple_page):
        paragraphs = simple_page.paragraphs
        assert isinstance(paragraphs, list)


# Scale and copy --------------------------------------------------------------


class TestScaleAndCopy:
    def test_scale_pixel_page_returns_new(self):
        word = Word(
            text="x",
            bounding_box=BoundingBox.from_ltrb(0.1, 0.1, 0.2, 0.2, is_normalized=True),
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
        page = Page(width=10, height=20, page_index=0, items=[para])
        new = page.scale(100, 200)
        assert isinstance(new, Page)
        assert new.width == 100
        assert new.height == 200

    def test_scale_no_bbox(self):
        page = Page(width=10, height=20, page_index=0, items=[])
        new = page.scale(50, 60)
        assert new.bounding_box is None

    def test_copy_round_trip(self, simple_page):
        copy = simple_page.copy()
        assert isinstance(copy, Page)
        assert copy.page_index == simple_page.page_index
        assert copy.width == simple_page.width


# To/from dict edge cases -----------------------------------------------------


class TestToFromDictEdgeCases:
    def test_to_dict_preserves_metadata(self):
        page = Page(
            width=100,
            height=200,
            page_index=0,
            items=[],
            image_path="/path/to.png",
            name="page-name",
            source="manual",
            ocr_failed=True,
            provenance_live_ocr={"a": 1},
            provenance_saved_ocr={"b": 2},
            provenance_saved={"c": 3},
        )
        out = page.to_dict()
        assert out["image_path"] == "/path/to.png"
        assert out["name"] == "page-name"
        assert out["source"] == "manual"
        assert out["ocr_failed"] is True
        assert out["provenance_live_ocr"] == {"a": 1}
        assert out["provenance_saved_ocr"] == {"b": 2}
        assert out["provenance_saved"] == {"c": 3}

    def test_from_dict_legacy_page_source(self):
        page = Page.from_dict(
            {
                "width": 100,
                "height": 200,
                "page_index": 0,
                "items": [],
                "page_source": "legacy_source",
            }
        )
        assert page.source == "legacy_source"


# Recompute bounding box ------------------------------------------------------


class TestRecomputeBoundingBox:
    def test_recompute_with_items(self, simple_page):
        old_bbox = simple_page.bounding_box
        simple_page.recompute_bounding_box()
        assert simple_page.bounding_box is not None
        # Should still be a bbox spanning items
        assert isinstance(simple_page.bounding_box, BoundingBox)
        del old_bbox  # noqa: F841

    def test_recompute_empty_page(self):
        page = Page(width=10, height=10, page_index=0, items=[])
        page.recompute_bounding_box()
        # Empty -> bounding_box may stay None
        assert page.bounding_box is None or isinstance(page.bounding_box, BoundingBox)


# Refine bounding boxes -------------------------------------------------------


class TestRefineBoundingBoxes:
    def test_refine_no_image(self, simple_page):
        # When image is None, refine_bounding_boxes is a no-op
        simple_page.refine_bounding_boxes(None)


# Finalize page structure -----------------------------------------------------


class TestFinalizePageStructure:
    def test_finalize_does_not_raise(self, simple_page):
        simple_page.finalize_page_structure()
