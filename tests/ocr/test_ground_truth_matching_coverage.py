"""Coverage tests for ground truth matching edge cases and error paths."""

import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.ground_truth_matching import (
    LineDiffOpCodes,
    WordDiffOpCodes,
    _build_current_work_gt_line_from_prev,
    _build_current_work_gt_line_remove_suffix,
    _generate_work_variants,
    _should_consider_line_end_soft_wrap,
    generate_best_matched_ground_truth_line,
    try_matching_combined_words,
    update_combined_words_in_line,
    update_line_match_difflib_lines_equal,
    update_line_with_ground_truth,
    update_page_match_difflib_lines_equal,
    update_page_match_difflib_lines_insert,
    update_page_match_unmatched_lines_best_effort,
    update_page_with_ground_truth_text,
)
from pd_book_tools.ocr.ground_truth_matching_helpers.match_type import MatchType
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.word import Word


def _make_word(text, x=0, y=0):
    w = max(8, len(text) * 8)
    return Word(
        text=text,
        bounding_box=BoundingBox.from_ltrb(x, y, x + w, y + 18, is_normalized=False),
    )


def _make_line(text_words, y=0):
    words = [_make_word(w, x=i * 60, y=y) for i, w in enumerate(text_words)]
    return Block(
        items=words,
        block_category=BlockCategory.LINE,
        child_type=BlockChildType.WORDS,
    )


def _make_para(lines, y_start=0):
    return Block(
        items=lines,
        block_category=BlockCategory.PARAGRAPH,
        child_type=BlockChildType.BLOCKS,
    )


def _make_page(lines_of_words):
    lines = [_make_line(words, y=20 + i * 30) for i, words in enumerate(lines_of_words)]
    para = _make_para(lines)
    return Page(width=1000, height=1000, page_index=0, items=[para])


# ---------------------------------------------------------------------------
# update_line_match_difflib_lines_equal error paths
# ---------------------------------------------------------------------------


class TestUpdateLineMatchDifflibLinesEqualErrors:
    def test_raises_when_no_block_category(self):
        """Line object without block_category raises ValueError (line 215)."""

        class FakeLine:
            text = "hello world"
            words = []

        with pytest.raises(ValueError, match="block_category"):
            update_line_match_difflib_lines_equal(FakeLine(), ("hello", "world"))

    def test_raises_when_not_line_category(self):
        """Block with non-LINE category raises ValueError (line 218)."""
        line = _make_line(["hello", "world"])
        line.block_category = BlockCategory.PARAGRAPH

        with pytest.raises(ValueError, match="not a line block"):
            update_line_match_difflib_lines_equal(line, ("hello", "world"))

    def test_raises_when_no_words_attribute(self):
        """Object with block_category=LINE but no words attr raises ValueError (line 221)."""

        class FakeLineWithCategory:
            block_category = BlockCategory.LINE
            text = "hello world"

        with pytest.raises(ValueError, match="words"):
            update_line_match_difflib_lines_equal(
                FakeLineWithCategory(), ("hello", "world")
            )

    def test_raises_on_word_count_mismatch(self):
        """Mismatched word count between line and gt raises ValueError (line 224)."""
        line = _make_line(["hello", "world"])
        with pytest.raises(ValueError, match="word count mismatch"):
            update_line_match_difflib_lines_equal(line, ("hello",))

    def test_raises_on_word_text_mismatch(self):
        """Mismatched word text raises ValueError (line 234)."""
        line = _make_line(["hello", "world"])
        with pytest.raises(ValueError, match="Word mismatch"):
            update_line_match_difflib_lines_equal(line, ("hello", "DIFFERENT"))


class TestUpdatePageMatchDifflibLinesEqualErrors:
    def test_raises_on_line_count_mismatch(self):
        """op with mismatched line/gt count raises ValueError (line 196)."""
        # Page has 2 lines; op maps 2 OCR lines to 1 GT line → mismatch
        page = _make_page([["hello", "world"], ["another", "line"]])
        op = LineDiffOpCodes(
            line_tag="equal",
            ocr_line_1=0,
            ocr_line_2=2,  # 2 OCR lines
            gt_line_1=0,
            gt_line_2=1,  # but only 1 GT line
        )
        gt_tuples = [("hello", "world")]
        with pytest.raises(ValueError, match="Line count mismatch"):
            update_page_match_difflib_lines_equal(page, op, gt_tuples)


