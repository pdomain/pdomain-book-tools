"""Tests for ground truth matching functionality."""

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.ground_truth_matching import (
    WordDiffOpCodes,
    try_matching_combined_words,
    update_line_with_ground_truth_replace_words,
    update_page_with_ground_truth_text,
)
from pd_book_tools.ocr.ground_truth_matching_helpers.character_groups import (
    CharacterGroups,
)
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.word import Word


def _make_line(text_words, y):
    """Build a simple Block(LINE) at y-row from a sequence of word strings."""
    words = []
    x = 0
    for w in text_words:
        width = max(8, len(w) * 8)
        words.append(
            Word(
                text=w,
                bounding_box=BoundingBox.from_ltrb(
                    x, y, x + width, y + 18, is_normalized=False
                ),
            )
        )
        x += width + 4
    return Block(
        items=words,
        block_category=BlockCategory.LINE,
        child_type=BlockChildType.WORDS,
    )


def _make_page(lines_of_words):
    """Build a Page from an ordered list of word-string lists, one per line."""
    line_blocks = [
        _make_line(words, y=20 + i * 30) for i, words in enumerate(lines_of_words)
    ]
    return Page(width=1000, height=1000, page_index=0, items=line_blocks)


class TestGroundTruthMatching:
    """Test ground truth matching functions."""

    def test_update_line_with_ground_truth_replace_words_preserves_existing_unmatched(
        self,
    ):
        """Test that replace words operation preserves existing unmatched ground truth words."""
        # Create a line with some OCR words
        words = [
            Word(
                text="hello",
                bounding_box=BoundingBox.from_ltrb(0, 0, 50, 20, is_normalized=False),
            ),
            Word(
                text="world",
                bounding_box=BoundingBox.from_ltrb(60, 0, 110, 20, is_normalized=False),
            ),
        ]

        line = Block(
            items=words,
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )

        # Pre-populate the line with some unmatched ground truth words
        # (as would happen from previous "insert" operations)
        line.unmatched_ground_truth_words = [
            (0, "previous"),
            (1, "unmatched"),
        ]

        # Create a replace operation
        op = WordDiffOpCodes(
            word_tag="replace",
            ocr_word_1=0,
            ocr_word_2=2,
            gt_word_1=0,
            gt_word_2=3,  # More GT words than OCR words
        )

        ocr_line_tuple = ("hello", "world")
        ground_truth_tuple = ("hi", "there", "extra")

        # Call the function
        combined_ocr_word_nbrs, new_combined_words = (
            update_line_with_ground_truth_replace_words(
                line=line,
                op=op,
                ocr_line_tuple=ocr_line_tuple,
                ground_truth_tuple=ground_truth_tuple,
                auto_combine=False,  # Disable auto combine for predictable behavior
            )
        )

        # The function should preserve existing unmatched words
        # and add new unmatched words from the current operation
        assert line.unmatched_ground_truth_words is not None

        # Should contain the original unmatched words plus the new one
        unmatched_texts = [word[1] for word in line.unmatched_ground_truth_words]
        assert "previous" in unmatched_texts
        assert "unmatched" in unmatched_texts
        assert "extra" in unmatched_texts

        # Should have 3 total unmatched words
        assert len(line.unmatched_ground_truth_words) == 3

    def test_update_line_with_ground_truth_multiple_replace_operations(self):
        """Test that multiple replace operations preserve all unmatched ground truth words."""
        # Create a line with OCR words
        words = [
            Word(
                text="hello",
                bounding_box=BoundingBox.from_ltrb(0, 0, 50, 20, is_normalized=False),
            ),
        ]

        line = Block(
            items=words,
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )

        # First, simulate an insert operation that adds unmatched words
        line.unmatched_ground_truth_words = [(0, "inserted_word")]

        # Then call a replace operation that should preserve the existing unmatched words
        op = WordDiffOpCodes(
            word_tag="replace",
            ocr_word_1=0,
            ocr_word_2=1,
            gt_word_1=0,
            gt_word_2=2,  # More GT words than OCR words
        )

        ocr_line_tuple = ("hello",)
        ground_truth_tuple = ("hi", "extra_from_replace")

        # Call the function - this should preserve the inserted_word and add extra_from_replace
        combined_ocr_word_nbrs, new_combined_words = (
            update_line_with_ground_truth_replace_words(
                line=line,
                op=op,
                ocr_line_tuple=ocr_line_tuple,
                ground_truth_tuple=ground_truth_tuple,
                auto_combine=False,
            )
        )

        # Should have both the original and new unmatched words
        assert line.unmatched_ground_truth_words is not None
        unmatched_texts = [word[1] for word in line.unmatched_ground_truth_words]

        # Should contain both the original inserted word and the new extra word
        assert "inserted_word" in unmatched_texts, (
            "Original unmatched word should be preserved"
        )
        assert "extra_from_replace" in unmatched_texts, (
            "New unmatched word should be added"
        )
        assert len(line.unmatched_ground_truth_words) == 2, (
            "Should have exactly 2 unmatched words"
        )

    def test_update_line_with_ground_truth_replace_words_empty_initial_list(self):
        """Test that function works correctly when starting with empty unmatched list."""
        words = [
            Word(
                text="hello",
                bounding_box=BoundingBox.from_ltrb(0, 0, 50, 20, is_normalized=False),
            ),
        ]

        line = Block(
            items=words,
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )

        # Start with empty list (this is the normal case)
        line.unmatched_ground_truth_words = []

        op = WordDiffOpCodes(
            word_tag="replace",
            ocr_word_1=0,
            ocr_word_2=1,
            gt_word_1=0,
            gt_word_2=2,  # More GT words than OCR words
        )

        ocr_line_tuple = ("hello",)
        ground_truth_tuple = ("hi", "extra")

        combined_ocr_word_nbrs, new_combined_words = (
            update_line_with_ground_truth_replace_words(
                line=line,
                op=op,
                ocr_line_tuple=ocr_line_tuple,
                ground_truth_tuple=ground_truth_tuple,
                auto_combine=False,
            )
        )

        # Should have one unmatched word
        assert line.unmatched_ground_truth_words is not None
        assert len(line.unmatched_ground_truth_words) == 1
        assert line.unmatched_ground_truth_words[0][1] == "extra"

    def test_no_combined_words_found_with_misspelled_ocr(self):
        """Test that no combined words are found when OCR has misspellings that don't combine well."""
        # Create OCR words with misspellings: ['tbe', 'Jounding','of','tbe', 'Gopernment']
        words = [
            Word(
                text="tbe",
                bounding_box=BoundingBox.from_ltrb(0, 0, 30, 20, is_normalized=False),
            ),
            Word(
                text="Jounding",
                bounding_box=BoundingBox.from_ltrb(35, 0, 100, 20, is_normalized=False),
            ),
            Word(
                text="of",
                bounding_box=BoundingBox.from_ltrb(
                    105, 0, 125, 20, is_normalized=False
                ),
            ),
            Word(
                text="tbe",
                bounding_box=BoundingBox.from_ltrb(
                    130, 0, 160, 20, is_normalized=False
                ),
            ),
            Word(
                text="Gopernment",
                bounding_box=BoundingBox.from_ltrb(
                    165, 0, 245, 20, is_normalized=False
                ),
            ),
        ]

        line = Block(
            items=words,
            block_category=BlockCategory.LINE,
            child_type=BlockChildType.WORDS,
        )

        # Ground truth: 'The Founding of the Government'
        ocr_line_tuple = ("tbe", "Jounding", "of", "tbe", "Gopernment")
        ground_truth_tuple = ("The", "Founding", "of", "the", "Government")

        # Call the function to update the line with ground truth
        from pd_book_tools.ocr.ground_truth_matching import (
            update_line_with_ground_truth,
        )

        update_line_with_ground_truth(
            line=line,
            ocr_line_tuple=ocr_line_tuple,
            ground_truth_tuple=ground_truth_tuple,
            auto_combine=True,  # Enable auto combine to test that no combinations are found
        )

        # Verify no words were combined (all words should still exist as separate entities)
        assert len(line.words) == 5, "Should still have 5 separate words"

        # Check that each word has ground truth text assigned (from the replace operations)
        expected_gt_texts = ["The", "Founding", "of", "the", "Government"]
        for i, word in enumerate(line.words):
            assert word.ground_truth_text == expected_gt_texts[i], (
                f"Word {i} should have ground truth '{expected_gt_texts[i]}', "
                f"but got '{word.ground_truth_text}'"
            )

        # Verify that no words have been marked as combined
        for word in line.words:
            # Check that no word has been marked as the result of a combination
            assert (
                word.ground_truth_match_keys.get("match_type")
                != "difflib-line-replace-word-replace-combined"
            ), f"Word '{word.text}' should not be marked as combined"

    def test_try_matching_combined_words_individual_scores_higher(self):
        """Test case where individual word matches better than combined."""

        # Helper to create a Word object for testing
        def create_test_word(text, x=0, y=0, width=10, height=10):
            top_left = Point(x=x, y=y)
            bottom_right = Point(x=x + width, y=y + height)
            bbox = BoundingBox(top_left=top_left, bottom_right=bottom_right)
            return Word(text=text, bounding_box=bbox, ocr_confidence=0.9)

        # Create OCR words: "hello" and "world"
        ocr_words = [create_test_word("hello", 0, 0), create_test_word("world", 20, 0)]

        # OCR tuple matches the words
        ocr_tuple = ("hello", "world")

        # Ground truth has perfect matches for individual words
        gt_tuple = ("hello", "world")

        # Call the function
        result = try_matching_combined_words(ocr_words, ocr_tuple, gt_tuple)

        # Should return empty list since individual words score 100% each
        # and combining them would score lower
        assert len(result) == 0, (
            "Should not combine when individual words score perfectly"
        )

    def test_try_matching_combined_words_combination_scores_higher(self):
        """Test case where combination matches better than individuals."""

        # Helper to create a Word object for testing
        def create_test_word(text, x=0, y=0, width=10, height=10):
            top_left = Point(x=x, y=y)
            bottom_right = Point(x=x + width, y=y + height)
            bbox = BoundingBox(top_left=top_left, bottom_right=bottom_right)
            return Word(text=text, bounding_box=bbox, ocr_confidence=0.9)

        # Create OCR words that when combined match GT better
        ocr_words = [create_test_word("hel", 0, 0), create_test_word("lo", 15, 0)]

        ocr_tuple = ("hel", "lo")

        # Ground truth has a single word that matches the combination
        gt_tuple = ("hello",)

        result = try_matching_combined_words(ocr_words, ocr_tuple, gt_tuple)

        # Should combine since "hel" + "lo" = "hello" matches GT better than individual words
        assert len(result) > 0, "Should combine when combination scores higher"
        if result:
            combined_word = result[0][3]  # The combined Word object
            assert combined_word.text == "hello", (
                f"Expected combined text 'hello', got '{combined_word.text}'"
            )
            assert combined_word.ground_truth_text == "hello", (
                f"Expected GT text 'hello', got '{combined_word.ground_truth_text}'"
            )


