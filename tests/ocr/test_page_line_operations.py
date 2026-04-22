"""Tests for Page line/word/paragraph structural operations."""

from __future__ import annotations

import numpy as np

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.word import Word


def _bbox(x1: int, y1: int, x2: int, y2: int) -> BoundingBox:
    return BoundingBox(Point(x1, y1), Point(x2, y2), is_normalized=False)


def _word(text: str, gt: str | None, x: int) -> Word:
    return Word(
        text=text,
        bounding_box=_bbox(x, 0, x + 10, 10),
        ocr_confidence=1.0,
        ground_truth_text=gt,
    )


def _line(words: list[Word], x: int) -> Block:
    return Block(
        items=words,
        bounding_box=_bbox(x, 0, x + 20, 10),
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )


def _paragraph(lines: list[Block], y: int) -> Block:
    return Block(
        items=lines,
        bounding_box=_bbox(0, y, 80, y + 20),
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
    )


class TestMergeLines:
    def test_merge_lines_success(self):
        """Merging multiple lines into the first selected line."""
        line1 = _line([_word("a", "A", 0)], 0)
        line2 = _line([_word("b", "B", 20)], 20)
        line3 = _line([_word("c", "C", 40)], 40)
        page = Page(width=100, height=100, page_index=0, items=[line1, line2, line3])

        result = page.merge_lines([0, 2])

        assert result is True
        assert len(page.lines) == 2
        assert [word.text for word in page.lines[0].words] == ["a", "c"]
        assert page.lines[0].text == "a c"
        assert page.lines[0].ground_truth_text == "A C"

    def test_merge_lines_requires_two_indices(self):
        """Merge fails when fewer than two lines are selected."""
        page = Page(
            width=100,
            height=100,
            page_index=0,
            items=[_line([_word("a", "A", 0)], 0), _line([_word("b", "B", 20)], 20)],
        )

        assert page.merge_lines([0]) is False
        assert page.merge_lines([]) is False

    def test_merge_lines_invalid_index(self):
        """Merge fails with out-of-range indices."""
        page = Page(
            width=100,
            height=100,
            page_index=0,
            items=[_line([_word("a", "A", 0)], 0), _line([_word("b", "B", 20)], 20)],
        )

        result = page.merge_lines([0, 5])

        assert result is False
        assert len(page.lines) == 2

    def test_merge_lines_recomputes_paragraph_bbox_across_paragraphs(self):
        """Merging lines across paragraphs should recompute destination paragraph bbox."""
        line1 = _line([_word("alpha", "A", 0)], 0)
        line2 = _line([_word("beta", "B", 20)], 20)
        para1 = Block(
            items=[line1],
            bounding_box=_bbox(0, 0, 20, 10),
            child_type=BlockChildType.BLOCKS,
            block_category=BlockCategory.PARAGRAPH,
        )
        para2 = Block(
            items=[line2],
            bounding_box=_bbox(20, 0, 40, 10),
            child_type=BlockChildType.BLOCKS,
            block_category=BlockCategory.PARAGRAPH,
        )
        page = Page(width=100, height=100, page_index=0, items=[para1, para2])

        result = page.merge_lines([0, 1])

        assert result is True
        assert len(page.lines) == 1
        assert len(page.paragraphs) == 1
        merged_paragraph = page.paragraphs[0]
        assert merged_paragraph.bounding_box is not None
        assert merged_paragraph.bounding_box.top_left.x == 0
        assert merged_paragraph.bounding_box.bottom_right.x == 30

    def test_merge_lines_falls_back_on_malformed_bbox_metadata(self, monkeypatch):
        """Merge should still succeed when Block.merge fails with NoneType.is_normalized."""
        line1 = _line([_word("alpha", "A", 0)], 0)
        line2 = _line([_word("beta", "B", 20)], 20)
        page = Page(width=100, height=100, page_index=0, items=[line1, line2])

        def _broken_merge(_self, _other):
            raise AttributeError("'NoneType' object has no attribute 'is_normalized'")

        monkeypatch.setattr(Block, "merge", _broken_merge)

        result = page.merge_lines([0, 1])

        assert result is True
        assert len(page.lines) == 1
        assert [word.text for word in page.lines[0].words] == ["alpha", "beta"]

    def test_merge_lines_ignores_finalize_malformed_bbox_error(self, monkeypatch):
        """Merge should succeed when finalize recompute raises NoneType.is_normalized."""
        line1 = _line([_word("alpha", "A", 0)], 0)
        line2 = _line([_word("beta", "B", 20)], 20)
        page = Page(width=100, height=100, page_index=0, items=[line1, line2])

        original_recompute = Block.recompute_bounding_box

        def _broken_merge(_self, _other):
            raise AttributeError("'NoneType' object has no attribute 'is_normalized'")

        def _sometimes_broken_recompute(self):
            if self is page.lines[0]:
                raise AttributeError(
                    "'NoneType' object has no attribute 'is_normalized'"
                )
            return original_recompute(self)

        monkeypatch.setattr(Block, "merge", _broken_merge)
        monkeypatch.setattr(
            Block, "recompute_bounding_box", _sometimes_broken_recompute
        )

        result = page.merge_lines([0, 1])

        assert result is True
        assert len(page.lines) == 1
        assert [word.text for word in page.lines[0].words] == ["alpha", "beta"]

    def test_merge_lines_removes_empty_paragraphs_when_finalize_is_malformed(
        self, monkeypatch
    ):
        """Even when finalize path hits malformed geometry, empty paragraphs are removed."""
        line1 = _line([_word("alpha", "A", 0)], 0)
        line2 = _line([_word("beta", "B", 20)], 20)
        para1 = _paragraph([line1], 0)
        para2 = _paragraph([line2], 30)
        page = Page(width=100, height=100, page_index=0, items=[para1, para2])

        monkeypatch.setattr(
            page,
            "finalize_page_structure",
            lambda: (_ for _ in ()).throw(
                AttributeError("'NoneType' object has no attribute 'is_normalized'")
            ),
        )

        result = page.merge_lines([0, 1])

        assert result is True
        assert len(page.lines) == 1
        assert len(page.paragraphs) == 1
        assert [line.text for line in page.paragraphs[0].lines] == ["alpha beta"]


