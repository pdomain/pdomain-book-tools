"""Bounded deterministic matching over immutable physical token documents."""

from __future__ import annotations

from dataclasses import dataclass

from pdomain_book_tools.matching.models import (
    MatchAlternative,
    MatchDocument,
    MatchGraph,
    MatchOperation,
    MatchOperationKind,
    MatchPolicy,
    MatchQuarantineReason,
    MatchRelation,
    MatchRelationKind,
    MatchToken,
    canonical_relation_path_bytes,
)
from pdomain_book_tools.typography.normalization import build_comparison_view
from pdomain_book_tools.typography.spans import split_graphemes


@dataclass(frozen=True)
class _Path:
    """One complete-or-partial monotonic path retained by the dynamic program."""

    total_cost: float
    relations: tuple[MatchRelation, ...]

    @property
    def canonical_bytes(self) -> bytes:
        """Return the policy's stable secondary ordering key."""
        return canonical_relation_path_bytes(self.relations)


def match_documents(
    source_document: MatchDocument,
    target_document: MatchDocument,
    *,
    policy: MatchPolicy,
) -> MatchGraph:
    """Match two token documents without changing either document or its IDs.

    The bounded search retains two paths at each monotonic token-index state.
    A resource cap returns a complete but quarantined fallback, rather than a
    partially searched result or an accepted greedy path.
    """
    source_tokens = _ordered_tokens(source_document)
    target_tokens = _ordered_tokens(target_document)
    cells: dict[tuple[int, int], list[_Path]] = {(0, 0): [_Path(0.0, ())]}
    state_count = 1
    transition_count = 0
    state_exhausted = False
    transition_exhausted = False
    source_count = len(source_tokens)
    target_count = len(target_tokens)

    for source_index in range(source_count + 1):
        for target_index in range(target_count + 1):
            current = tuple(cells.get((source_index, target_index), ()))
            for path in current:
                for relation, cost, next_state in _transitions(
                    source_tokens,
                    target_tokens,
                    source_index=source_index,
                    target_index=target_index,
                    policy=policy,
                ):
                    if transition_count >= policy.max_transition_count:
                        transition_exhausted = True
                        break
                    transition_count += 1
                    if next_state not in cells:
                        if state_count >= policy.max_state_count:
                            state_exhausted = True
                            continue
                        cells[next_state] = []
                        state_count += 1
                    _retain_path(
                        cells[next_state],
                        _Path(
                            total_cost=path.total_cost + cost,
                            relations=(*path.relations, relation),
                        ),
                    )
                if transition_exhausted:
                    break
            if transition_exhausted:
                break
        if transition_exhausted:
            break

    complete = tuple(cells.get((source_count, target_count), ()))
    if state_exhausted or transition_exhausted or not complete:
        reasons = _exhaustion_reasons(
            state_exhausted=state_exhausted,
            transition_exhausted=transition_exhausted,
        )
        return _quarantined_fallback(
            source_document,
            target_document,
            policy=policy,
            source_tokens=source_tokens,
            target_tokens=target_tokens,
            reasons=reasons,
            state_count=state_count,
            transition_count=transition_count,
        )

    best = complete[0]
    runner_up = complete[1] if len(complete) > 1 else None
    return _graph_from_paths(
        source_document,
        target_document,
        policy=policy,
        best=best,
        runner_up=runner_up,
        warnings=(
            f"bounded matcher evaluated {state_count} states and {transition_count} transitions",
        ),
    )


def _ordered_tokens(document: MatchDocument) -> tuple[MatchToken, ...]:
    """Return the immutable tokens in declared physical reading order."""
    return tuple(
        token for page in document.pages for line in page.lines for token in line.tokens
    )


