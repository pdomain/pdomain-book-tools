from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from pdomain_book_tools.pgdp.f2 import (
    F2NormalizationKind,
    F2TokenKind,
    tokenize_f2,
)

FIXTURES = Path(__file__).parent / "fixtures"
FIXTURE_PROVENANCE = json.loads((FIXTURES / "SOURCES.json").read_text())
FIXTURE_NAMES = tuple(sorted(FIXTURE_PROVENANCE["fixtures"]))


def test_visible_grapheme_maps_to_raw_bytes() -> None:
    payload = "<i>e\u0301</i>,".encode()

    parsed = tokenize_f2(payload)

    assert parsed.visible_text == "e\u0301,"
    assert parsed.graphemes[0].text == "e\u0301"
    assert (
        parsed.graphemes[0].source_slices[0].artifact_sha256
        == hashlib.sha256(payload).hexdigest()
    )
    assert parsed.graphemes[0].source_slices[0].byte_start == 3
    assert parsed.graphemes[0].source_slices[0].byte_end == 6
    assert parsed.graphemes[1].source_slices[0].byte_start == 10
    assert parsed.graphemes[1].source_slices[0].byte_end == 11


@pytest.mark.parametrize(
    ("fixture_name", "expected_visible"),
    [
        (
            "projectID62930b71a45bb-a0000.txt",
            "Photo aquatinte Boussod_Valadon & Co.\r\n",
        ),
        (
            "projectID673cd4c091c6a-0920.txt",
            "\r\nLes\u00b4bi·an (l[)e]z\u00b4b[)i]·[)a]n) adj. 1. Of.\r\n\r\n",
        ),
        ("projectID61f8a50869170-1810.txt", '"spuuns."\r\n'),
        (
            "nested-i-b.txt",
            "Sun Dodger says you always can draw the\r\nQueens if you have got the Jack.\r\n",
        ),
        ("nested-b-i.txt", "and WORK gives us\r\n"),
        ("nested-i-sc.txt", "The HEALTHY LIFE\r\nBEVERAGE BOOK\r\n"),
        ("nested-sc-i.txt", "V. The Baron Korff      50\r\n"),
        (
            "projectID6489c4e9d4e74-2090-g.txt",
            "JESUS, because he shall deliver his people\r\n",
        ),
        ("audited-unicode-combining.txt", "e\u0301,\n"),
    ],
)
def test_audited_fixtures_keep_only_visible_text(
    fixture_name: str, expected_visible: str
) -> None:
    parsed = tokenize_f2((FIXTURES / fixture_name).read_bytes())

    assert parsed.visible_text == expected_visible
    assert all(token.kind is not F2TokenKind.UNKNOWN for token in parsed.tokens)


def test_known_tags_and_controls_are_retained_as_tokens() -> None:
    parsed = tokenize_f2(b"<i>x</i><b>y</b><sc>z</sc><g>a b</g><f>c</f><u>d</u>")

    assert sum(token.kind is F2TokenKind.OPEN_TAG for token in parsed.tokens) == 6
    assert sum(token.kind is F2TokenKind.CLOSE_TAG for token in parsed.tokens) == 6
    assert parsed.visible_text == "xyzabcd"


def test_letter_spacing_removal_is_an_explicit_non_visible_token() -> None:
    parsed = tokenize_f2(b"<g>A B</g>")

    assert parsed.visible_text == "AB"
    assert parsed.normalizations[0].kind is F2NormalizationKind.LETTER_SPACE_REMOVED
    assert parsed.normalizations[0].replacement_text == ""
    removed_space = next(
        token for token in parsed.tokens if token.kind is F2TokenKind.NORMALIZATION
    )
    assert removed_space.text == " "
    assert removed_space.visible_text == ""
    assert removed_space.normalization_kind is F2NormalizationKind.LETTER_SPACE_REMOVED


def test_unknown_construct_is_a_warning_token_without_a_crash() -> None:
    parsed = tokenize_f2(b"one <blink>two</blink> three")

    assert parsed.visible_text == "one <blink>two</blink> three"
    assert "unknown_construct" in parsed.warning_codes
    assert any(token.kind is F2TokenKind.UNKNOWN for token in parsed.tokens)


