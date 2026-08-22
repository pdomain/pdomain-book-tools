from __future__ import annotations

import base64
import hashlib
import json
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from pdomain_book_tools.geometry import BoundingBox, Point
from pdomain_book_tools.typography import (
    TYPOGRAPHY_PAGE_RECORD_EXTERNAL_F2_SCHEMA_VERSION,
    TYPOGRAPHY_PAGE_RECORD_LEGACY_SCHEMA_VERSION,
    AlignmentEvidence,
    ArtifactRef,
    ArtifactReference,
    ArtifactSource,
    ConfidenceTier,
    Grapheme,
    KnowledgeState,
    LabelSource,
    OcrTokenRef,
    ParserControlEvidence,
    ParserControlKind,
    ParserNormalizationEvidence,
    ParserNormalizationKind,
    ParserNoteEvidence,
    ParserNoteStatus,
    SourceCoordinateSpace,
    SourceSlice,
    StyleLabel,
    StyleSpan,
    TargetCoordinateSpace,
    TextIdentity,
    TypographyPageRecord,
)

_F2_BYTES = b'{"001.png":"<i>x</i>"}'
_F2_SHA256 = hashlib.sha256(_F2_BYTES).hexdigest()
_PAGE_TEXT = "<i>x</i>"
_PAGE_SHA256 = hashlib.sha256(_PAGE_TEXT.encode()).hexdigest()
_IMAGE_SHA256 = "b" * 64


def _artifact(*, source: ArtifactSource, sha256: str) -> ArtifactRef:
    return ArtifactRef(
        source=source,
        source_url=None,
        local_path="artifact.bin",
        retrieved_at=datetime(2026, 8, 21, tzinfo=UTC),
        sha256=sha256,
        version="1",
        license_ref=None,
    )


def _record() -> TypographyPageRecord:
    image_artifact = _artifact(source=ArtifactSource.HUMAN, sha256=_IMAGE_SHA256)
    f2_artifact = _artifact(source=ArtifactSource.PGDP_F2, sha256=_F2_SHA256)
    source_slice = SourceSlice(
        artifact_sha256=_F2_SHA256,
        byte_start=15,
        byte_end=16,
    )
    style_span = StyleSpan(
        label=StyleLabel.ITALIC,
        start=0,
        end=1,
        state=KnowledgeState.POSITIVE,
        label_source=LabelSource.F2,
        confidence_tier=ConfidenceTier.GOLD,
        source_slices=(source_slice,),
        rule_ref="pgdp-f2:i",
        semantic_reason=None,
        warnings=(),
    )
    return TypographyPageRecord(
        schema_version="1.0",
        identity=TextIdentity(
            work_id="work-1",
            edition_id="edition-1",
            book_id="book-1",
            project_id="project-1",
            pg_ebook_id=None,
            se_repository=None,
            page_id="001.png",
            image_artifact=image_artifact,
            text_artifacts=(f2_artifact,),
        ),
        original_f2_artifact_base64=base64.b64encode(_F2_BYTES).decode(),
        original_f2_artifact_sha256=_F2_SHA256,
        f2_page_key="001.png",
        f2_page_value_lexical_byte_range=(11, 21),
        f2_decoded_page_utf8_sha256=_PAGE_SHA256,
        parsed_text="x",
        graphemes=(
            Grapheme(
                index=0,
                text="x",
                source_slices=(source_slice,),
                normalized_from=None,
            ),
        ),
        ocr_tokens=(
            OcrTokenRef(
                token_id="word-1",
                text="x",
                confidence=0.99,
                bbox=BoundingBox(
                    top_left=Point(0, 0, is_normalized=False),
                    bottom_right=Point(10, 10, is_normalized=False),
                ),
                line_id="line-1",
                grapheme_start=0,
                grapheme_end=1,
                alignment_id="alignment-1",
            ),
        ),
        style_spans=(style_span,),
        structural_context=("body",),
        parser_warnings=("fixture_warning",),
        alignments=(
            AlignmentEvidence(
                alignment_id="alignment-1",
                method="exact",
                source_artifact_sha256=_F2_SHA256,
                target_artifact_sha256=_IMAGE_SHA256,
                source_coordinate_space=SourceCoordinateSpace.SOURCE_GRAPHEMES,
                target_coordinate_space=TargetCoordinateSpace.OCR_GRAPHEMES,
                source_range=(0, 1),
                target_range=(0, 1),
                operations=(),
                score=1.0,
                margin=None,
                alternatives=(),
                accepted=True,
            ),
        ),
        project_comments_artifact=None,
        guideline_version="2026-08-21",
    )