class TestDeleteLines:
    def test_delete_lines_success(self):
        """Deleting selected lines removes them from the page."""
        line1 = _line([_word("a", "A", 0)], 0)
        line2 = _line([_word("b", "B", 20)], 20)
        line3 = _line([_word("c", "C", 40)], 40)
        page = Page(width=100, height=100, page_index=0, items=[line1, line2, line3])

        result = page.delete_lines([1, 2])

        assert result is True
        assert len(page.lines) == 1
        assert page.lines[0].text == "a"

    def test_delete_lines_requires_selection(self):
        """Deletion fails when no lines are selected."""
        page = Page(
            width=100,
            height=100,
            page_index=0,
            items=[_line([_word("a", "A", 0)], 0), _line([_word("b", "B", 20)], 20)],
        )

        assert page.delete_lines([]) is False

    def test_delete_lines_invalid_index(self):
        """Deletion fails with out-of-range indices."""
        page = Page(
            width=100,
            height=100,
            page_index=0,
            items=[_line([_word("a", "A", 0)], 0), _line([_word("b", "B", 20)], 20)],
        )

        result = page.delete_lines([0, 5])

        assert result is False
        assert len(page.lines) == 2


class TestDeleteParagraphs:
    def test_delete_paragraphs_success(self):
        """Deleting selected paragraphs removes them from the page."""
        para1 = _paragraph([_line([_word("a", "A", 0)], 0)], 0)
        para2 = _paragraph([_line([_word("b", "B", 20)], 20)], 30)
        page = Page(width=100, height=100, page_index=0, items=[para1, para2])

        result = page.delete_paragraphs([1])

        assert result is True
        assert len(page.paragraphs) == 1
        assert page.paragraphs[0].text == "a"

    def test_merge_paragraphs_handles_malformed_bbox_during_remove_item(self):
        """Paragraph merge should succeed when remove_item recompute hits malformed geometry."""
        para1 = _paragraph([_line([_word("a", "A", 0)], 0)], 0)
        para2 = _paragraph([_line([_word("b", "B", 20)], 20)], 30)
        malformed_para = _paragraph([_line([_word("c", "C", 40)], 40)], 60)
        page = Page(
            width=100,
            height=100,
            page_index=0,
            items=[para1, para2, malformed_para],
        )
        malformed_para.bounding_box = None

        paragraphs = list(page.paragraphs)
        index_a = next(i for i, p in enumerate(paragraphs) if p.lines[0].text == "a")
        index_b = next(i for i, p in enumerate(paragraphs) if p.lines[0].text == "b")

        result = page.merge_paragraphs([index_a, index_b])

        assert result is True
        assert len(page.paragraphs) == 2
        line_texts_by_paragraph = [
            [line.text for line in para.lines] for para in page.paragraphs
        ]
        assert ["a", "b"] in line_texts_by_paragraph


