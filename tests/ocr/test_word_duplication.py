from __future__ import annotations

import pytest

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.geometry.point import Point
from pdomain_book_tools.ocr.word import Word


def _bbox(left: float, top: float, right: float, bottom: float) -> BoundingBox:
    return BoundingBox(
        top_left=Point(left, top, is_normalized=True),
        bottom_right=Point(right, bottom, is_normalized=True),
        is_normalized=True,
    )


def _word(text: str, left: float, top: float, right: float, bottom: float) -> Word:
    return Word(
        text=text, bounding_box=_bbox(left, top, right, bottom), ocr_confidence=0.95
    )


def test_no_duplication_reports_nothing() -> None:
    from pdomain_book_tools.ocr.reorganize_page_utils import find_duplicated_words

    pre = [_word("alpha", 0.1, 0.1, 0.2, 0.2), _word("beta", 0.3, 0.1, 0.4, 0.2)]
    post = list(pre)
    assert find_duplicated_words(pre, post) == []


def test_a_word_appearing_twice_after_is_reported() -> None:
    from pdomain_book_tools.ocr.reorganize_page_utils import find_duplicated_words

    alpha = _word("alpha", 0.1, 0.1, 0.2, 0.2)
    pre = [alpha]
    post = [alpha, alpha]
    errors = find_duplicated_words(pre, post)
    assert len(errors) == 1
    assert "alpha" in errors[0]
    assert "duplicated" in errors[0]


def test_a_pre_existing_duplicate_is_not_flagged() -> None:
    from pdomain_book_tools.ocr.reorganize_page_utils import find_duplicated_words

    alpha = _word("alpha", 0.1, 0.1, 0.2, 0.2)
    pre = [alpha, alpha]
    post = [alpha, alpha]
    assert find_duplicated_words(pre, post) == []


def test_a_dropped_word_is_not_reported_as_duplication() -> None:
    from pdomain_book_tools.ocr.reorganize_page_utils import find_duplicated_words

    alpha = _word("alpha", 0.1, 0.1, 0.2, 0.2)
    beta = _word("beta", 0.3, 0.1, 0.4, 0.2)
    assert find_duplicated_words([alpha, beta], [alpha]) == []


def test_empty_text_words_are_ignored_like_the_drop_validator() -> None:
    from pdomain_book_tools.ocr.reorganize_page_utils import find_duplicated_words

    blank = _word("", 0.1, 0.1, 0.2, 0.2)
    assert find_duplicated_words([blank], [blank, blank]) == []


def test_a_brand_new_word_absent_from_pre_is_not_flagged() -> None:
    """A word with no pre-existing signature is recovered content, not a
    duplicate — e.g. the cursive drop-cap fallback synthesizing a Word for a
    glyph OCR missed entirely. Duplication requires the signature to have
    already existed in ``pre_words``.
    """
    from pdomain_book_tools.ocr.reorganize_page_utils import find_duplicated_words

    alpha = _word("alpha", 0.1, 0.1, 0.2, 0.2)
    recovered = _word("O", 0.5, 0.5, 0.6, 0.6)
    assert find_duplicated_words([alpha], [alpha, recovered]) == []


def test_strict_mode_raises_on_duplication() -> None:
    from pdomain_book_tools.ocr.reorganize_page_utils import (
        ReorganizeDuplicatedWordsError,
        raise_if_words_duplicated,
    )

    alpha = _word("alpha", 0.1, 0.1, 0.2, 0.2)
    with pytest.raises(ReorganizeDuplicatedWordsError, match="duplicated 1 word"):
        raise_if_words_duplicated([alpha], [alpha, alpha], strict=True)


def test_non_strict_mode_returns_the_errors_without_raising() -> None:
    from pdomain_book_tools.ocr.reorganize_page_utils import raise_if_words_duplicated

    alpha = _word("alpha", 0.1, 0.1, 0.2, 0.2)
    errors = raise_if_words_duplicated([alpha], [alpha, alpha], strict=False)
    assert len(errors) == 1