def test_page_record_preserves_full_f2_artifact_bytes() -> None:
    record = _record()

    encoded = record.to_json_bytes()
    decoded = TypographyPageRecord.from_json_bytes(encoded)

    assert base64.b64decode(decoded.original_f2_artifact_base64 or "") == _F2_BYTES
    assert decoded.to_json_bytes() == encoded


def test_legacy_embedded_f2_wire_omits_external_reference_field() -> None:
    payload = json.loads(_record().to_json_bytes())

    assert payload["schema_version"] == TYPOGRAPHY_PAGE_RECORD_LEGACY_SCHEMA_VERSION
    assert "external_f2_artifact" not in payload


def test_page_record_accepts_external_f2_artifact_without_embedded_bytes() -> None:
    data = _record().model_dump(mode="json")
    data["schema_version"] = TYPOGRAPHY_PAGE_RECORD_EXTERNAL_F2_SCHEMA_VERSION
    data["original_f2_artifact_base64"] = None
    data["external_f2_artifact"] = ArtifactReference(
        artifact_id="pgdp-f2",
        relative_path="artifacts/F2.json",
        sha256=_F2_SHA256,
        media_type="application/json",
    ).model_dump(mode="json")

    record = TypographyPageRecord.model_validate(data)

    assert record.original_f2_artifact_base64 is None
    assert record.external_f2_artifact is not None
    assert record.external_f2_artifact.sha256 == _F2_SHA256
    assert record.revalidate_external_f2_artifact(_F2_BYTES) is None
    assert (
        json.loads(record.to_json_bytes())["external_f2_artifact"]["sha256"]
        == _F2_SHA256
    )


def test_legacy_schema_rejects_an_external_f2_artifact() -> None:
    data = _record().model_dump(mode="json")
    data["external_f2_artifact"] = ArtifactReference(
        artifact_id="pgdp-f2",
        relative_path="artifacts/F2.json",
        sha256=_F2_SHA256,
    ).model_dump(mode="json")

    with pytest.raises(ValidationError, match=r"schema_version 1\.0"):
        TypographyPageRecord.model_validate(data)


def test_external_schema_requires_an_external_f2_artifact() -> None:
    data = _record().model_dump(mode="json")
    data["schema_version"] = TYPOGRAPHY_PAGE_RECORD_EXTERNAL_F2_SCHEMA_VERSION

    with pytest.raises(ValidationError, match=r"schema_version 1\.1"):
        TypographyPageRecord.model_validate(data)


def test_external_f2_record_model_copy_revalidates_artifact_reference() -> None:
    data = _record().model_dump(mode="json")
    data["schema_version"] = TYPOGRAPHY_PAGE_RECORD_EXTERNAL_F2_SCHEMA_VERSION
    data["original_f2_artifact_base64"] = None
    data["external_f2_artifact"] = ArtifactReference(
        artifact_id="pgdp-f2",
        relative_path="artifacts/F2.json",
        sha256=_F2_SHA256,
    ).model_dump(mode="json")
    record = TypographyPageRecord.model_validate(data)
    corrupted_reference = ArtifactReference.model_construct(
        artifact_id="",
        relative_path="../F2.json",
        sha256=_F2_SHA256,
        media_type=None,
    )

    with pytest.raises(ValidationError, match="artifact_id"):
        record.model_copy(update={"external_f2_artifact": corrupted_reference})


def test_external_f2_revalidation_reconstructs_corrupted_record() -> None:
    data = _record().model_dump(mode="json")
    data["schema_version"] = TYPOGRAPHY_PAGE_RECORD_EXTERNAL_F2_SCHEMA_VERSION
    data["original_f2_artifact_base64"] = None
    data["external_f2_artifact"] = ArtifactReference(
        artifact_id="pgdp-f2",
        relative_path="artifacts/F2.json",
        sha256=_F2_SHA256,
    ).model_dump(mode="json")
    record = TypographyPageRecord.model_validate(data)
    corrupted_reference = ArtifactReference.model_construct(
        artifact_id="",
        relative_path="../F2.json",
        sha256=_F2_SHA256,
        media_type=None,
    )
    object.__setattr__(record, "external_f2_artifact", corrupted_reference)

    with pytest.raises(ValidationError, match="artifact_id"):
        record.revalidate_external_f2_artifact(_F2_BYTES)


