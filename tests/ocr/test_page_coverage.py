"""Coverage-focused tests for Page (rendering, structural ops, helpers)."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
import pytest

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pdomain_book_tools.ocr.page import Page
from pdomain_book_tools.ocr.word import Word

ImageArray = npt.NDArray[np.uint8]

# Fixtures ---------------------------------------------------------------------


@pytest.fixture
def simple_word() -> Word:
    return Word(
        text="abc",
        bounding_box=BoundingBox.from_ltrb(10, 10, 30, 20, is_normalized=False),
        ocr_confidence=0.9,
    )


@pytest.fixture
def simple_line(simple_word: Word) -> Block:
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
def simple_paragraph(simple_line: Block) -> Block:
    return Block(
        items=[simple_line],
        block_category=BlockCategory.PARAGRAPH,
        child_type=BlockChildType.BLOCKS,
    )


@pytest.fixture
def simple_page(simple_paragraph: Block) -> Page:
    return Page(
        width=100,
        height=200,
        page_index=0,
        blocks=[simple_paragraph],
    )


@pytest.fixture
def two_paragraph_page() -> Page:
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
        blocks=[para1, para2],
    )


# Property aliases and metadata -----------------------------------------------


class TestPropertyAliases:
    def test_index_alias_get_set(self, simple_page: Page) -> None:
        assert simple_page.index == simple_page.page_index
        simple_page.index = 7
        assert simple_page.page_index == 7

    def test_page_source_alias_removed(self, simple_page: Page) -> None:
        """Task 4: page_source (alias for source) removed along with source field."""
        assert not hasattr(simple_page, "page_source")
        assert not hasattr(simple_page, "source")

    def test_resolved_dimensions_uses_width_height(self, simple_page: Page) -> None:
        assert simple_page.resolved_dimensions == (100.0, 200.0)

    def test_resolved_dimensions_falls_back_to_image(self) -> None:
        page = Page(width=0, height=0, page_index=0, blocks=[])
        page._image_array = np.zeros((50, 70, 3), dtype=np.uint8)
        assert page.resolved_dimensions == (70.0, 50.0)

    def test_resolved_dimensions_zero_when_neither(self) -> None:
        page = Page(width=0, height=0, page_index=0, blocks=[])
        assert page.resolved_dimensions == (0.0, 0.0)


# is_content_normalized --------------------------------------------------------


class TestIsContentNormalized:
    def test_normalized_words(self) -> None:
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
        page = Page(width=100, height=100, page_index=0, blocks=[para])
        assert page.is_content_normalized is True

    def test_pixel_words(self, simple_page: Page) -> None:
        assert simple_page.is_content_normalized is False

    def test_empty_page(self) -> None:
        page = Page(width=100, height=100, page_index=0, blocks=[])
        assert page.is_content_normalized is False


# Add/Remove items -------------------------------------------------------------


class TestAddRemoveItem:
    def test_add_item_validates_type(self, simple_page: Page) -> None:
        with pytest.raises(TypeError, match="Block"):
            simple_page.add_item("not a block")

    def test_add_item_appends_and_recomputes(self, simple_page: Page) -> None:
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

    def test_remove_item(self, simple_page: Page) -> None:
        target = simple_page.items[0]
        simple_page.remove_item(target)
        assert target not in simple_page.items

    def test_remove_item_not_found(self, simple_page: Page) -> None:
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

    def test_items_setter_rejects_non_collection(self, simple_page: Page) -> None:
        with pytest.raises(TypeError, match="must be a collection"):
            simple_page.items = 42

    def test_items_setter_rejects_non_block_items(self, simple_page: Page) -> None:
        with pytest.raises(TypeError, match="must be of type Block"):
            simple_page.items = ["not a block"]


# Remove line if exists --------------------------------------------------------


class TestRemoveLineIfExists:
    def test_removes_top_level_line(self) -> None:
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
        page = Page(width=50, height=50, page_index=0, blocks=[line])
        assert page.remove_line_if_exists(line) is True

    def test_removes_nested_line(self, simple_page: Page, simple_line: Block) -> None:
        # simple_page has a paragraph containing simple_line
        assert simple_page.remove_line_if_exists(simple_line) is True

    def test_returns_false_when_missing(self, simple_page: Page) -> None:
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
    def test_no_op_on_empty_page(self) -> None:
        page = Page(width=10, height=10, page_index=0, blocks=[])
        # Should be a no-op
        page.remove_empty_items()
        assert page.items == []


# CV2 image rendering ---------------------------------------------------------


class TestCv2NumpyImage:
    def test_constructor_accepts_ndarray(self) -> None:
        """cv2_numpy_page_image assigned directly after construction."""
        img: ImageArray = np.zeros((100, 200, 3), dtype=np.uint8)
        page = Page(width=200, height=100, page_index=0, blocks=[])
        page.cv2_numpy_page_image = img
        assert page.cv2_numpy_page_image is not None

    def test_setter_validates_type(self, simple_page: Page) -> None:
        with pytest.raises(TypeError, match="ndarray"):
            simple_page.cv2_numpy_page_image = "not an array"  # type: ignore[assignment]

    def test_setter_accepts_none_clears(self, simple_page: Page) -> None:
        simple_page.cv2_numpy_page_image = None
        # Now property getter returns None
        assert simple_page.cv2_numpy_page_image is None

    def test_setter_creates_overlay_images(self, simple_page: Page) -> None:
        img: ImageArray = np.zeros((200, 100, 3), dtype=np.uint8)
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

    def test_render_with_match_scores(self, simple_page: Page) -> None:
        """Exercise the matched-word color branch."""
        img: ImageArray = np.zeros((200, 100, 3), dtype=np.uint8)
        word = simple_page.words[0]
        word.ground_truth_text = "abc"
        word.ground_truth_match_keys = {"match_score": 95}
        word2 = simple_page.words[1]
        word2.ground_truth_text = "def"
        word2.ground_truth_match_keys = {"match_score": 75}
        simple_page.cv2_numpy_page_image = img
        # No exception means the branches succeeded

    def test_render_with_perfect_match(self, simple_page: Page) -> None:
        img: ImageArray = np.zeros((200, 100, 3), dtype=np.uint8)
        word = simple_page.words[0]
        word.ground_truth_text = "abc"
        word.ground_truth_match_keys = {"match_score": 100}
        simple_page.cv2_numpy_page_image = img

    def test_render_with_low_match_score(self, simple_page: Page) -> None:
        img: ImageArray = np.zeros((200, 100, 3), dtype=np.uint8)
        word = simple_page.words[0]
        word.ground_truth_text = "abc"
        word.ground_truth_match_keys = {"match_score": 50}
        simple_page.cv2_numpy_page_image = img


# Text/ground-truth properties ------------------------------------------------


class TestTextProperties:
    def test_text(self, simple_page: Page) -> None:
        assert isinstance(simple_page.text, str)

    def test_ground_truth_text(self, simple_page: Page) -> None:
        assert isinstance(simple_page.ground_truth_text, str)

    def test_ground_truth_exact_match_when_no_gt(self, simple_page: Page) -> None:
        # No ground truth set on items -> exact match cannot be true
        assert simple_page.ground_truth_exact_match is False

    def test_copy_ocr_to_ground_truth(self, simple_page: Page) -> None:
        assert simple_page.copy_ocr_to_ground_truth() is True

    def test_copy_ocr_to_ground_truth_no_text(self) -> None:
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
        page = Page(width=100, height=100, page_index=0, blocks=[para])
        assert page.copy_ocr_to_ground_truth() is False

    def test_copy_ground_truth_to_ocr(self, simple_page: Page) -> None:
        for w in simple_page.words:
            w.ground_truth_text = "GT"
        assert simple_page.copy_ground_truth_to_ocr() is True

    def test_clear_ground_truth(self, simple_page: Page) -> None:
        for w in simple_page.words:
            w.ground_truth_text = "GT"
        assert simple_page.clear_ground_truth() is True


# Spatial line search ---------------------------------------------------------


class TestSpatialHelpers:
    def test_closest_line_by_y_range(self, simple_line: Block) -> None:
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

    def test_closest_line_by_y_range_falls_back(self, simple_line: Block) -> None:
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

    def test_closest_line_by_midpoint(self, simple_line: Block) -> None:
        result = Page.closest_line_by_midpoint(
            [simple_line], midpoint_y=14.0, fallback_line=simple_line
        )
        assert result is simple_line

    def test_closest_line_by_midpoint_none_returns_fallback(
        self, simple_line: Block
    ) -> None:
        result = Page.closest_line_by_midpoint(
            [simple_line], midpoint_y=None, fallback_line=simple_line
        )
        assert result is simple_line

    def test_closest_line_by_midpoint_no_usable_lines(self) -> None:
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
    def test_same_line_returns_true(self, simple_line: Block) -> None:
        word = simple_line.words[0]
        assert Page.move_word_between_lines(simple_line, simple_line, word) is True

    def test_move_word(self, simple_line: Block) -> None:
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
    def test_valid_index(self, simple_page: Page) -> None:
        words = simple_page.validated_line_words(0)
        assert words is not None
        assert len(words) > 0

    def test_invalid_negative(self, simple_page: Page) -> None:
        assert simple_page.validated_line_words(-1) is None

    def test_invalid_too_large(self, simple_page: Page) -> None:
        assert simple_page.validated_line_words(100) is None


# Find / remove nested block --------------------------------------------------


class TestFindParentBlock:
    def test_find_top_level(self, simple_page: Page, simple_paragraph: Block) -> None:
        parent = simple_page.find_parent_block(simple_paragraph)
        assert parent is simple_page

    def test_find_nested(self, simple_page: Page, simple_line: Block) -> None:
        parent = simple_page.find_parent_block(simple_line)
        # Parent is the paragraph containing the line
        assert parent is not None

    def test_not_found(self, simple_page: Page) -> None:
        unrelated = Block(
            items=[],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        assert simple_page.find_parent_block(unrelated) is None


class TestRemoveNestedBlock:
    def test_remove_top_level(self, simple_page: Page, simple_paragraph: Block) -> None:
        assert simple_page.remove_nested_block(simple_paragraph) is True

    def test_remove_nested(self, simple_page: Page, simple_line: Block) -> None:
        assert simple_page.remove_nested_block(simple_line) is True

    def test_not_found(self, simple_page: Page) -> None:
        unrelated = Block(
            items=[],
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        assert simple_page.remove_nested_block(unrelated) is False


# Replace block with split paragraphs -----------------------------------------


class TestReplaceBlockWithSplitParagraphs:
    def test_replace_paragraph(self, two_paragraph_page: Page) -> None:
        para = two_paragraph_page.items[0]
        lines = list(para.lines)
        result = two_paragraph_page.replace_block_with_split_paragraphs(para, lines)
        assert result is True

    def test_paragraph_not_found_returns_false(self, simple_page: Page) -> None:
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
    def test_returns_first_valid(self) -> None:
        bbox1 = None
        bbox2 = BoundingBox.from_ltrb(0, 0, 10, 10, is_normalized=False)
        result = Page.first_usable_bbox([bbox1, bbox2])
        assert result is bbox2

    def test_returns_none_when_no_usable(self) -> None:
        result = Page.first_usable_bbox([None, None])
        assert result is None


# Add/remove ground truth -----------------------------------------------------


class TestRemoveGroundTruth:
    def test_remove_ground_truth(self, simple_page: Page) -> None:
        """Task 4: unmatched_ground_truth_lines removed; remove_ground_truth still clears word GT."""
        from pdomain_book_tools.ocr.gt_orphans import GtOrphans

        for w in simple_page.words:
            w.ground_truth_text = "GT"
        # Task 4: unmatched GT now lives in gt_orphans.lines
        simple_page.gt_orphans = GtOrphans(lines=[(0, "extra")])
        simple_page.remove_ground_truth()
        for w in simple_page.words:
            assert w.ground_truth_text == ""
        # gt_orphans is NOT cleared by remove_ground_truth (it's persistent content, not a cache)
        assert not hasattr(simple_page, "unmatched_ground_truth_lines")
        assert simple_page.gt_orphans is not None
        assert simple_page.gt_orphans.lines == [(0, "extra")]


# Paragraphs property ---------------------------------------------------------


class TestParagraphs:
    def test_paragraphs(self, simple_page: Page) -> None:
        paragraphs = simple_page.paragraphs
        assert isinstance(paragraphs, list)


# Scale and copy --------------------------------------------------------------


class TestScaleAndCopy:
    def test_scale_pixel_page_returns_new(self) -> None:
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
        page = Page(width=10, height=20, page_index=0, blocks=[para])
        new = page.scale(100, 200)
        assert isinstance(new, Page)
        assert new.width == 100
        assert new.height == 200

    def test_scale_no_bbox(self) -> None:
        page = Page(width=10, height=20, page_index=0, blocks=[])
        new = page.scale(50, 60)
        assert new.bounding_box is None

    def test_copy_round_trip(self, simple_page: Page) -> None:
        copy = simple_page.copy()
        assert isinstance(copy, Page)
        assert copy.page_index == simple_page.page_index
        assert copy.width == simple_page.width


# To/from dict edge cases -----------------------------------------------------


class TestToFromDictEdgeCases:
    def test_to_dict_preserves_name(self) -> None:
        """Task 4: only name remains as optional metadata in to_dict."""
        page = Page(
            width=100,
            height=200,
            page_index=0,
            blocks=[],
            name="page-name",
        )
        out = page.to_dict()
        assert out["name"] == "page-name"
        # Removed fields must not appear
        for removed in (
            "image_path",
            "source",
            "ocr_failed",
            "provenance_live_ocr",
            "provenance_saved_ocr",
            "provenance_saved",
            "ocr_provenance",
            "rotation_applied",
        ):
            assert removed not in out

    def test_from_dict_legacy_page_source(self) -> None:
        """Task 4: legacy page_source key is silently ignored (source field removed)."""
        page = Page.from_dict(
            {
                "width": 100,
                "height": 200,
                "page_index": 0,
                "items": [],
                "page_source": "legacy_source",
            }
        )
        assert not hasattr(page, "source")
        assert not hasattr(page, "page_source")


# Recompute bounding box ------------------------------------------------------


class TestRecomputeBoundingBox:
    def test_recompute_with_items(self, simple_page: Page) -> None:
        old_bbox = simple_page.bounding_box
        simple_page.recompute_bounding_box()
        assert simple_page.bounding_box is not None
        # Should still be a bbox spanning items
        assert isinstance(simple_page.bounding_box, BoundingBox)
        del old_bbox

    def test_recompute_empty_page(self) -> None:
        page = Page(width=10, height=10, page_index=0, blocks=[])
        page.recompute_bounding_box()
        # Empty -> bounding_box may stay None
        assert page.bounding_box is None or isinstance(page.bounding_box, BoundingBox)


# Refine bounding boxes -------------------------------------------------------


class TestRefineBoundingBoxes:
    def test_refine_no_image(self, simple_page: Page) -> None:
        # When image is None, refine_bounding_boxes is a no-op
        simple_page.refine_bounding_boxes(None)

    def test_refine_with_explicit_image_covers_false_branch(
        self, simple_page: Page
    ) -> None:
        """Line 2985->2992 False branch: image is NOT None, skip the if-image-is-None block."""
        img: ImageArray = np.zeros((100, 200, 3), dtype=np.uint8)
        # Pass image directly; skips the 'if image is None' block at 2985
        simple_page.refine_bounding_boxes(img)


# Finalize page structure -----------------------------------------------------


class TestFinalizePageStructure:
    def test_finalize_does_not_raise(self, simple_page: Page) -> None:
        simple_page.finalize_page_structure()
