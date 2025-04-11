import logging
from collections import namedtuple
from difflib import SequenceMatcher
from enum import Enum

from numpy import mean as np_mean
from thefuzz.fuzz import ratio as fuzz_ratio

from pd_book_tools.geometry import BoundingBox
from pd_book_tools.ocr.block import Block, BlockCategory
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.word import Word

# Configure logging
logger = logging.getLogger(__name__)


class CharacterGroups(Enum):
    HYPHEN = ["-"]
    ENDASH = ["–"]
    EMDASH = ["—"]
    FIGUREDASH = ["‒"]
    TWOEMDASH = ["⸺"]
    THREEEMDASH = ["⸻"]
    HORIZONTAL_BAR = ["―"]
    NOBREAK_HYPHEN = ["‑"]
    MINUS = ["−"]
    DASHES = list(
        set(
            HYPHEN
            + ENDASH
            + EMDASH
            + FIGUREDASH
            + TWOEMDASH
            + THREEEMDASH
            + HORIZONTAL_BAR
            + NOBREAK_HYPHEN
            + MINUS
        )
    )
    SINGLE_QUOTE = ["'", "‘", "’"]
    DOUBLE_QUOTE = ['"', "“", "”"]
    QUOTES = list(set(SINGLE_QUOTE + DOUBLE_QUOTE))
    SINGLE_PRIME = ["'", "′"]
    DOUBLE_PRIME = ['"', "″"]
    PRIMES = list(set(SINGLE_PRIME + DOUBLE_PRIME))
    QUOTES_AND_PRIMES = list(set(QUOTES + PRIMES))

    def __contains__(self, char):
        return char in self.value


LineDiffOpCodes = namedtuple(
    "LineDiffOpCodes",
    ["line_tag", "ocr_line_1", "ocr_line_2", "gt_line_1", "gt_line_2"],
)
WordDiffOpCodes = namedtuple(
    "WordDiffOpCodes",
    ["word_tag", "ocr_word_1", "ocr_word_2", "gt_word_1", "gt_word_2"],
)
LineMatchScores = namedtuple(
    "LineMatchScores",
    ["ocr_line_nbr", "gt_line_nbr", "ground_truth_text", "match_score"],
)
WordMatchScores = namedtuple(
    "WordMatchScores",
    ["ocr_word_nbr", "gt_word_nbr", "ground_truth_text", "match_score"],
)


class MatchType(Enum):
    WORD_EXACTLY_EQUAL = "word-exactly-equal"
    "Word is exactly equal to GT word"

    WORD_NEARLY_EQUAL_DUE_TO_PUNCTUATION = "word-nearly-equal-due-to-punctuation"
    "For use if I implement punctuation matching (quotes, primes, dashes) between OCR and GT in the future"

    # Line-level match types
    LINE_EQUAL = "difflib-line-equal"
    LINE_REPLACE = "difflib-line-replace"
    LINE_DELETE = "difflib-line-delete"
    LINE_INSERT = "difflib-line-insert"

    # Word-level match types (For use with LINE_REPLACE)
    LINE_REPLACE_WORD_EQUAL = LINE_REPLACE + "-word-equal"
    LINE_REPLACE_WORD_REPLACE = LINE_REPLACE + "-word-replace"
    LINE_REPLACE_WORD_REPLACE_COMBINED = LINE_REPLACE + "-word-replace-combined"
    LINE_REPLACE_WORD_DELETE = LINE_REPLACE + "-word-delete"
    LINE_REPLACE_WORD_INSERT = LINE_REPLACE + "-word-insert"


