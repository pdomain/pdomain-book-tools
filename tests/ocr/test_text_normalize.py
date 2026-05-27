"""Tests for pdomain_book_tools.ocr.text_normalize."""

from __future__ import annotations

import pytest

from pdomain_book_tools.ocr import (
    apply_text_normalizations,
    normalize_curly_quotes,
    normalize_em_dash,
)
from pdomain_book_tools.ocr.text_normalize import (
    apply_text_normalizations as _apply_via_module,
)

# Cover all 8 curly-quote glyphs that the helper must normalize.
_CURLY_SINGLE_GLYPHS = [
    "\u2018",  # LEFT SINGLE QUOTATION MARK
    "\u2019",  # RIGHT SINGLE QUOTATION MARK
    "\u201a",  # SINGLE LOW-9 QUOTATION MARK
    "\u201b",  # SINGLE HIGH-REVERSED-9 QUOTATION MARK
]
_CURLY_DOUBLE_GLYPHS = [
    "\u201c",  # LEFT DOUBLE QUOTATION MARK
    "\u201d",  # RIGHT DOUBLE QUOTATION MARK
    "\u201e",  # DOUBLE LOW-9 QUOTATION MARK
    "\u201f",  # DOUBLE HIGH-REVERSED-9 QUOTATION MARK
]


@pytest.mark.parametrize("glyph", _CURLY_SINGLE_GLYPHS)
def test_normalize_curly_quotes_single_variants(glyph: str) -> None:
    """Each curly single-quote variant collapses to ASCII apostrophe."""
    assert normalize_curly_quotes(f"a{glyph}b") == "a'b"


@pytest.mark.parametrize("glyph", _CURLY_DOUBLE_GLYPHS)
def test_normalize_curly_quotes_double_variants(glyph: str) -> None:
    """Each curly double-quote variant collapses to ASCII double quote."""
    assert normalize_curly_quotes(f"a{glyph}b") == 'a"b'


def test_normalize_curly_quotes_passthrough_when_clean() -> None:
    assert (
        normalize_curly_quotes("plain ascii 'text' here") == "plain ascii 'text' here"
    )


def test_normalize_curly_quotes_empty_string() -> None:
    assert normalize_curly_quotes("") == ""


def test_normalize_em_dash_basic() -> None:
    assert normalize_em_dash("a\u2014b") == "a--b"


def test_normalize_em_dash_multiple() -> None:
    assert normalize_em_dash("x\u2014y\u2014z") == "x--y--z"


def test_normalize_em_dash_passthrough() -> None:
    assert normalize_em_dash("no em dash here") == "no em dash here"


def test_normalize_em_dash_empty_string() -> None:
    assert normalize_em_dash("") == ""


def test_apply_text_normalizations_both_off_is_identity() -> None:
    text = "she said \u201chi\u201d \u2014 then left"
    assert (
        apply_text_normalizations(
            text,
            straight_quotes=False,
            em_dash_to_double_hyphen=False,
        )
        == text
    )


def test_apply_text_normalizations_both_on_applies_both() -> None:
    text = "she said \u201chi\u201d \u2014 then \u2018left\u2019"
    expected = "she said \"hi\" -- then 'left'"
    assert (
        apply_text_normalizations(
            text,
            straight_quotes=True,
            em_dash_to_double_hyphen=True,
        )
        == expected
    )


def test_apply_text_normalizations_only_straight_quotes() -> None:
    text = "she said \u201chi\u201d \u2014 left"
    expected = 'she said "hi" \u2014 left'
    assert (
        apply_text_normalizations(
            text,
            straight_quotes=True,
            em_dash_to_double_hyphen=False,
        )
        == expected
    )


def test_apply_text_normalizations_only_em_dash() -> None:
    text = "she said \u201chi\u201d \u2014 left"
    expected = "she said \u201chi\u201d -- left"
    assert (
        apply_text_normalizations(
            text,
            straight_quotes=False,
            em_dash_to_double_hyphen=True,
        )
        == expected
    )


def test_apply_text_normalizations_none_returns_empty_string() -> None:
    """Blank pages may yield None text; the helper tolerates it."""
    assert (
        apply_text_normalizations(
            None,
            straight_quotes=True,
            em_dash_to_double_hyphen=True,
        )
        == ""
    )


def test_apply_text_normalizations_empty_string_returns_empty_string() -> None:
    assert (
        apply_text_normalizations(
            "",
            straight_quotes=True,
            em_dash_to_double_hyphen=True,
        )
        == ""
    )


def test_module_import_path_is_stable() -> None:
    """Verify the direct submodule import path also works."""
    assert _apply_via_module is apply_text_normalizations
