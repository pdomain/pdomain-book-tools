from __future__ import annotations

import hashlib
import math

import pytest
from pydantic import ValidationError

from pdomain_book_tools.geometry import BoundingBox
from pdomain_book_tools.typography import (
    ConfidenceTier,
    KnowledgeState,
    LabelSource,
    OcrTokenRef,
    SourceSlice,
    StyleLabel,
    StyleSpan,
)
from pdomain_book_tools.typography.alignment import (
    AlignmentConfig,
    AlignmentEdit,
    AlignmentEditKind,
    ProjectedBoundingBox,
    ProjectedStyleSpan,
    TokenAlignmentResult,
    align_tokens,
    project_style_span,
    project_token_ranges,
)
from pdomain_book_tools.typography.normalization import build_comparison_view

_SOURCE_SHA256 = "a" * 64
_TARGET_SHA256 = "b" * 64


def _token(
    token_id: str,
    text: str,
    *,
    start: int = 0,
    end: int = 1,
    x: int = 0,
) -> OcrTokenRef:
    return OcrTokenRef(
        token_id=token_id,
        text=text,
        confidence=0.99,
        bbox=BoundingBox.from_ltrb(x, 0, x + 10, 10, is_normalized=False),
        line_id="line-1",
        grapheme_start=start,
        grapheme_end=end,
        alignment_id="unbound",
    )


def test_alignment_maps_punctuation_into_a_separate_ocr_token() -> None:
    result = align_tokens(
        build_comparison_view("Hello,"),
        (_token("word", "Hello"), _token("punctuation", ",", x=10)),
        config=AlignmentConfig(low_margin_threshold=0.5),
    )

    assert result.accepted is True
    assert result.best_cost == 0
    assert result.token_source_ranges == ((0, 5), (5, 6))


def test_alignment_uses_compact_backpointer_state_for_page_scale_input() -> None:
    text = "a" * 240
    result = align_tokens(build_comparison_view(text), (_token("page", text),))

    assert result.best_cost == 0
    assert result.dp_state_count <= 6 * (len(text) + 1) ** 2


def test_alignment_maps_one_source_word_to_two_ocr_words() -> None:
    result = align_tokens(
        build_comparison_view("cannot"),
        (_token("can", "can"), _token("not", "not", x=10)),
    )

    assert result.accepted is True
    assert result.token_source_ranges == ((0, 3), (3, 6))


def test_alignment_maps_two_source_words_to_one_ocr_word() -> None:
    result = align_tokens(
        build_comparison_view("to-day"),
        (_token("today", "today"),),
    )

    assert result.accepted is True
    assert any(
        edit.kind is AlignmentEditKind.SOURCE_ONLY_DELETION for edit in result.best_path
    )
    assert result.token_source_ranges == ((0, 6),)


def test_alignment_handles_a_page_break_fragment_and_a_ligature() -> None:
    fragment = align_tokens(
        build_comparison_view("overcoat"),
        (_token("over", "over"), _token("coat", "coat", x=10)),
    )
    ligature = align_tokens(
        build_comparison_view("office"),
        (_token("office", "oﬃce"),),
    )

    assert fragment.token_source_ranges == ((0, 4), (4, 8))
    assert ligature.accepted is False
    assert any(
        edit.kind is AlignmentEditKind.SUBSTITUTION for edit in ligature.best_path
    )


def test_alignment_retains_deleted_source_characters_and_combining_marks() -> None:
    deleted = align_tokens(build_comparison_view("colour"), (_token("color", "color"),))
    combining = align_tokens(build_comparison_view("e\u0301"), (_token("accent", "é"),))

    assert any(
        edit.kind is AlignmentEditKind.SOURCE_ONLY_DELETION
        for edit in deleted.best_path
    )
    assert combining.best_cost == 0
    assert combining.token_source_ranges == ((0, 1),)


def test_alignment_uses_small_caps_case_and_validated_letter_spacing_views() -> None:
    small_caps = align_tokens(
        build_comparison_view("THE", small_caps_case_insensitive=True),
        (_token("the", "the"),),
    )
    letter_spaced = align_tokens(
        build_comparison_view("T H E", letter_spaced_ranges=((0, 5),)),
        (_token("the", "THE"),),
    )

    assert small_caps.best_cost == 0
    assert letter_spaced.best_cost == 0


def test_alignment_rejects_an_ambiguous_low_margin_path_and_serializes_threshold() -> (
    None
):
    result = align_tokens(
        build_comparison_view("aa"),
        (_token("a", "a"),),
        config=AlignmentConfig(low_margin_threshold=1.0),
    )
    evidence = result.to_evidence(
        alignment_id="alignment-1",
        source_artifact_sha256=_SOURCE_SHA256,
        target_artifact_sha256=_TARGET_SHA256,
    )

    assert result.runner_up_margin == 0
    assert result.accepted is False
    assert evidence.low_margin_threshold == 1.0
    assert evidence.accepted is False