def _transitions(
    source_tokens: tuple[MatchToken, ...],
    target_tokens: tuple[MatchToken, ...],
    *,
    source_index: int,
    target_index: int,
    policy: MatchPolicy,
) -> tuple[tuple[MatchRelation, float, tuple[int, int]], ...]:
    """Return every bounded monotonic relation from one token-index state."""
    transitions: list[tuple[MatchRelation, float, tuple[int, int]]] = []
    source_remaining = len(source_tokens) - source_index
    target_remaining = len(target_tokens) - target_index
    if source_remaining and target_remaining:
        relation, cost = _paired_relation(
            (source_tokens[source_index],),
            (target_tokens[target_index],),
            policy=policy,
        )
        transitions.append((relation, cost, (source_index + 1, target_index + 1)))
        for target_size in range(2, min(policy.max_merge_size, target_remaining) + 1):
            relation, cost = _paired_relation(
                (source_tokens[source_index],),
                target_tokens[target_index : target_index + target_size],
                policy=policy,
            )
            transitions.append(
                (relation, cost, (source_index + 1, target_index + target_size))
            )
        for source_size in range(2, min(policy.max_merge_size, source_remaining) + 1):
            relation, cost = _paired_relation(
                source_tokens[source_index : source_index + source_size],
                (target_tokens[target_index],),
                policy=policy,
            )
            transitions.append(
                (relation, cost, (source_index + source_size, target_index + 1))
            )
    if source_remaining:
        token = source_tokens[source_index]
        transitions.append(
            (
                _source_only_relation(token),
                policy.source_only_cost,
                (source_index + 1, target_index),
            )
        )
    if target_remaining:
        token = target_tokens[target_index]
        transitions.append(
            (
                _target_only_relation(token),
                policy.target_only_cost,
                (source_index, target_index + 1),
            )
        )
    return tuple(transitions)


def _paired_relation(
    source_tokens: tuple[MatchToken, ...],
    target_tokens: tuple[MatchToken, ...],
    *,
    policy: MatchPolicy,
) -> tuple[MatchRelation, float]:
    """Create one bounded paired relation and its deterministic local cost."""
    source_text = "".join(token.text for token in source_tokens)
    target_text = "".join(token.text for token in target_tokens)
    source_view = build_comparison_view(source_text, casefold_all=True)
    target_view = build_comparison_view(target_text, casefold_all=True)
    exact = source_view.graphemes == target_view.graphemes
    relation_kind = _paired_kind(source_tokens, target_tokens)
    source_grapheme_count = len(split_graphemes(source_text))
    target_grapheme_count = len(split_graphemes(target_text))
    operation = MatchOperation(
        kind=(MatchOperationKind.MATCH if exact else MatchOperationKind.SUBSTITUTION),
        source_grapheme_range=(0, source_grapheme_count),
        target_grapheme_range=(0, target_grapheme_count),
    )
    return (
        MatchRelation(
            kind=relation_kind,
            source_token_ids=tuple(token.token_id for token in source_tokens),
            target_token_ids=tuple(token.token_id for token in target_tokens),
            operations=(operation,),
            warnings=(
                f"comparison normalization {policy.comparison_normalization_version}",
            ),
        ),
        policy.exact_match_cost if exact else policy.substitution_cost,
    )


def _paired_kind(
    source_tokens: tuple[MatchToken, ...], target_tokens: tuple[MatchToken, ...]
) -> MatchRelationKind:
    """Return the only valid relation kind for a bounded paired transition."""
    if len(source_tokens) == 1 and len(target_tokens) == 1:
        return MatchRelationKind.ONE_TO_ONE
    if len(source_tokens) == 1:
        return MatchRelationKind.SOURCE_TO_FRAGMENTS
    return MatchRelationKind.SOURCES_TO_ONE


def _source_only_relation(token: MatchToken) -> MatchRelation:
    """Return one physical source-only relation without changing its token."""
    grapheme_count = len(split_graphemes(token.text))
    return MatchRelation(
        kind=MatchRelationKind.SOURCE_ONLY,
        source_token_ids=(token.token_id,),
        target_token_ids=(),
        operations=(
            MatchOperation(
                kind=MatchOperationKind.SOURCE_ONLY_DELETION,
                source_grapheme_range=(0, grapheme_count),
                target_grapheme_range=(0, 0),
            ),
        ),
    )