def update_page_with_ground_truth_text(
    page: Page,
    ground_truth_page: str,
):
    """
    Match ground truth words against the OCR on a page.
    This is for source text of a complete page, where the source does not have bounding boxes.

    Use difflib to match against the text.

    This is used for model training and evaluation purposes. Attempt to match this all up so
    we only have to make a few adjustments to feed the ground truth data into the model to train it.

    Ground truth lines that have no corresponding OCR lines are added
    to the unmatched_ground_truth_lines list.
    """

    # Sequence Matcher needs ordered tuples, so convert lists + dicts into tuples of tuples of strings
    #   example: ( ( "line1word1", "line1word2" ), ("line2word1", "line2word2") )
    ocr_tuples = [tuple([word.text for word in line.words]) for line in page.lines]

    ground_truth_lines_text = [
        line.strip() for line in ground_truth_page.splitlines() if line.strip()
    ]
    ground_truth_tuples = [tuple(line.split()) for line in ground_truth_lines_text]

    full_line_matcher = SequenceMatcher(None, ocr_tuples, ground_truth_tuples)

    opcodes_list = full_line_matcher.get_opcodes()

    for o in opcodes_list:
        op = LineDiffOpCodes(*o)
        if op.line_tag == "delete":
            update_page_match_difflib_lines_delete(
                page=page,
                op=op,
            )
        elif op.line_tag == "equal":
            update_page_match_difflib_lines_equal(
                page=page,
                op=op,
                ground_truth_tuples=ground_truth_tuples,
            )
        elif op.line_tag == "insert":
            update_page_match_difflib_lines_insert(
                page=page,
                op=op,
                ocr_tuples=ocr_tuples,
                ground_truth_tuples=ground_truth_tuples,
            )
        elif op.line_tag == "replace":
            update_page_match_difflib_lines_replace(
                page=page,
                op=op,
                ocr_tuples=ocr_tuples,
                ground_truth_tuples=ground_truth_tuples,
            )
        else:
            raise ValueError(f"Unknown line tag: {op.line_tag}")


def update_page_match_difflib_lines_delete(page: Page, op: LineDiffOpCodes):
    """
    Currently for lines that don't exist in Ground Truth, but do exist in OCR, do nothing
    """
    logger.info(
        "DELETE - LINES exist in OCR that do not appear to exist in Ground Truth data"
    )
    return None


def update_page_match_difflib_lines_equal(
    page: Page, op: LineDiffOpCodes, ground_truth_tuples: tuple[tuple[str]]
):
    """
    Add Ground Truth Data to lines that are equal between OCR and ground truth.
    """
    lines = page.lines[op.ocr_line_1 : op.ocr_line_2]
    ground_truth_lines = ground_truth_tuples[op.gt_line_1 : op.gt_line_2]
    if len(lines) != len(ground_truth_lines):
        raise ValueError(
            f"Line count mismatch: {len(lines)} vs {len(ground_truth_lines)}"
        )
    for line, ground_truth_line in zip(lines, ground_truth_lines):
        update_line_match_difflib_lines_equal(line, ground_truth_line)


def update_line_match_difflib_lines_equal(line: Block, ground_truth_line: tuple[str]):
    """
    Add Ground Truth Data to a line where the line and ground truth are known to be equivalent
    """
    if line.block_category != BlockCategory.LINE:
        raise ValueError("Line is not a line block")
    if len(line.words) != len(ground_truth_line):
        raise ValueError(
            f"Line word count mismatch: {len(line.words)} vs {len(ground_truth_line)}"
        )
    word: Word
    for word_idx, word in enumerate(line.words):
        if word.text != ground_truth_line[word_idx]:
            raise ValueError(
                f"Word mismatch: {word.text} vs {ground_truth_line[word_idx]}"
            )
        word.ground_truth_text = ground_truth_line[word_idx]
        word.ground_truth_match_keys = {
            "match_type": MatchType.LINE_EQUAL.value,
            "match_score": 100,
        }


