from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pdomain_book_contracts.sources.pgdp.f2.parser as parser_module
import pytest

from pdomain_book_tools.pgdp.f2.parser import F2Parser
from pdomain_book_tools.pgdp.f2.project_rules import ProjectRule, ProjectRuleRegistry
from pdomain_book_tools.typography.labels import (
    ConfidenceTier,
    KnowledgeState,
    StyleLabel,
)
from pdomain_book_tools.typography.records import (
    ArtifactRef,
    ArtifactSource,
    ParserControlKind,
    ParserNormalizationKind,
    ParserNoteStatus,
    TextIdentity,
    TypographyPageRecord,
)

if TYPE_CHECKING:
    from pdomain_book_tools.pgdp.f2.offsets import LexicalF2Index
    from pdomain_book_tools.pgdp.f2.tokens import F2JsonPage

_MOUNTED_F2_PATH = Path(
    "/workspaces/pdomain-data/pgdp-corpus/projectID6814e35a6b014/rounds/F2.json"
)


def _artifact(*, payload: bytes, source: ArtifactSource, path: str) -> ArtifactRef:
    return ArtifactRef(
        source=source,
        source_url=None,
        local_path=path,
        retrieved_at=dt.datetime(2026, 8, 21, tzinfo=dt.UTC),
        sha256=hashlib.sha256(payload).hexdigest(),
        version="fixture-v1",
        license_ref="public-domain",
    )


def _identity(*, f2_artifact: bytes, project_id: str = "project-1") -> TextIdentity:
    f2_ref = _artifact(
        payload=f2_artifact,
        source=ArtifactSource.PGDP_F2,
        path="fixtures/F2.json",
    )
    image_ref = _artifact(
        payload=b"image",
        source=ArtifactSource.PGDP_F2,
        path="fixtures/page.png",
    )
    return TextIdentity(
        work_id="work-1",
        edition_id="edition-1",
        book_id="book-1",
        project_id=project_id,
        pg_ebook_id=None,
        se_repository=None,
        page_id="001.png",
        image_artifact=image_ref,
        text_artifacts=(f2_ref,),
    )


def _parse(
    page_text: str,
    *,
    project_comments: bytes | None = None,
    parser: F2Parser | None = None,
    include_project_comments_artifact: bool = True,
) -> TypographyPageRecord:
    artifact = json.dumps({"001.png": page_text}, separators=(",", ":")).encode()
    comments_artifact = (
        _artifact(
            payload=project_comments,
            source=ArtifactSource.PGDP_F2,
            path="fixtures/project-comments.txt",
        )
        if project_comments is not None and include_project_comments_artifact
        else None
    )
    return (parser or F2Parser()).parse_page(
        f2_artifact_bytes=artifact,
        page_key="001.png",
        identity=_identity(f2_artifact=artifact),
        project_comments_bytes=project_comments,
        project_comments_artifact=comments_artifact,
        guideline_version="pgdp-guidelines-2026-08-21",
    )


def test_parser_emits_maximal_overlapping_spans_and_keeps_punctuation_outside() -> None:
    record = _parse("<i><b>word</b></i>,")

    assert record.parsed_text == "word,"
    assert [(span.label, span.start, span.end) for span in record.style_spans] == [
        (StyleLabel.BOLD, 0, 4),
        (StyleLabel.ITALIC, 0, 4),
    ]
    assert all(span.state is KnowledgeState.POSITIVE for span in record.style_spans)
    assert all(
        span.confidence_tier is ConfidenceTier.GOLD for span in record.style_spans
    )
    assert all(span.end == 4 for span in record.style_spans)


def test_parser_records_small_caps_case_normalization_evidence() -> None:
    record = _parse("<sc>A\u0301bC</sc>")

    span = record.style_spans[0]
    assert span.label is StyleLabel.SMALL_CAPS
    assert span.warnings == ("small_caps_case_normalized",)
    assert "small_caps_case_normalized" in record.parser_warnings
    assert [
        (operation.grapheme_indices, operation.replacement_text)
        for operation in record.normalization_operations
    ] == [
        ((0,), "a\u0301"),
        ((2,), "c"),
    ]
    assert all(
        operation.kind is ParserNormalizationKind.SMALL_CAPS_CASE_NORMALIZED
        for operation in record.normalization_operations
    )
    assert record.parsed_text == "A\u0301bC"


def test_parser_keeps_letter_spacing_removal_in_the_grapheme_source_map() -> None:
    record = _parse("<g>A B</g>")

    assert record.parsed_text == "AB"
    assert record.style_spans[0].label is StyleLabel.LETTER_SPACED
    assert (
        record.graphemes[0].source_slices[0].byte_end
        < record.graphemes[1].source_slices[0].byte_start
    )
    assert "letter_space_removed" in record.parser_warnings