def _target_only_relation(token: MatchToken) -> MatchRelation:
    """Return one physical target-only relation without changing its token."""
    grapheme_count = len(split_graphemes(token.text))
    return MatchRelation(
        kind=MatchRelationKind.TARGET_ONLY,
        source_token_ids=(),
        target_token_ids=(token.token_id,),
        operations=(
            MatchOperation(
                kind=MatchOperationKind.TARGET_ONLY_INSERTION,
                source_grapheme_range=(0, 0),
                target_grapheme_range=(0, grapheme_count),
            ),
        ),
    )


def _retain_path(paths: list[_Path], candidate: _Path) -> None:
    """Keep the two distinct paths with the policy's deterministic ordering."""
    if any(path.canonical_bytes == candidate.canonical_bytes for path in paths):
        return
    paths.append(candidate)
    paths.sort(key=lambda path: (path.total_cost, path.canonical_bytes))
    del paths[2:]


def _exhaustion_reasons(
    *,
    state_exhausted: bool,
    transition_exhausted: bool,
) -> tuple[MatchQuarantineReason, ...]:
    """Return explicit reasons why bounded search cannot be accepted."""
    reasons: list[MatchQuarantineReason] = []
    if state_exhausted:
        reasons.append(MatchQuarantineReason.STATE_LIMIT_EXHAUSTED)
    if transition_exhausted:
        reasons.append(MatchQuarantineReason.TRANSITION_LIMIT_EXHAUSTED)
    return tuple(reasons)


def _quarantined_fallback(
    source_document: MatchDocument,
    target_document: MatchDocument,
    *,
    policy: MatchPolicy,
    source_tokens: tuple[MatchToken, ...],
    target_tokens: tuple[MatchToken, ...],
    reasons: tuple[MatchQuarantineReason, ...],
    state_count: int,
    transition_count: int,
) -> MatchGraph:
    """Return a complete review-only path when the bounded search is exhausted."""
    relations = tuple(_source_only_relation(token) for token in source_tokens) + tuple(
        _target_only_relation(token) for token in target_tokens
    )
    total_cost = (
        len(source_tokens) * policy.source_only_cost
        + len(target_tokens) * policy.target_only_cost
    )
    return MatchGraph(
        source_document=source_document,
        target_document=target_document,
        policy=policy,
        best_alternative=MatchAlternative(
            total_cost=total_cost,
            relations=relations,
            warnings=("bounded search fallback",),
        ),
        runner_up_alternative=None,
        runner_up_margin=None,
        accepted=False,
        quarantine_reasons=reasons,
        warnings=(
            f"bounded matcher stopped after {state_count} states and {transition_count} transitions",
        ),
    )


def _graph_from_paths(
    source_document: MatchDocument,
    target_document: MatchDocument,
    *,
    policy: MatchPolicy,
    best: _Path,
    runner_up: _Path | None,
    warnings: tuple[str, ...],
) -> MatchGraph:
    """Build a canonical graph and quarantine close alternatives before review."""
    best_alternative = MatchAlternative(
        total_cost=best.total_cost,
        relations=best.relations,
    )
    runner_up_alternative = (
        None
        if runner_up is None
        else MatchAlternative(
            total_cost=runner_up.total_cost,
            relations=runner_up.relations,
        )
    )
    margin = None if runner_up is None else runner_up.total_cost - best.total_cost
    reasons = _ambiguity_reasons(margin, policy=policy)
    return MatchGraph(
        source_document=source_document,
        target_document=target_document,
        policy=policy,
        best_alternative=best_alternative,
        runner_up_alternative=runner_up_alternative,
        runner_up_margin=margin,
        accepted=not reasons,
        quarantine_reasons=reasons,
        warnings=warnings,
    )


def _ambiguity_reasons(
    margin: float | None, *, policy: MatchPolicy
) -> tuple[MatchQuarantineReason, ...]:
    """Return review reasons for equal or insufficiently separated paths."""
    if margin is None:
        return ()
    reasons: list[MatchQuarantineReason] = []
    if margin == 0:
        reasons.append(MatchQuarantineReason.TIE)
    if margin < policy.low_margin_threshold:
        reasons.append(MatchQuarantineReason.LOW_MARGIN)
    return tuple(reasons)