class TestDeleteWords:
    def test_delete_words_success(self):
        """Deleting selected words removes only the targeted words."""
        line = _line(
            [_word("alpha", "A", 0), _word("beta", "B", 20), _word("gamma", "C", 40)],
            0,
        )
        page = Page(width=100, height=100, page_index=0, items=[line])

        result = page.delete_words([(0, 1)])

        assert result is True
        assert [word.text for word in page.lines[0].words] == ["alpha", "gamma"]

    def test_delete_words_removes_line_when_it_becomes_empty(self):
        """Deleting the final word from a line removes the now-empty line."""
        line1 = _line([_word("alpha", "A", 0)], 0)
        line2 = _line([_word("beta", "B", 20)], 20)
        paragraph = _paragraph([line1, line2], 0)
        page = Page(width=100, height=100, page_index=0, items=[paragraph])

        result = page.delete_words([(0, 0)])

        assert result is True
        assert len(page.lines) == 1
        assert page.lines[0].text == "beta"


class TestMergeWords:
    def test_merge_word_left_success(self):
        """Merging word left concatenates with the immediate left neighbor."""
        line = _line(
            [_word("alpha", "A", 0), _word("beta", "B", 20), _word("gamma", "C", 40)],
            0,
        )
        page = Page(width=100, height=100, page_index=0, items=[line])

        result = page.lines[0].merge_word_left(1)

        assert result is True
        assert [word.text for word in page.lines[0].words] == ["alphabeta", "gamma"]
        assert [word.ground_truth_text for word in page.lines[0].words] == ["", ""]
        merged_box = page.lines[0].words[0].bounding_box
        assert merged_box.top_left.x == 0
        assert merged_box.bottom_right.x == 30

    def test_merge_word_right_success(self):
        """Merging word right concatenates with the immediate right neighbor."""
        line = _line(
            [_word("alpha", "A", 0), _word("beta", "B", 20), _word("gamma", "C", 40)],
            0,
        )
        page = Page(width=100, height=100, page_index=0, items=[line])

        result = page.lines[0].merge_word_right(1)

        assert result is True
        assert [word.text for word in page.lines[0].words] == ["alpha", "betagamma"]
        assert [word.ground_truth_text for word in page.lines[0].words] == ["", ""]
        merged_box = page.lines[0].words[1].bounding_box
        assert merged_box.top_left.x == 20
        assert merged_box.bottom_right.x == 50

    def test_merge_word_left_fails_for_first_word(self):
        """Merging left on the first word fails."""
        line = _line([_word("alpha", "A", 0), _word("beta", "B", 20)], 0)
        page = Page(width=100, height=100, page_index=0, items=[line])

        result = page.lines[0].merge_word_left(0)

        assert result is False
        assert [word.text for word in page.lines[0].words] == ["alpha", "beta"]