def test_parser_quarantines_notes_and_marks_the_record_ineligible() -> None:
    record = _parse("before[**P1: unsure]after")

    assert record.parsed_text == "beforeafter"
    assert "note_quarantine" in record.parser_warnings
    assert record.training_eligible is False
    assert record.parser_notes[0].question_status is ParserNoteStatus.COMMENT
    assert record.parser_notes[0].page_review_content == "P1: unsure"
    assert record.parser_notes[0].source_slices
    assert record.to_json_bytes()


def test_parser_marks_question_notes_as_question_evidence() -> None:
    record = _parse("before[**P2: kicked?]after")

    assert record.parser_notes[0].question_status is ParserNoteStatus.QUESTION


def test_unclosed_note_remains_typed_quarantine_evidence() -> None:
    artifact = b'{"001.png":"before[**P2: kicked?"}'
    note_start = artifact.index(b"[**P2: kicked?")
    record = F2Parser().parse_page(
        f2_artifact_bytes=artifact,
        page_key="001.png",
        identity=_identity(f2_artifact=artifact),
        guideline_version="pgdp-guidelines-2026-08-21",
    )

    assert record.parsed_text == "before"
    assert "".join(grapheme.text for grapheme in record.graphemes) == "before"
    assert record.parser_notes[0].raw_text == "[**P2: kicked?"
    assert record.parser_notes[0].question_status is ParserNoteStatus.QUESTION
    assert [
        (source_slice.byte_start, source_slice.byte_end)
        for source_slice in record.parser_notes[0].source_slices
    ] == [
        (index, index + 1)
        for index in range(note_start, note_start + len(b"[**P2: kicked?"))
    ]
    assert "note_quarantine" in record.parser_warnings
    assert record.training_eligible is False


def test_parser_resolves_superscript_and_subscript_tokens_to_independent_spans() -> (
    None
):
    record = _parse("x^2 and y_{ij}")

    assert record.parsed_text == "x2 and yij"
    assert [(span.label, span.start, span.end) for span in record.style_spans] == [
        (StyleLabel.SUPERSCRIPT, 1, 2),
        (StyleLabel.SUBSCRIPT, 8, 10),
    ]


def test_parser_retains_block_context_without_an_inline_style() -> None:
    record = _parse("/#\n<b>quote</b>\n#/")

    assert record.structural_context == ("display_block",)
    assert [(span.label, span.start, span.end) for span in record.style_spans] == [
        (StyleLabel.BOLD, 1, 6)
    ]


def test_unresolved_font_change_is_unknown_and_quarantined() -> None:
    record = _parse('"<f>spuuns</f>."')

    span = record.style_spans[0]
    assert span.label is StyleLabel.FONT_OTHER_REVIEWED
    assert span.state is KnowledgeState.UNKNOWN
    assert "ambiguous_font_change" in span.warnings
    assert record.training_eligible is False


def test_project_authorized_underlining_is_positive_and_evidence_bound() -> None:
    comments = b"Use <u> for printed underlining."
    rule = ProjectRule(
        project_id="project-1",
        project_comments_sha256=hashlib.sha256(comments).hexdigest(),
        tag_name="u",
        label=StyleLabel.UNDERLINE,
        rule_ref="project-1/u/v1",
    )
    parser = F2Parser(ProjectRuleRegistry((rule,)))

    record = _parse("<u>underlined</u>", project_comments=comments, parser=parser)

    span = record.style_spans[0]
    assert span.label is StyleLabel.UNDERLINE
    assert span.state is KnowledgeState.POSITIVE
    assert span.rule_ref == "project-1/u/v1"
    assert record.training_eligible is True


def test_project_comments_bytes_require_an_explicit_matching_artifact() -> None:
    with pytest.raises(ValueError, match="project_comments_artifact"):
        _parse(
            "<u>underlined</u>",
            project_comments=b"Use <u> for printed underlining.",
            include_project_comments_artifact=False,
        )


def test_unapproved_underlining_is_unknown_and_quarantined() -> None:
    record = _parse("<u>underlined</u>", project_comments=b"No underline rule.")

    span = record.style_spans[0]
    assert span.label is StyleLabel.UNDERLINE
    assert span.state is KnowledgeState.UNKNOWN
    assert "unapproved_underline" in span.warnings
    assert record.training_eligible is False


def test_malformed_input_remains_serializable_but_ineligible() -> None:
    record = _parse("<sc>unclosed")

    assert "unclosed_tag" in record.parser_warnings
    assert record.training_eligible is False
    assert record.to_json_bytes()