def update_page_match_difflib_lines_insert(
    page: Page, op: LineDiffOpCodes, ground_truth_tuples
):
    """
    Entire Lines that exist in Ground Truth for a page, but do NOT exist in OCR.
    Add these to a list of 'unmatched lines' on the page
    """
    for ocr_line_offset, gt_line_nbr in enumerate(range(op.gt_line_1, op.gt_line_2)):
        ocr_line_nbr = op.ocr_line_1 + ocr_line_offset
        page.unmatched_ground_truth_lines.append(
            (ocr_line_nbr, " ".join(ground_truth_tuples[gt_line_nbr]))
        )
    logger.info(
        "INSERT - LINES exist in Ground Truth that do not appear to exist in OCR data"
    )


def update_page_match_difflib_lines_replace(
    page: Page, op: LineDiffOpCodes, ocr_tuples, ground_truth_tuples
):
    if (op.ocr_line_2 - op.ocr_line_1) == (op.gt_line_2 - op.gt_line_1):
        # If the same number of lines are in the GT and OCR diff match, run matching on the words in the line
        for ocr_line_nbr in range(op.ocr_line_1, op.ocr_line_2):
            gt_line_nbr = op.gt_line_1 + (ocr_line_nbr - op.ocr_line_1)
            ground_truth_text = " ".join(ground_truth_tuples[gt_line_nbr])
            previous_line_ground_truth_text = " ".join(
                ground_truth_tuples[gt_line_nbr - 1] if gt_line_nbr > 0 else ""
            )
            update_line_with_best_matched_ground_truth_text(
                line=page.lines[ocr_line_nbr],
                ground_truth_text=ground_truth_text,
                previous_ground_truth_text=previous_line_ground_truth_text,
            )
    else:
        update_page_match_difflib_lines_replace_different_line_count(
            page, op, ocr_tuples, ground_truth_tuples
        )


def update_line_with_best_matched_ground_truth_text(
    line: Block,
    ground_truth_text: str,
    previous_ground_truth_text: str = "",
):
    ocr_line_tuple = tuple(line.word_list)

    ocr_text = " ".join(ocr_line_tuple)
    best_match_gt_line, _ = generate_best_matched_ground_truth_line(
        ocr_text=ocr_text,
        ground_truth_text=ground_truth_text,
        previous_ground_truth_text=previous_ground_truth_text,
    )
    best_match_gt_line_tuple = tuple(best_match_gt_line.split())

    update_line_with_ground_truth(
        line=line,
        ocr_line_tuple=ocr_line_tuple,
        ground_truth_tuple=best_match_gt_line_tuple,
    )


def update_line_with_ground_truth(line: Block, ocr_line_tuple, ground_truth_tuple):
    word_matcher = SequenceMatcher(None, ocr_line_tuple, ground_truth_tuple)
    opcodes_list = word_matcher.get_opcodes()

    combined_ocr_word_nbrs, new_combined_words = [], []

    for o in opcodes_list:
        op = WordDiffOpCodes(*o)
        if op.word_tag == "delete":
            # Word is in OCR but not GT
            # Do Nothing
            logger.debug("Word in OCR but Not GT. Do Nothing.")
        elif op.word_tag == "equal":
            for i, ocr_word_nbr in enumerate(range(op.ocr_word_1, op.ocr_word_2)):
                gt_word_nbr = op.gt_word_1 + i
                word = line.words[ocr_word_nbr]
                word.ground_truth_text = ground_truth_tuple[gt_word_nbr]
                word.ground_truth_match_keys = {
                    "match_type": MatchType.WORD_EXACTLY_EQUAL.value,
                    "match_score": 100,
                }
        elif op.word_tag == "insert":
            # Word is in GT but not OCR
            # Add word to OCR line with GT details
            line.unmatched_ground_truth_words.append(
                (op.ocr_word_1, ground_truth_tuple[op.gt_word_1])
            )
        elif op.word_tag == "replace":
            c, n = update_line_with_ground_truth_replace_words(
                line=line,
                op=op,
                ocr_line_tuple=ocr_line_tuple,
                ground_truth_tuple=ground_truth_tuple,
            )
            combined_ocr_word_nbrs.extend(c)
            new_combined_words.extend(n)

    if combined_ocr_word_nbrs or new_combined_words:
        update_combined_words_in_line(
            line=line,
            combined_ocr_word_nbrs=combined_ocr_word_nbrs,
            new_combined_words=new_combined_words,
        )


