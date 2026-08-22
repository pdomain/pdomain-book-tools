"""Tests for lossless PGDP physical-continuation decoding."""

from __future__ import annotations

import hashlib

import pytest

from pdomain_book_tools.matching import (
    ArtifactRange,
    MatchDocument,
    MatchLine,
    MatchPage,
    MatchToken,
    PgdpContinuationBoundary,
    PgdpContinuationDecision,
    PgdpContinuationQuarantineReason,
    PgdpRound,
    PgdpUnmappedMarkerEvidence,
    decode_pgdp_continuations,
)
from pdomain_book_tools.typography.spans import split_graphemes


def _round_document(
    round_: PgdpRound, pages: tuple[tuple[str, tuple[str, ...]], ...]
) -> tuple[MatchDocument, bytes]:
    """Build one exact round document and its untouched fixture bytes."""
    payload = "\n".join("\n".join(lines) for _page_id, lines in pages).encode("utf-8")
    artifact_id = round_.value
    artifact_sha256 = hashlib.sha256(payload).hexdigest()
    byte_offset = 0
    grapheme_offset = 0
    match_pages: list[MatchPage] = []
    for page_index, (page_id, lines) in enumerate(pages):
        match_lines: list[MatchLine] = []
        for line_index, text in enumerate(lines):
            text_bytes = text.encode("utf-8")
            graphemes = split_graphemes(text)
            grapheme_byte_offset = byte_offset
            artifact_ranges: list[ArtifactRange] = []
            for grapheme_index, grapheme in enumerate(graphemes):
                grapheme_bytes = grapheme.encode("utf-8")
                artifact_ranges.append(
                    ArtifactRange(
                        artifact_id=artifact_id,
                        artifact_sha256=artifact_sha256,
                        byte_start=grapheme_byte_offset,
                        byte_end=grapheme_byte_offset + len(grapheme_bytes),
                        grapheme_start=grapheme_offset + grapheme_index,
                        grapheme_end=grapheme_offset + grapheme_index + 1,
                    )
                )
                grapheme_byte_offset += len(grapheme_bytes)
            match_lines.append(
                MatchLine(
                    line_id=f"{page_id}-line-{line_index + 1}",
                    tokens=(
                        MatchToken(
                            token_id=(f"{artifact_id}-{page_id}-line-{line_index + 1}"),
                            text=text,
                            artifact_ranges=tuple(artifact_ranges),
                        ),
                    ),
                )
            )
            byte_offset += len(text_bytes) + 1
            grapheme_offset += len(graphemes) + 1
        if page_index + 1 < len(pages):
            byte_offset += 0
            grapheme_offset += 0
        match_pages.append(MatchPage(page_id=page_id, lines=tuple(match_lines)))
    return MatchDocument(
        document_id=f"{artifact_id}-document", pages=tuple(match_pages)
    ), payload


def _decode(
    pages: tuple[tuple[str, tuple[str, ...]], ...],
    *,
    p3_pages: tuple[tuple[str, tuple[str, ...]], ...] | None = None,
):
    f2, f2_bytes = _round_document(PgdpRound.F2, pages)
    p3, p3_bytes = _round_document(PgdpRound.P3, p3_pages or pages)
    result = decode_pgdp_continuations(f2, p3)
    return result, f2_bytes, p3_bytes


@pytest.mark.parametrize(
    ("pages", "left", "right", "candidates", "boundary", "decision"),
    [
        (
            (("001", ("bread-*winners",)),),
            "bread-",
            "winners",
            ("breadwinners", "bread-winners"),
            PgdpContinuationBoundary.SAME_LINE,
            PgdpContinuationDecision.AMBIGUOUS,
        ),
        (
            (("058", ("sim-*",)), ("059", ("*plicity",))),
            "sim-",
            "plicity",
            ("simplicity", "sim-plicity"),
            PgdpContinuationBoundary.PAGE,
            PgdpContinuationDecision.AMBIGUOUS,
        ),
        (
            (("062", ("ad-*",)), ("063", ("*vantages",))),
            "ad-",
            "vantages",
            ("advantages", "ad-vantages"),
            PgdpContinuationBoundary.PAGE,
            PgdpContinuationDecision.AMBIGUOUS,
        ),
        (
            (("014", ("Tam--*",)), ("015", ("*far",))),
            "Tam--",
            "far",
            ("Tam--far",),
            PgdpContinuationBoundary.PAGE,
            PgdpContinuationDecision.PRESERVE_PUNCTUATION,
        ),
        (
            (("054", ("unmannerly*",)), ("055", ("*--for",))),
            "unmannerly",
            "--for",
            ("unmannerly--for",),
            PgdpContinuationBoundary.PAGE,
            PgdpContinuationDecision.PRESERVE_PUNCTUATION,
        ),
    ],
)
def test_decoder_keeps_real_physical_fragments_and_logical_candidates(
    pages: tuple[tuple[str, tuple[str, ...]], ...],
    left: str,
    right: str,
    candidates: tuple[str, ...],
    boundary: PgdpContinuationBoundary,
    decision: PgdpContinuationDecision,
) -> None:
    result, f2_bytes, p3_bytes = _decode(pages)

    assert len(result.continuations) == 1
    continuation = result.continuations[0]
    assert continuation.left_fragment.text == left
    assert continuation.right_fragment.text == right
    assert (
        tuple(candidate.text for candidate in continuation.logical_candidates)
        == candidates
    )
    assert continuation.boundary == boundary
    assert continuation.decision == decision
    assert tuple(evidence.round for evidence in continuation.marker_evidence) == (
        PgdpRound.F2,
        PgdpRound.P3,
    )
    assert f2_bytes == bytes(f2_bytes)
    assert p3_bytes == bytes(p3_bytes)
    for fragment in (continuation.left_fragment, continuation.right_fragment):
        assert len(fragment.grapheme_ranges) == len(fragment.text)
        assert all(
            source_range.grapheme_end - source_range.grapheme_start == 1
            for source_range in fragment.grapheme_ranges
        )