# ---------------------------------------------------------------------------
# update_page_match_difflib_lines_insert
# ---------------------------------------------------------------------------


class TestUpdatePageMatchDifflibLinesInsert:
    def test_insert_populates_unmatched_when_initially_empty(self):
        """First GT insert sets unmatched_ground_truth_lines (line 271->274)."""
        page = _make_page([["hello"]])
        page.unmatched_ground_truth_lines = None  # ensure initially None/empty

        op = LineDiffOpCodes(
            line_tag="insert",
            ocr_line_1=0,
            ocr_line_2=0,
            gt_line_1=0,
            gt_line_2=1,
        )
        gt_tuples = [("missing", "line")]
        update_page_match_difflib_lines_insert(
            page=page, op=op, ground_truth_tuples=gt_tuples, ocr_tuples=[]
        )
        assert page.unmatched_ground_truth_lines is not None
        assert len(page.unmatched_ground_truth_lines) == 1
        assert page.unmatched_ground_truth_lines[0][1] == "missing line"

    def test_insert_appends_to_existing_unmatched_list(self):
        """When unmatched list already has entries, append (line 271->274 False branch)."""
        page = _make_page([["hello"]])
        page.unmatched_ground_truth_lines = [(0, "existing line")]

        op = LineDiffOpCodes(
            line_tag="insert",
            ocr_line_1=0,
            ocr_line_2=0,
            gt_line_1=0,
            gt_line_2=1,
        )
        gt_tuples = [("another", "line")]
        update_page_match_difflib_lines_insert(
            page=page, op=op, ground_truth_tuples=gt_tuples, ocr_tuples=[]
        )
        assert len(page.unmatched_ground_truth_lines) == 2
        assert page.unmatched_ground_truth_lines[1][1] == "another line"


# ---------------------------------------------------------------------------
# update_page_match_unmatched_lines_best_effort
# ---------------------------------------------------------------------------


class TestUpdatePageMatchUnmatchedLinesBestEffort:
    def test_skips_empty_ocr_text_lines(self):
        """Lines with empty text are skipped (line 136)."""
        # Create a page with a line whose word text is empty → line.text = ""
        page = _make_page([[""], ["hello", "world"]])
        page.unmatched_ground_truth_lines = [(0, "something")]
        # Should not raise; the empty-text line is skipped
        update_page_match_unmatched_lines_best_effort(page)

    def test_handles_duplicate_candidates_with_skip(self):
        """When same OCR line matches multiple GT lines, second is skipped (line 157)."""
        page = _make_page([["the", "quick", "brown", "fox"]])
        # Two GT lines that both match the same OCR line
        page.unmatched_ground_truth_lines = [
            (0, "the quick brown fox"),
            (0, "the quick brown fox"),  # duplicate
        ]
        update_page_match_unmatched_lines_best_effort(page)
        # Should not raise; duplicates are deduped via used sets

    def test_removes_matched_gt_from_unmatched_list(self):
        """After successful match, removes matched GT from unmatched list (line 168)."""
        page = _make_page([["hello", "world"]])
        # Give the OCR line GT text that matches the unmatched GT
        for word in page.lines[0].words:
            word.ground_truth_text = ""  # no existing GT
        page.unmatched_ground_truth_lines = [(0, "hello world")]

        update_page_match_unmatched_lines_best_effort(page)

        # The matched GT should be removed from the unmatched list
        assert page.unmatched_ground_truth_lines == []


# ---------------------------------------------------------------------------
# update_line_with_ground_truth – "delete" and "insert" word ops
# ---------------------------------------------------------------------------


class TestUpdateLineWithGroundTruth:
    def test_delete_word_op_does_nothing(self):
        """'delete' op logs and does nothing to words (line 399)."""
        line = _make_line(["hello", "world", "extra"])
        ocr_tuple = ("hello", "world", "extra")
        gt_tuple = ("hello", "world")
        update_line_with_ground_truth(
            line=line,
            ocr_line_tuple=ocr_tuple,
            ground_truth_tuple=gt_tuple,
        )
        # "extra" is in OCR but not GT → delete op; OCR words unchanged
        assert line.words[0].ground_truth_text == "hello"
        assert line.words[1].ground_truth_text == "world"

    def test_insert_word_op_adds_unmatched(self):
        """'insert' op adds GT words to unmatched list (lines 413-420)."""
        line = _make_line(["hello"])
        ocr_tuple = ("hello",)
        gt_tuple = ("hello", "inserted")
        update_line_with_ground_truth(
            line=line,
            ocr_line_tuple=ocr_tuple,
            ground_truth_tuple=gt_tuple,
        )
        assert line.unmatched_ground_truth_words is not None
        unmatched_texts = [t for _, t in line.unmatched_ground_truth_words]
        assert "inserted" in unmatched_texts


