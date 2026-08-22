"""Bounded deterministic matching over immutable physical token documents."""

from __future__ import annotations

from dataclasses import dataclass

from pdomain_book_tools.matching.models import (
    ArtifactRange,
    MatchAlternative,
    MatchComparisonNormalization,
    MatchContinuationReference,
    MatchDocument,
    MatchGraph,
    MatchOperation,
    MatchOperationKind,
    MatchPolicy,
    MatchQuarantineReason,
    MatchRelation,
    MatchRelationKind,
    MatchSearchEvidence,
    MatchSearchPathEvidence,
    MatchTieBreakRule,
    MatchToken,
    canonical_relation_path_bytes,
)
from pdomain_book_tools.matching.pgdp_continuations import (
    PgdpContinuation,
    PgdpContinuationDecision,
)
from pdomain_book_tools.typography.normalization import (
    ComparisonView,
    build_comparison_view,
)
from pdomain_book_tools.typography.spans import split_graphemes


@dataclass(frozen=True)
class _Path:
    """One complete-or-partial monotonic path retained by the dynamic program."""

    total_cost: float
    relations: tuple[MatchRelation, ...]


@dataclass(frozen=True)
class _ContinuationInput:
    """Validated PGDP adapter data kept outside the source-neutral graph model."""

    continuation_id: str
    decision: str
    left_fragment_token_id: str
    right_fragment_token_id: str
    left_fragment_text: str
    right_fragment_text: str
    left_fragment_grapheme_ranges: tuple[ArtifactRange, ...]
    right_fragment_grapheme_ranges: tuple[ArtifactRange, ...]