def test_rejected_alignment_cannot_project_ocr_token_ranges() -> None:
    tokens = (_token("a", "a"),)
    result = align_tokens(
        build_comparison_view("aa"),
        tokens,
        config=AlignmentConfig(low_margin_threshold=1.0),
    )

    with pytest.raises(ValueError, match="accepted"):
        project_token_ranges(tokens, result, alignment_id="alignment-1")


def test_case_fold_expansion_uses_canonical_ocr_grapheme_coordinates() -> None:
    result = align_tokens(
        build_comparison_view("SS", small_caps_case_insensitive=True),
        (_token("sharp-s", "ẞ"),),
    )
    evidence = result.to_evidence(
        alignment_id="alignment-1",
        source_artifact_sha256=_SOURCE_SHA256,
        target_artifact_sha256=_TARGET_SHA256,
    )

    assert result.target_grapheme_count == 1
    assert tuple(edit.target_range for edit in result.best_path) == ((0, 1), (0, 1))
    assert evidence.target_range == (0, 1)


def test_combining_equivalence_uses_one_canonical_ocr_grapheme_coordinate() -> None:
    result = align_tokens(
        build_comparison_view("e\u0301"),
        (_token("accent", "é"),),
    )

    assert result.target_grapheme_count == 1
    assert result.best_path[0].target_range == (0, 1)


def test_target_soft_hyphen_removal_keeps_canonical_ocr_count() -> None:
    result = align_tokens(
        build_comparison_view("cooperate"),
        (_token("word", "co\u00adoperate"),),
    )
    evidence = result.to_evidence(
        alignment_id="alignment-1",
        source_artifact_sha256=_SOURCE_SHA256,
        target_artifact_sha256=_TARGET_SHA256,
    )

    assert result.target_grapheme_count == 10
    assert evidence.target_range == (0, 10)
    assert all(edit.target_range[1] <= 10 for edit in result.best_path)


def test_target_case_fold_expansion_preserves_ocr_token_boundaries() -> None:
    result = align_tokens(
        build_comparison_view("SSx", small_caps_case_insensitive=True),
        (_token("sharp-s", "ẞ"), _token("x", "x", x=10)),
    )

    assert result.target_grapheme_count == 2
    assert result.token_source_ranges == ((0, 2), (2, 3))
    assert all(edit.target_range[1] <= 2 for edit in result.best_path)


def test_alignment_retains_an_explicit_unaligned_target_only_token() -> None:
    tokens = (_token("source", "a"), _token("inserted", "x", x=10))

    result = align_tokens(build_comparison_view("a"), tokens)
    bound = project_token_ranges(tokens, result, alignment_id="alignment-1")

    assert result.token_source_ranges == ((0, 1), None)
    assert tuple(token.token_id for token in bound) == ("source",)


def test_alignment_evidence_rejects_an_accepted_low_margin_record() -> None:
    result = align_tokens(
        build_comparison_view("aa"),
        (_token("a", "a"),),
        config=AlignmentConfig(low_margin_threshold=1.0),
    )
    evidence_data = result.to_evidence(
        alignment_id="alignment-1",
        source_artifact_sha256=_SOURCE_SHA256,
        target_artifact_sha256=_TARGET_SHA256,
    ).model_dump()
    evidence_data["accepted"] = True

    with pytest.raises(ValidationError, match="accepted"):
        type(
            result.to_evidence(
                alignment_id="alignment-1",
                source_artifact_sha256=_SOURCE_SHA256,
                target_artifact_sha256=_TARGET_SHA256,
            )
        ).model_validate(evidence_data)


def test_alignment_evidence_is_deterministic_and_binds_projected_tokens() -> None:
    source = build_comparison_view("The green overcoat")
    tokens = (
        _token("the", "The"),
        _token("green", "green", x=10),
        _token("overcoat", "overcoat", x=20),
    )
    result = align_tokens(source, tokens)

    evidence = result.to_evidence(
        alignment_id="alignment-1",
        source_artifact_sha256=_SOURCE_SHA256,
        target_artifact_sha256=_TARGET_SHA256,
    )
    bound = project_token_ranges(tokens, result, alignment_id=evidence.alignment_id)

    assert result.to_json_bytes() == result.to_json_bytes()
    assert tuple(token.alignment_id for token in bound) == ("alignment-1",) * 3
    assert tuple((token.grapheme_start, token.grapheme_end) for token in bound) == (
        (0, 3),
        (4, 9),
        (10, 18),
    )
    assert hashlib.sha256(result.to_json_bytes()).hexdigest()


