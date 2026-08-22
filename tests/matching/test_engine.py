"""Tests for the bounded, immutable document matcher."""

from __future__ import annotations

from pdomain_book_tools.matching import (
    MatchDocument,
    MatchLine,
    MatchPage,
    MatchPolicy,
    MatchQuarantineReason,
    MatchToken,
    match_documents,
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


def test_quarantines_when_transition_bound_is_exhausted() -> None:
    graph = match_documents(
        _document("source", "a"),
        _document("target", "a"),
        policy=_policy(max_transition_count=1),
    )

    assert not graph.accepted
    assert MatchQuarantineReason.TRANSITION_LIMIT_EXHAUSTED in graph.quarantine_reasons


def test_preserves_punctuation_and_unicode_grapheme_ranges() -> None:
    graph = match_documents(
        _document("source", "Tam--far", "cafe\u0301"),
        _document("target", "Tam--far", "café"),
        policy=_policy(),
    )

    assert graph.accepted
    second_relation = graph.best_alternative.relations[1]
    operation = second_relation.operations[0]
    assert operation.source_grapheme_range == (0, 4)
    assert operation.target_grapheme_range == (0, 4)