def match_documents(
    source_document: MatchDocument,
    target_document: MatchDocument,
    *,
    policy: MatchPolicy,
    pgdp_continuations: tuple[PgdpContinuation, ...] = (),
) -> MatchGraph:
    """Match two token documents without changing either document or its IDs.

    The bounded search retains two paths at each monotonic token-index state.
    A resource cap returns a complete but quarantined fallback, rather than a
    partially searched result or an accepted greedy path.
    """
    source_tokens = _ordered_tokens(source_document)
    target_tokens = _ordered_tokens(target_document)
    continuation_inputs, continuation_reasons, continuation_warnings = (
        _continuation_inputs(pgdp_continuations)
    )
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
                    continuation_inputs=continuation_inputs,
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
                        policy=policy,
                    )
                if transition_exhausted:
                    break
            if transition_exhausted:
                break
        if transition_exhausted:
            break

    complete = tuple(cells.get((source_count, target_count), ()))
    search_evidence = _search_evidence(
        cells,
        source_token_count=source_count,
        target_token_count=target_count,
        state_count=state_count,
        transition_count=transition_count,
        policy=policy,
    )
    if state_exhausted or transition_exhausted:
        reasons = _exhaustion_reasons(
            state_exhausted=state_exhausted,
            transition_exhausted=transition_exhausted,
        )
        if complete:
            return _graph_from_paths(
                source_document,
                target_document,
                policy=policy,
                best=complete[0],
                runner_up=complete[1] if len(complete) > 1 else None,
                quarantine_reasons=(*reasons, *continuation_reasons),
                continuation_inputs=continuation_inputs,
                search_evidence=search_evidence,
                warnings=(
                    f"bounded matcher stopped after {state_count} states and {transition_count} transitions",
                    *continuation_warnings,
                ),
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
            search_evidence=search_evidence,
            continuation_reasons=continuation_reasons,
            continuation_warnings=continuation_warnings,
            continuation_inputs=continuation_inputs,
        )

    if not complete:
        return _quarantined_fallback(
            source_document,
            target_document,
            policy=policy,
            source_tokens=source_tokens,
            target_tokens=target_tokens,
            reasons=(MatchQuarantineReason.TRANSITION_LIMIT_EXHAUSTED,),
            state_count=state_count,
            transition_count=transition_count,
            search_evidence=search_evidence,
            continuation_reasons=continuation_reasons,
            continuation_warnings=continuation_warnings,
            continuation_inputs=continuation_inputs,
        )

    best = complete[0]
    runner_up = complete[1] if len(complete) > 1 else None
    return _graph_from_paths(
        source_document,
        target_document,
        policy=policy,
        best=best,
        runner_up=runner_up,
        quarantine_reasons=continuation_reasons,
        continuation_inputs=continuation_inputs,
        search_evidence=search_evidence,
        warnings=(
            f"bounded matcher evaluated {state_count} states and {transition_count} transitions",
            *continuation_warnings,
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
    continuation_inputs: tuple[_ContinuationInput, ...],
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
            continuation_inputs=continuation_inputs,
        )
        transitions.append((relation, cost, (source_index + 1, target_index + 1)))
        for target_size in range(2, min(policy.max_merge_size, target_remaining) + 1):
            relation, cost = _paired_relation(
                (source_tokens[source_index],),
                target_tokens[target_index : target_index + target_size],
                policy=policy,
                continuation_inputs=continuation_inputs,
            )
            transitions.append(
                (relation, cost, (source_index + 1, target_index + target_size))
            )
        for source_size in range(2, min(policy.max_merge_size, source_remaining) + 1):
            relation, cost = _paired_relation(
                source_tokens[source_index : source_index + source_size],
                (target_tokens[target_index],),
                policy=policy,
                continuation_inputs=continuation_inputs,
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
    continuation_inputs: tuple[_ContinuationInput, ...],
) -> tuple[MatchRelation, float]:
    """Create one bounded paired relation and its deterministic local cost."""
    source_text = "".join(token.text for token in source_tokens)
    target_text = "".join(token.text for token in target_tokens)
    source_view = _comparison_view(source_text, policy=policy)
    target_view = _comparison_view(target_text, policy=policy)
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
            source_comparison=source_view,
            target_comparison=target_view,
            continuation_references=_relation_continuation_references(
                source_tokens,
                target_tokens,
                continuation_inputs=continuation_inputs,
            ),
            warnings=(f"comparison normalization {policy.comparison_normalization}",),
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


def _retain_path(paths: list[_Path], candidate: _Path, *, policy: MatchPolicy) -> None:
    """Keep the two distinct paths with the policy's deterministic ordering."""
    if any(
        _path_key(path, policy=policy) == _path_key(candidate, policy=policy)
        for path in paths
    ):
        return
    paths.append(candidate)
    paths.sort(key=lambda path: _path_key(path, policy=policy))
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
    search_evidence: MatchSearchEvidence,
    continuation_reasons: tuple[MatchQuarantineReason, ...],
    continuation_warnings: tuple[str, ...],
    continuation_inputs: tuple[_ContinuationInput, ...],
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
        quarantine_reasons=_unique_reasons(
            (
                *reasons,
                *continuation_reasons,
                *(
                    (MatchQuarantineReason.INCOMPATIBLE_CONTINUATION,)
                    if continuation_inputs
                    else ()
                ),
            )
        ),
        search_evidence=search_evidence,
        warnings=(
            f"bounded matcher stopped after {state_count} states and {transition_count} transitions",
            *continuation_warnings,
        ),
    )