def try_matching_combined_words(
    matched_ocr_line_words, ocr_line_tuple, ground_truth_tuple
):
    """
    Try to match combined words in OCR line with single-word ground truth.
    e.g. ["<word>", ";"] OCR might be "<word>;" GT
    if so, merge the two words in the OCR line
    and update the ground truth text
    """
    # Combine adjoining OCR words and see if they closely match single-word ground truth
    # e.g. ["<word>", ";"] OCR might be "<word>;" GT
    # if so, merge the two words in the OCR line
    # and update the ground truth text

    # TODO: Add logic to find quotation marks, ending apostrophes, and prime marks and ensure they're part of the single "word"

    ocr_combination_tuple = tuple(
        [
            (
                ocr_word_start,
                ocr_word_end,
                "".join(ocr_line_tuple[ocr_word_start:ocr_word_end]),
                ocr_line_tuple[ocr_word_start:ocr_word_end],
            )
            for ocr_word_start in range(0, len(ocr_line_tuple))
            for ocr_word_end in range(ocr_word_start + 1, len(ocr_line_tuple) + 1)
        ]
    )

    match_scores = [
        (
            fuzz_ratio(
                ocr_combination_tuple[ocr_combination_nbr][2].strip(),
                ground_truth_tuple[gt_word_nbr].strip(),
            ),
            (
                ocr_combination_tuple[ocr_combination_nbr][0],
                ocr_combination_tuple[ocr_combination_nbr][1],
            ),
            ocr_combination_tuple[ocr_combination_nbr][2].strip(),
            ocr_combination_tuple[ocr_combination_nbr][3],
            ground_truth_tuple[gt_word_nbr].strip(),
            gt_word_nbr,
        )
        for ocr_combination_nbr in range(0, len(ocr_combination_tuple))
        for gt_word_nbr in range(0, len(ground_truth_tuple))
    ]

    # Only match to fairly confident words (> 70)
    sorted_match_scores = sorted(match_scores, key=lambda x: (-x[0], x[1][0]))

    sorted_match_scores = [s for s in sorted_match_scores if s[0] >= 80]

    combined_words = []
    while True:
        if not sorted_match_scores:
            break
        # Get the best match score
        s = sorted_match_scores.pop(0)
        (
            score,
            combination_start_end,
            combined_word,
            ocr_combination_tuple,
            gt_word,
            gt_word_nbr,
        ) = s
        combination_start, combination_end = combination_start_end
        matched_words = matched_ocr_line_words[combination_start:combination_end]
        # Create a new word object with the combined word
        # Then remove the words from the line
        combined_word_text = "".join([word.text for word in matched_words])
        combined_word_bbox = BoundingBox.union(
            word.bounding_box for word in matched_words
        )
        combined_word = Word(
            text=combined_word_text,
            bounding_box=combined_word_bbox,
            ocr_confidence=np_mean([word.ocr_confidence for word in matched_words]),
            ground_truth_text=gt_word,
            ground_truth_match_keys={
                "match_type": MatchType.LINE_REPLACE_WORD_REPLACE_COMBINED.value,
                "match_score": score,
            },
        )
        combined_words.append(
            (combination_start, combination_end, gt_word_nbr, combined_word)
        )
        sorted_match_scores = [
            s
            for s in sorted_match_scores
            if not any(
                s[1][0] <= n <= s[1][1]
                for n in range(combination_start, combination_end)
            )
        ]

    logger.debug("Combined words found: " + str(combined_words))

    return combined_words


