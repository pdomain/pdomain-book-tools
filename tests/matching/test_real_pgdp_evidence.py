"""Real PGDP continuation evidence retained as metadata-only fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel

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
    PgdpRound,
    decode_pgdp_continuations,
    match_documents,
)
from pdomain_book_tools.typography.spans import split_graphemes


class _ArtifactFixture(BaseModel):
    """The pinned identity of one locally held PGDP round artifact."""

    artifact_id: str
    sha256: str


class _SourceRangeFixture(BaseModel):
    """The contiguous raw-artifact range for one minimal fixture token."""

    byte_start: int
    byte_end: int
    grapheme_start: int
    grapheme_end: int


class _TokenFixture(BaseModel):
    """One minimal physical PGDP token without surrounding corpus text."""

    page_id: str
    line_id: str
    token_id: str
    text: str
    source_range: _SourceRangeFixture


class _RoundFixture(BaseModel):
    """Ordered minimal token evidence for one PGDP round."""

    tokens: tuple[_TokenFixture, ...]


class _RoundsFixture(BaseModel):
    """The F2 and P3 evidence for one continuation."""

    f2: _RoundFixture
    p3: _RoundFixture


class _ExpectedFixture(BaseModel):
    """The decoder and matcher outcome that the corpus attests."""

    boundary: PgdpContinuationBoundary
    decision: PgdpContinuationDecision
    logical_candidates: tuple[str, ...]
    marker_counts: tuple[int, int]
    target_text: str


class _CaseFixture(BaseModel):
    """One metadata-only continuation case from the local PGDP corpus."""

    case_id: str
    rounds: _RoundsFixture
    expected: _ExpectedFixture


class _ArtifactsFixture(BaseModel):
    """The source-artifact identities used by the metadata-only cases."""

    f2: _ArtifactFixture
    p3: _ArtifactFixture


class _Fixture(BaseModel):
    """The complete pinned fixture for one local PGDP project."""

    project_id: str
    artifacts: _ArtifactsFixture
    cases: tuple[_CaseFixture, ...]


_FIXTURE_PATH = (
    Path(__file__).parents[1] / "fixtures" / "matching" / "pgdp-continuations.json"
)


@pytest.fixture(scope="module")
def real_evidence() -> _Fixture:
    """Load only corpus metadata and minimal continuation fragments."""
    return _Fixture.model_validate_json(_FIXTURE_PATH.read_text(encoding="utf-8"))


def _ranges(
    token: _TokenFixture, artifact: _ArtifactFixture
) -> tuple[ArtifactRange, ...]:
    """Expand one contiguous metadata range into exact grapheme source ranges."""
    source_range = token.source_range
    graphemes = split_graphemes(token.text)
    ranges: list[ArtifactRange] = []
    byte_offset = source_range.byte_start
    for grapheme_index, grapheme in enumerate(graphemes):
        grapheme_bytes = grapheme.encode("utf-8")
        ranges.append(
            ArtifactRange(
                artifact_id=artifact.artifact_id,
                artifact_sha256=artifact.sha256,
                byte_start=byte_offset,
                byte_end=byte_offset + len(grapheme_bytes),
                grapheme_start=source_range.grapheme_start + grapheme_index,
                grapheme_end=source_range.grapheme_start + grapheme_index + 1,
            )
        )
        byte_offset += len(grapheme_bytes)
    assert byte_offset == source_range.byte_end
    assert source_range.grapheme_start + len(graphemes) == source_range.grapheme_end
    return tuple(ranges)


def _document(
    round_: PgdpRound, artifact: _ArtifactFixture, fixture: _RoundFixture
) -> MatchDocument:
    """Reconstruct one minimal physical round document from fixture metadata."""
    return MatchDocument(
        document_id=f"{round_.value}-real-evidence",
        pages=tuple(
            MatchPage(
                page_id=token.page_id,
                lines=(
                    MatchLine(
                        line_id=token.line_id,
                        tokens=(
                            MatchToken(
                                token_id=token.token_id,
                                text=token.text,
                                artifact_ranges=_ranges(token, artifact),
                            ),
                        ),
                    ),
                ),
            )
            for token in fixture.tokens
        ),
    )


def _surface_document(continuation: PgdpContinuation) -> MatchDocument:
    """Build marker-free physical fragments while retaining their source ranges."""
    left = continuation.left_fragment
    right = continuation.right_fragment
    if left.token_id == right.token_id:
        tokens = (
            MatchToken(
                token_id=left.token_id,
                text=left.text + right.text,
                artifact_ranges=left.grapheme_ranges + right.grapheme_ranges,
            ),
        )
    else:
        tokens = (
            MatchToken(
                token_id=left.token_id,
                text=left.text,
                artifact_ranges=left.grapheme_ranges,
            ),
            MatchToken(
                token_id=right.token_id,
                text=right.text,
                artifact_ranges=right.grapheme_ranges,
            ),
        )
    return MatchDocument(
        document_id=f"surface-{continuation.continuation_id}",
        pages=(
            MatchPage(
                page_id="surface",
                lines=(MatchLine(line_id="surface-line", tokens=tokens),),
            ),
        ),
    )


def _target_document(text: str) -> MatchDocument:
    """Build the minimal logical-text side of one real continuation match."""
    return MatchDocument(
        document_id="logical-target",
        pages=(
            MatchPage(
                page_id="logical-target-page",
                lines=(
                    MatchLine(
                        line_id="logical-target-line",
                        tokens=(MatchToken(token_id="logical-target", text=text),),
                    ),
                ),
            ),
        ),
    )


def _policy() -> MatchPolicy:
    """Return a bounded policy whose review state comes from PGDP evidence."""
    return MatchPolicy(
        policy_id="real-pgdp-evidence",
        version="1",
        low_margin_threshold=0,
        max_merge_size=2,
        max_state_count=100,
        max_transition_count=100,
    )


@pytest.mark.parametrize(
    "case_index",
    range(5),
    ids=(
        "bread-winners",
        "tam-far",
        "unmannerly-for",
        "sim-plicity",
        "ad-vantages",
    ),
)
def test_real_pgdp_continuations_decode_match_and_preserve_exact_ranges(
    real_evidence: _Fixture, case_index: int
) -> None:
    """Decode and match each attested case without retaining its raw page bytes."""
    case = real_evidence.cases[case_index]
    f2 = _document(PgdpRound.F2, real_evidence.artifacts.f2, case.rounds.f2)
    p3 = _document(PgdpRound.P3, real_evidence.artifacts.p3, case.rounds.p3)
    f2_before = f2.model_dump(mode="json")
    p3_before = p3.model_dump(mode="json")

    first = decode_pgdp_continuations(f2, p3)
    second = decode_pgdp_continuations(f2, p3)

    assert first.to_json_bytes() == second.to_json_bytes()
    assert f2.model_dump(mode="json") == f2_before
    assert p3.model_dump(mode="json") == p3_before
    assert len(first.continuations) == 1
    continuation = first.continuations[0]
    assert continuation.boundary is case.expected.boundary
    assert continuation.decision is case.expected.decision
    assert tuple(candidate.text for candidate in continuation.logical_candidates) == (
        case.expected.logical_candidates
    )
    assert (
        tuple(evidence.marker_count for evidence in continuation.marker_evidence)
        == case.expected.marker_counts
    )

    artifacts_by_round = {
        PgdpRound.F2: real_evidence.artifacts.f2,
        PgdpRound.P3: real_evidence.artifacts.p3,
    }
    round_fixtures_by_round = {
        PgdpRound.F2: case.rounds.f2,
        PgdpRound.P3: case.rounds.p3,
    }
    for evidence in continuation.round_evidence:
        artifact = artifacts_by_round[evidence.round]
        token_fixtures = {
            token.token_id: token
            for token in round_fixtures_by_round[evidence.round].tokens
        }
        for fragment in (evidence.left_fragment, evidence.right_fragment):
            token = token_fixtures[fragment.token_id]
            source_ranges = _ranges(token, artifact)
            fragment_start = token.text.index(fragment.text)
            fragment_end = fragment_start + len(split_graphemes(fragment.text))
            assert (
                fragment.grapheme_ranges == source_ranges[fragment_start:fragment_end]
            )
            assert all(
                source_range.artifact_id == artifact.artifact_id
                and source_range.artifact_sha256 == artifact.sha256
                for source_range in fragment.grapheme_ranges
            )
        for source_range in evidence.marker_evidence.marker_ranges:
            assert any(
                source_range == ranges[marker_index]
                for token in token_fixtures.values()
                for marker_index, marker in enumerate(split_graphemes(token.text))
                if marker == "*"
                for ranges in (_ranges(token, artifact),)
            )

    source = _surface_document(continuation)
    target = _target_document(case.expected.target_text)
    graph = match_documents(
        source,
        target,
        policy=_policy(),
        pgdp_continuations=(continuation,),
    )
    repeated_graph = match_documents(
        source,
        target,
        policy=_policy(),
        pgdp_continuations=(continuation,),
    )

    assert graph.to_json_bytes() == repeated_graph.to_json_bytes()
    if case.expected.decision is PgdpContinuationDecision.AMBIGUOUS:
        assert not graph.accepted
        assert MatchQuarantineReason.UNRESOLVED_CONTINUATION in graph.quarantine_reasons
    else:
        assert graph.accepted
        assert (
            graph.best_alternative.relations[0]
            .continuation_references[0]
            .continuation_id
            == continuation.continuation_id
        )