def _graph_from_paths(
    source_document: MatchDocument,
    target_document: MatchDocument,
    *,
    policy: MatchPolicy,
    best: _Path,
    runner_up: _Path | None,
    quarantine_reasons: tuple[MatchQuarantineReason, ...],
    continuation_inputs: tuple[_ContinuationInput, ...],
    search_evidence: MatchSearchEvidence,
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
    reasons = _unique_reasons(
        (
            *quarantine_reasons,
            *_missing_continuation_reasons(
                best,
                runner_up,
                continuation_inputs=continuation_inputs,
            ),
            *_ambiguity_reasons(margin, policy=policy),
        )
    )
    return MatchGraph(
        source_document=source_document,
        target_document=target_document,
        policy=policy,
        best_alternative=best_alternative,
        runner_up_alternative=runner_up_alternative,
        runner_up_margin=margin,
        accepted=not reasons,
        quarantine_reasons=reasons,
        search_evidence=search_evidence,
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


def _comparison_view(text: str, *, policy: MatchPolicy) -> ComparisonView:
    """Build the policy-selected source-preserving comparison view."""
    if (
        policy.comparison_normalization
        is MatchComparisonNormalization.UNICODE_CASEFOLD_V1
    ):
        return build_comparison_view(text, casefold_all=True)
    msg = f"unsupported comparison normalization {policy.comparison_normalization}"
    raise ValueError(msg)


def _path_key(path: _Path, *, policy: MatchPolicy) -> tuple[float, bytes]:
    """Return the policy-selected total-cost and deterministic tie-break key."""
    if policy.tie_break_rule is MatchTieBreakRule.CANONICAL_RELATION_PATH_BYTES_V1:
        return path.total_cost, canonical_relation_path_bytes(path.relations)
    msg = f"unsupported tie-break rule {policy.tie_break_rule}"
    raise ValueError(msg)


def _continuation_inputs(
    continuations: tuple[PgdpContinuation, ...],
) -> tuple[
    tuple[_ContinuationInput, ...],
    tuple[MatchQuarantineReason, ...],
    tuple[str, ...],
]:
    """Adapt resolved PGDP data while leaving graph contracts source-neutral."""
    inputs: list[_ContinuationInput] = []
    reasons: list[MatchQuarantineReason] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    for continuation in continuations:
        continuation_id = continuation.continuation_id
        if continuation_id is None:
            msg = "validated PGDP continuation must have a continuation_id"
            raise ValueError(msg)
        if continuation_id in seen_ids:
            reasons.append(MatchQuarantineReason.INCOMPATIBLE_CONTINUATION)
            warnings.append(f"duplicate PGDP continuation {continuation_id}")
            continue
        seen_ids.add(continuation_id)
        if (
            continuation.decision is PgdpContinuationDecision.AMBIGUOUS
            or continuation.quarantine_reasons
        ):
            reasons.append(MatchQuarantineReason.UNRESOLVED_CONTINUATION)
            warnings.append(f"unresolved PGDP continuation {continuation_id}")
            continue
        inputs.append(
            _ContinuationInput(
                continuation_id=continuation_id,
                decision=continuation.decision.value,
                left_fragment_token_id=continuation.left_fragment.token_id,
                right_fragment_token_id=continuation.right_fragment.token_id,
                left_fragment_text=continuation.left_fragment.text,
                right_fragment_text=continuation.right_fragment.text,
                left_fragment_grapheme_ranges=(
                    continuation.left_fragment.grapheme_ranges
                ),
                right_fragment_grapheme_ranges=(
                    continuation.right_fragment.grapheme_ranges
                ),
            )
        )
    return tuple(inputs), _unique_reasons(tuple(reasons)), tuple(warnings)


def _relation_continuation_references(
    source_tokens: tuple[MatchToken, ...],
    target_tokens: tuple[MatchToken, ...],
    *,
    continuation_inputs: tuple[_ContinuationInput, ...],
) -> tuple[MatchContinuationReference, ...]:
    """Attach PGDP provenance when both physical fragments share one relation side."""
    source_ids = tuple(token.token_id for token in source_tokens)
    target_ids = tuple(token.token_id for token in target_tokens)
    source_id_set = frozenset(source_ids)
    target_id_set = frozenset(target_ids)
    references: list[MatchContinuationReference] = []
    for continuation in continuation_inputs:
        fragment_ids = frozenset(
            (
                continuation.left_fragment_token_id,
                continuation.right_fragment_token_id,
            )
        )
        source_matches = fragment_ids.issubset(source_id_set) and (
            _continuation_matches_tokens(continuation, source_tokens)
        )
        target_matches = fragment_ids.issubset(target_id_set) and (
            _continuation_matches_tokens(continuation, target_tokens)
        )
        if not source_matches and not target_matches:
            continue
        references.append(
            MatchContinuationReference(
                continuation_id=continuation.continuation_id,
                decision=continuation.decision,
                left_fragment_token_id=continuation.left_fragment_token_id,
                right_fragment_token_id=continuation.right_fragment_token_id,
                left_fragment_grapheme_ranges=(
                    continuation.left_fragment_grapheme_ranges
                ),
                right_fragment_grapheme_ranges=(
                    continuation.right_fragment_grapheme_ranges
                ),
                relation_source_token_ids=source_ids,
                relation_target_token_ids=target_ids,
            )
        )
    return tuple(references)


def _continuation_matches_tokens(
    continuation: _ContinuationInput, tokens: tuple[MatchToken, ...]
) -> bool:
    """Validate both physical fragments against exact token text and ranges."""
    tokens_by_id = {token.token_id: token for token in tokens}
    left_token = tokens_by_id.get(continuation.left_fragment_token_id)
    right_token = tokens_by_id.get(continuation.right_fragment_token_id)
    if left_token is None or right_token is None:
        return False
    return _fragment_matches_token(
        continuation.left_fragment_text,
        continuation.left_fragment_grapheme_ranges,
        left_token,
    ) and _fragment_matches_token(
        continuation.right_fragment_text,
        continuation.right_fragment_grapheme_ranges,
        right_token,
    )


def _fragment_matches_token(
    fragment_text: str,
    fragment_ranges: tuple[ArtifactRange, ...],
    token: MatchToken,
) -> bool:
    """Return whether a continuation fragment exactly projects onto one token."""
    fragment_graphemes = split_graphemes(fragment_text)
    token_graphemes = split_graphemes(token.text)
    if len(fragment_graphemes) != len(fragment_ranges):
        return False
    if len(token_graphemes) != len(token.artifact_ranges):
        return False
    token_graphemes_by_range = {
        artifact_range: grapheme
        for grapheme, artifact_range in zip(
            token_graphemes, token.artifact_ranges, strict=True
        )
    }
    return all(
        token_graphemes_by_range.get(artifact_range) == grapheme
        for grapheme, artifact_range in zip(
            fragment_graphemes, fragment_ranges, strict=True
        )
    )


def _search_evidence(
    cells: dict[tuple[int, int], list[_Path]],
    *,
    source_token_count: int,
    target_token_count: int,
    state_count: int,
    transition_count: int,
    policy: MatchPolicy,
) -> MatchSearchEvidence:
    """Preserve the best complete and partial dynamic-program paths."""
    complete = tuple(cells.get((source_token_count, target_token_count), ()))
    partial_candidates: list[tuple[tuple[int, int], _Path]] = []
    for state, paths in cells.items():
        if state == (source_token_count, target_token_count):
            continue
        partial_candidates.extend((state, path) for path in paths)
    partial_candidates.sort(key=lambda item: _path_key(item[1], policy=policy))
    partial_paths = tuple(
        _search_path_evidence(path, state=state)
        for state, path in partial_candidates[:2]
    )
    return MatchSearchEvidence(
        source_token_count=source_token_count,
        target_token_count=target_token_count,
        state_count=state_count,
        transition_count=transition_count,
        max_state_count=policy.max_state_count,
        max_transition_count=policy.max_transition_count,
        best_complete_path=(
            None
            if not complete
            else _search_path_evidence(
                complete[0], state=(source_token_count, target_token_count)
            )
        ),
        runner_up_complete_path=(
            None
            if len(complete) < 2
            else _search_path_evidence(
                complete[1], state=(source_token_count, target_token_count)
            )
        ),
        partial_paths=partial_paths,
    )


def _search_path_evidence(
    path: _Path, *, state: tuple[int, int]
) -> MatchSearchPathEvidence:
    """Snapshot one internal path as immutable public search evidence."""
    return MatchSearchPathEvidence(
        source_tokens_consumed=state[0],
        target_tokens_consumed=state[1],
        total_cost=path.total_cost,
        relations=path.relations,
    )


def _missing_continuation_reasons(
    best: _Path,
    runner_up: _Path | None,
    *,
    continuation_inputs: tuple[_ContinuationInput, ...],
) -> tuple[MatchQuarantineReason, ...]:
    """Quarantine resolved PGDP evidence that no returned relation can carry."""
    projected_ids = {
        reference.continuation_id
        for path in (best, runner_up)
        if path is not None
        for relation in path.relations
        for reference in relation.continuation_references
    }
    if all(
        continuation.continuation_id in projected_ids
        for continuation in continuation_inputs
    ):
        return ()
    return (MatchQuarantineReason.INCOMPATIBLE_CONTINUATION,)


def _unique_reasons(
    reasons: tuple[MatchQuarantineReason, ...],
) -> tuple[MatchQuarantineReason, ...]:
    """Preserve first occurrence while returning canonical immutable reasons."""
    return tuple(dict.fromkeys(reasons))