def update_line_with_ground_truth_replace_words(
    line: Block, op: WordDiffOpCodes, ocr_line_tuple, ground_truth_tuple
):
    """
    Update the line with the best matched ground truth text
    when the number of words in the OCR line and ground truth line are different.
    """
    matched_ocr_line_tuple = ocr_line_tuple[op.ocr_word_1 : op.ocr_word_2]
    matched_ground_truth_tuple = ground_truth_tuple[op.gt_word_1 : op.gt_word_2]

    logger.debug("Matched OCR Line Tuple", matched_ocr_line_tuple)
    logger.debug("Matched GT Line Tuple", matched_ground_truth_tuple)

    matched_ocr_line_words = [
        word for word in line.words[op.ocr_word_1 : op.ocr_word_2]
    ]

    combined_word_detail = try_matching_combined_words(
        matched_ocr_line_words, matched_ocr_line_tuple, matched_ground_truth_tuple
    )
    # Check if the combined words in the OCR line closely match the ground truth line
    # If so, update the line with the combined words

    # TODO:
    #   Check if ground truth word includes a double or single quote character.
    #   OCR can misread these as short one or two character words
    #   If such a short word is in OCR but not in GT, and GT has ", ',
    #   prime or double prime, then combine the two OCR words
    #   Also, generally, the previous GT bounding box will be "higher" and smaller than the current one - "superscripted"
    #   Join these together as well.

    # Iterate over the remaining words
    # Update each word with best matched ground truth text. If there are then more
    # GT words than OCR words, append them to the unmatched list.
    combined_ocr_word_nbrs = list(
        set(
            [
                (r + op.ocr_word_1)
                for combination_start, combination_end, _, _ in combined_word_detail
                for r in range(combination_start, combination_end)
            ]
        )
    )

    combined_gt_word_nbrs = list(
        set(
            [
                (gt_word_nbr + op.gt_word_1)
                for _, _, gt_word_nbr, _ in combined_word_detail
            ]
        )
    )

    to_match_gt_word_nbrs = [
        gt_word_nbr
        for gt_word_nbr in range(op.gt_word_1, op.gt_word_2)
        if gt_word_nbr not in combined_gt_word_nbrs
    ]

    logger.debug(
        "To Match GT Words"
        + str([ground_truth_tuple[w] for w in to_match_gt_word_nbrs])
    )
    logger.debug("Combined GT Word Nbrs" + str(combined_gt_word_nbrs))

    for ocr_word_nbr in range(op.ocr_word_1, op.ocr_word_2):
        if not to_match_gt_word_nbrs:
            # If there's no more GT words to match
            break

        if ocr_word_nbr in combined_ocr_word_nbrs:
            # Skip these, they will be combined after we add the other GT data
            continue

        logger.debug("OCR Word Nbr for update" + str(ocr_word_nbr))
        logger.debug("GT Word Nbr" + str(ocr_word_nbr))

        gt_word_nbr = to_match_gt_word_nbrs.pop(0)
        word = line.words[ocr_word_nbr]
        word.ground_truth_text = ground_truth_tuple[gt_word_nbr]
        word.ground_truth_match_keys = {
            "match_type": MatchType.LINE_REPLACE_WORD_REPLACE.value,
            "match_score": word.fuzz_score_against(word.ground_truth_text),
        }

    # If there are any GT words left, add them at end of the group as 'unmatched' words
    for gt_word_nbr in to_match_gt_word_nbrs:
        if gt_word_nbr in combined_gt_word_nbrs:
            continue
        # Add unmatched GT word to the line
        line.unmatched_ground_truth_words.append(
            (op.ocr_word_2 - 1, ground_truth_tuple[gt_word_nbr])
        )

    # Add the combined words to the line
    new_combined_words = [c[3] for c in combined_word_detail]

    # Remove and add words to the line at the END of all the matching, so we don't mess up the other updates
    return combined_ocr_word_nbrs, new_combined_words


