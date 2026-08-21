from __future__ import annotations

import pytest

from pdomain_book_tools.typography import (
    ConfidenceTier,
    KnowledgeState,
    LabelSource,
    StyleLabel,
)


def test_style_labels_match_the_canonical_taxonomy() -> None:
    assert {label.value for label in StyleLabel} == {
        "italic",
        "bold",
        "small_caps",
        "letter_spaced",
        "superscript",
        "subscript",
        "underline",
        "font_blackletter",
        "font_antiqua",
        "font_upright_in_italic",
        "font_other_reviewed",
    }


def test_regular_is_not_a_positive_style_label() -> None:
    with pytest.raises(ValueError, match="regular"):
        StyleLabel("regular")


@pytest.mark.parametrize(
    ("enum_type", "values"),
    [
        (
            KnowledgeState,
            {"positive", "verified_negative", "unknown", "conflict"},
        ),
        (
            LabelSource,
            {"f2", "gutenberg_html", "se_computed_css", "human", "synthetic"},
        ),
        (ConfidenceTier, {"gold", "silver", "bronze", "quarantine"}),
    ],
)
def test_controlled_vocabularies_reject_unknown_values(
    enum_type: type[KnowledgeState] | type[LabelSource] | type[ConfidenceTier],
    values: set[str],
) -> None:
    assert {member.value for member in enum_type} == values
    with pytest.raises(ValueError, match="not-a-canonical-value"):
        enum_type("not-a-canonical-value")