class TestCharacterGroups:
    """Test the CharacterGroups enum functionality."""

    def test_character_groups_hyphen_contains(self):
        """Test that hyphen group contains expected characters."""
        assert "-" in CharacterGroups.HYPHEN
        assert "a" not in CharacterGroups.HYPHEN

    def test_character_groups_endash_contains(self):
        """Test that en-dash group contains expected characters."""
        assert "–" in CharacterGroups.ENDASH
        assert "-" not in CharacterGroups.ENDASH

    def test_character_groups_emdash_contains(self):
        """Test that em-dash group contains expected characters."""
        assert "—" in CharacterGroups.EMDASH
        assert "-" not in CharacterGroups.EMDASH

    def test_character_groups_all_dashes(self):
        """Test that DASHES contains all dash types."""
        assert "-" in CharacterGroups.DASHES  # hyphen
        assert "–" in CharacterGroups.DASHES  # en-dash
        assert "—" in CharacterGroups.DASHES  # em-dash
        assert "‒" in CharacterGroups.DASHES  # figure dash
        assert "⸺" in CharacterGroups.DASHES  # two-em dash
        assert "⸻" in CharacterGroups.DASHES  # three-em dash
        assert "―" in CharacterGroups.DASHES  # horizontal bar
        assert "‑" in CharacterGroups.DASHES  # non-break hyphen
        assert "−" in CharacterGroups.DASHES  # minus
        assert "a" not in CharacterGroups.DASHES

    def test_character_groups_single_quote_contains(self):
        """Test that single quote group contains expected characters."""
        assert "'" in CharacterGroups.SINGLE_QUOTE
        assert "'" in CharacterGroups.SINGLE_QUOTE
        assert "'" in CharacterGroups.SINGLE_QUOTE
        assert '"' not in CharacterGroups.SINGLE_QUOTE

    def test_character_groups_double_quote_contains(self):
        """Test that double quote group contains expected characters."""
        assert '"' in CharacterGroups.DOUBLE_QUOTE
        assert '"' in CharacterGroups.DOUBLE_QUOTE  # left double quote
        assert '"' in CharacterGroups.DOUBLE_QUOTE  # right double quote
        assert "'" not in CharacterGroups.DOUBLE_QUOTE

    def test_character_groups_quotes_contains_both(self):
        """Test that QUOTES contains both single and double quotes."""
        assert "'" in CharacterGroups.QUOTES
        assert "'" in CharacterGroups.QUOTES
        assert '"' in CharacterGroups.QUOTES
        assert '"' in CharacterGroups.QUOTES  # left double quote
        assert '"' in CharacterGroups.QUOTES  # right double quote
        assert "a" not in CharacterGroups.QUOTES

    def test_character_groups_primes_contains(self):
        """Test that primes group contains expected characters."""
        assert "′" in CharacterGroups.SINGLE_PRIME
        assert "″" in CharacterGroups.DOUBLE_PRIME
        assert "′" in CharacterGroups.PRIMES
        assert "″" in CharacterGroups.PRIMES
        assert "a" not in CharacterGroups.PRIMES

    def test_character_groups_quotes_and_primes(self):
        """Test that QUOTES_AND_PRIMES contains all quote and prime characters."""
        assert "'" in CharacterGroups.QUOTES_AND_PRIMES
        assert "'" in CharacterGroups.QUOTES_AND_PRIMES
        assert '"' in CharacterGroups.QUOTES_AND_PRIMES
        assert '"' in CharacterGroups.QUOTES_AND_PRIMES  # left double quote
        assert "′" in CharacterGroups.QUOTES_AND_PRIMES
        assert "″" in CharacterGroups.QUOTES_AND_PRIMES
        assert "a" not in CharacterGroups.QUOTES_AND_PRIMES