def test_decoder_retains_asymmetric_marker_evidence_without_inventing_conflict() -> (
    None
):
    result, _f2_bytes, _p3_bytes = _decode(
        (("058", ("sim-*",)), ("059", ("*plicity",))),
        p3_pages=(("058", ("sim-*",)), ("059", ("plicity",))),
    )

    continuation = result.continuations[0]
    assert continuation.quarantine_reasons == ()
    assert [evidence.marker_count for evidence in continuation.marker_evidence] == [
        2,
        1,
    ]


def test_decoder_quarantines_nonadjacent_page_markers() -> None:
    result, _f2_bytes, _p3_bytes = _decode(
        (("001", ("alpha-*",)), ("003", ("*omega",)))
    )

    assert result.continuations == ()
    assert {marker.reason for marker in result.quarantined_markers} == {
        PgdpContinuationQuarantineReason.NONADJACENT_MARKERS
    }


def test_decoder_quarantines_orphan_leading_and_trailing_markers() -> None:
    result, _f2_bytes, _p3_bytes = _decode((("001", ("*leading", "trailing*")),))

    assert result.continuations == ()
    assert {marker.reason for marker in result.quarantined_markers} == {
        PgdpContinuationQuarantineReason.ORPHAN_LEADING_MARKER,
        PgdpContinuationQuarantineReason.ORPHAN_TRAILING_MARKER,
    }


def test_decoder_quarantines_round_conflicts() -> None:
    result, _f2_bytes, _p3_bytes = _decode(
        (("001", ("bread-*winners",)),),
        p3_pages=(("001", ("bread-*losers",)),),
    )

    assert len(result.continuations) == 1
    assert result.continuations[0].quarantine_reasons == (
        PgdpContinuationQuarantineReason.ROUND_CONFLICT,
    )


def test_decoder_quarantines_empty_fragments() -> None:
    result, _f2_bytes, _p3_bytes = _decode((("001", ("*",)),))

    assert result.continuations == ()
    assert {marker.reason for marker in result.quarantined_markers} == {
        PgdpContinuationQuarantineReason.EMPTY_FRAGMENT,
    }


def test_decoder_quarantines_range_mismatches_without_fabricating_marker_ranges() -> (
    None
):
    document, _artifact_bytes = _round_document(
        PgdpRound.F2, (("001", ("bread-*winners",)),)
    )
    malformed_token = (
        document.pages[0]
        .lines[0]
        .tokens[0]
        .model_copy(
            update={
                "artifact_ranges": document.pages[0]
                .lines[0]
                .tokens[0]
                .artifact_ranges[:1]
            }
        )
    )
    malformed_document = document.model_copy(
        update={
            "pages": (
                document.pages[0].model_copy(
                    update={
                        "lines": (
                            document.pages[0]
                            .lines[0]
                            .model_copy(update={"tokens": (malformed_token,)}),
                        )
                    }
                ),
            )
        }
    )
    p3, _p3_bytes = _round_document(PgdpRound.P3, (("001", ("bread-*winners",)),))

    result = decode_pgdp_continuations(malformed_document, p3)

    quarantined = next(
        marker
        for marker in result.quarantined_markers
        if marker.reason is PgdpContinuationQuarantineReason.SOURCE_RANGE_MISMATCH
    )
    assert quarantined.marker_evidence is None
    assert isinstance(quarantined.unmapped_marker_evidence, PgdpUnmappedMarkerEvidence)
    assert quarantined.unmapped_marker_evidence.token_artifact_ranges == (
        malformed_token.artifact_ranges[0],
    )


def test_decoder_reconciles_repeated_text_by_physical_structure() -> None:
    f2, _f2_bytes = _round_document(
        PgdpRound.F2,
        (("001", ("same-*word",)), ("002", ("same-*word",))),
    )
    p3, _p3_bytes = _round_document(
        PgdpRound.P3,
        (("002", ("same-*word",)), ("001", ("same-*word",))),
    )

    result = decode_pgdp_continuations(f2, p3)

    assert len(result.continuations) == 2
    page_one_marker = p3.pages[1].lines[0].tokens[0].artifact_ranges[5]
    page_two_marker = p3.pages[0].lines[0].tokens[0].artifact_ranges[5]
    assert result.continuations[0].marker_evidence[1].marker_ranges == (
        page_one_marker,
    )
    assert result.continuations[1].marker_evidence[1].marker_ranges == (
        page_two_marker,
    )
