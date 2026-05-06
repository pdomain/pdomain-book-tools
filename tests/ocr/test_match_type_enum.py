"""Regression locks for the MatchType enum surface.

L-21: ``WORD_NEARLY_EQUAL_DUE_TO_PUNCTUATION`` was a placeholder member with
zero consumers in pd_book_tools, the test suite, or any sibling pd-* repo.
The orphaned ``"TODO: ..."`` string following it was an expression, not a
docstring, so the intent was not even captured. Removed in the L-21 fix.

This test pins the enum surface so the dead member cannot be silently
re-added without a corresponding consumer.
"""

import pytest

from pd_book_tools.ocr.ground_truth_matching_helpers.match_type import MatchType


def test_word_nearly_equal_due_to_punctuation_not_present():
    """L-21 removal lock: the placeholder member must stay gone until the
    punctuation-aware matching pipeline is actually implemented and assigns
    it somewhere."""
    assert not hasattr(MatchType, "WORD_NEARLY_EQUAL_DUE_TO_PUNCTUATION")
    with pytest.raises(ValueError):
        MatchType("word-nearly-equal-due-to-punctuation")
