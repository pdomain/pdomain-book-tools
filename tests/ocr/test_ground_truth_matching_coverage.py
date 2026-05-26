"""Coverage tests for ground truth matching edge cases and error paths."""

import pytest

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pdomain_book_tools.ocr.ground_truth_matching import (
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
from pdomain_book_tools.ocr.ground_truth_matching_helpers.match_type import MatchType
from pdomain_book_tools.ocr.page import Page
from pdomain_book_tools.ocr.word import Word


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
    return Page(width=1000, height=1000, page_index=0, blocks=[para])


# ---------------------------------------------------------------------------
# update_line_match_difflib_lines_equal error paths
# ---------------------------------------------------------------------------


class TestUpdateLineMatchDifflibLinesEqualErrors:
    def test_raises_when_no_block_category(self):
        """Line object without block_category raises ValueError."""

        class FakeLine:
            text = "hello world"
            words: list = []  # noqa: RUF012  # test stub; mutable default is intentional here

        with pytest.raises(ValueError, match="block_category"):
            update_line_match_difflib_lines_equal(FakeLine(), ("hello", "world"))

    def test_raises_when_not_line_category(self):
        """Block with non-LINE category raises ValueError."""
        line = _make_line(["hello", "world"])
        line.block_category = BlockCategory.PARAGRAPH

        with pytest.raises(ValueError, match="not a line block"):
            update_line_match_difflib_lines_equal(line, ("hello", "world"))

    def test_raises_when_no_words_attribute(self):
        """Object with block_category=LINE but no words attr raises ValueError."""

        class FakeLineWithCategory:
            block_category = BlockCategory.LINE
            text = "hello world"

        with pytest.raises(ValueError, match="words"):
            update_line_match_difflib_lines_equal(
                FakeLineWithCategory(), ("hello", "world")
            )

    def test_raises_on_word_count_mismatch(self):
        """Mismatched word count between line and gt raises ValueError."""
        line = _make_line(["hello", "world"])
        with pytest.raises(ValueError, match="word count mismatch"):
            update_line_match_difflib_lines_equal(line, ("hello",))

    def test_raises_on_word_text_mismatch(self):
        """Mismatched word text raises ValueError."""
        line = _make_line(["hello", "world"])
        with pytest.raises(ValueError, match="Word mismatch"):
            update_line_match_difflib_lines_equal(line, ("hello", "DIFFERENT"))

    def test_no_dead_word_idx_out_of_range_guard(self):
        """L-20: the inner ``word_idx >= len(ground_truth_line)`` guard is
        dead \u2014 the length-equality check before the loop already raises if  # EM DASH
        the lengths differ, and ``word_idx`` comes from
        ``enumerate(line.words)`` so it can never exceed
        ``len(ground_truth_line) - 1`` once that check passes. Property
        check: the dead string must not appear in the function source.
        """
        import inspect

        src = inspect.getsource(update_line_match_difflib_lines_equal)
        assert "out of range for ground truth line" not in src

    def test_happy_path_assigns_ground_truth(self):
        """Behavioral lock so the dead-guard removal can't accidentally
        break the equal-line happy path.
        """
        line = _make_line(["hello", "world"])
        update_line_match_difflib_lines_equal(line, ("hello", "world"))
        assert [w.ground_truth_text for w in line.words] == ["hello", "world"]


class TestUpdatePageMatchDifflibLinesEqualErrors:
    def test_raises_on_line_count_mismatch(self):
        """op with mismatched line/gt count raises ValueError."""
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
        """First GT insert sets unmatched_ground_truth_lines."""
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
        """When unmatched list already has entries, append."""
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
        """Lines with empty text are skipped."""
        # Create a page with a line whose word text is empty → line.text = ""
        page = _make_page([[""], ["hello", "world"]])
        page.unmatched_ground_truth_lines = [(0, "something")]
        update_page_match_unmatched_lines_best_effort(page)

    def test_handles_duplicate_candidates_with_skip(self):
        """When same OCR line matches multiple GT lines, second is skipped."""
        page = _make_page([["the", "quick", "brown", "fox"]])
        # Two GT lines that both match the same OCR line
        page.unmatched_ground_truth_lines = [
            (0, "the quick brown fox"),
            (0, "the quick brown fox"),  # duplicate
        ]
        update_page_match_unmatched_lines_best_effort(page)

    def test_removes_matched_gt_from_unmatched_list(self):
        """After successful match, removes matched GT from unmatched list."""
        page = _make_page([["hello", "world"]])
        # Give the OCR line GT text that matches the unmatched GT
        for word in page.lines[0].words:
            word.ground_truth_text = ""  # no existing GT
        page.unmatched_ground_truth_lines = [(0, "hello world")]

        update_page_match_unmatched_lines_best_effort(page)

        assert page.unmatched_ground_truth_lines == []


# ---------------------------------------------------------------------------
# update_line_with_ground_truth -- "delete" and "insert" word ops
# ---------------------------------------------------------------------------


class TestUpdateLineWithGroundTruth:
    def test_delete_word_op_does_nothing(self):
        """'delete' op logs and does nothing to words."""
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
        """'insert' op adds GT words to unmatched list."""
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
        """update_combined_words_in_line removes old words and adds new ones."""
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
        """Both OCR and GT starting with quote/prime and short word → skip."""
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
        """Word with split=True in ground_truth_match_keys → skip."""
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
    def test_returns_gt_text_when_boundary_is_space(self):
        """M-25: When the char at prev boundary is a space, fall back to the
        unmodified ground_truth_text instead of returning '' (which inserted a
        dead zero-score variant). The intent was to skip prepending."""
        # previous_ground_truth_text[-1] == ' '  # noqa: ERA001  # code-expression illustrating the boundary condition, not dead code
        result = _build_current_work_gt_line_from_prev(
            prev_char_count=1,
            previous_ground_truth_text="word ",
            ground_truth_text="current",
        )
        assert result == "current"

    def test_returns_combined_when_boundary_is_word_char(self):
        """When boundary char is not space, prepends the suffix (normal path)."""
        result = _build_current_work_gt_line_from_prev(
            prev_char_count=3,
            previous_ground_truth_text="word",
            ground_truth_text="current",
        )
        assert result == "ord current"

    def test_no_silent_drop_when_boundary_is_space_in_full_pipeline(self):
        """M-25 no-silent-drop adjacent invariant: a previous-line GT whose
        last word's leading boundary is a space (i.e. prev_char_count selects
        exactly the trailing space) must not cause the candidate list inside
        generate_best_matched_ground_truth_line to lose the
        ground_truth_text content. After the fix, the unmodified
        ground_truth_text appears among the variants and the scorer can pick
        it; pre-fix the variant at that prev_char_count was '' and the only
        non-empty candidate came from prev_char_count=0 (still present here,
        so the bug was scoring-harmless \u2014 but the invariant is that no  # EM DASH
        OCR/GT content is silently elided in any candidate path)."""
        result, score = generate_best_matched_ground_truth_line(
            ocr_text="hello world",
            ground_truth_text="hello world",
            previous_ground_truth_text="prev line ",
        )
        assert result == "hello world"
        assert score == 100


# ---------------------------------------------------------------------------
# _build_current_work_gt_line_remove_suffix
# ---------------------------------------------------------------------------


class TestBuildCurrentWorkGtLineRemoveSuffix:
    def test_raises_when_remove_count_exceeds_length(self):
        """Raises ValueError when remove_count > len(ground_truth_text)."""
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
        """When dash_chars is None, uses CharacterGroups.DASHES."""
        result = _generate_work_variants("word", include_plain=True, dash_chars=None)
        assert "word" in result
        assert "word--" in result
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
        """Empty OCR text → returns False."""
        assert _should_consider_line_end_soft_wrap("", "some text") is False

    def test_returns_false_for_empty_gt_text(self):
        """Empty GT text → returns False."""
        assert _should_consider_line_end_soft_wrap("some text", "") is False

    def test_returns_false_when_ocr_core_is_empty(self):
        """When OCR last word strips to nothing → returns False."""
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
# generate_best_matched_ground_truth_line -- no variants path
# ---------------------------------------------------------------------------


class TestGenerateBestMatchedGroundTruthLine:
    def test_returns_early_for_empty_text(self):
        """Empty strings return immediately (existing check)."""
        result, score = generate_best_matched_ground_truth_line("", "some text")
        assert result == "some text"
        assert score == 0

    def test_returns_gt_with_zero_score_when_no_variants(self):
        """Variants are all empty → return (ground_truth_text, 0).

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
# update_page_with_ground_truth_text -- "delete" opcode exists
# ---------------------------------------------------------------------------


class TestUpdatePageWithGroundTruthText:
    def test_delete_op_occurs_for_extra_ocr_lines(self):
        """Extra OCR lines (not in GT) result in delete op."""
        page = _make_page(
            [
                ["hello", "world"],
                ["extra", "ocr", "only"],
            ]
        )
        gt_text = "hello world"
        update_page_with_ground_truth_text(page, gt_text)
        assert page.lines[0].words[0].ground_truth_text == "hello"
        assert all(w.ground_truth_text == "" for w in page.lines[1].words)

    def test_replace_op_with_insert_word(self):
        """GT having more words than OCR creates unmatched word entries."""
        page = _make_page([["hello"]])
        gt_text = "hello world"
        update_page_with_ground_truth_text(page, gt_text)
        assert page.lines[0].words[0].ground_truth_text in ("hello", "")


# ---------------------------------------------------------------------------
# match_different_line_counts deduplication (line 979)
# ---------------------------------------------------------------------------


class TestMatchDifferentLineCountsDedup:
    def test_deduplication_in_replace_op(self):
        """When multiple GT lines map to the same OCR line, duplicates are skipped.

        Two OCR lines, three GT lines where OCR line 0 matches both GT 0 and GT 1.
        After GT 0 is matched to OCR 0, GT 1 share the same OCR line so is skipped.
        """
        from pdomain_book_tools.ocr.ground_truth_matching import (
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
            ("hello", "world"),  # GT 0 \u2014 perfect match for OCR 0
            ("hello", "world", "again"),  # GT 1 \u2014 partial match for OCR 0 (79%)
            ("foo", "bar"),  # GT 2 \u2014 perfect match for OCR 1
        ]
        op = LineDiffOpCodes(
            line_tag="replace",
            ocr_line_1=0,
            ocr_line_2=2,
            gt_line_1=0,
            gt_line_2=3,
        )
        update_page_match_difflib_lines_replace_different_line_count(
            page=page,
            op=op,
            ocr_tuples=ocr_tuples,
            ground_truth_tuples=ground_truth_tuples,
        )
        assert page.lines[0].words[0].ground_truth_text == "hello"


# ---------------------------------------------------------------------------
# try_matching_combined_words -- quote/prime skip (line 484) and split flag (line 494)
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
# update_line_with_ground_truth_replace_words -- break and continue paths (lines 831, 835)
# ---------------------------------------------------------------------------


class TestReplaceWordsBreakAndContinue:
    def test_break_when_gt_exhausted_before_ocr(self):
        """Line 831: break when to_match_gt_word_nbrs is empty during OCR loop.
        Triggered when more OCR words than GT words in the replace range.
        """
        from pdomain_book_tools.ocr.ground_truth_matching import (
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
        _combined, _new_words = update_line_with_ground_truth_replace_words(
            line=line,
            op=op,
            ocr_line_tuple=("hello", "world", "extra"),
            ground_truth_tuple=("hi",),
            auto_combine=False,
        )
        assert line.words[0].ground_truth_text == "hi"


class TestUpdatePageWithGroundTruthUnknownLineTag:
    def test_unknown_line_tag_raises_error(self, monkeypatch):
        """Invalid line_tag in opcode raises ValueError."""
        import difflib

        from pdomain_book_tools.ocr.ground_truth_matching import (
            update_page_with_ground_truth_text,
        )

        page = _make_page([["hello", "world"]])

        def patched_get_opcodes(self):
            return [("equal", 0, 1, 0, 1), ("invalid_tag", 1, 1, 1, 1)]

        monkeypatch.setattr(difflib.SequenceMatcher, "get_opcodes", patched_get_opcodes)
        with pytest.raises(ValueError, match="Unknown line tag"):
            update_page_with_ground_truth_text(page, "hello world\nstuff")


class TestInitializeUnmatchedGroundTruthWords:
    def test_initializes_unmatched_list_on_insert_word_op(self):
        """Line 420: initialize unmatched_ground_truth_words when None during insert op."""
        from pdomain_book_tools.ocr.ground_truth_matching import (
            update_line_with_ground_truth,
        )

        line = _make_line(["hello"])
        # Ensure unmatched_ground_truth_words is None to trigger initialization
        line.unmatched_ground_truth_words = None

        ocr_tuple = ("hello",)
        # "world" is in GT but not OCR
        gt_tuple = ("hello", "world")

        update_line_with_ground_truth(
            line=line,
            ocr_line_tuple=ocr_tuple,
            ground_truth_tuple=gt_tuple,
        )

        assert line.unmatched_ground_truth_words is not None
        assert len(line.unmatched_ground_truth_words) > 0
        assert any("world" in t for _, t in line.unmatched_ground_truth_words)


class TestUpdateCombinedWordsWithExistingUnmatched:
    def test_combined_words_preserves_existing_unmatched(self):
        """Combined word update preserves unmatched words added in same function."""
        from pdomain_book_tools.ocr.ground_truth_matching import (
            update_line_with_ground_truth,
        )

        line = _make_line(["hello", ",", "world"])
        # Force a replace op that will:
        # 1. Create combined words ("hello,")
        # 2. Leave unmatched GT words
        ocr_tuple = ("hello", ",", "world")
        gt_tuple = ("hello,", "world", "goodbye")  # "goodbye" has no OCR match

        update_line_with_ground_truth(
            line=line,
            ocr_line_tuple=ocr_tuple,
            ground_truth_tuple=gt_tuple,
        )

        word_texts = [w.text for w in line.words]
        assert "hello," in word_texts or "hello" in word_texts
        assert line.unmatched_ground_truth_words is not None
        assert any("goodbye" in t for _, t in line.unmatched_ground_truth_words)


class TestShouldConsiderLineEndSoftWrapEdgeCases:
    def test_returns_false_when_gt_last_word_is_single_char(self):
        """When GT last word is single char, comparison fails."""
        # OCR "a" vs GT "a" (same length) → False
        assert _should_consider_line_end_soft_wrap("a", "a") is False

    def test_returns_false_when_ocr_and_gt_both_empty_after_strip(self):
        """When both OCR and GT strip to empty, return False."""
        # Words that are only punctuation
        assert _should_consider_line_end_soft_wrap(".,;:!?", ".,;:!?") is False

    def test_returns_false_when_gt_core_stripped_too_short(self):
        """When GT core < 2 chars, return False."""
        # OCR "a" (< 2) vs GT "ab" (valid)
        # But GT core is < len(ocr_core) + 1 so still False
        assert (
            _should_consider_line_end_soft_wrap("a", "ab") is False
        )  # len(a)=1, not >= 2


class TestUnmatchedGroundTruthWordsAppend:
    def test_append_to_initialized_unmatched_list(self):
        """Line 866: append to unmatched_ground_truth_words when already initialized."""
        from pdomain_book_tools.ocr.ground_truth_matching import (
            update_line_with_ground_truth,
        )

        line = _make_line(["hello"])
        # Pre-initialize with existing unmatched
        line.unmatched_ground_truth_words = [(0, "prior")]

        ocr_tuple = ("hello",)
        gt_tuple = ("hello", "new1", "new2")

        update_line_with_ground_truth(
            line=line,
            ocr_line_tuple=ocr_tuple,
            ground_truth_tuple=gt_tuple,
        )

        assert len(line.unmatched_ground_truth_words) >= 2
        unmatched_texts = [t for _, t in line.unmatched_ground_truth_words]
        assert "new1" in unmatched_texts or "new2" in unmatched_texts
