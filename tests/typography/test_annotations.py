from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from pdomain_book_tools.typography import (
    ConfidenceTier,
    KnowledgeState,
    LabelSource,
    StyleLabel,
    StyleSpan,
    TypographyAnnotations,
)


def _span(label: StyleLabel, start: int, end: int) -> StyleSpan:
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


def test_reviewed_regular_annotations_are_empty_but_present() -> None:
    annotations = TypographyAnnotations(spans=[])

    assert annotations.spans == ()
    assert annotations.whole_word_labels == ()


def test_whole_word_labels_are_derived_from_complete_coverage() -> None:
    annotations = TypographyAnnotations(
        grapheme_count=4,
        spans=[
            _span(StyleLabel.ITALIC, 0, 2),
            _span(StyleLabel.ITALIC, 2, 4),
            _span(StyleLabel.BOLD, 1, 4),
        ],
    )

    assert annotations.whole_word_labels == (StyleLabel.ITALIC,)


def test_inconsistent_whole_word_labels_are_rejected() -> None:
    with pytest.raises(ValidationError, match="whole_word_labels"):
        TypographyAnnotations(
            grapheme_count=3,
            spans=[_span(StyleLabel.ITALIC, 0, 2)],
            whole_word_labels=[StyleLabel.ITALIC],
        )


def test_annotation_metadata_round_trips_byte_stably() -> None:
    annotations = TypographyAnnotations(
        grapheme_count=1,
        spans=[_span(StyleLabel.BOLD, 0, 1)],
        source=LabelSource.HUMAN,
        model_version=None,
        confidence=0.95,
        calibration_version="calibration-1",
        reviewer_id="reviewer-1",
        reviewed_at=datetime(2026, 8, 21, 20, tzinfo=UTC),
        warnings=["reviewed"],
    )

    encoded = annotations.to_json_bytes()

    assert TypographyAnnotations.from_json_bytes(encoded).to_json_bytes() == encoded


def test_annotation_confidence_must_be_a_probability() -> None:
    with pytest.raises(ValidationError, match="confidence"):
        TypographyAnnotations(spans=[], confidence=-0.1)