def update_combined_words_in_line(
    line: Block,
    combined_ocr_word_nbrs: list[int],
    new_combined_words: list[Word],
):
    # If there are any combined words:
    # - remove existing words
    # - add combined words to the line

    # Delete in reverse order
    for ocr_word_nbr in sorted(combined_ocr_word_nbrs, reverse=True):
        del line.items[ocr_word_nbr]

    for cw in new_combined_words:
        line.items.add(cw)


def match_different_line_counts(op: LineDiffOpCodes, ocr_tuples, ground_truth_tuples):
    GroundTruthText = namedtuple(
        "GroundTruthText", ["gt_line_nbr", "current_text", "previous_text"]
    )
    ground_truth_text_list: list[GroundTruthText] = []

    for gt_line_nbr in range(op.gt_line_1, op.gt_line_2):
        current_text = " ".join(ground_truth_tuples[gt_line_nbr])
        previous_text = (
            " ".join(ground_truth_tuples[gt_line_nbr - 1]) if gt_line_nbr > 0 else ""
        )
        ground_truth_text_list.append(
            GroundTruthText(gt_line_nbr, current_text, previous_text)
        )

    match_scores = []
    for ocr_line_nbr in range(op.ocr_line_1, op.ocr_line_2):
        ocr_text = " ".join(ocr_tuples[ocr_line_nbr])
        nowrap_match_list = [
            (
                *generate_best_matched_ground_truth_line(
                    ocr_text=ocr_text,
                    ground_truth_text=gt.current_text,
                    previous_ground_truth_text=gt.previous_text,
                ),
                gt.gt_line_nbr,
            )
            for gt in ground_truth_text_list
        ]
        nowrap_results = [
            LineMatchScores(ocr_line_nbr, gt_line_nbr, ground_truth_text, score)
            for ground_truth_text, score, gt_line_nbr in nowrap_match_list
        ]
        match_scores.extend(nowrap_results)

        # Test also the case where an OCR line exists
        # but only the "previous" GT line exists
        # (where 'wrapping' eliminated a line).
        wrap_match_list = [
            (
                *generate_best_matched_ground_truth_line(
                    ocr_text=ocr_text,
                    ground_truth_text="",
                    previous_ground_truth_text=gt.current_text,
                ),
                gt.gt_line_nbr,
            )
            for gt in ground_truth_text_list
        ]
        wrap_results = [
            LineMatchScores(ocr_line_nbr, gt_line_nbr, ground_truth_text, score)
            for ground_truth_text, score, gt_line_nbr in wrap_match_list
        ]
        match_scores.extend(wrap_results)
    return match_scores


def update_page_match_difflib_lines_replace_different_line_count(
    page: Page, op: LineDiffOpCodes, ocr_tuples, ground_truth_tuples
):
    # More or Fewer OCR Lines than GT Lines
    # Match best lines, add any missing GT lines to page unmatched
    match_scores: list[LineMatchScores] = match_different_line_counts(
        op, ocr_tuples, ground_truth_tuples
    )

    # Order by match scores, breaking ties by ocr line number.
    # Take best match score, then remove all matches for that ocr line, then get next, etc
    # sort match scores by score desc and then by ocr line number ascending
    # Only match to fairly confident lines (> 70)
    sorted_match_scores = sorted(
        match_scores, key=lambda x: (-x.match_score, x.ocr_line_nbr)
    )
    sorted_match_scores = [s for s in sorted_match_scores if s.match_score >= 70]

    done = False
    matched_ocr_lines = []
    while (not done) and sorted_match_scores:
        next_score_tuple = sorted_match_scores.pop(0)
        matched_ocr_lines.append(next_score_tuple)
        # remove all entries for this OCR line number
        sorted_match_scores = [
            s
            for s in sorted_match_scores
            if s.ocr_line_nbr != next_score_tuple.ocr_line_nbr
        ]
        if len(matched_ocr_lines) == (op.ocr_line_2 - op.ocr_line_1):
            done = True

    # Once all Matched OCR lines are found, update ground truth
    for m in matched_ocr_lines:
        ocr_line_nbr = m.ocr_line_nbr
        ground_truth_text = m.ground_truth_text
        line = page.lines[ocr_line_nbr]
        ocr_line_tuple = ocr_tuples[ocr_line_nbr]
        ground_truth_tuple = tuple(ground_truth_text.split())
        update_line_with_ground_truth(
            line=line,
            ocr_line_tuple=ocr_line_tuple,
            ground_truth_tuple=ground_truth_tuple,
        )

    # Finally, for those GT lines that are not matched to OCR lines, add them to the unmatched list
    for gt_line_nbr in range(op.gt_line_1, op.gt_line_2):
        # Check if this GT line is already matched
        if any(m.gt_line_nbr == gt_line_nbr for m in matched_ocr_lines):
            continue
        # Add unmatched GT line to the page after the OCR lines
        ground_truth_text = " ".join(ground_truth_tuples[gt_line_nbr])
        page.unmatched_ground_truth_lines.append((op.ocr_line_2 - 1, ground_truth_text))