def test_style_projection_splits_at_word_boxes_but_keeps_stable_source_span_id() -> (
    None
):
    source_span = StyleSpan(
        label=StyleLabel.ITALIC,
        start=1,
        end=5,
        state=KnowledgeState.POSITIVE,
        label_source=LabelSource.F2,
        confidence_tier=ConfidenceTier.GOLD,
        source_slices=(
            SourceSlice(artifact_sha256=_SOURCE_SHA256, byte_start=1, byte_end=5),
        ),
        rule_ref="f2:i",
        semantic_reason=None,
        warnings=(),
    )
    tokens = (
        _token("first", "abc", start=0, end=3),
        _token("second", "def", start=3, end=6, x=10),
    )

    projections = project_style_span(
        source_span,
        source_span_id="span-italic-1",
        tokens=tokens,
    )

    assert [(item.token_id, item.source_range) for item in projections] == [
        ("first", (1, 3)),
        ("second", (3, 5)),
    ]
    assert {item.source_span_id for item in projections} == {"span-italic-1"}
    assert all(item.source_span == source_span for item in projections)
    assert all(item.character_boxes is None for item in projections)


def test_projected_style_span_keeps_optional_character_boxes() -> None:
    source_span = StyleSpan(
        label=StyleLabel.ITALIC,
        start=0,
        end=1,
        state=KnowledgeState.POSITIVE,
        label_source=LabelSource.F2,
        confidence_tier=ConfidenceTier.GOLD,
        source_slices=(
            SourceSlice(artifact_sha256=_SOURCE_SHA256, byte_start=0, byte_end=1),
        ),
        rule_ref=None,
        semantic_reason=None,
        warnings=(),
    )
    box = BoundingBox.from_ltrb(0, 0, 10, 10, is_normalized=False)

    projected = ProjectedStyleSpan(
        source_span_id="span-italic-1",
        source_span=source_span,
        token_id="word-1",
        source_range=(0, 1),
        crop_bbox=box,
        character_boxes=(box,),
    )

    assert projected.character_boxes is not None
    assert projected.to_json_bytes() == projected.to_json_bytes()


def test_projected_style_span_accepts_a_list_of_optional_character_boxes() -> None:
    source_span = StyleSpan(
        label=StyleLabel.ITALIC,
        start=0,
        end=1,
        state=KnowledgeState.POSITIVE,
        label_source=LabelSource.F2,
        confidence_tier=ConfidenceTier.GOLD,
        source_slices=(
            SourceSlice(artifact_sha256=_SOURCE_SHA256, byte_start=0, byte_end=1),
        ),
        rule_ref=None,
        semantic_reason=None,
        warnings=(),
    )
    box = BoundingBox.from_ltrb(0, 0, 10, 10, is_normalized=False)

    projected = ProjectedStyleSpan(
        source_span_id="span-italic-1",
        source_span=source_span,
        token_id="word-1",
        source_range=(0, 1),
        crop_bbox=box,
        character_boxes=[box],
    )

    assert projected.character_boxes is not None


def test_projected_style_span_snapshots_input_boxes_immutably() -> None:
    source_span = StyleSpan(
        label=StyleLabel.ITALIC,
        start=0,
        end=1,
        state=KnowledgeState.POSITIVE,
        label_source=LabelSource.F2,
        confidence_tier=ConfidenceTier.GOLD,
        source_slices=(
            SourceSlice(artifact_sha256=_SOURCE_SHA256, byte_start=0, byte_end=1),
        ),
        rule_ref=None,
        semantic_reason=None,
        warnings=(),
    )
    input_box = BoundingBox.from_ltrb(0, 0, 10, 10, is_normalized=False)
    projected = ProjectedStyleSpan(
        source_span_id="span-italic-1",
        source_span=source_span,
        token_id="word-1",
        source_range=(0, 1),
        crop_bbox=input_box,
        character_boxes=(input_box,),
    )

    input_box.top_left = input_box.bottom_right

    assert isinstance(projected.crop_bbox, ProjectedBoundingBox)
    assert projected.crop_bbox.left == 0
    assert projected.character_boxes is not None
    assert isinstance(projected.character_boxes[0], ProjectedBoundingBox)
    assert projected.character_boxes[0].left == 0
    with pytest.raises(ValidationError):
        projected.crop_bbox.left = 99