class TestSplitWord:
    def test_split_word_success(self):
        """Splitting a word creates two words and clears GT for the line."""
        line = _line([_word("alphabet", "ALPHABET", 0), _word("gamma", "GAMMA", 20)], 0)
        page = Page(width=100, height=100, page_index=0, items=[line])

        result = page.split_word(0, 0, 0.5)

        assert result is True
        assert [word.text for word in page.lines[0].words] == ["alph", "abet", "gamma"]
        assert [word.ground_truth_text for word in page.lines[0].words] == ["", "", ""]

    def test_split_word_rejects_edge_fraction(self):
        """Split fails when requested at start/end boundaries."""
        line = _line([_word("alpha", "A", 0)], 0)
        page = Page(width=100, height=100, page_index=0, items=[line])

        assert page.split_word(0, 0, 0.0) is False
        assert page.split_word(0, 0, 1.0) is False

    def test_split_word_vertical_assigns_split_pieces_to_closest_line(self):
        """Vertical split moves both split words to the closest line by midpoint."""
        source_word = Word(
            text="alphabet",
            bounding_box=_bbox(0, 34, 12, 54),
            ocr_confidence=1.0,
            ground_truth_text="ALPHABET",
        )
        source_line = Block(
            items=[source_word],
            bounding_box=_bbox(0, 0, 20, 10),
            child_type=BlockChildType.WORDS,
            block_category=BlockCategory.LINE,
        )
        lower_line = Block(
            items=[_word("delta", "DELTA", 20)],
            bounding_box=_bbox(0, 40, 80, 50),
            child_type=BlockChildType.WORDS,
            block_category=BlockCategory.LINE,
        )
        page = Page(
            width=100, height=100, page_index=0, items=[source_line, lower_line]
        )

        result = page.split_word_vertically_and_assign_to_closest_line(0, 0, 0.5)

        assert result is True
        assert all(
            word.text != "alphabet" for line in page.lines for word in line.words
        )
        target_line_words = None
        for line in page.lines:
            line_words = [word.text for word in line.words]
            if line_words[:2] == ["alph", "abet"]:
                target_line_words = line.words
                break
        assert target_line_words is not None
        assert all(word.ground_truth_text == "" for word in target_line_words)


class TestReboxWord:
    def test_rebox_word_replaces_word_bounding_box(self):
        """Reboxing replaces the target word bounding box coordinates."""
        line = _line([_word("alpha", "A", 0)], 0)
        page = Page(width=200, height=100, page_index=0, items=[line])

        result = page.rebox_word(0, 0, 30.0, 5.0, 70.0, 25.0)

        assert result is True
        updated_bbox = page.lines[0].words[0].bounding_box
        assert updated_bbox.top_left.x == 30.0
        assert updated_bbox.top_left.y == 5.0
        assert updated_bbox.bottom_right.x == 70.0
        assert updated_bbox.bottom_right.y == 25.0

    def test_rebox_word_runs_word_refine_helpers(self, monkeypatch):
        """Rebox auto-refines the updated word when a page image exists."""
        line = _line([_word("alpha", "A", 0)], 0)
        page = Page(width=200, height=100, page_index=0, items=[line])
        target_word = page.lines[0].words[0]

        dummy_image = np.zeros((100, 200, 3), dtype=np.uint8)
        monkeypatch.setattr(
            type(page), "cv2_numpy_page_image", property(lambda self: dummy_image)
        )

        seen = []
        target_word.crop_bottom = lambda img: seen.append("crop")

        result = page.rebox_word(0, 0, 30.0, 5.0, 70.0, 25.0)

        assert result is True