def _build_current_work_gt_line_from_prev(
    prev_char_count, previous_ground_truth_text, ground_truth_text
):
    """
    Build a working ground truth line by adding characters from the previous line.
    """
    if prev_char_count != 0:
        if previous_ground_truth_text[-prev_char_count] == " ":
            return None
        logger.debug(
            "Add Prev | %s | %s",
            previous_ground_truth_text[-prev_char_count],
            previous_ground_truth_text[-prev_char_count:],
        )
        gt_prev_characters = previous_ground_truth_text[-prev_char_count:].strip()
        return f"{gt_prev_characters} {ground_truth_text}"
    return ground_truth_text


def _build_current_work_gt_line_remove_suffix(remove_count, ground_truth_text):
    if remove_count <= len(ground_truth_text):
        return ground_truth_text[0:-remove_count].rstrip()
    else:
        raise ValueError("Cannot remove more characters than exist in the string")


def _generate_work_variants(base_text):
    """Generate variants of the base text with dashes appended."""
    return [base_text, base_text + "--"] + [
        base_text + dash for dash in CharacterGroups.DASHES.value
    ]


def generate_best_matched_ground_truth_line(
    ocr_text, ground_truth_text="", previous_ground_truth_text=""
):
    """
    Generate a "best line" ground truth to compare to by:
        - adding characters from previous line's GT
        - removing characters from last word of GT and adding a hyphen, em-dash, or long dash to each
            (iff there's a hyphen, em-dash, or long dash at end of OCR line)
    """
    variants = [
        (
            _build_current_work_gt_line_from_prev(
                prev_char_count, previous_ground_truth_text, ground_truth_text
            )
        ).strip()
        for prev_char_count in range(
            0, (len(previous_ground_truth_text)) - previous_ground_truth_text.rfind(" ")
        )
    ]
    if ocr_text.strip()[-1] in CharacterGroups.DASHES.value:
        # If the last character of the OCR text is a dash
        # generate a set of variants that remove letters from GT text
        variants = [
            (_build_current_work_gt_line_remove_suffix(j, prefix_variant)).strip()
            for j in range(0, (len(ground_truth_text) - ground_truth_text.rfind(" ")))
            for prefix_variant in variants
        ]
        variants = [
            item.strip()
            for sublist in [
                _generate_work_variants(variant)
                for variant in variants
                if variant is not None and variant.strip() != ""
            ]
            for item in sublist
        ]

    if not variants:
        return ground_truth_text, 0

    ratios = [fuzz_ratio(ocr_text.strip(), variant.strip()) for variant in variants]

    logger.debug("Ratios & Text Variants" + str(list(zip(variants, ratios))))

    best_ratio = max(ratios)
    best_work = variants[ratios.index(best_ratio)]

    logger.debug("Best Work | " + str(best_work) + " | " + str(best_ratio))

    return best_work, best_ratio