def test_unknown_tag_body_is_quarantined_without_parsing_inner_controls() -> None:
    payload = b"<unknown>^x[**note]</unknown>"

    parsed = tokenize_f2(payload)

    assert parsed.visible_text == payload.decode()
    assert "unknown_construct" in parsed.warning_codes
    assert all(
        token.kind not in {F2TokenKind.SUPERSCRIPT, F2TokenKind.NOTE}
        for token in parsed.tokens
    )
    assert sum(token.kind is F2TokenKind.UNKNOWN for token in parsed.tokens) == 3


def test_unknown_tag_with_hyphen_and_attributes_quarantines_inner_controls() -> None:
    payload = b'<unknown-tag data="x">^x[**note]</unknown-tag>'

    parsed = tokenize_f2(payload)

    assert parsed.visible_text == payload.decode()
    assert all(
        token.kind not in {F2TokenKind.SUPERSCRIPT, F2TokenKind.NOTE}
        for token in parsed.tokens
    )
    assert sum(token.kind is F2TokenKind.UNKNOWN for token in parsed.tokens) == 3


def test_unknown_tag_with_tab_attribute_quarantines_inner_controls() -> None:
    payload = b'<unknown-tag\tdata="x">^x[**note]</unknown-tag>'

    parsed = tokenize_f2(payload)

    assert parsed.visible_text == payload.decode()
    assert all(
        token.kind not in {F2TokenKind.SUPERSCRIPT, F2TokenKind.NOTE}
        for token in parsed.tokens
    )
    assert sum(token.kind is F2TokenKind.UNKNOWN for token in parsed.tokens) == 3


def test_unclosed_unknown_tag_quarantines_the_remainder_and_is_page_local() -> None:
    malformed = tokenize_f2(b"<unknown>^x[**note]")
    clean = tokenize_f2(b"plain")

    assert malformed.visible_text == "<unknown>^x[**note]"
    assert "unclosed_unknown_tag" in malformed.warning_codes
    assert all(
        token.kind not in {F2TokenKind.SUPERSCRIPT, F2TokenKind.NOTE}
        for token in malformed.tokens
    )
    assert clean.visible_text == "plain"
    assert clean.warning_codes == ()


def test_malformed_unknown_tag_is_quarantined_and_is_page_local() -> None:
    malformed = tokenize_f2(b"<unknown^x")
    clean = tokenize_f2(b"plain")

    assert malformed.visible_text == "<unknown^x"
    assert "invalid_construct" in malformed.warning_codes
    assert all(token.kind is not F2TokenKind.SUPERSCRIPT for token in malformed.tokens)
    assert clean.visible_text == "plain"
    assert clean.warning_codes == ()


def test_malformed_delimiters_have_linear_index_scan_evidence() -> None:
    payload = b"<" * 4096

    parsed = tokenize_f2(payload)

    assert parsed.visible_text == payload.decode()
    assert parsed.delimiter_scan_count == len(payload) * 2
    assert parsed.opaque_tag_scan_count == len(payload)


def test_unknown_tag_close_lookup_has_linear_scan_evidence() -> None:
    payload = b"<unknown>" + b"<" * 4096 + b"</unknown>"

    parsed = tokenize_f2(payload)

    assert parsed.visible_text == payload.decode()
    assert parsed.delimiter_scan_count == len(payload) * 2
    assert parsed.opaque_tag_scan_count <= len(payload) * 2


@pytest.mark.parametrize("payload", [b"<i", b"^", b"^{word"])
def test_truncated_control_is_quarantined_as_an_unknown_token(payload: bytes) -> None:
    parsed = tokenize_f2(payload)

    assert "invalid_construct" in parsed.warning_codes
    assert any(token.kind is F2TokenKind.UNKNOWN for token in parsed.tokens)


def test_unclosed_tag_is_page_local() -> None:
    malformed = tokenize_f2(b"<sc>first")
    clean = tokenize_f2(b"second")

    assert "unclosed_tag" in malformed.warning_codes
    assert clean.warning_codes == ()
    assert clean.visible_text == "second"