class TestNudgeWordBbox:
    def test_nudge_word_bbox_expands_and_contracts_size(self):
        """Nudging resizes bbox dimensions, not translation."""
        line = _line([_word("alpha", "A", 20)], 20)
        page = Page(width=200, height=100, page_index=0, items=[line])

        result = page.nudge_word_bbox(0, 0, 3.0, 3.0, 2.0, 2.0)

        assert result is True
        updated_bbox = page.lines[0].words[0].bounding_box
        assert updated_bbox.top_left.x == 17.0
        assert updated_bbox.top_left.y == 0.0
        assert updated_bbox.bottom_right.x == 33.0
        assert updated_bbox.bottom_right.y == 12.0

        contract_result = page.nudge_word_bbox(0, 0, -2.0, -2.0, -1.0, -1.0)

        assert contract_result is True
        contracted_bbox = page.lines[0].words[0].bounding_box
        assert contracted_bbox.top_left.x == 19.0
        assert contracted_bbox.top_left.y == 1.0
        assert contracted_bbox.bottom_right.x == 31.0
        assert contracted_bbox.bottom_right.y == 11.0

    def test_nudge_word_bbox_can_skip_refine_helpers(self, monkeypatch):
        """Nudging with refine_after=False does not call word refine helpers."""
        from unittest.mock import MagicMock

        line = _line([_word("alpha", "A", 20)], 20)
        page = Page(width=200, height=100, page_index=0, items=[line])
        word = page.lines[0].words[0]

        word.crop_bottom = MagicMock()
        word.expand_to_content = MagicMock()

        result = page.nudge_word_bbox(0, 0, 3.0, 3.0, 2.0, 2.0, refine_after=False)

        assert result is True
        word.crop_bottom.assert_not_called()
        word.expand_to_content.assert_not_called()


class TestParagraphSplitting:
    def test_split_paragraph_after_line_success(self):
        """Splitting after selected line splits one paragraph into two."""
        line1 = _line([_word("a", "A", 0)], 0)
        line2 = _line([_word("b", "B", 20)], 20)
        para = _paragraph([line1, line2], 0)
        page = Page(width=100, height=100, page_index=0, items=[para])

        result = page.split_paragraph_after_line(0)

        assert result is True
        assert len(page.paragraphs) == 2
        assert page.paragraphs[0].lines[0].text == "a"
        assert page.paragraphs[1].lines[0].text == "b"

    def test_split_paragraph_after_line_fails_on_last_line(self):
        """Splitting after last line fails (no trailing segment)."""
        line1 = _line([_word("a", "A", 0)], 0)
        line2 = _line([_word("b", "B", 20)], 20)
        para = _paragraph([line1, line2], 0)
        page = Page(width=100, height=100, page_index=0, items=[para])

        result = page.split_paragraph_after_line(1)

        assert result is False
        assert len(page.paragraphs) == 1

    def test_split_paragraph_with_selected_lines_success(self):
        """Selected lines split a paragraph into selected and unselected groups."""
        line1 = _line([_word("a", "A", 0)], 0)
        line2 = _line([_word("b", "B", 20)], 20)
        line3 = _line([_word("c", "C", 40)], 40)
        para = _paragraph([line1, line2, line3], 0)
        page = Page(width=100, height=100, page_index=0, items=[para])

        result = page.split_paragraph_with_selected_lines([0, 2])

        assert result is True
        assert len(page.paragraphs) == 2
        assert [line.text for line in page.paragraphs[0].lines] == ["a", "c"]
        assert [line.text for line in page.paragraphs[1].lines] == ["b"]

    def test_split_paragraph_with_selected_lines_fails_across_paragraphs(self):
        """Split-by-selection fails when lines span multiple paragraphs."""
        para1 = _paragraph([_line([_word("a", "A", 0)], 0)], 0)
        para2 = _paragraph([_line([_word("b", "B", 20)], 20)], 30)
        page = Page(width=100, height=100, page_index=0, items=[para1, para2])

        result = page.split_paragraph_with_selected_lines([0, 1])

        assert result is False
        assert len(page.paragraphs) == 2


