"""Tests for the bounded, immutable document matcher."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.matching import (
    ArtifactRange,
    MatchDocument,
    MatchLine,
    MatchPage,
    MatchPolicy,
    MatchQuarantineReason,
    MatchToken,
    PgdpContinuation,
    PgdpContinuationBoundary,
    PgdpContinuationDecision,
    PgdpLogicalCandidate,
    PgdpMarkerEvidence,
    PgdpPhysicalFragment,
    PgdpRound,
    PgdpRoundContinuationEvidence,
    canonical_relation_path_bytes,
    match_documents,
)
from pdomain_book_tools.typography import (
    OcrTokenRef,
    align_tokens,
    build_comparison_view,
)


def _document(identifier: str, *texts: str) -> MatchDocument:
    """Build a one-line document with stable physical token IDs."""
    return MatchDocument(
        document_id=identifier,
        pages=(
            MatchPage(
                page_id=f"{identifier}-page",
                lines=(
                    MatchLine(
                        line_id=f"{identifier}-line",
                        tokens=tuple(
                            MatchToken(token_id=f"{identifier}-{index}", text=text)
                            for index, text in enumerate(texts)
                        ),
                    ),
                ),
            ),
        ),
    )


def _policy(**updates: object) -> MatchPolicy:
    """Return a deterministic policy suitable for small matcher examples."""
    values: dict[str, object] = {
        "policy_id": "test-policy",
        "version": "1",
        "low_margin_threshold": 0.5,
        "max_merge_size": 2,
        "max_state_count": 100,
        "max_transition_count": 100,
    }
    values.update(updates)
    return MatchPolicy.model_validate(values)


def _ranges(text: str, *, offset: int) -> tuple[ArtifactRange, ...]:
    """Build exact ASCII fixture ranges for a physical PGDP fragment."""
    return tuple(
        ArtifactRange(
            artifact_id="f2",
            artifact_sha256="a" * 64,
            byte_start=offset + index,
            byte_end=offset + index + 1,
            grapheme_start=offset + index,
            grapheme_end=offset + index + 1,
        )
        for index, _character in enumerate(text)
    )


def _resolved_continuation(
    *, left_token_id: str | None = None, right_token_id: str | None = None
) -> PgdpContinuation:
    """Return one validated physical PGDP continuation for matcher projection."""
    resolved_left_token_id = left_token_id or "source-0"
    resolved_right_token_id = right_token_id or "source-1"
    left = PgdpPhysicalFragment(
        text="Tam--",
        token_id=resolved_left_token_id,
        page_id="source-page",
        line_id="source-line",
        grapheme_ranges=_ranges("Tam--", offset=0),
    )
    right = PgdpPhysicalFragment(
        text="far",
        token_id=resolved_right_token_id,
        page_id="source-page",
        line_id="source-line",
        grapheme_ranges=_ranges("far", offset=6),
    )
    markers = PgdpMarkerEvidence(
        round=PgdpRound.F2,
        marker_ranges=(
            ArtifactRange(
                artifact_id="f2",
                artifact_sha256="a" * 64,
                byte_start=5,
                byte_end=6,
                grapheme_start=5,
                grapheme_end=6,
            ),
        ),
    )
    return PgdpContinuation(
        left_fragment=left,
        right_fragment=right,
        boundary=PgdpContinuationBoundary.LINE,
        marker_evidence=(markers,),
        round_evidence=(
            PgdpRoundContinuationEvidence(
                round=PgdpRound.F2,
                left_fragment=left,
                right_fragment=right,
                marker_evidence=markers,
            ),
        ),
        logical_candidates=(
            PgdpLogicalCandidate(
                text="Tam--far",
                decision=PgdpContinuationDecision.PRESERVE_PUNCTUATION,
            ),
        ),
        decision=PgdpContinuationDecision.PRESERVE_PUNCTUATION,
    )


def _pgdp_source_document() -> MatchDocument:
    """Return physical source tokens with the exact continuation fragment ranges."""
    return MatchDocument(
        document_id="source",
        pages=(
            MatchPage(
                page_id="source-page",
                lines=(
                    MatchLine(
                        line_id="source-line",
                        tokens=(
                            MatchToken(
                                token_id="source-0",
                                text="Tam--",
                                artifact_ranges=_ranges("Tam--", offset=0),
                            ),
                            MatchToken(
                                token_id="source-1",
                                text="far",
                                artifact_ranges=_ranges("far", offset=6),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )


def _inline_repeated_continuation(*, reverse_left_ranges: bool) -> PgdpContinuation:
    """Return an inline repeated-character continuation with exact fragment ranges."""
    token_ranges = _ranges("aaaa*", offset=0)
    left_ranges = token_ranges[:2]
    if reverse_left_ranges:
        left_ranges = tuple(reversed(left_ranges))
    left = PgdpPhysicalFragment(
        text="aa",
        token_id="source-0",
        page_id="source-page",
        line_id="source-line",
        grapheme_ranges=left_ranges,
    )
    right = PgdpPhysicalFragment(
        text="aa",
        token_id="source-0",
        page_id="source-page",
        line_id="source-line",
        grapheme_ranges=token_ranges[2:4],
    )
    markers = PgdpMarkerEvidence(round=PgdpRound.F2, marker_ranges=(token_ranges[4],))
    return PgdpContinuation(
        left_fragment=left,
        right_fragment=right,
        boundary=PgdpContinuationBoundary.SAME_LINE,
        marker_evidence=(markers,),
        round_evidence=(
            PgdpRoundContinuationEvidence(
                round=PgdpRound.F2,
                left_fragment=left,
                right_fragment=right,
                marker_evidence=markers,
            ),
        ),
        logical_candidates=(
            PgdpLogicalCandidate(
                text="aaaa",
                decision=PgdpContinuationDecision.JOIN_WITHOUT_HYPHEN,
            ),
        ),
        decision=PgdpContinuationDecision.JOIN_WITHOUT_HYPHEN,
    )


def _inline_repeated_source_document() -> MatchDocument:
    """Return one physical token retaining both inline continuation fragments."""
    return MatchDocument(
        document_id="source",
        pages=(
            MatchPage(
                page_id="source-page",
                lines=(
                    MatchLine(
                        line_id="source-line",
                        tokens=(
                            MatchToken(
                                token_id="source-0",
                                text="aaaa*",
                                artifact_ranges=_ranges("aaaa*", offset=0),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )


def test_matches_exact_tokens_without_mutating_documents() -> None:
    source = _document("source", "Saint")
    target = _document("target", "SAINT")

    graph = match_documents(source, target, policy=_policy())

    assert graph.accepted
    assert graph.best_alternative.total_cost == 0
    relation = graph.best_alternative.relations[0]
    assert relation.kind.value == "one_to_one"
    assert relation.source_token_ids == ("source-0",)
    assert relation.target_token_ids == ("target-0",)
    assert source.pages[0].lines[0].tokens[0].text == "Saint"
    assert target.pages[0].lines[0].tokens[0].text == "SAINT"


def test_matches_one_source_token_to_physical_target_fragments() -> None:
    graph = match_documents(
        _document("source", "firefly"),
        _document("target", "fire", "fly"),
        policy=_policy(),
    )

    relation = graph.best_alternative.relations[0]
    assert graph.accepted
    assert relation.kind.value == "source_to_fragments"
    assert relation.target_token_ids == ("target-0", "target-1")


def test_matches_pgdp_logical_candidate_to_unchanged_physical_fragments() -> None:
    """The PGDP decoder owns marker evidence; the engine only keeps token IDs."""
    source = _document("pgdp-logical", "simplicity")
    target = _document("ocr-physical", "sim", "plicity")

    graph = match_documents(source, target, policy=_policy())

    relation = graph.best_alternative.relations[0]
    assert graph.accepted
    assert relation.kind.value == "source_to_fragments"
    assert relation.target_token_ids == ("ocr-physical-0", "ocr-physical-1")
    assert target.pages[0].lines[0].tokens[0].text == "sim"
    assert target.pages[0].lines[0].tokens[1].text == "plicity"


def test_matches_physical_source_fragments_to_one_target_token() -> None:
    graph = match_documents(
        _document("source", "fire", "fly"),
        _document("target", "firefly"),
        policy=_policy(),
    )

    relation = graph.best_alternative.relations[0]
    assert graph.accepted
    assert relation.kind.value == "sources_to_one"
    assert relation.source_token_ids == ("source-0", "source-1")


def test_retains_source_only_relation() -> None:
    graph = match_documents(
        _document("source", "alpha"), _document("target"), policy=_policy()
    )

    assert graph.accepted
    assert graph.best_alternative.relations[0].kind.value == "source_only"


def test_retains_target_only_relation() -> None:
    graph = match_documents(
        _document("source"), _document("target", "beta"), policy=_policy()
    )

    assert graph.accepted
    assert graph.best_alternative.relations[0].kind.value == "target_only"


def test_quarantines_equal_cost_paths_and_uses_canonical_path_order() -> None:
    graph = match_documents(
        _document("source", "a"),
        _document("target", "b"),
        policy=_policy(
            substitution_cost=2,
            source_only_cost=1,
            target_only_cost=1,
        ),
    )

    assert not graph.accepted
    assert MatchQuarantineReason.TIE in graph.quarantine_reasons
    assert graph.runner_up_alternative is not None
    assert graph.runner_up_margin == 0
    assert graph.best_alternative.relations[0].kind.value == "one_to_one"


def test_quarantines_a_margin_below_the_policy_threshold() -> None:
    graph = match_documents(
        _document("source", "a"),
        _document("target", "a"),
        policy=_policy(low_margin_threshold=3, source_only_cost=1, target_only_cost=1),
    )

    assert not graph.accepted
    assert MatchQuarantineReason.LOW_MARGIN in graph.quarantine_reasons
    assert graph.runner_up_margin == 2


def test_quarantines_when_state_bound_is_exhausted() -> None:
    graph = match_documents(
        _document("source", "a", "b"),
        _document("target", "a", "b"),
        policy=_policy(max_state_count=1),
    )

    assert not graph.accepted
    assert MatchQuarantineReason.STATE_LIMIT_EXHAUSTED in graph.quarantine_reasons
    assert graph.best_alternative.relations
    assert graph.search_evidence is not None
    assert graph.search_evidence.partial_paths[0].source_tokens_consumed == 0
    assert graph.search_evidence.partial_paths[0].target_tokens_consumed == 0


def test_stops_state_search_at_the_configured_bound() -> None:
    """A state cap must stop traversal instead of scanning the entire grid."""
    token_texts = tuple("a" for _ in range(80))
    graph = match_documents(
        _document("source", *token_texts),
        _document("target", *token_texts),
        policy=_policy(max_state_count=2, max_transition_count=10_000),
    )

    assert not graph.accepted
    assert MatchQuarantineReason.STATE_LIMIT_EXHAUSTED in graph.quarantine_reasons
    assert graph.search_evidence is not None
    assert graph.search_evidence.state_count == 2
    assert graph.search_evidence.state_iteration_count <= 2
    assert graph.search_evidence.transition_count <= 3
    assert graph.search_evidence.partial_paths


def test_quarantines_when_transition_bound_is_exhausted() -> None:
    graph = match_documents(
        _document("source", "a"),
        _document("target", "a"),
        policy=_policy(max_transition_count=1),
    )

    assert not graph.accepted
    assert MatchQuarantineReason.TRANSITION_LIMIT_EXHAUSTED in graph.quarantine_reasons
    assert graph.search_evidence is not None
    assert graph.search_evidence.best_complete_path is not None
    assert graph.best_alternative.relations == (
        graph.search_evidence.best_complete_path.relations
    )


def test_preserves_punctuation_and_unicode_grapheme_ranges() -> None:
    graph = match_documents(
        _document("source", "Tam--far", "cafe\u0301"),
        _document("target", "Tam--far", "café"),
        policy=_policy(),
    )

    assert graph.accepted
    second_relation = graph.best_alternative.relations[1]
    assert tuple(
        (
            operation.kind.value,
            operation.source_grapheme_range,
            operation.target_grapheme_range,
        )
        for operation in second_relation.operations
    ) == (
        ("match", (0, 1), (0, 1)),
        ("match", (1, 2), (1, 2)),
        ("match", (2, 3), (2, 3)),
        ("match", (3, 4), (3, 4)),
    )
    assert second_relation.source_comparison is not None
    assert second_relation.target_comparison is not None
    assert second_relation.source_comparison.source_grapheme_map == (
        (0,),
        (1,),
        (2,),
        (3,),
    )
    assert second_relation.target_comparison.source_grapheme_map == (
        (0,),
        (1,),
        (2,),
        (3,),
    )


def test_emits_deterministic_grapheme_edits_and_ranks_minor_differences() -> None:
    minor = match_documents(
        _document("source", "cat"), _document("target", "cut"), policy=_policy()
    )
    unrelated = match_documents(
        _document("source", "cat"), _document("target", "dog"), policy=_policy()
    )

    minor_relation = minor.best_alternative.relations[0]
    assert tuple(operation.kind.value for operation in minor_relation.operations) == (
        "match",
        "substitution",
        "match",
    )
    assert minor.best_alternative.total_cost == 1
    assert unrelated.best_alternative.total_cost == 3
    assert minor.best_alternative.total_cost < unrelated.best_alternative.total_cost


def test_grapheme_edit_kinds_match_typography_alignment_for_a_simple_token() -> None:
    graph = match_documents(
        _document("source", "cat"), _document("target", "cut"), policy=_policy()
    )
    typography_alignment = align_tokens(
        build_comparison_view("cat", casefold_all=True),
        (
            OcrTokenRef(
                token_id="target-token",
                text="cut",
                confidence=0.99,
                bbox=BoundingBox.from_ltrb(0, 0, 1, 1, is_normalized=False),
                line_id="target-line",
                grapheme_start=0,
                grapheme_end=3,
                alignment_id="unbound",
            ),
        ),
    )

    assert tuple(
        operation.kind.value
        for operation in graph.best_alternative.relations[0].operations
    ) == tuple(edit.kind.value for edit in typography_alignment.best_path)


def test_projects_casefold_expansions_to_raw_grapheme_ranges() -> None:
    graph = match_documents(
        _document("source", "ß"), _document("target", "ss"), policy=_policy()
    )

    relation = graph.best_alternative.relations[0]
    assert graph.accepted
    assert len(relation.operations) == 1
    assert relation.operations[0].kind.value == "match"
    assert relation.operations[0].source_grapheme_range == (0, 1)
    assert relation.operations[0].target_grapheme_range == (0, 2)


def test_attaches_resolved_pgdp_continuation_to_its_physical_relation() -> None:
    continuation = _resolved_continuation()
    original = continuation.model_dump(mode="json")

    graph = match_documents(
        _pgdp_source_document(),
        _document("target", "Tam--far"),
        policy=_policy(),
        pgdp_continuations=(continuation,),
    )

    relation = graph.best_alternative.relations[0]
    assert graph.accepted
    assert (
        relation.continuation_references[0].continuation_id
        == continuation.continuation_id
    )
    assert relation.continuation_references[0].relation_source_token_ids == (
        "source-0",
        "source-1",
    )
    reference = relation.continuation_references[0]
    assert reference.evidence_artifact_id == "pgdp-continuations"
    assert reference.evidence_artifact_path == (
        f"continuations/{continuation.continuation_id}.json"
    )
    assert len(reference.evidence_sha256) == 64
    assert continuation.model_dump(mode="json") == original


@pytest.mark.parametrize(
    ("decision", "logical_text"),
    [
        (PgdpContinuationDecision.JOIN_WITHOUT_HYPHEN, "Tamfar"),
        (PgdpContinuationDecision.KEEP_HYPHEN, "Tam--far"),
        (PgdpContinuationDecision.LEAVE_SEPARATE, "Tam-- far"),
        (PgdpContinuationDecision.PRESERVE_PUNCTUATION, "Tam--far"),
    ],
)
def test_resolved_pgdp_decision_selects_its_declared_logical_candidate(
    decision: PgdpContinuationDecision, logical_text: str
) -> None:
    continuation = _resolved_continuation().model_copy(
        update={
            "logical_candidates": (
                PgdpLogicalCandidate(text=logical_text, decision=decision),
            ),
            "decision": decision,
        }
    )

    graph = match_documents(
        _pgdp_source_document(),
        _document("target", logical_text),
        policy=_policy(),
        pgdp_continuations=(continuation,),
    )

    relation = graph.best_alternative.relations[0]
    assert graph.accepted
    assert relation.continuation_references[0].decision == decision.value
    assert graph.best_alternative.total_cost == 0
    assert any(
        warning.startswith(f"PGDP logical candidate {continuation.continuation_id}")
        for warning in relation.warnings
    )


def test_quarantines_incompatible_pgdp_continuation_evidence() -> None:
    graph = match_documents(
        _pgdp_source_document(),
        _document("target", "Tam--far"),
        policy=_policy(),
        pgdp_continuations=(
            _resolved_continuation(left_token_id="other-0", right_token_id="other-1"),
        ),
    )

    assert not graph.accepted
    assert MatchQuarantineReason.INCOMPATIBLE_CONTINUATION in graph.quarantine_reasons


def test_quarantines_pgdp_continuation_with_fragment_text_mismatch() -> None:
    continuation = _resolved_continuation().model_copy(
        update={
            "left_fragment": PgdpPhysicalFragment(
                text="Tum--",
                token_id="source-0",
                page_id="source-page",
                line_id="source-line",
                grapheme_ranges=_ranges("Tum--", offset=0),
            )
        }
    )

    graph = match_documents(
        _pgdp_source_document(),
        _document("target", "Tam--far"),
        policy=_policy(),
        pgdp_continuations=(continuation,),
    )

    assert not graph.accepted
    assert MatchQuarantineReason.INCOMPATIBLE_CONTINUATION in graph.quarantine_reasons
    assert graph.best_alternative.relations[0].continuation_references == ()


def test_quarantines_pgdp_continuation_with_fragment_range_mismatch() -> None:
    continuation = _resolved_continuation().model_copy(
        update={
            "right_fragment": PgdpPhysicalFragment(
                text="far",
                token_id="source-1",
                page_id="source-page",
                line_id="source-line",
                grapheme_ranges=_ranges("far", offset=20),
            )
        }
    )

    graph = match_documents(
        _pgdp_source_document(),
        _document("target", "Tam--far"),
        policy=_policy(),
        pgdp_continuations=(continuation,),
    )

    assert not graph.accepted
    assert MatchQuarantineReason.INCOMPATIBLE_CONTINUATION in graph.quarantine_reasons
    assert graph.best_alternative.relations[0].continuation_references == ()


def test_attaches_contiguous_inline_fragment_range_slices() -> None:
    graph = match_documents(
        _inline_repeated_source_document(),
        _document("target", "aaaa"),
        policy=_policy(),
        pgdp_continuations=(_inline_repeated_continuation(reverse_left_ranges=False),),
    )

    assert graph.accepted
    assert len(graph.best_alternative.relations[0].continuation_references) == 1


def test_quarantines_reversed_repeated_character_fragment_ranges() -> None:
    graph = match_documents(
        _inline_repeated_source_document(),
        _document("target", "aaaa"),
        policy=_policy(),
        pgdp_continuations=(_inline_repeated_continuation(reverse_left_ranges=True),),
    )

    assert not graph.accepted
    assert MatchQuarantineReason.INCOMPATIBLE_CONTINUATION in graph.quarantine_reasons
    assert graph.best_alternative.relations[0].continuation_references == ()


def test_quarantines_ambiguous_pgdp_continuation_evidence() -> None:
    continuation = _resolved_continuation().model_copy(
        update={
            "logical_candidates": (
                PgdpLogicalCandidate(
                    text="Tamfar",
                    decision=PgdpContinuationDecision.JOIN_WITHOUT_HYPHEN,
                ),
                PgdpLogicalCandidate(
                    text="Tam--far",
                    decision=PgdpContinuationDecision.PRESERVE_PUNCTUATION,
                ),
            ),
            "decision": PgdpContinuationDecision.AMBIGUOUS,
        }
    )

    graph = match_documents(
        _document("source", "Tam--", "far"),
        _document("target", "Tam--far"),
        policy=_policy(),
        pgdp_continuations=(continuation,),
    )

    assert not graph.accepted
    assert MatchQuarantineReason.UNRESOLVED_CONTINUATION in graph.quarantine_reasons


def test_rejects_unknown_normalization_policy_label() -> None:
    with pytest.raises(ValidationError):
        _policy(comparison_normalization="unknown")


def test_repeated_runs_keep_best_and_runner_order_canonical() -> None:
    source = _document("source", "a")
    target = _document("target", "b")
    policy = _policy(substitution_cost=2, source_only_cost=1, target_only_cost=1)

    first = match_documents(source, target, policy=policy)
    second = match_documents(source, target, policy=policy)

    assert first.to_json_bytes() == second.to_json_bytes()
    assert first.runner_up_alternative is not None
    assert first.best_alternative.total_cost <= first.runner_up_alternative.total_cost
    assert canonical_relation_path_bytes(
        first.best_alternative.relations
    ) < canonical_relation_path_bytes(first.runner_up_alternative.relations)