@pytest.mark.parametrize("tag_name", ["i", "sc", "g", "f", "u"])
def test_unclosed_style_tags_are_quarantined_without_synthesized_spans(
    tag_name: str,
) -> None:
    record = _parse(f"<{tag_name}>unclosed")
    clean = _parse("<i>closed</i>")

    assert record.style_spans == ()
    assert record.parser_controls[0].tag_name == tag_name
    assert record.parser_controls[0].kind is ParserControlKind.UNCLOSED_STYLE_TAG
    assert record.parser_controls[0].source_slices
    assert "unclosed_tag" in record.parser_warnings
    assert record.training_eligible is False
    assert len(clean.style_spans) == 1
    assert clean.parser_warnings == ()


@pytest.mark.parametrize(
    "page_text",
    ["#/text", "/*text#/", "/#text"],
)
def test_malformed_blocks_are_retained_but_block_training(page_text: str) -> None:
    record = _parse(page_text)

    assert record.training_eligible is False
    assert any(warning.endswith("block") for warning in record.parser_warnings)


def test_unclosed_font_change_keeps_its_ambiguity_warning_on_the_page() -> None:
    record = _parse("<f>unclosed")

    assert "ambiguous_font_change" in record.parser_warnings
    assert "unclosed_tag" in record.parser_warnings


@pytest.mark.skipif(
    not _MOUNTED_F2_PATH.is_file(),
    reason="mounted PGDP corpus fixture is not available",
)
def test_optional_mounted_pgdp_page_has_supported_markup() -> None:
    project_root = Path("/workspaces/pdomain-data/pgdp-corpus/projectID6814e35a6b014")
    artifact = (project_root / "rounds" / "F2.json").read_bytes()
    identity = _identity(f2_artifact=artifact, project_id="6814e35a6b014")

    record = F2Parser().parse_page(
        f2_artifact_bytes=artifact,
        page_key="011.png",
        identity=identity,
        project_comments_bytes=None,
        guideline_version="pgdp-guidelines-2026-08-21",
    )

    assert record.f2_page_key == "011.png"
    assert any(span.label is StyleLabel.ITALIC for span in record.style_spans)
    assert any(span.label is StyleLabel.SMALL_CAPS for span in record.style_spans)
    assert record.structural_context == ("poetry_block",)


def test_parser_reuses_a_bounded_lexical_index_by_artifact_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = b'{"001.png":"<i>one</i>","002.png":"<b>two</b>"}'
    calls = 0
    original_read = parser_module.read_lexical_index

    def counted_read(payload: bytes) -> LexicalF2Index:
        nonlocal calls
        calls += 1
        return original_read(payload)

    monkeypatch.setattr(parser_module, "read_lexical_index", counted_read)
    parser = F2Parser(document_cache_size=1)
    identity = _identity(f2_artifact=artifact)

    parser.parse_page(
        f2_artifact_bytes=artifact,
        page_key="001.png",
        identity=identity,
        guideline_version="pgdp-guidelines-2026-08-21",
    )
    parser.parse_page(
        f2_artifact_bytes=artifact,
        page_key="002.png",
        identity=identity,
        guideline_version="pgdp-guidelines-2026-08-21",
    )

    assert calls == 1


def test_parser_evicts_the_oldest_cached_document_deterministically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_artifact = b'{"001.png":"one"}'
    second_artifact = b'{"001.png":"two"}'
    calls = 0
    original_read = parser_module.read_lexical_index

    def counted_read(payload: bytes) -> LexicalF2Index:
        nonlocal calls
        calls += 1
        return original_read(payload)

    monkeypatch.setattr(parser_module, "read_lexical_index", counted_read)
    parser = F2Parser(document_cache_size=1)

    for artifact in (first_artifact, second_artifact, first_artifact):
        parser.parse_page(
            f2_artifact_bytes=artifact,
            page_key="001.png",
            identity=_identity(f2_artifact=artifact),
            guideline_version="pgdp-guidelines-2026-08-21",
        )

    assert calls == 3


def test_parser_tokenizes_only_the_selected_page_from_a_cached_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = b'{"001.png":"<i>one</i>","002.png":"<b>two</b>"}'
    selected_pages: list[str] = []
    original_read = parser_module.read_f2_json_page

    def counted_read(
        payload: bytes, page_key: str, index: LexicalF2Index
    ) -> F2JsonPage:
        selected_pages.append(page_key)
        return original_read(payload, page_key, index)

    monkeypatch.setattr(parser_module, "read_f2_json_page", counted_read)
    parser = F2Parser(document_cache_size=1)
    identity = _identity(f2_artifact=artifact)

    parser.parse_page(
        f2_artifact_bytes=artifact,
        page_key="002.png",
        identity=identity,
        guideline_version="pgdp-guidelines-2026-08-21",
    )

    assert selected_pages == ["002.png"]
    assert all(
        type(cached_index).__name__ == "LexicalF2Index"
        for cached_index in parser._index_cache.values()
    )