def test_unclosed_note_is_retained_as_an_invalid_token() -> None:
    payload = (FIXTURES / "projectID62930b71a45bb-p3640-unclosed-sc.txt").read_bytes()

    parsed = tokenize_f2(payload)

    assert "unclosed_tag" in parsed.warning_codes
    assert "unclosed_note" in parsed.warning_codes
    assert any(token.kind is F2TokenKind.UNKNOWN for token in parsed.tokens)


def test_four_audited_nesting_orders_stay_page_local() -> None:
    payload = b"".join(
        (FIXTURES / fixture_name).read_bytes()
        for fixture_name in (
            "nested-i-b.txt",
            "nested-b-i.txt",
            "nested-i-sc.txt",
            "nested-sc-i.txt",
        )
    )
    parsed = tokenize_f2(payload)

    assert "Sun Dodger" in parsed.visible_text
    assert "Baron Korff" in parsed.visible_text
    assert parsed.warning_codes == ()


def test_every_visible_grapheme_reconstructs_from_direct_raw_slices() -> None:
    payload = "<i>e\u0301</i>,".encode()

    parsed = tokenize_f2(payload)

    assert (
        "".join(
            b"".join(
                payload[source_slice.byte_start : source_slice.byte_end]
                for source_slice in grapheme.source_slices
            ).decode()
            for grapheme in parsed.graphemes
        )
        == parsed.visible_text
    )


@pytest.mark.parametrize("fixture_name", FIXTURE_NAMES)
def test_fixture_serialization_is_deterministic(fixture_name: str) -> None:
    payload = (FIXTURES / fixture_name).read_bytes()

    assert tokenize_f2(payload).to_json_bytes() == tokenize_f2(payload).to_json_bytes()


@pytest.mark.parametrize("fixture_name", FIXTURE_NAMES)
def test_fixture_graphemes_reconstruct_from_raw_source_slices(
    fixture_name: str,
) -> None:
    payload = (FIXTURES / fixture_name).read_bytes()
    parsed = tokenize_f2(payload)

    reconstructed = "".join(
        b"".join(
            payload[source_slice.byte_start : source_slice.byte_end]
            for source_slice in grapheme.source_slices
        ).decode()
        for grapheme in parsed.graphemes
    )
    assert reconstructed == parsed.visible_text


@pytest.mark.parametrize("truncate_at", range(0, len(b"<i>word</i>[**note]^{xy}")))
def test_truncated_controls_never_raise_or_share_state(truncate_at: int) -> None:
    payload = b"<i>word</i>[**note]^{xy}"[:truncate_at]

    parsed = tokenize_f2(payload)
    next_page = tokenize_f2(b"plain")

    assert isinstance(parsed.visible_text, str)
    assert next_page.visible_text == "plain"
    assert next_page.warning_codes == ()


@pytest.mark.parametrize("tag_name", ["i", "b", "sc", "g", "f", "u"])
@pytest.mark.parametrize("truncate_at", range(0, len(b"<i>word</i>")))
def test_truncated_supported_tags_never_leak_state(
    tag_name: str, truncate_at: int
) -> None:
    payload = f"<{tag_name}>word</{tag_name}>".encode()[:truncate_at]

    parsed = tokenize_f2(payload)
    next_page = tokenize_f2(b"plain")

    assert isinstance(parsed.visible_text, str)
    assert next_page.visible_text == "plain"
    assert next_page.warning_codes == ()


@pytest.mark.parametrize(
    "fixture_name",
    ["nested-i-b.txt", "nested-b-i.txt", "nested-i-sc.txt", "nested-sc-i.txt"],
)
def test_truncated_audited_nesting_examples_never_leak_state(fixture_name: str) -> None:
    payload = (FIXTURES / fixture_name).read_bytes()

    for truncate_at in range(len(payload)):
        parsed = tokenize_f2(payload[:truncate_at])
        next_page = tokenize_f2(b"plain")
        assert isinstance(parsed.visible_text, str)
        assert next_page.visible_text == "plain"
        assert next_page.warning_codes == ()