def test_external_f2_record_rejects_reference_hash_drift() -> None:
    data = _record().model_dump(mode="json")
    data["schema_version"] = TYPOGRAPHY_PAGE_RECORD_EXTERNAL_F2_SCHEMA_VERSION
    data["original_f2_artifact_base64"] = None
    data["external_f2_artifact"] = ArtifactReference(
        artifact_id="pgdp-f2",
        relative_path="artifacts/F2.json",
        sha256="0" * 64,
    ).model_dump(mode="json")

    with pytest.raises(ValidationError, match=r"external_f2_artifact\.sha256"):
        TypographyPageRecord.model_validate(data)


def test_external_f2_record_revalidates_its_lexical_range_against_supplied_bytes() -> (
    None
):
    data = _record().model_dump(mode="json")
    data["schema_version"] = TYPOGRAPHY_PAGE_RECORD_EXTERNAL_F2_SCHEMA_VERSION
    data["original_f2_artifact_base64"] = None
    data["external_f2_artifact"] = ArtifactReference(
        artifact_id="pgdp-f2",
        relative_path="artifacts/F2.json",
        sha256=_F2_SHA256,
    ).model_dump(mode="json")
    data["f2_page_value_lexical_byte_range"] = [12, 20]

    record = TypographyPageRecord.model_validate(data)

    with pytest.raises(ValueError, match="lexical"):
        record.revalidate_external_f2_artifact(_F2_BYTES)


def test_page_record_rejects_embedded_and_external_f2_artifacts_together() -> None:
    data = _record().model_dump(mode="json")
    data["schema_version"] = TYPOGRAPHY_PAGE_RECORD_EXTERNAL_F2_SCHEMA_VERSION
    data["external_f2_artifact"] = ArtifactReference(
        artifact_id="pgdp-f2",
        relative_path="artifacts/F2.json",
        sha256=_F2_SHA256,
    ).model_dump(mode="json")

    with pytest.raises(ValidationError, match="mutually exclusive"):
        TypographyPageRecord.model_validate(data)


def test_page_record_rejects_f2_page_evidence_without_an_artifact_representation() -> (
    None
):
    data = _record().model_dump(mode="json")
    data["original_f2_artifact_base64"] = None

    with pytest.raises(ValidationError, match="embedded or external"):
        TypographyPageRecord.model_validate(data)


def test_external_f2_record_rejects_grapheme_outside_declared_lexical_range() -> None:
    data = _record().model_dump(mode="json")
    data["schema_version"] = TYPOGRAPHY_PAGE_RECORD_EXTERNAL_F2_SCHEMA_VERSION
    data["original_f2_artifact_base64"] = None
    data["external_f2_artifact"] = ArtifactReference(
        artifact_id="pgdp-f2",
        relative_path="artifacts/F2.json",
        sha256=_F2_SHA256,
    ).model_dump(mode="json")
    data["graphemes"][0]["source_slices"][0]["byte_start"] = 0

    with pytest.raises(ValidationError, match="lexical byte range"):
        TypographyPageRecord.model_validate(data)


def test_page_record_rejects_forged_grapheme_f2_provenance() -> None:
    record = _record()
    forged_grapheme = record.graphemes[0].model_copy(
        update={
            "source_slices": (
                SourceSlice(
                    artifact_sha256=_IMAGE_SHA256,
                    byte_start=15,
                    byte_end=16,
                ),
            )
        }
    )
    with pytest.raises(ValidationError, match="F2-backed grapheme"):
        record.model_copy(update={"graphemes": (forged_grapheme,)})


def test_page_record_rejects_forged_style_f2_bounds() -> None:
    record = _record()
    forged_span = record.style_spans[0].model_copy(
        update={
            "source_slices": (
                SourceSlice(
                    artifact_sha256=_F2_SHA256,
                    byte_start=15,
                    byte_end=len(_F2_BYTES) + 1,
                ),
            )
        }
    )
    with pytest.raises(ValidationError, match="F2-backed style"):
        record.model_copy(update={"style_spans": (forged_span,)})


def test_page_record_rejects_forged_alignment_artifact_hashes() -> None:
    record = _record()
    forged_source = record.alignments[0].model_copy(
        update={"source_artifact_sha256": "c" * 64}
    )
    forged_target = record.alignments[0].model_copy(
        update={"target_artifact_sha256": _F2_SHA256}
    )

    with pytest.raises(ValidationError, match="alignment source_artifact"):
        TypographyPageRecord.model_validate(
            record.model_copy(update={"alignments": (forged_source,)}).model_dump()
        )
    with pytest.raises(ValidationError, match="OCR alignment target"):
        TypographyPageRecord.model_validate(
            record.model_copy(update={"alignments": (forged_target,)}).model_dump()
        )