class TestSplitLineOps:
    def test_split_line_after_word_success(self):
        """Splitting a line after a selected word produces two lines."""
        line = _line(
            [_word("alpha", "A", 0), _word("beta", "B", 20), _word("gamma", "C", 40)],
            0,
        )
        para = _paragraph([line], 0)
        page = Page(width=120, height=100, page_index=0, items=[para])

        result = page.split_line_after_word(0, 0)

        assert result is True
        assert len(page.lines) == 2
        assert [word.text for word in page.lines[0].words] == ["alpha"]
        assert [word.text for word in page.lines[1].words] == ["beta", "gamma"]

    def test_split_line_after_word_fails_on_last_word(self):
        """Splitting after the last word fails because trailing segment is empty."""
        line = _line([_word("alpha", "A", 0), _word("beta", "B", 20)], 0)
        para = _paragraph([line], 0)
        page = Page(width=120, height=100, page_index=0, items=[para])

        result = page.split_line_after_word(0, 1)

        assert result is False

    def test_split_line_with_selected_words_moves_words_into_single_new_line(self):
        """Selected words from multiple lines move into one new line."""
        line1 = _line(
            [_word("alpha", "A", 0), _word("beta", "B", 20), _word("gamma", "C", 40)],
            0,
        )
        line2 = _line(
            [_word("delta", "D", 0), _word("epsilon", "E", 20), _word("zeta", "F", 40)],
            20,
        )
        para = _paragraph([line1, line2], 0)
        page = Page(width=180, height=120, page_index=0, items=[para])

        result = page.split_line_with_selected_words([(0, 1), (1, 0), (1, 2)])

        assert result is True
        assert len(page.lines) == 3
        line_signatures = [
            tuple(word.text for word in line.words) for line in page.lines
        ]
        assert ("alpha", "gamma") in line_signatures
        assert ("epsilon",) in line_signatures
        assert sorted(("beta", "delta", "zeta")) in [
            sorted(signature) for signature in line_signatures
        ]

    def test_split_line_with_selected_words_across_paragraphs_creates_single_line_paragraph(
        self,
    ):
        """Cross-paragraph selection still creates one consolidated new line."""
        para1_line = _line(
            [_word("alpha", "A", 0), _word("beta", "B", 20), _word("gamma", "C", 40)],
            0,
        )
        para2_line = _line(
            [_word("delta", "D", 0), _word("epsilon", "E", 20), _word("zeta", "F", 40)],
            20,
        )
        para1 = _paragraph([para1_line], 0)
        para2 = _paragraph([para2_line], 20)
        page = Page(width=180, height=120, page_index=0, items=[para1, para2])

        result = page.split_line_with_selected_words([(0, 1), (1, 0)])

        assert result is True
        assert len(page.paragraphs) == 3
        line_signatures = [
            [tuple(word.text for word in line.words) for line in paragraph.lines]
            for paragraph in page.paragraphs
        ]
        assert [("alpha", "gamma")] in line_signatures
        assert [("epsilon", "zeta")] in line_signatures
        flattened = [signature[0] for signature in line_signatures if signature]
        assert tuple(sorted(("beta", "delta"))) in [
            tuple(sorted(words)) for words in flattened
        ]
        assert len(page.lines) == 3

    def test_split_line_with_selected_words_all_words_from_line_succeeds(self):
        """Selecting all words from a line is a valid extraction."""
        line = _line(
            [
                _word("in", "in", 0),
                _word("the", "the", 20),
                _word("XVIIIth", "XVIIIth", 40),
                _word("Century", "Century", 70),
            ],
            0,
        )
        para = _paragraph([line], 0)
        page = Page(width=180, height=120, page_index=0, items=[para])

        result = page.split_line_with_selected_words([(0, 0), (0, 1), (0, 2), (0, 3)])

        assert result is True
        assert len(page.lines) == 1
        assert [word.text for word in page.lines[0].words] == [
            "in",
            "the",
            "XVIIIth",
            "Century",
        ]


