from enum import Enum


class MatchType(Enum):
    WORD_EXACTLY_EQUAL = "word-exactly-equal"
    "Word is exactly equal to GT word"

    # TODO: re-introduce WORD_NEARLY_EQUAL_DUE_TO_PUNCTUATION when
    # punctuation-aware matching (quotes, primes, dashes) is implemented
    # between OCR and GT. Removed because nothing in the matching pipeline
    # ever assigned it and the prior placeholder string after the member
    # was an orphaned expression, not a docstring.

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