def test_page_record_rejects_ocr_token_ranges_beyond_the_token_count() -> None:
    record = _record()
    second_grapheme = record.graphemes[0].model_copy(update={"index": 1})
    expanded_token = record.ocr_tokens[0].model_copy(
        update={"text": "xx", "grapheme_end": 2}
    )
    token_alignment = record.alignments[0].model_copy(
        update={
            "target_coordinate_space": TargetCoordinateSpace.OCR_TOKENS,
            "target_range": (0, 2),
        }
    )
    with pytest.raises(ValidationError, match="OCR token count"):
        record.model_copy(
            update={
                "parsed_text": "xx",
                "graphemes": (record.graphemes[0], second_grapheme),
                "ocr_tokens": (expanded_token,),
                "alignments": (token_alignment,),
            }
        )


@pytest.mark.parametrize(
    "runner_up_operations",
    [
        [
            {
                "kind": "match",
                "source_range": (0, 1),
                "target_range": (0, 0),
            }
        ],
        [
            {
                "kind": "match",
                "source_range": (0, 2),
                "target_range": (0, 2),
            },
            {
                "kind": "match",
                "source_range": (1, 2),
                "target_range": (1, 2),
            },
        ],
    ],
)
def test_alignment_evidence_rejects_forged_runner_up_operations(
    runner_up_operations: list[dict[str, object]],
) -> None:
    data = _record().alignments[0].model_dump()
    data["source_range"] = (0, 2)
    data["target_range"] = (0, 2)
    data["runner_up_operations"] = runner_up_operations

    with pytest.raises(ValidationError, match=r"runner_up_operations|must consume"):
        AlignmentEvidence.model_validate(data)


def test_page_record_defaults_and_serializes_training_eligibility() -> None:
    record = _record()
    legacy_data = record.model_dump(mode="json")
    legacy_data.pop("training_eligible", None)

    restored = TypographyPageRecord.model_validate(legacy_data)

    assert restored.training_eligible is True
    assert record.model_dump(mode="json")["training_eligible"] is True


def test_page_record_round_trips_typed_parser_evidence() -> None:
    record = _record().model_copy(
        update={
            "parser_notes": (
                ParserNoteEvidence(
                    raw_text="[**P1: unsure]",
                    page_review_content="P1: unsure",
                    question_status=ParserNoteStatus.COMMENT,
                    source_slices=(
                        SourceSlice(
                            artifact_sha256=_F2_SHA256,
                            byte_start=11,
                            byte_end=21,
                        ),
                    ),
                ),
            ),
            "normalization_operations": (
                ParserNormalizationEvidence(
                    kind=ParserNormalizationKind.LETTER_SPACE_REMOVED,
                    source_slices=(
                        SourceSlice(
                            artifact_sha256=_F2_SHA256,
                            byte_start=11,
                            byte_end=12,
                        ),
                    ),
                    replacement_text="",
                    grapheme_indices=(),
                ),
            ),
        }
    )

    restored = TypographyPageRecord.from_json_bytes(record.to_json_bytes())

    assert restored == record


@pytest.mark.parametrize(
    ("field_name", "evidence"),
    [
        (
            "parser_notes",
            {
                "raw_text": "[**P1: unsure]",
                "page_review_content": "P1: unsure",
                "question_status": "comment",
                "source_slices": [
                    {
                        "artifact_sha256": _IMAGE_SHA256,
                        "byte_start": 11,
                        "byte_end": 21,
                    }
                ],
            },
        ),
        (
            "normalization_operations",
            {
                "kind": "letter_space_removed",
                "source_slices": [
                    {
                        "artifact_sha256": _F2_SHA256,
                        "byte_start": 11,
                        "byte_end": len(_F2_BYTES) + 1,
                    }
                ],
                "replacement_text": "",
                "grapheme_indices": [],
            },
        ),
    ],
)
def test_page_record_rejects_forged_parser_evidence_source_slices(
    field_name: str, evidence: dict[str, object]
) -> None:
    data = _record().model_dump(mode="json")
    data[field_name] = [evidence]

    with pytest.raises(ValidationError, match="parser evidence"):
        TypographyPageRecord.model_validate(data)


def test_page_record_binds_unresolved_control_evidence_to_f2_bytes() -> None:
    data = _record().model_dump(mode="json")
    data["parser_controls"] = [
        ParserControlEvidence(
            kind=ParserControlKind.UNCLOSED_STYLE_TAG,
            tag_name="i",
            raw_text="<i>",
            source_slices=(
                SourceSlice(
                    artifact_sha256=_F2_SHA256,
                    byte_start=11,
                    byte_end=14,
                ),
            ),
        ).model_dump(mode="json")
    ]

    assert TypographyPageRecord.model_validate(data).parser_controls[0].tag_name == "i"