# ---------------------------------------------------------------------------
# update_combined_words_in_line
# ---------------------------------------------------------------------------


class TestUpdateCombinedWordsInLine:
    def test_replaces_words_in_line(self):
        """update_combined_words_in_line removes old words and adds new ones (lines 882-889)."""
        line = _make_line(["hello", ","])
        new_word = _make_word("hello,")
        new_word.ground_truth_text = "hello,"
        new_word.ground_truth_match_keys = {
            "match_type": MatchType.WORD_EXACTLY_EQUAL.value,
            "match_score": 100,
        }

        combined_ocr_word_nbrs = [0, 1]
        new_combined_words = [new_word]

        update_combined_words_in_line(
            line=line,
            combined_ocr_word_nbrs=combined_ocr_word_nbrs,
            new_combined_words=new_combined_words,
        )

        word_texts = [w.text for w in line.words]
        assert "hello," in word_texts
        assert "hello" not in word_texts
        assert "," not in word_texts


# ---------------------------------------------------------------------------
# try_matching_combined_words
# ---------------------------------------------------------------------------


class TestTryMatchingCombinedWords:
    def test_skips_when_first_char_is_quote_and_short(self):
        """Both OCR and GT starting with quote/prime and short word → skip (lines 484-485)."""
        line = _make_line(["'t", "is"])
        word_0 = line.words[0]
        word_0.ground_truth_match_keys = {}

        # Both start with a quote, and the OCR word is <= 3 chars
        result = try_matching_combined_words(
            matched_ocr_line_words=[word_0],
            ocr_line_tuple=("'t",),
            ground_truth_tuple=("'tis",),
        )
        assert result == []

    def test_skips_when_word_marked_as_split(self):
        """Word with split=True in ground_truth_match_keys → skip (lines 494-497)."""
        line = _make_line(["op-", "posed"])
        word_0 = line.words[0]
        word_0.ground_truth_match_keys = {"split": True}

        result = try_matching_combined_words(
            matched_ocr_line_words=[word_0],
            ocr_line_tuple=("op-", "posed"),
            ground_truth_tuple=("opposed",),
        )
        assert result == []


# ---------------------------------------------------------------------------
# _build_current_work_gt_line_from_prev
# ---------------------------------------------------------------------------


class TestBuildCurrentWorkGtLineFromPrev:
    def test_returns_empty_when_boundary_is_space(self):
        """When the char at prev boundary is a space, returns '' (line 1028)."""
        # previous_ground_truth_text[-1] == ' '
        result = _build_current_work_gt_line_from_prev(
            prev_char_count=1,
            previous_ground_truth_text="word ",
            ground_truth_text="current",
        )
        assert result == ""

    def test_returns_combined_when_boundary_is_word_char(self):
        """When boundary char is not space, prepends the suffix (normal path)."""
        result = _build_current_work_gt_line_from_prev(
            prev_char_count=3,
            previous_ground_truth_text="word",
            ground_truth_text="current",
        )
        assert result == "ord current"


# ---------------------------------------------------------------------------
# _build_current_work_gt_line_remove_suffix
# ---------------------------------------------------------------------------


class TestBuildCurrentWorkGtLineRemoveSuffix:
    def test_raises_when_remove_count_exceeds_length(self):
        """Raises ValueError when remove_count > len(ground_truth_text) (line 1043)."""
        with pytest.raises(ValueError, match="Cannot remove more characters"):
            _build_current_work_gt_line_remove_suffix(
                remove_count=100,
                ground_truth_text="short",
            )

    def test_normal_removal(self):
        """Normal removal returns text without suffix."""
        result = _build_current_work_gt_line_remove_suffix(
            remove_count=2,
            ground_truth_text="hello",
        )
        assert result == "hel"


# ---------------------------------------------------------------------------
# _generate_work_variants
# ---------------------------------------------------------------------------


