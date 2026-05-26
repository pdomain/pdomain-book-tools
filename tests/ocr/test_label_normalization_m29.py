"""Regression tests for M-29:

`normalize_text_style_labels(['regular', 'italics'])` previously returned
`['regular', 'italics']`. The redundant `'regular'` sentinel was only stripped
inside `Word.update_style_attributes`, so a `Word` constructed directly with
`text_style_labels=['regular', 'italics']` stored the inconsistent state, and
that survived `to_dict`/`from_dict` round-trips.

The fix mirrors the strip logic into `normalize_text_style_labels` (and the
parallel `normalize_text_style_label_scopes` helper) so every entry point —
constructor, normalization helper, `update_style_attributes`, deserialization —
produces the same canonical representation.
"""

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.ocr.label_normalization import (
    normalize_text_style_label_scopes,
    normalize_text_style_labels,
)
from pdomain_book_tools.ocr.word import Word


class TestNormalizeTextStyleLabelsStripsRegular:
    def test_regular_stripped_when_other_label_present(self):
        # Direct symptom from the review.
        assert normalize_text_style_labels(["regular", "italics"]) == ["italics"]

    def test_regular_stripped_when_other_label_present_reversed(self):
        # Order should not matter.
        assert normalize_text_style_labels(["italics", "regular"]) == ["italics"]

    def test_regular_stripped_with_multiple_other_labels(self):
        assert normalize_text_style_labels(["regular", "italics", "bold"]) == [
            "italics",
            "bold",
        ]

    def test_regular_kept_when_alone(self):
        # Solo 'regular' must remain — it is the canonical default.
        assert normalize_text_style_labels(["regular"]) == ["regular"]

    def test_empty_input_defaults_to_regular(self):
        # Empty/None still defaults to ['regular'] (existing contract).
        assert normalize_text_style_labels([]) == ["regular"]
        assert normalize_text_style_labels(None) == ["regular"]

    def test_case_normalizes_then_strips(self):
        # Mixed case input still normalizes, then 'regular' strips.
        assert normalize_text_style_labels(["Regular", "Italics"]) == ["italics"]

    def test_no_regular_no_strip(self):
        # When 'regular' was never present, output is just dedup.
        assert normalize_text_style_labels(["italics", "bold", "italics"]) == [
            "italics",
            "bold",
        ]


class TestWordConstructorAppliesStripping:
    def test_word_init_strips_regular_when_other_present(self):
        word = Word(
            text="hello",
            bounding_box=BoundingBox.from_ltrb(0, 0, 60, 20, is_normalized=False),
            ocr_confidence=0.9,
            text_style_labels=["regular", "italics"],
        )
        assert word.text_style_labels == ["italics"]
        # Scopes must stay aligned with labels (no orphan 'regular' scope).
        assert "regular" not in word.text_style_label_scopes
        assert word.text_style_label_scopes == {"italics": "whole"}

    def test_word_round_trip_canonicalizes(self):
        # Even if a legacy serialized form contains both labels, round-trip
        # must canonicalize to the stripped form on load.
        legacy_payload = {
            "text": "hello",
            "bounding_box": BoundingBox.from_ltrb(
                0, 0, 60, 20, is_normalized=False
            ).to_dict(),
            "ocr_confidence": 0.9,
            "text_style_labels": ["regular", "italics"],
            "text_style_label_scopes": {"regular": "whole", "italics": "whole"},
        }
        word = Word.from_dict(legacy_payload)
        assert word.text_style_labels == ["italics"]
        assert word.text_style_label_scopes == {"italics": "whole"}

        # And a second round-trip is stable.
        re_serialized = word.to_dict()
        word2 = Word.from_dict(re_serialized)
        assert word2.text_style_labels == ["italics"]
        assert word2.text_style_label_scopes == {"italics": "whole"}


class TestNormalizeTextStyleLabelScopesStripsRegular:
    def test_scopes_strip_regular_when_other_label_present(self):
        # The scopes helper must stay in lockstep with the labels helper.
        result = normalize_text_style_label_scopes(
            ["regular", "italics"], {"regular": "whole", "italics": "part"}
        )
        assert "regular" not in result
        assert result == {"italics": "part"}

    def test_scopes_keep_regular_when_alone(self):
        result = normalize_text_style_label_scopes(["regular"], None)
        assert result == {"regular": "whole"}
