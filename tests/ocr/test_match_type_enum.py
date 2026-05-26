"""Regression locks for the MatchType enum surface.

L-21: ``WORD_NEARLY_EQUAL_DUE_TO_PUNCTUATION`` was a placeholder member with
zero consumers in pdomain_book_tools, the test suite, or any sibling pd-* repo.
The orphaned ``"TODO: ..."`` string following it was an expression, not a
docstring, so the intent was not even captured. Removed in the L-21 fix.

L-22: ``LINE_REPLACE_WORD_EQUAL`` was likewise defined but never assigned
anywhere; removed in the L-22 fix.

These tests pin the enum surface so the dead members cannot be silently
re-added without a corresponding consumer.
"""

import pytest

from pdomain_book_tools.ocr.ground_truth_matching_helpers.match_type import MatchType


def test_word_nearly_equal_due_to_punctuation_not_present():
    """L-21 removal lock: the placeholder member must stay gone until the
    punctuation-aware matching pipeline is actually implemented and assigns
    it somewhere."""
    assert not hasattr(MatchType, "WORD_NEARLY_EQUAL_DUE_TO_PUNCTUATION")
    with pytest.raises(ValueError):
        MatchType("word-nearly-equal-due-to-punctuation")


def test_line_replace_word_equal_not_present():
    """L-22 removal lock: the placeholder member must stay gone until
    update_line_with_ground_truth_replace_words actually assigns it (i.e.
    detects fuzz_score == 100 pairings inside a replace span and tags them
    distinctly from LINE_REPLACE_WORD_REPLACE)."""
    assert not hasattr(MatchType, "LINE_REPLACE_WORD_EQUAL")
    with pytest.raises(ValueError):
        MatchType("difflib-line-replace-word-equal")


def test_match_type_surface_is_minimal_and_documented():
    """Lock the full set of MatchType values currently in use; a future
    addition must update this list (and add a real consumer)."""
    actual = {m.value for m in MatchType}
    expected = {
        "word-exactly-equal",
        "difflib-line-equal",
        "difflib-line-replace",
        "difflib-line-delete",
        "difflib-line-insert",
        "difflib-line-replace-word-replace",
        "difflib-line-replace-word-replace-combined",
        "difflib-line-replace-word-delete",
        "difflib-line-replace-word-insert",
    }
    assert actual == expected