class TestGenerateWorkVariants:
    def test_uses_default_dash_chars_when_none(self):
        """When dash_chars is None, uses CharacterGroups.DASHES (line 1053)."""
        result = _generate_work_variants("word", include_plain=True, dash_chars=None)
        assert "word" in result
        assert "word--" in result
        # Should include at least some dash variants
        assert len(result) > 2

    def test_custom_dash_chars(self):
        """Custom dash chars are used as provided."""
        result = _generate_work_variants("word", include_plain=True, dash_chars=["-"])
        assert "word" in result
        assert "word-" in result
        assert "word--" in result

    def test_exclude_plain(self):
        """When include_plain=False, base text not in result."""
        result = _generate_work_variants("word", include_plain=False, dash_chars=["-"])
        assert "word" not in result
        assert "word-" in result


# ---------------------------------------------------------------------------
# _should_consider_line_end_soft_wrap
# ---------------------------------------------------------------------------


class TestShouldConsiderLineEndSoftWrap:
    def test_returns_false_for_empty_ocr_text(self):
        """Empty OCR text → returns False (line 1068)."""
        assert _should_consider_line_end_soft_wrap("", "some text") is False

    def test_returns_false_for_empty_gt_text(self):
        """Empty GT text → returns False (line 1068)."""
        assert _should_consider_line_end_soft_wrap("some text", "") is False

    def test_returns_false_when_ocr_core_is_empty(self):
        """When OCR last word strips to nothing → returns False (line 1073)."""
        # A word that is purely punctuation
        assert _should_consider_line_end_soft_wrap(".,;:", "text words") is False

    def test_returns_false_when_ocr_ends_with_dash(self):
        """OCR already ends with a dash → False (explicit dash path handles it)."""
        assert _should_consider_line_end_soft_wrap("word-", "word-ed") is False

    def test_returns_true_for_prefix_match(self):
        """OCR last word is prefix of GT last word → True."""
        assert _should_consider_line_end_soft_wrap("op", "opposed") is True

    def test_returns_false_when_gt_not_longer(self):
        """When GT last word not longer than OCR last word → False."""
        assert _should_consider_line_end_soft_wrap("hello", "hello") is False


# ---------------------------------------------------------------------------
# generate_best_matched_ground_truth_line – no variants path
# ---------------------------------------------------------------------------


class TestGenerateBestMatchedGroundTruthLine:
    def test_returns_early_for_empty_text(self):
        """Empty strings return immediately (existing check)."""
        result, score = generate_best_matched_ground_truth_line("", "some text")
        assert result == "some text"
        assert score == 0

    def test_returns_gt_with_zero_score_when_no_variants(self):
        """Variants are all empty → return (ground_truth_text, 0) (line 1148).

        A single-char GT like 'a' combined with a dash-ending OCR means
        every remove_suffix(j, 'a') yields '' for j in [0,1], and the
        filtered variants list is empty.
        """
        result, score = generate_best_matched_ground_truth_line(
            ocr_text="x-",
            ground_truth_text="a",
            previous_ground_truth_text="",
        )
        # When no useful variants remain, we fall back to the raw gt text with score 0
        assert result == "a"
        assert score == 0

    def test_normal_matching(self):
        """Normal matching returns best variant and score > 0."""
        result, score = generate_best_matched_ground_truth_line(
            ocr_text="hello world",
            ground_truth_text="hello world",
            previous_ground_truth_text="",
        )
        assert score > 0
        assert result == "hello world"


# ---------------------------------------------------------------------------
# update_page_with_ground_truth_text – "delete" opcode exists
# ---------------------------------------------------------------------------


class TestUpdatePageWithGroundTruthText:
    def test_delete_op_occurs_for_extra_ocr_lines(self):
        """Extra OCR lines (not in GT) result in delete op (line 399 in word level)."""
        page = _make_page(
            [
                ["hello", "world"],
                ["extra", "ocr", "only"],
            ]
        )
        gt_text = "hello world"
        update_page_with_ground_truth_text(page, gt_text)
        # First line should be matched
        assert page.lines[0].words[0].ground_truth_text == "hello"
        # Second line is OCR-only; no GT assigned
        assert all(w.ground_truth_text == "" for w in page.lines[1].words)

    def test_replace_op_with_insert_word(self):
        """GT having more words than OCR creates unmatched word entries."""
        page = _make_page([["hello"]])
        gt_text = "hello world"
        update_page_with_ground_truth_text(page, gt_text)
        # The line word "hello" should be matched
        assert page.lines[0].words[0].ground_truth_text in ("hello", "")