class TestGroupSelectedWords:
    def test_group_selected_words_into_new_paragraph_success(self):
        """Selected words move to a new paragraph with one line per source line."""
        line1 = _line(
            [_word("alpha", "A", 0), _word("beta", "B", 20), _word("gamma", "C", 40)],
            0,
        )
        line2 = _line(
            [_word("delta", "D", 0), _word("epsilon", "E", 20), _word("zeta", "F", 40)],
            20,
        )
        para = _paragraph([line1, line2], 0)
        page = Page(width=160, height=100, page_index=0, items=[para])

        result = page.group_selected_words_into_new_paragraph([(0, 1), (1, 0), (1, 2)])

        assert result is True
        assert len(page.paragraphs) == 2
        assert [word.text for word in page.paragraphs[0].lines[0].words] == [
            "alpha",
            "gamma",
        ]
        assert [word.text for word in page.paragraphs[0].lines[1].words] == ["epsilon"]
        new_paragraph_lines = [
            tuple(word.text for word in line.words) for line in page.paragraphs[1].lines
        ]
        assert sorted(new_paragraph_lines) == sorted([("beta",), ("delta", "zeta")])

    def test_group_selected_words_into_new_paragraph_allows_full_line_selection(self):
        """Grouping allows moving all words from a selected line."""
        line = _line([_word("alpha", "A", 0), _word("beta", "B", 20)], 0)
        para = _paragraph([line], 0)
        page = Page(width=120, height=100, page_index=0, items=[para])

        result = page.group_selected_words_into_new_paragraph([(0, 0), (0, 1)])

        assert result is True
        assert len(page.paragraphs) == 1
        assert [word.text for word in page.paragraphs[0].lines[0].words] == [
            "alpha",
            "beta",
        ]

    def test_group_selected_words_into_new_paragraph_allows_multi_paragraph_selection(
        self,
    ):
        """Grouping allows selected words from multiple source paragraphs."""
        para1_line = _line(
            [_word("alpha", "A", 0), _word("beta", "B", 20), _word("gamma", "C", 40)],
            0,
        )
        para2_line = _line(
            [_word("delta", "D", 0), _word("epsilon", "E", 20), _word("zeta", "F", 40)],
            20,
        )
        para1 = _paragraph([para1_line], 0)
        para2 = _paragraph([para2_line], 20)
        page = Page(width=160, height=120, page_index=0, items=[para1, para2])

        selected_keys: list[tuple[int, int]] = []
        for line_index, line in enumerate(page.lines):
            for word_index, word in enumerate(line.words):
                if word.text in {"beta", "delta"}:
                    selected_keys.append((line_index, word_index))

        result = page.group_selected_words_into_new_paragraph(selected_keys)

        assert result is True
        assert len(page.paragraphs) == 3
        paragraph_line_signatures = [
            sorted(tuple(word.text for word in line.words) for line in paragraph.lines)
            for paragraph in page.paragraphs
        ]
        assert [("alpha", "gamma")] in paragraph_line_signatures
        assert [("epsilon", "zeta")] in paragraph_line_signatures
        assert sorted([("beta",), ("delta",)]) in paragraph_line_signatures

    def test_group_selected_words_into_new_paragraph_allows_cross_container_selection(
        self,
    ):
        """Grouping allows source paragraphs under different parent containers."""
        para1_line = _line(
            [_word("alpha", "A", 0), _word("beta", "B", 20), _word("gamma", "C", 40)],
            0,
        )
        para2_line = _line(
            [_word("delta", "D", 0), _word("epsilon", "E", 20), _word("zeta", "F", 40)],
            20,
        )
        para1 = _paragraph([para1_line], 0)
        para2 = _paragraph([para2_line], 20)
        container1 = Block(
            items=[para1],
            bounding_box=_bbox(0, 0, 80, 40),
            child_type=BlockChildType.BLOCKS,
            block_category=BlockCategory.BLOCK,
        )
        container2 = Block(
            items=[para2],
            bounding_box=_bbox(100, 0, 180, 40),
            child_type=BlockChildType.BLOCKS,
            block_category=BlockCategory.BLOCK,
        )
        page = Page(width=220, height=120, page_index=0, items=[container1, container2])

        selected_keys: list[tuple[int, int]] = []
        for line_index, line in enumerate(page.lines):
            for word_index, word in enumerate(line.words):
                if word.text in {"beta", "delta"}:
                    selected_keys.append((line_index, word_index))

        result = page.group_selected_words_into_new_paragraph(selected_keys)

        assert result is True
        paragraph_line_signatures = [
            sorted(tuple(word.text for word in line.words) for line in paragraph.lines)
            for paragraph in page.paragraphs
        ]
        assert [("alpha", "gamma")] in paragraph_line_signatures
        assert [("epsilon", "zeta")] in paragraph_line_signatures
        assert sorted([("beta",), ("delta",)]) in paragraph_line_signatures