def test_projected_style_span_rejects_nonfinite_or_mixed_coordinate_boxes() -> None:
    source_span = StyleSpan(
        label=StyleLabel.ITALIC,
        start=0,
        end=1,
        state=KnowledgeState.POSITIVE,
        label_source=LabelSource.F2,
        confidence_tier=ConfidenceTier.GOLD,
        source_slices=(
            SourceSlice(artifact_sha256=_SOURCE_SHA256, byte_start=0, byte_end=1),
        ),
        rule_ref=None,
        semantic_reason=None,
        warnings=(),
    )
    pixel_box = BoundingBox.from_ltrb(0, 0, 10, 10, is_normalized=False)
    normalized_box = BoundingBox.from_ltrb(0, 0, 1, 1, is_normalized=True)
    nonfinite_box = BoundingBox.from_ltrb(0, 0, math.inf, 10, is_normalized=False)

    with pytest.raises(ValidationError, match="coordinate"):
        ProjectedStyleSpan(
            source_span_id="span-italic-1",
            source_span=source_span,
            token_id="word-1",
            source_range=(0, 1),
            crop_bbox=pixel_box,
            character_boxes=(normalized_box,),
        )
    with pytest.raises(ValidationError, match="finite"):
        ProjectedStyleSpan(
            source_span_id="span-italic-1",
            source_span=source_span,
            token_id="word-1",
            source_range=(0, 1),
            crop_bbox=nonfinite_box,
        )


@pytest.mark.parametrize(
    ("left", "top", "right", "bottom", "is_normalized"),
    [
        (-1.0, 0.0, 1.0, 1.0, False),
        (0.0, 0.0, 1.1, 1.0, True),
    ],
)
def test_projected_bounding_box_rejects_invalid_coordinate_space_bounds(
    left: float,
    top: float,
    right: float,
    bottom: float,
    is_normalized: bool,
) -> None:
    with pytest.raises(ValidationError, match="coordinate"):
        ProjectedBoundingBox(
            left=left,
            top=top,
            right=right,
            bottom=bottom,
            is_normalized=is_normalized,
        )


@pytest.mark.parametrize(
    ("kind", "source_range", "target_range"),
    [
        (AlignmentEditKind.MATCH, (0, 0), (0, 1)),
        (AlignmentEditKind.SUBSTITUTION, (0, 1), (0, 0)),
        (AlignmentEditKind.SOURCE_ONLY_DELETION, (0, 1), (0, 1)),
        (AlignmentEditKind.TARGET_ONLY_INSERTION, (0, 1), (0, 1)),
    ],
)
def test_alignment_edit_rejects_ranges_incompatible_with_its_kind(
    kind: AlignmentEditKind,
    source_range: tuple[int, int],
    target_range: tuple[int, int],
) -> None:
    with pytest.raises(ValidationError, match="must"):
        AlignmentEdit(
            kind=kind,
            source_range=source_range,
            target_range=target_range,
        )


def test_alignment_result_rejects_forged_out_of_range_or_overlapping_ranges() -> None:
    result = align_tokens(build_comparison_view("ab"), (_token("word", "ab"),))
    out_of_range = result.model_dump()
    out_of_range["best_path"][0]["target_range"] = (0, 3)
    overlapping = result.model_dump()
    overlapping["best_path"][1]["source_range"] = (0, 2)

    with pytest.raises(ValidationError, match="target_range"):
        TokenAlignmentResult.model_validate(out_of_range)
    with pytest.raises(ValidationError, match="overlap"):
        TokenAlignmentResult.model_validate(overlapping)


def test_alignment_result_rejects_forged_out_of_range_token_projection() -> None:
    result = align_tokens(build_comparison_view("ab"), (_token("word", "ab"),))
    forged = result.model_dump()
    forged["token_source_ranges"] = [(0, 3)]

    with pytest.raises(ValidationError, match="token_source_ranges"):
        TokenAlignmentResult.model_validate(forged)


def test_alignment_result_rejects_forged_empty_token_projection() -> None:
    result = align_tokens(build_comparison_view("ab"), (_token("word", "ab"),))
    forged = result.model_dump()
    forged["token_source_ranges"] = [(1, 1)]

    with pytest.raises(ValidationError, match="token_source_ranges"):
        TokenAlignmentResult.model_validate(forged)


def test_alignment_preserves_a_token_boundary_before_a_combining_mark() -> None:
    result = align_tokens(
        build_comparison_view("e\u0301"),
        (_token("base", "e"), _token("mark", "\u0301", x=10)),
    )

    assert result.target_grapheme_count == 2
    assert result.token_source_ranges == ((0, 1), None)


def test_alignment_evidence_rejects_a_negative_runner_up_margin() -> None:
    result = align_tokens(
        build_comparison_view("aa"),
        (_token("a", "a"),),
        config=AlignmentConfig(low_margin_threshold=1.0),
    )
    evidence_data = result.to_evidence(
        alignment_id="alignment-1",
        source_artifact_sha256=_SOURCE_SHA256,
        target_artifact_sha256=_TARGET_SHA256,
    ).model_dump()
    evidence_data["margin"] = -1.0

    with pytest.raises(ValidationError, match="margin"):
        type(
            result.to_evidence(
                alignment_id="alignment-1",
                source_artifact_sha256=_SOURCE_SHA256,
                target_artifact_sha256=_TARGET_SHA256,
            )
        ).model_validate(evidence_data)