def test_page_record_rejects_mismatched_f2_hash() -> None:
    data = _record().model_dump(mode="json")
    data["original_f2_artifact_sha256"] = "0" * 64

    with pytest.raises(ValidationError, match="original_f2_artifact_sha256"):
        TypographyPageRecord.model_validate(data)


def test_page_record_rejects_invalid_decoded_page_hash() -> None:
    data = _record().model_dump(mode="json")
    data["f2_decoded_page_utf8_sha256"] = "not-a-sha256"

    with pytest.raises(ValidationError, match="f2_decoded_page_utf8_sha256"):
        TypographyPageRecord.model_validate(data)


def test_page_record_rejects_invalid_lexical_range() -> None:
    data = _record().model_dump(mode="json")
    data["f2_page_value_lexical_byte_range"] = [21, 11]

    with pytest.raises(ValidationError, match="lexical"):
        TypographyPageRecord.model_validate(data)


def test_page_record_rejects_lexical_value_for_another_page() -> None:
    data = _record().model_dump(mode="json")
    data["f2_page_key"] = "002.png"

    with pytest.raises(ValidationError, match="f2_page_key"):
        TypographyPageRecord.model_validate(data)


def test_page_record_rejects_range_for_another_page_with_same_value() -> None:
    artifact_bytes = b'{"001.png":"<i>x</i>","002.png":"<i>x</i>"}'
    artifact_hash = hashlib.sha256(artifact_bytes).hexdigest()
    first_value_start = artifact_bytes.index(b'"<i>x</i>"')
    data = _record().model_dump(mode="json")
    data["original_f2_artifact_base64"] = base64.b64encode(artifact_bytes).decode()
    data["original_f2_artifact_sha256"] = artifact_hash
    data["identity"]["text_artifacts"][0]["sha256"] = artifact_hash
    data["f2_page_key"] = "002.png"
    data["f2_page_value_lexical_byte_range"] = [
        first_value_start,
        first_value_start + len(b'"<i>x</i>"'),
    ]

    with pytest.raises(ValidationError, match="lexical byte range"):
        TypographyPageRecord.model_validate(data)


def test_page_record_rejects_wrong_decoded_page_hash() -> None:
    data = _record().model_dump(mode="json")
    data["f2_decoded_page_utf8_sha256"] = "0" * 64

    with pytest.raises(ValidationError, match="decoded page"):
        TypographyPageRecord.model_validate(data)


def test_page_record_rejects_noncontiguous_graphemes() -> None:
    data = _record().model_dump(mode="json")
    data["graphemes"][0]["index"] = 1

    with pytest.raises(ValidationError, match="contiguous"):
        TypographyPageRecord.model_validate(data)


def test_page_record_rejects_ocr_token_outside_page() -> None:
    data = _record().model_dump(mode="json")
    data["ocr_tokens"][0]["grapheme_end"] = 2

    with pytest.raises(ValidationError, match="OCR token"):
        TypographyPageRecord.model_validate(data)


def test_page_record_rejects_unknown_token_alignment() -> None:
    data = _record().model_dump(mode="json")
    data["ocr_tokens"][0]["alignment_id"] = "missing"

    with pytest.raises(ValidationError, match="alignment_id"):
        TypographyPageRecord.model_validate(data)


def test_artifact_requires_version_and_valid_sha256() -> None:
    data = _artifact(source=ArtifactSource.HUMAN, sha256=_IMAGE_SHA256).model_dump()
    data["version"] = ""
    data["sha256"] = "bad"

    with pytest.raises(ValidationError):
        ArtifactRef.model_validate(data)


def test_source_slice_requires_valid_artifact_sha256() -> None:
    with pytest.raises(ValidationError, match="artifact_sha256"):
        SourceSlice(
            artifact_sha256="bad",
            byte_start=0,
            byte_end=1,
        )


def test_ocr_token_rejects_invalid_confidence() -> None:
    data = _record().ocr_tokens[0].model_dump()
    data["confidence"] = 1.1

    with pytest.raises(ValidationError, match="confidence"):
        OcrTokenRef.model_validate(data)


def test_alignment_alternatives_are_recursively_immutable() -> None:
    data = _record().alignments[0].model_dump()
    data["alternatives"] = [{"operations": ["replace"]}]

    evidence = AlignmentEvidence.model_validate(data)
    alternative = evidence.alternatives[0]

    assert not hasattr(alternative, "__setitem__")
    assert isinstance(alternative["operations"], tuple)