class TestAddWordToPage:
    """Tests for Page.add_word_to_page, including 2D nearest-line selection."""

    def _make_line(self, words, x1, y1, x2, y2):
        return Block(
            items=words,
            bounding_box=BoundingBox(Point(x1, y1), Point(x2, y2), is_normalized=False),
            child_type=BlockChildType.WORDS,
            block_category=BlockCategory.LINE,
        )

    def test_add_word_inserts_into_only_line(self):
        """A word drawn over the single line is inserted into it."""
        line = self._make_line([_word("hello", "Hello", 0)], 0, 0, 100, 10)
        page = Page(width=200, height=100, page_index=0, items=[line])

        result = page.add_word_to_page(50, 0, 80, 10, text="new")

        assert result is True
        word_texts = [w.text for w in page.lines[0].words]
        assert "new" in word_texts

    def test_add_word_selects_line_by_y_range(self):
        """center_y inside line2's Y range but not line1's goes to line2."""
        line1 = self._make_line([_word("top", "Top", 0)], 0, 0, 100, 10)
        line2 = self._make_line([_word("bottom", "Bottom", 0)], 0, 50, 100, 60)
        page = Page(width=200, height=100, page_index=0, items=[line1, line2])

        result = page.add_word_to_page(10, 53, 40, 57, text="near")

        assert result is True
        line2_texts = [w.text for w in page.lines[1].words]
        assert "near" in line2_texts
        line1_texts = [w.text for w in page.lines[0].words]
        assert "near" not in line1_texts

    def test_add_word_parallel_columns_x_breaks_tie(self):
        """Parallel columns at same Y: both are Y-range candidates, X breaks the tie."""
        left_line = self._make_line([_word("left", "Left", 5)], 0, 40, 80, 60)
        right_line = self._make_line([_word("right", "Right", 125)], 120, 40, 200, 60)
        page = Page(width=200, height=100, page_index=0, items=[left_line, right_line])

        result = page.add_word_to_page(150, 45, 170, 55, text="col")

        assert result is True
        lines = list(page.lines)
        right_words = [w.text for w in lines[1].words]
        left_words = [w.text for w in lines[0].words]
        assert "col" in right_words
        assert "col" not in left_words

    def test_add_word_x_breaks_tie_when_both_lines_contain_center_y(self):
        """Both lines span center_y; the one with the nearer center X wins."""
        line_a = self._make_line([_word("a", "A", 0)], 0, 30, 60, 50)
        line_b = self._make_line([_word("b", "B", 140)], 140, 30, 200, 50)
        page = Page(width=200, height=100, page_index=0, items=[line_a, line_b])

        result = page.add_word_to_page(5, 38, 15, 42, text="near_a")

        assert result is True
        lines = list(page.lines)
        line_a_words = [w.text for w in lines[0].words]
        assert "near_a" in line_a_words
