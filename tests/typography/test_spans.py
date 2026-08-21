from __future__ import annotations

import pytest
from pydantic import ValidationError

from pdomain_book_tools.typography import (
    GRAPHEME_SEGMENTATION_VERSION,
    ConfidenceTier,
    KnowledgeState,
    LabelSource,
    SourceSlice,
    StyleLabel,
    StyleSpan,
    TypographySpans,
    split_graphemes,
)

_ARTIFACT_SHA256 = "a" * 64


def _style_span(label: StyleLabel, start: int, end: int) -> StyleSpan:
    return StyleSpan(
        label=label,
        start=start,
        end=end,
        state=KnowledgeState.POSITIVE,
        label_source=LabelSource.HUMAN,
        confidence_tier=ConfidenceTier.GOLD,
        source_slices=(),
        rule_ref=None,
        semantic_reason=None,
        warnings=(),
    )


def test_overlapping_spans_remain_independent() -> None:
    spans = TypographySpans(
        grapheme_count=5,
        spans=[
            _style_span(StyleLabel.ITALIC, 0, 5),
            _style_span(StyleLabel.BOLD, 1, 4),
        ],
    )

    assert spans.labels_at(2) == {StyleLabel.ITALIC, StyleLabel.BOLD}


def test_multiple_spans_for_the_same_label_remain_independent() -> None:
    spans = TypographySpans(
        grapheme_count=5,
        spans=[
            _style_span(StyleLabel.ITALIC, 0, 1),
            _style_span(StyleLabel.ITALIC, 3, 5),
        ],
    )

    assert spans.spans[0] != spans.spans[1]
    assert spans.labels_at(1) == set()


@pytest.mark.parametrize(
    "span",
    [
        _style_span(StyleLabel.ITALIC, 0, 2),
        _style_span(StyleLabel.ITALIC, 1, 2),
    ],
)
def test_span_end_cannot_exceed_grapheme_count(span: StyleSpan) -> None:
    with pytest.raises(ValidationError, match="grapheme_count"):
        TypographySpans(grapheme_count=1, spans=[span])


@pytest.mark.parametrize(
    ("start", "end"),
    [(-1, 1), (0, 0), (2, 1)],
)
def test_span_requires_a_nonempty_half_open_range(start: int, end: int) -> None:
    with pytest.raises(ValidationError, match="half-open"):
        _style_span(StyleLabel.BOLD, start, end)


def test_empty_spans_are_valid_for_reviewed_regular_text() -> None:
    spans = TypographySpans(grapheme_count=0, spans=[])

    assert spans.spans == ()


def test_grapheme_count_cannot_be_negative() -> None:
    with pytest.raises(ValidationError, match="nonnegative"):
        TypographySpans(grapheme_count=-1, spans=[])


def test_source_slice_requires_a_nonempty_half_open_byte_range() -> None:
    with pytest.raises(ValidationError, match="half-open"):
        SourceSlice(
            artifact_sha256=_ARTIFACT_SHA256,
            byte_start=4,
            byte_end=4,
        )


def test_source_slice_requires_an_artifact_identity() -> None:
    with pytest.raises(ValidationError, match="artifact_sha256"):
        SourceSlice.model_validate({"byte_start": 0, "byte_end": 1})


def test_indices_reject_coercion() -> None:
    with pytest.raises(ValidationError, match="int_type"):
        SourceSlice.model_validate(
            {
                "artifact_sha256": _ARTIFACT_SHA256,
                "byte_start": "0",
                "byte_end": 1,
            }
        )
    with pytest.raises(ValidationError, match="int_type"):
        TypographySpans.model_validate({"grapheme_count": True, "spans": []})


def test_validated_span_collection_cannot_be_mutated() -> None:
    spans = TypographySpans(
        grapheme_count=1,
        spans=[_style_span(StyleLabel.ITALIC, 0, 1)],
    )

    assert isinstance(spans.spans, tuple)
    assert not hasattr(spans.spans, "append")


def test_style_span_requires_state_and_evidence() -> None:
    with pytest.raises(ValidationError, match="state"):
        StyleSpan.model_validate({"label": StyleLabel.ITALIC, "start": 0, "end": 1})


def test_grapheme_segmentation_handles_combining_marks_and_zwj_sequences() -> None:
    assert GRAPHEME_SEGMENTATION_VERSION
    assert split_graphemes("e\u0301\U0001f469\u200d\U0001f4bb") == (
        "e\u0301",
        "\U0001f469\u200d\U0001f4bb",
    )


def test_labels_at_rejects_an_out_of_range_index() -> None:
    spans = TypographySpans(grapheme_count=1, spans=[])

    with pytest.raises(IndexError, match="grapheme index"):
        spans.labels_at(1)


def test_canonical_json_round_trip_is_byte_stable() -> None:
    spans = TypographySpans(
        grapheme_count=3,
        spans=[
            _style_span(StyleLabel.SMALL_CAPS, 0, 3),
            _style_span(StyleLabel.BOLD, 1, 2),
        ],
    )

    encoded = spans.to_json_bytes()
    decoded = TypographySpans.from_json_bytes(encoded)

    assert decoded == spans
    assert decoded.to_json_bytes() == encoded


def test_unknown_serialized_label_is_rejected() -> None:
    span = _style_span(StyleLabel.ITALIC, 0, 1).model_dump(mode="json")
    span["label"] = "regular"

    with pytest.raises(ValidationError, match="regular"):
        TypographySpans.model_validate({"grapheme_count": 1, "spans": [span]})
