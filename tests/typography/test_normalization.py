from __future__ import annotations

import pytest
from pydantic import ValidationError

from pdomain_book_tools.typography.normalization import (
    ComparisonOperationKind,
    build_comparison_view,
)


def test_canonical_equivalent_combining_grapheme_keeps_source_map() -> None:
    view = build_comparison_view("e\u0301")

    assert view.graphemes == ("é",)
    assert view.source_grapheme_map == ((0,),)
    assert view.operations[0].kind is ComparisonOperationKind.UNICODE_CANONICAL


def test_quotes_and_dashes_use_approved_equivalents_only() -> None:
    view = build_comparison_view("\u201cword\u201d\u2014\u2018x\u2019")

    assert "".join(view.graphemes) == "\"word\"-'x'"
    assert [operation.kind for operation in view.operations] == [
        ComparisonOperationKind.QUOTE_EQUIVALENCE,
        ComparisonOperationKind.QUOTE_EQUIVALENCE,
        ComparisonOperationKind.DASH_EQUIVALENCE,
        ComparisonOperationKind.QUOTE_EQUIVALENCE,
        ComparisonOperationKind.QUOTE_EQUIVALENCE,
    ]


def test_small_caps_case_comparison_is_explicit() -> None:
    unchanged = build_comparison_view("SMALL")
    folded = build_comparison_view("SMALL", small_caps_ranges=((0, 5),))

    assert unchanged.text == "SMALL"
    assert folded.text == "small"
    assert folded.operations[0].kind is ComparisonOperationKind.SMALL_CAPS_CASE_FOLDED


def test_small_caps_case_folding_resegments_an_expanding_grapheme() -> None:
    view = build_comparison_view("STRAßE", small_caps_ranges=((0, 6),))

    assert view.graphemes == ("s", "t", "r", "a", "s", "s", "e")
    assert view.source_grapheme_map == ((0,), (1,), (2,), (3,), (4,), (4,), (5,))


def test_soft_hyphen_is_removed_only_from_comparison_view() -> None:
    view = build_comparison_view("co\u00adoperate")

    assert view.text == "cooperate"
    assert view.source_text == "co\u00adoperate"
    assert view.operations[0].kind is ComparisonOperationKind.SOFT_HYPHEN_REMOVED
    assert view.source_grapheme_map == (
        (0,),
        (1,),
        (3,),
        (4,),
        (5,),
        (6,),
        (7,),
        (8,),
        (9,),
    )


def test_letter_space_removal_requires_a_validated_explicit_range() -> None:
    view = build_comparison_view("H E L L O", letter_spaced_ranges=((0, 9),))

    assert view.text == "HELLO"
    assert [operation.kind for operation in view.operations] == [
        ComparisonOperationKind.LETTER_SPACE_REMOVED,
    ]
    assert view.source_grapheme_map == ((0,), (2,), (4,), (6,), (8,))


def test_letter_space_removal_rejects_an_ordinary_space() -> None:
    with pytest.raises(ValueError, match="alternate"):
        build_comparison_view("two words", letter_spaced_ranges=((0, 8),))


def test_normalization_view_and_operation_map_are_immutable_and_canonical() -> None:
    view = build_comparison_view("A\u00adB")

    with pytest.raises(ValidationError):
        view.graphemes += ("x",)

    assert view.to_json_bytes() == view.to_json_bytes()


def test_comparison_view_rejects_a_nonmonotonic_source_map() -> None:
    with pytest.raises(ValidationError, match="monotonic"):
        build_comparison_view("ab").model_validate(
            {
                "source_text": "ab",
                "graphemes": ["a", "b"],
                "source_grapheme_map": [[1], [0]],
                "operations": [],
            }
        )