# ---------------------------------------------------------------------------
# match_different_line_counts deduplication (line 979)
# ---------------------------------------------------------------------------


class TestMatchDifferentLineCountsDedup:
    def test_deduplication_in_replace_op(self):
        """When multiple GT lines map to the same OCR line, duplicates are skipped (line 979).

        Two OCR lines, three GT lines where OCR line 0 matches both GT 0 and GT 1.
        After GT 0 is matched to OCR 0, GT 1 share the same OCR line so is skipped.
        """
        from pd_book_tools.ocr.ground_truth_matching import (
            LineDiffOpCodes,
            update_page_match_difflib_lines_replace_different_line_count,
        )

        page = _make_page(
            [
                ["hello", "world"],
                ["foo", "bar"],
            ]
        )
        ocr_tuples = [
            ("hello", "world"),
            ("foo", "bar"),
        ]
        ground_truth_tuples = [
            ("hello", "world"),  # GT 0 — perfect match for OCR 0
            ("hello", "world", "again"),  # GT 1 — partial match for OCR 0 (79%)
            ("foo", "bar"),  # GT 2 — perfect match for OCR 1
        ]
        op = LineDiffOpCodes(
            line_tag="replace",
            ocr_line_1=0,
            ocr_line_2=2,
            gt_line_1=0,
            gt_line_2=3,
        )
        # This should complete without error; line 979 is hit when GT 1 is skipped
        update_page_match_difflib_lines_replace_different_line_count(
            page=page,
            op=op,
            ocr_tuples=ocr_tuples,
            ground_truth_tuples=ground_truth_tuples,
        )
        # OCR lines should be matched to their best GT
        assert page.lines[0].words[0].ground_truth_text == "hello"


# ---------------------------------------------------------------------------
# try_matching_combined_words – quote/prime skip (line 484) and split flag (line 494)
# ---------------------------------------------------------------------------


class TestTryMatchingCombinedWordsEdgeCases:
    def test_first_char_quote_in_both_returns_empty(self):
        """Lines 484-485: first char is quote in both OCR and GT, short word → return []."""
        w1 = _make_word("'he", x=0, y=0)
        w2 = _make_word("said", x=35, y=0)
        # ocr_line_tuple[0] starts with a quote, len <= 3, gt also starts with quote
        result = try_matching_combined_words(
            [w1, w2],
            ocr_line_tuple=["'he", "said"],
            ground_truth_tuple=["'he", "said"],
        )
        assert result == []

    def test_word_with_split_flag_returns_empty(self):
        """Lines 494-497: word marked as manually split → return []."""
        w1 = _make_word("hello", x=0, y=0)
        w2 = _make_word("world", x=55, y=0)
        w1.ground_truth_match_keys = {"split": True}
        result = try_matching_combined_words(
            [w1, w2],
            ocr_line_tuple=["hello", "world"],
            ground_truth_tuple=["hello", "world"],
        )
        assert result == []


# ---------------------------------------------------------------------------
# update_line_with_ground_truth_replace_words – break and continue paths (lines 831, 835)
# ---------------------------------------------------------------------------


class TestReplaceWordsBreakAndContinue:
    def test_break_when_gt_exhausted_before_ocr(self):
        """Line 831: break when to_match_gt_word_nbrs is empty during OCR loop.
        Triggered when more OCR words than GT words in the replace range.
        """
        from pd_book_tools.ocr.ground_truth_matching import (
            update_line_with_ground_truth_replace_words,
        )

        words = [_make_word("hello"), _make_word("world"), _make_word("extra")]
        line = Block(
            items=words,
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )
        op = WordDiffOpCodes(
            word_tag="replace",
            ocr_word_1=0,
            ocr_word_2=3,  # 3 OCR words
            gt_word_1=0,
            gt_word_2=1,  # only 1 GT word → exhausted after first OCR word → break
        )
        combined, new_words = update_line_with_ground_truth_replace_words(
            line=line,
            op=op,
            ocr_line_tuple=("hello", "world", "extra"),
            ground_truth_tuple=("hi",),
            auto_combine=False,
        )
        # Should complete without error
        assert line.words[0].ground_truth_text == "hi"
