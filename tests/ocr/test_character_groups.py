"""Determinism tests for CharacterGroups (regression for review M-26).

Combined character-group constants (DASHES, QUOTES, PRIMES,
QUOTES_AND_PRIMES) must have a deterministic, insertion-ordered list value.

Background: previously these were built with ``list(set(...))`` whose
iteration order is non-deterministic across Python interpreter runs once
``PYTHONHASHSEED`` differs. Tied-variant choices in
``ground_truth_matching`` then resolved differently across runs even on
identical inputs. Fix is ``list(dict.fromkeys(...))``: dedup while
preserving insertion order (stable for Python 3.7+).

These tests lock the expected ordered values so a future refactor can't
silently regress to set-based dedup.
"""

from pd_book_tools.ocr.ground_truth_matching_helpers.character_groups import (
    CharacterGroups,
)


def test_dashes_deterministic_order():
    # Insertion order: HYPHEN, ENDASH, EMDASH, FIGUREDASH, TWOEMDASH,
    # THREEEMDASH, HORIZONTAL_BAR, NOBREAK_HYPHEN, MINUS. No duplicates
    # exist among these literals so dedup is a no-op, only ordering matters.
    assert CharacterGroups.DASHES.value == [
        "-",
        "\u2013",  # EN DASH
        "—",
        "\u2012",  # FIGURE DASH
        "⸺",
        "⸻",
        "―",
        "\u2011",  # NON-BREAKING HYPHEN
        "\u2212",  # MINUS SIGN
    ]


def test_quotes_deterministic_order():
    # SINGLE_QUOTE then DOUBLE_QUOTE; no overlap.
    assert CharacterGroups.QUOTES.value == [
        "'",
        "\u2018",
        "\u2019",
        '"',
        "“",
        "”",
    ]  # LEFT/RIGHT SINGLE QUOTATION MARK


def test_primes_deterministic_order():
    # SINGLE_PRIME then DOUBLE_PRIME; no overlap.
    assert CharacterGroups.PRIMES.value == ["'", "\u2032", '"', "″"]  # PRIME


def test_quotes_and_primes_deterministic_order():
    # QUOTES first then PRIMES, with the ASCII apostrophe and the ASCII
    # double quote already in QUOTES so the dedup drops them when PRIMES
    # would re-introduce them. Insertion-ordered dedup keeps the first
    # occurrence.
    assert CharacterGroups.QUOTES_AND_PRIMES.value == [
        "'",
        "\u2018",  # LEFT SINGLE QUOTATION MARK
        "\u2019",  # RIGHT SINGLE QUOTATION MARK
        '"',
        "“",
        "”",
        "\u2032",  # PRIME
        "″",
    ]
