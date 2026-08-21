from __future__ import annotations

import hashlib

import pytest

from pdomain_book_tools.pgdp.f2 import read_f2_json


def test_lexical_json_reader_maps_escaped_characters_to_artifact_bytes() -> None:
    artifact = b'{"p001.png":"<i>e\\u0301</i>,\\n"}'

    document = read_f2_json(artifact)

    page = document.pages[0]
    assert page.page_key == "p001.png"
    assert page.decoded_text == "<i>e\u0301</i>,\n"
    assert (
        page.decoded_page_utf8_sha256
        == hashlib.sha256(page.decoded_text.encode()).hexdigest()
    )
    assert page.lexical_value_byte_range == (12, len(artifact) - 1)
    accent = page.characters[4]
    assert accent.text == "\u0301"
    assert accent.source_slice.artifact_sha256 == hashlib.sha256(artifact).hexdigest()
    assert (
        artifact[accent.source_slice.byte_start : accent.source_slice.byte_end]
        == b"\\u0301"
    )


def test_json_pages_produce_artifact_relative_source_slices() -> None:
    artifact = b'{"a.png":"<i>a</i>,","b.png":"<sc>b"}'

    document = read_f2_json(artifact)

    assert document.pages[0].parsed.visible_text == "a,"
    assert document.pages[0].parsed.graphemes[0].source_slices[0].byte_start == 13
    assert "unclosed_tag" in document.pages[1].parsed.warning_codes
    assert document.to_json_bytes() == read_f2_json(artifact).to_json_bytes()


def test_escaped_json_graphemes_keep_one_slice_per_decoded_character() -> None:
    artifact = b'{"p001.png":"e\\u0301"}'

    document = read_f2_json(artifact)

    page = document.pages[0]
    assert page.parsed.graphemes[0].text == "e\u0301"
    assert len(page.parsed.graphemes[0].source_slices) == 2
    assert tuple(character.text for character in page.characters[0:2]) == (
        "e",
        "\u0301",
    )
    character_text_by_slice = {
        (
            character.source_slice.byte_start,
            character.source_slice.byte_end,
        ): character.text
        for character in page.characters
    }
    assert (
        "".join(
            "".join(
                character_text_by_slice[
                    (source_slice.byte_start, source_slice.byte_end)
                ]
                for source_slice in grapheme.source_slices
            )
            for grapheme in page.parsed.graphemes
        )
        == page.parsed.visible_text
    )


def test_json_reader_rejects_non_string_page_values() -> None:
    artifact = b'{"p001.png": 12}'

    with pytest.raises(ValueError, match="JSON strings"):
        read_f2_json(artifact)


def test_json_reader_rejects_a_trailing_comma() -> None:
    artifact = b'{"p001.png":"text",}'

    with pytest.raises(ValueError, match="trailing comma"):
        read_f2_json(artifact)
