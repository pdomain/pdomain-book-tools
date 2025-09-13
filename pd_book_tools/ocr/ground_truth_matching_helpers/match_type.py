from enum import Enum


class MatchType(Enum):
    WORD_EXACTLY_EQUAL = "word-exactly-equal"
    "Word is exactly equal to GT word"

    WORD_NEARLY_EQUAL_DUE_TO_PUNCTUATION = "word-nearly-equal-due-to-punctuation"
    "TODO: For use if/when I implement punctuation matching (quotes, primes, dashes) between OCR and GT in the future"

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