class TestUpdatePageWithGroundTruthText:
    """Page-level tests for update_page_with_ground_truth_text.

    These exercise the difflib line-level matching logic, including the
    similarity-based fallback used when same-line-count `replace` blocks
    are positionally misaligned (e.g. an image caption placed at a
    different position in OCR vs ground truth).
    """

    def _gt_lines(self, page):
        return [(line.text, line.base_ground_truth_text or "") for line in page.lines]

    def test_paragraph_rearranged_around_caption_matches_correctly(self):
        """Regression test: caption between paragraph halves in OCR but
        moved past the paragraph in GT must NOT positionally match the
        caption line to a paragraph line just because line counts agree.
        """
        ocr_lines = [
            [
                "money",
                "in",
                "particular",
                "had",
                "fallen",
                "so",
                "in",
                "value",
                "that",
                "the",
                "com-",
            ],
            ["GENERAL", "GEORCE", "WASBISGTONS", "COACH", "AND", "FOUR"],
            [
                "modity",
                "must",
                "have",
                "been",
                "valueless",
                "indeed",
                "which",
                "fell",
                "un-",
            ],
            [
                "der",
                "the",
                "reproach",
                "of",
                "being",
                "not",
                "worth",
                "a",
                "continental.",
            ],
        ]
        gt_text = "\n".join(
            [
                "money in particular had fallen so in value that the commodity",
                "must have been valueless indeed which fell under",
                "the reproach of being not worth a continental.",
                "",
                "GENERAL GEORGE WASHINGTON'S COACH AND FOUR",
            ]
        )

        page = _make_page(ocr_lines)
        update_page_with_ground_truth_text(page, gt_text)

        line_texts = [line.text for line in page.lines]
        gts = [line.base_ground_truth_text or "" for line in page.lines]

        # The caption OCR line must NOT be paired with the paragraph GT line.
        caption_idx = line_texts.index("GENERAL GEORCE WASBISGTONS COACH AND FOUR")
        assert "valueless" not in gts[caption_idx], (
            f"Caption line was incorrectly matched to paragraph GT: "
            f"{gts[caption_idx]!r}"
        )

        # The OCR caption line should match the GT caption line.
        assert "GEORGE" in gts[caption_idx] and "WASHINGTON" in gts[caption_idx]

        # The paragraph lines should be matched to their paragraph GT lines.
        # (The first paragraph line ends with "com-" in OCR, so the matcher
        # may store the dash-wrapped variant of the GT line as the base GT.)
        para_first_idx = 0
        assert "money" in gts[para_first_idx] and "particular" in gts[para_first_idx]
        assert "GEORGE" not in gts[para_first_idx]

        para_third_idx = 2
        assert "valueless" in gts[para_third_idx] or "fell" in gts[para_third_idx]
        assert "GEORGE" not in gts[para_third_idx]

    def test_same_count_replace_with_rearranged_lines_uses_similarity(self):
        """Two lines with OCR errors that are reordered between OCR and GT
        produce a same-count `replace` opcode. The similarity-based fallback
        should still pair them correctly rather than positionally."""
        # Both lines have OCR errors so SequenceMatcher can't find any tuple
        # equality and emits a single same-count `replace` block.
        ocr_lines = [
            ["Tbe", "quiek", "browm", "fox"],
            ["jumps", "ovcr", "tbe", "lazv", "dog"],
        ]
        gt_text = "\n".join(
            [
                "jumps over the lazy dog",
                "The quick brown fox",
            ]
        )

        page = _make_page(ocr_lines)
        update_page_with_ground_truth_text(page, gt_text)

        gts = [line.base_ground_truth_text or "" for line in page.lines]
        # OCR line 0 ("Tbe quiek browm fox") should match the "The quick..."
        # GT line, NOT the "jumps over..." GT line.
        assert "quick" in gts[0] and "fox" in gts[0]
        assert "jumps" not in gts[0]
        # OCR line 1 ("jumps ovcr tbe lazv dog") should match the "jumps..." GT.
        assert "jumps" in gts[1] and "dog" in gts[1]
        assert "fox" not in gts[1]

    def test_aligned_lines_still_match_positionally(self):
        """Sanity check: when OCR and GT lines align, matching is unchanged
        and each line gets its corresponding GT text."""
        ocr_lines = [
            ["The", "quick", "brown", "fox"],
            ["jumps", "over", "the", "lazy", "dog"],
            ["and", "runs", "away"],
        ]
        gt_text = "\n".join(
            [
                "The quick brown fox",
                "jumps over the lazy dog",
                "and runs away",
            ]
        )

        page = _make_page(ocr_lines)
        update_page_with_ground_truth_text(page, gt_text)

        # All lines should match exactly via the LINE_EQUAL path.
        for line, expected in zip(
            page.lines,
            ["The quick brown fox", "jumps over the lazy dog", "and runs away"],
        ):
            for word in line.words:
                assert word.ground_truth_text is not None
            joined_gt = " ".join((w.ground_truth_text or "") for w in line.words)
            assert joined_gt == expected

    def test_aligned_lines_with_minor_ocr_errors_match_positionally(self):
        """Same-count replace block with minor per-line errors should still
        use positional pairing (no fallback), since each pair scores high."""
        ocr_lines = [
            ["The", "quiek", "brown", "fox"],  # 'quiek' typo
            ["jumps", "over", "tbe", "lazy", "dog"],  # 'tbe' typo
            ["and", "runs", "awayy"],  # extra letter
        ]
        gt_text = "\n".join(
            [
                "The quick brown fox",
                "jumps over the lazy dog",
                "and runs away",
            ]
        )

        page = _make_page(ocr_lines)
        update_page_with_ground_truth_text(page, gt_text)

        gts = [line.base_ground_truth_text or "" for line in page.lines]
        assert "quick" in gts[0] and "fox" in gts[0]
        assert "the" in gts[1] and "dog" in gts[1]
        assert "away" in gts[2]

    def test_unmatched_gt_lines_recorded(self):
        """GT lines with no matching OCR line should be added to
        page.unmatched_ground_truth_lines."""
        ocr_lines = [
            ["First", "line", "of", "text"],
            ["Last", "line", "of", "text"],
        ]
        gt_text = "\n".join(
            [
                "First line of text",
                "An entirely different middle line that has no OCR equivalent",
                "Last line of text",
            ]
        )

        page = _make_page(ocr_lines)
        update_page_with_ground_truth_text(page, gt_text)

        unmatched = page.unmatched_ground_truth_lines or []
        unmatched_texts = [t for _, t in unmatched]
        assert any("entirely different middle line" in t for t in unmatched_texts)

    def test_header_and_page_number_ignored_but_inline_name_lines_match(self):
        """Regression: non-GT header/page number OCR lines should not block
        matching for intervening content lines like 'ROBERT'/'MORRIS'.
        """
        ocr_lines = [
            ["BETWEEN", "WAR", "AND", "PEACE"],
            [
                "de",
                "Rochambeau,",
                "upon",
                "his",
                "personal",
                "credit,",
                "to",
                "do",
                "it.",
            ],
            [
                "But",
                "even",
                "Morris,",
                "trained",
                "merchant",
                "and",
                "financier",
                "that",
            ],
            ["ROBERT"],
            ["MORRIS"],
            [
                "he",
                "was,",
                "could",
                "not",
                "make",
                "something",
                "out",
                "of",
                "nothing.",
                "The",
            ],
            [
                "States",
                "would",
                "not",
                "tax",
                "their",
                "people",
                "for",
                "the",
                "support",
                "of",
            ],
            [
                "the",
                "Confederation.",
                "It",
                "took",
                "eighteen",
                "months",
                "to",
                "collect",
            ],
            [
                "one-fifth",
                "of",
                "the",
                "taxes",
                "assigned",
                "them",
                "in",
                "1783.",
                "They",
            ],
            ["31"],
        ]

        gt_text = "\n".join(
            [
                "de Rochambeau, upon his personal credit, to do it.",
                "But even Morris, trained merchant and financier that",
                "he was, could not make something out of nothing. The",
                "States would not tax their people for the support of",
                "the Confederation. It took eighteen months to collect",
                "one-fifth of the taxes assigned them in 1783. They",
                "ROBERT",
                "MORRIS",
            ]
        )

        page = _make_page(ocr_lines)
        update_page_with_ground_truth_text(page, gt_text)

        # Header and page number are OCR-only; they should remain unmatched.
        header_line = page.lines[0]
        page_number_line = page.lines[-1]
        assert header_line.text == "BETWEEN WAR AND PEACE"
        assert all((w.ground_truth_text or "") == "" for w in header_line.words)
        assert page_number_line.text == "31"
        assert all((w.ground_truth_text or "") == "" for w in page_number_line.words)

        # Inline inserted name lines must still match their GT lines.
        robert_line = page.lines[3]
        morris_line = page.lines[4]
        assert robert_line.text == "ROBERT"
        assert morris_line.text == "MORRIS"
        assert [w.ground_truth_text for w in robert_line.words] == ["ROBERT"]
        assert [w.ground_truth_text for w in morris_line.words] == ["MORRIS"]

        # Main paragraph lines should still align to GT text.
        line1_gt = " ".join((w.ground_truth_text or "") for w in page.lines[1].words)
        line2_gt = " ".join((w.ground_truth_text or "") for w in page.lines[2].words)
        line5_gt = " ".join((w.ground_truth_text or "") for w in page.lines[5].words)
        assert line1_gt == "de Rochambeau, upon his personal credit, to do it."
        assert line2_gt == "But even Morris, trained merchant and financier that"
        assert line5_gt == "he was, could not make something out of nothing. The"

    def test_hyphenated_line_break_preserves_split_when_previous_line_matches(self):
        """Regression: when OCR splits a GT word across lines with a trailing dash,
        keep the split as 'op-' and 'posed' when the preceding line already aligns.
        """
        ocr_lines = [
            ["which", "had", "rendered", "them", "homeless.", "Almost", "without"],
            [
                "exception",
                "they",
                "had",
                "been,",
                "in",
                "opinion,",
                "as",
                "thoroughly",
                "op-",
            ],
            [
                "posed",
                "as",
                "their",
                "neighbors",
                "to",
                "the",
                "policy",
                "of",
                "the",
                "King",
                "and",
            ],
        ]

        gt_text = "\n".join(
            [
                "which had rendered them homeless. Almost without",
                "exception they had been, in opinion, as thoroughly opposed",
                "as their neighbors to the policy of the King and",
            ]
        )

        page = _make_page(ocr_lines)
        update_page_with_ground_truth_text(page, gt_text)

        # Prior line is an exact anchor line.
        assert (
            " ".join((word.ground_truth_text or "") for word in page.lines[0].words)
            == "which had rendered them homeless. Almost without"
        )

        # The hyphenated OCR line should map to a hyphenated GT variant.
        assert page.lines[1].base_ground_truth_text == (
            "exception they had been, in opinion, as thoroughly op-"
        )

        # The next OCR line should receive the carried remainder of the split word.
        assert page.lines[2].base_ground_truth_text == (
            "posed as their neighbors to the policy of the King and"
        )

        # Word-level sanity checks for the split itself.
        assert page.lines[1].words[-1].text == "op-"
        assert page.lines[1].words[-1].ground_truth_text == "op-"
        assert page.lines[2].words[0].text == "posed"
        assert page.lines[2].words[0].ground_truth_text == "posed"

    def test_line_end_soft_wrap_without_visible_hyphen_still_restores_split(self):
        """If OCR misses the trailing hyphen at line end (e.g. 'op'), still
        restore a wrapped GT split as 'op-' and carry 'posed' to next line.
        """
        ocr_lines = [
            ["which", "had", "rendered", "them", "homeless.", "Almost", "without"],
            [
                "exception",
                "they",
                "had",
                "been,",
                "in",
                "opinion,",
                "as",
                "thoroughly",
                "op",
            ],
            [
                "posed",
                "as",
                "their",
                "neighbors",
                "to",
                "the",
                "policy",
                "of",
                "the",
                "King",
                "and",
            ],
        ]

        gt_text = "\n".join(
            [
                "which had rendered them homeless. Almost without",
                "exception they had been, in opinion, as thoroughly opposed",
                "as their neighbors to the policy of the King and",
            ]
        )

        page = _make_page(ocr_lines)
        update_page_with_ground_truth_text(page, gt_text)

        assert page.lines[1].base_ground_truth_text == (
            "exception they had been, in opinion, as thoroughly op-"
        )
        assert page.lines[2].base_ground_truth_text == (
            "posed as their neighbors to the policy of the King and"
        )

        assert page.lines[1].words[-1].text == "op"
        assert page.lines[1].words[-1].ground_truth_text == "op-"
        assert page.lines[2].words[0].ground_truth_text == "posed"
