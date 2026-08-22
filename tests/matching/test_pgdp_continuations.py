"""Tests for lossless PGDP physical-continuation decoding."""

from __future__ import annotations

import hashlib
import json

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
            tokens = (
                (
                    MatchToken(
                        token_id=f"{artifact_id}-{page_id}-line-{line_index + 1}",
                        text=text,
                        artifact_ranges=tuple(artifact_ranges),
                    ),
                )
                if text
                else ()
            )
            match_lines.append(
                MatchLine(
                    line_id=f"{page_id}-line-{line_index + 1}",
                    tokens=tokens,
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
            ("breadwinners", "bread-winners", "bread- winners"),
            PgdpContinuationBoundary.SAME_LINE,
            PgdpContinuationDecision.AMBIGUOUS,
        ),
        (
            (("058", ("sim-*",)), ("059", ("*plicity",))),
            "sim-",
            "plicity",
            ("simplicity", "sim-plicity", "sim- plicity"),
            PgdpContinuationBoundary.PAGE,
            PgdpContinuationDecision.AMBIGUOUS,
        ),
        (
            (("062", ("ad-*",)), ("063", ("*vantages",))),
            "ad-",
            "vantages",
            ("advantages", "ad-vantages", "ad- vantages"),
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
    assert result.continuations[0].round_evidence[0].right_fragment.text == "winners"
    assert result.continuations[0].round_evidence[1].right_fragment.text == "losers"
    assert tuple(
        evidence.round for evidence in result.continuations[0].marker_evidence
    ) == (
        PgdpRound.F2,
        PgdpRound.P3,
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


def test_decoder_reconciles_tokenized_rounds_by_page_local_marker_ordinal() -> None:
    f2, _f2_bytes = _round_document(PgdpRound.F2, (("001", ("bread-*winners",)),))
    p3, _p3_bytes = _round_document(PgdpRound.P3, (("001", ("bread-*winners",)),))
    p3_token = p3.pages[0].lines[0].tokens[0]
    split_p3 = p3.model_copy(
        update={
            "pages": (
                p3.pages[0].model_copy(
                    update={
                        "lines": (
                            p3.pages[0]
                            .lines[0]
                            .model_copy(
                                update={
                                    "tokens": (
                                        MatchToken(
                                            token_id="p3-left",
                                            text="bread-",
                                            artifact_ranges=p3_token.artifact_ranges[
                                                :6
                                            ],
                                        ),
                                        MatchToken(
                                            token_id="p3-right",
                                            text="*winners",
                                            artifact_ranges=p3_token.artifact_ranges[
                                                6:
                                            ],
                                        ),
                                    )
                                }
                            ),
                        )
                    }
                ),
            )
        }
    )

    result = decode_pgdp_continuations(f2, split_p3)

    assert len(result.continuations) == 1
    assert tuple(
        evidence.round for evidence in result.continuations[0].round_evidence
    ) == (
        PgdpRound.F2,
        PgdpRound.P3,
    )


def test_decoder_quarantines_a_marker_separated_by_a_blank_line() -> None:
    result, _f2_bytes, _p3_bytes = _decode((("001", ("alpha-*", "", "*omega")),))

    assert result.continuations == ()
    assert {marker.reason for marker in result.quarantined_markers} == {
        PgdpContinuationQuarantineReason.NONADJACENT_MARKERS
    }


def test_visible_hyphen_has_a_leave_separate_candidate() -> None:
    result, _f2_bytes, _p3_bytes = _decode((("001", ("bread-*winners",)),))

    assert tuple(
        candidate.decision for candidate in result.continuations[0].logical_candidates
    ) == (
        PgdpContinuationDecision.JOIN_WITHOUT_HYPHEN,
        PgdpContinuationDecision.KEEP_HYPHEN,
        PgdpContinuationDecision.LEAVE_SEPARATE,
    )
    assert result.continuations[0].logical_candidates[2].text == "bread- winners"


def _json_round_document(round_: PgdpRound, payload: bytes) -> MatchDocument:
    """Build a page document whose ranges point into a raw JSON payload."""
    decoded = json.loads(payload)
    pages: list[MatchPage] = []
    grapheme_offset = 0
    for page_key, text in decoded.items():
        encoded_text = text.encode("utf-8")
        encoded_value = b'"' + encoded_text + b'"'
        value_start = payload.index(encoded_value) + 1
        ranges: list[ArtifactRange] = []
        byte_offset = value_start
        for grapheme_index, grapheme in enumerate(split_graphemes(text)):
            encoded_grapheme = grapheme.encode("utf-8")
            ranges.append(
                ArtifactRange(
                    artifact_id=round_.value,
                    artifact_sha256=hashlib.sha256(payload).hexdigest(),
                    byte_start=byte_offset,
                    byte_end=byte_offset + len(encoded_grapheme),
                    grapheme_start=grapheme_offset + grapheme_index,
                    grapheme_end=grapheme_offset + grapheme_index + 1,
                )
            )
            byte_offset += len(encoded_grapheme)
        pages.append(
            MatchPage(
                page_id=page_key,
                lines=(
                    MatchLine(
                        line_id=f"{page_key}-line-1",
                        tokens=(
                            MatchToken(
                                token_id=f"{round_.value}-{page_key}-token-1",
                                text=text,
                                artifact_ranges=tuple(ranges),
                            ),
                        ),
                    ),
                ),
            )
        )
        grapheme_offset += len(split_graphemes(text))
    return MatchDocument(document_id=f"{round_.value}-json", pages=tuple(pages))


def test_json_page_payload_ranges_are_immutable_and_slice_exact_graphemes() -> None:
    f2_payload = b'{"058.png":"sim-*","059.png":"*plicity"}'
    p3_payload = b'{"058.png":"sim-*","059.png":"*plicity"}'
    f2 = _json_round_document(PgdpRound.F2, f2_payload)
    p3 = _json_round_document(PgdpRound.P3, p3_payload)
    f2_before = f2.model_dump(mode="json")
    p3_before = p3.model_dump(mode="json")
    f2_bytes_before = bytes(f2_payload)
    p3_bytes_before = bytes(p3_payload)

    result = decode_pgdp_continuations(f2, p3)

    assert f2.model_dump(mode="json") == f2_before
    assert p3.model_dump(mode="json") == p3_before
    assert f2_payload == f2_bytes_before
    assert p3_payload == p3_bytes_before
    continuation = result.continuations[0]
    source_payloads = {PgdpRound.F2: f2_payload, PgdpRound.P3: p3_payload}
    for evidence in continuation.round_evidence:
        for fragment in (evidence.left_fragment, evidence.right_fragment):
            for grapheme, source_range in zip(
                split_graphemes(fragment.text), fragment.grapheme_ranges, strict=True
            ):
                assert (
                    source_payloads[evidence.round][
                        source_range.byte_start : source_range.byte_end
                    ].decode("utf-8")
                    == grapheme
                )
        for source_range in evidence.marker_evidence.marker_ranges:
            assert (
                source_payloads[evidence.round][
                    source_range.byte_start : source_range.byte_end
                ]
                == b"*"
            )
