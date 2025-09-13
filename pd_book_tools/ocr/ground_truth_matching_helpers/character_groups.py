from enum import Enum


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
