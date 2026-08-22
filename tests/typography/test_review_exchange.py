"""Portable typography review and exchange contract tests."""

from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError

from pdomain_book_tools.typography.exchange import (
    ArtifactReference,
    CoordinateTransform,
    CoordinateTransformStage,
    CorrectionBundle,
    Evidence,
    LabelingBundle,
    ModelRun,
    ModelRunPurpose,
    PageGeometry,
    ReplacementArtifact,
    SourceOrientation,
    WordGeometry,
)
from pdomain_book_tools.typography.labels import ConfidenceTier, LabelSource
from pdomain_book_tools.typography.review import (
    CorrectionDecision,
    LabelState,
    ReviewDecision,
    ReviewState,
    TypographyCorrection,
    TypographySpan,
    TypographyTaxonomy,
    TypographyTaxonomyLabel,
    WordTypography,
    make_merged_word_id,
    make_split_word_id,
    make_word_id,
)
from pdomain_book_tools.typography.spans import GRAPHEME_SEGMENTATION_VERSION


def _taxonomy() -> TypographyTaxonomy:
    return TypographyTaxonomy(
        version="2026.08",
        labels=(
            TypographyTaxonomyLabel(
                value="italic",
                display_name="Italic",
                required_for_completion=True,
                trainable=True,
            ),
            TypographyTaxonomyLabel(
                value="bold",
                display_name="Bold",
                required_for_completion=True,
                trainable=True,
            ),
            TypographyTaxonomyLabel(
                value="printer_mark",
                display_name="Printer mark",
                required_for_completion=False,
                trainable=False,
            ),
        ),
    )


def _word(*, text: str = "e\u0301\U0001f469\u200d\U0001f4bb") -> WordTypography:
    taxonomy = _taxonomy()
    word_id = make_word_id(
        project_id="project-1",
        page_id="page-1",
        reading_order=3,
        text=text,
    )
    return WordTypography(
        word_id=word_id,
        text=text,
        text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        page_content_sha256="a" * 64,
        image_artifact_sha256="b" * 64,
        grapheme_map_version=GRAPHEME_SEGMENTATION_VERSION,
        taxonomy_version=taxonomy.version,
        taxonomy_hash=taxonomy.taxonomy_hash,
        label_states={"italic": LabelState.POSITIVE, "bold": LabelState.NEGATIVE},
        spans=(
            TypographySpan(
                span_id="span-1",
                label="italic",
                start=0,
                end=2,
                label_source=LabelSource.HUMAN,
                confidence_tier=ConfidenceTier.GOLD,
                alignment_evidence_id="evidence-1",
            ),
        ),
        source_evidence_ids=("evidence-1",),
        warnings=("fixture warning",),
        review_state=ReviewState.REVIEWED,
    )


def _transform_chain(
    orientation: SourceOrientation = SourceOrientation.UPRIGHT,
) -> tuple[CoordinateTransform, CoordinateTransform]:
    orientation_target_sizes = {
        SourceOrientation.UPRIGHT: (100, 200),
        SourceOrientation.ROTATE_90_CLOCKWISE: (200, 100),
        SourceOrientation.ROTATE_180: (100, 200),
        SourceOrientation.ROTATE_90_COUNTERCLOCKWISE: (200, 100),
    }
    orientation_affines = {
        SourceOrientation.UPRIGHT: (1, 0, 0, 0, 1, 0),
        SourceOrientation.ROTATE_90_CLOCKWISE: (0, -1, 200, 1, 0, 0),
        SourceOrientation.ROTATE_180: (-1, 0, 100, 0, -1, 200),
        SourceOrientation.ROTATE_90_COUNTERCLOCKWISE: (0, 1, 0, -1, 0, 100),
    }
    orientation_target_width, orientation_target_height = orientation_target_sizes[
        orientation
    ]
    crop_is_identity = (orientation_target_width, orientation_target_height) == (
        100,
        200,
    )
    return (
        CoordinateTransform(
            transform_id="orientation-transform",
            stage=CoordinateTransformStage.ORIENTATION,
            source_space="scan_pixels",
            target_space="oriented_pixels",
            source_coordinate_space_id="scan-v1",
            target_coordinate_space_id="oriented-v1",
            source_orientation=orientation,
            source_artifact_sha256="b" * 64,
            target_artifact_sha256="b" * 64,
            source_width=100,
            source_height=200,
            target_width=orientation_target_width,
            target_height=orientation_target_height,
            crop_recipe="identity",
            crop_recipe_version="1",
            padding_px=0,
            resampling="nearest",
            preprocessing_sha256="b" * 64,
            transform_version="1",
            affine=orientation_affines[orientation],
        ),
        CoordinateTransform(
            transform_id="crop-transform",
            stage=CoordinateTransformStage.CROP,
            source_space="oriented_pixels",
            target_space="image_pixels",
            source_coordinate_space_id="oriented-v1",
            target_coordinate_space_id="image-v1",
            source_orientation=SourceOrientation.UPRIGHT,
            source_artifact_sha256="b" * 64,
            target_artifact_sha256="b" * 64,
            source_width=orientation_target_width,
            source_height=orientation_target_height,
            target_width=100,
            target_height=200,
            crop_recipe="identity" if crop_is_identity else "resize",
            crop_recipe_version="1",
            padding_px=0,
            resampling="nearest",
            preprocessing_sha256="b" * 64,
            transform_version="1",
            affine=(1, 0, 0, 0, 1, 0) if crop_is_identity else (0.5, 0, 0, 0, 2, 0),
        ),
    )


def _apply_affine(
    affine: tuple[float, float, float, float, float, float],
    point: tuple[float, float],
) -> tuple[float, float]:
    x, y = point
    a, b, c, d, e, f = affine
    return (a * x + b * y + c, d * x + e * y + f)


def _inbound_artifacts() -> tuple[ArtifactReference, ...]:
    return tuple(
        ArtifactReference(
            artifact_id=artifact_id,
            relative_path=f"inbound/{artifact_id}.json",
            sha256=digest * 64,
            media_type="application/json",
        )
        for artifact_id, digest in (
            ("page", "a"),
            ("page-image", "b"),
            ("ocr-model", "1"),
            ("ocr-config", "2"),
            ("region-model", "3"),
            ("region-config", "4"),
            ("region-preprocessing", "5"),
            ("ocr-result", "d"),
            ("region-result", "e"),
            ("page-head", "f"),
        )
    )


def _inbound_model_runs() -> tuple[ModelRun, ModelRun]:
    return (
        ModelRun(
            run_id="ocr-run",
            purpose=ModelRunPurpose.OCR,
            model_name="ocr",
            model_version="1",
            input_artifact_sha256="b" * 64,
            output_artifact_sha256="d" * 64,
            model_artifact_sha256="1" * 64,
            config_sha256="2" * 64,
            preprocessing_sha256="b" * 64,
        ),
        ModelRun(
            run_id="region-run",
            purpose=ModelRunPurpose.PAGE_REGION,
            model_name="region",
            model_version="1",
            input_artifact_sha256="b" * 64,
            output_artifact_sha256="e" * 64,
            model_artifact_sha256="3" * 64,
            config_sha256="4" * 64,
            preprocessing_sha256="5" * 64,
        ),
    )


def _inbound_page_geometry(
    orientation: SourceOrientation = SourceOrientation.UPRIGHT,
) -> PageGeometry:
    return PageGeometry(
        page_id="page-1",
        page_sha256="a" * 64,
        source_image_artifact_sha256="b" * 64,
        image_artifact_sha256="b" * 64,
        page_head_sha256="f" * 64,
        ocr_artifact_sha256="d" * 64,
        page_region_artifact_sha256="e" * 64,
        coordinate_space="image_pixels",
        coordinate_space_id="image-v1",
        source_orientation=orientation,
        source_image_width=100,
        source_image_height=200,
        transform_ids=("orientation-transform", "crop-transform"),
        ocr_model_run_id="ocr-run",
        page_region_model_run_id="region-run",
        image_width=100,
        image_height=200,
    )


def _inbound_geometry_bundle(orientation: SourceOrientation) -> LabelingBundle:
    word = _word()
    geometry = WordGeometry(
        word_id=word.word_id,
        word_revision=word.word_revision,
        page_sha256="a" * 64,
        page_head_sha256="f" * 64,
        image_artifact_sha256="b" * 64,
        x0=0,
        y0=0,
        x1=1,
        y1=1,
        transform_id="crop-transform",
        coordinate_space_id="image-v1",
        source_orientation=orientation,
    )
    return LabelingBundle(
        bundle_id=None,
        schema_version="0.24.0",
        configuration_hash="e" * 64,
        taxonomy=_taxonomy(),
        page_id="page-1",
        page_sha256="a" * 64,
        image_sha256="b" * 64,
        text_sha256="c" * 64,
        page_head_sha256="f" * 64,
        artifacts=_inbound_artifacts(),
        words=(word,),
        page_geometry=_inbound_page_geometry(orientation),
        geometry=(geometry,),
        evidence=(
            Evidence(
                evidence_id="evidence-1",
                artifact_id="page-image",
                artifact_sha256="b" * 64,
                byte_start=0,
                byte_end=1,
            ),
        ),
        model_runs=_inbound_model_runs(),
        coordinate_transforms=_transform_chain(orientation),
    )


def test_taxonomy_hash_preserves_label_order_and_rejects_stale_value() -> None:
    taxonomy = _taxonomy()
    reversed_taxonomy = TypographyTaxonomy(
        version=taxonomy.version,
        labels=tuple(reversed(taxonomy.labels)),
    )

    assert taxonomy.taxonomy_hash != reversed_taxonomy.taxonomy_hash
    with pytest.raises(ValidationError, match="taxonomy_hash"):
        TypographyTaxonomy(
            version=taxonomy.version,
            labels=taxonomy.labels,
            taxonomy_hash="0" * 64,
        )


def test_word_typography_uses_unicode_graphemes_and_allows_overlapping_labels() -> None:
    word = _word()

    assert word.grapheme_count == 2
    assert word.spans[0].end == 2
    assert word.is_complete(_taxonomy())
    assert word.missing_required_labels(_taxonomy()) == ()


def test_unknown_is_not_reviewed_regular_text() -> None:
    taxonomy = _taxonomy()
    word = _word().model_copy(
        update={
            "label_states": {"italic": LabelState.UNKNOWN, "bold": LabelState.NEGATIVE},
            "spans": (),
            "review_state": ReviewState.DEFERRED,
        }
    )

    assert not word.is_complete(taxonomy)
    assert word.missing_required_labels(taxonomy) == ("italic",)


def test_word_rejects_stale_text_hash_and_incompatible_positive_span() -> None:
    word = _word()
    with pytest.raises(ValidationError, match="text_sha256"):
        WordTypography.model_validate({**word.model_dump(), "text_sha256": "0" * 64})
    with pytest.raises(ValidationError, match="positive label state"):
        WordTypography.model_validate(
            {
                **word.model_dump(),
                "label_states": {
                    "italic": LabelState.NEGATIVE,
                    "bold": LabelState.NEGATIVE,
                },
            }
        )


def test_word_rejects_positive_label_state_without_a_positive_span() -> None:
    word = _word()

    with pytest.raises(ValidationError, match="requires a positive typography span"):
        WordTypography.model_validate(
            {
                **word.model_dump(),
                "label_states": {
                    "italic": LabelState.POSITIVE,
                    "bold": LabelState.NEGATIVE,
                },
                "spans": (),
            }
        )


def test_word_rejects_non_uuidv5_ids() -> None:
    word = _word()

    with pytest.raises(ValidationError, match="UUIDv5"):
        WordTypography.model_validate({**word.model_dump(), "word_id": "not-a-uuid"})


def test_word_ids_are_stable_and_split_merge_ids_are_deterministic() -> None:
    word_id = make_word_id(
        project_id="project-1", page_id="page-1", reading_order=3, text="word"
    )

    assert word_id == make_word_id(
        project_id="project-1", page_id="page-1", reading_order=3, text="word"
    )
    assert word_id == "02805e70-d172-53b5-9bcc-83cb75881516"
    assert make_split_word_id(word_id, split_index=0) == make_split_word_id(
        word_id, split_index=0
    )
    assert make_merged_word_id(
        (word_id, make_split_word_id(word_id, split_index=0))
    ) == make_merged_word_id((word_id, make_split_word_id(word_id, split_index=0)))


def test_correction_keeps_word_id_and_requires_a_revision_chain() -> None:
    word = _word()
    correction = TypographyCorrection(
        correction_id="correction-1",
        word_id=word.word_id,
        revision=1,
        supersedes_id=None,
        base_page_sha256="a" * 64,
        base_image_sha256="b" * 64,
        base_text_sha256=word.text_sha256,
        base_word_revision=0,
        replacement_text_sha256=word.text_sha256,
        replacement_page_sha256=word.page_content_sha256,
        replacement_image_sha256=word.image_artifact_sha256,
        replacement_page_head_sha256="f" * 64,
        replacement_word_revision=1,
        taxonomy_version=word.taxonomy_version,
        taxonomy_hash=word.taxonomy_hash,
        grapheme_map_version=word.grapheme_map_version,
        page_head_sha256="f" * 64,
        labeler_id="reviewer-1",
        decision=CorrectionDecision.APPROVED_EDIT,
        replacement=word,
    )

    assert correction.replacement is word
    with pytest.raises(ValidationError, match="replacement does not match"):
        TypographyCorrection.model_validate(
            {**correction.model_dump(), "replacement_text_sha256": "c" * 64}
        )
    with pytest.raises(ValidationError, match="supersedes_id"):
        TypographyCorrection.model_validate(
            {**correction.model_dump(), "revision": 2, "supersedes_id": None}
        )
    with pytest.raises(ValidationError, match="word_id"):
        TypographyCorrection.model_validate(
            {
                **correction.model_dump(),
                "replacement": {**word.model_dump(), "word_id": "different"},
            }
        )


def test_bundles_verify_paths_hashes_optional_geometry_and_canonical_ids() -> None:
    word = _word()
    artifact = ArtifactReference(
        artifact_id="page-image",
        relative_path="projects/project-1/page-1.png",
        sha256="b" * 64,
        media_type="image/png",
    )
    bundle = LabelingBundle(
        bundle_id=None,
        schema_version="0.24.0",
        configuration_hash="e" * 64,
        taxonomy=_taxonomy(),
        page_id="page-1",
        page_sha256="a" * 64,
        image_sha256="b" * 64,
        text_sha256="c" * 64,
        page_head_sha256="f" * 64,
        artifacts=(artifact,),
        words=(word,),
        geometry=None,
        evidence=(
            Evidence(
                evidence_id="evidence-1",
                artifact_id="page-image",
                artifact_sha256="b" * 64,
                byte_start=0,
                byte_end=1,
            ),
        ),
        model_runs=(),
        coordinate_transforms=(),
    )
    same_bundle = LabelingBundle.model_validate(bundle.model_dump())

    assert artifact.verify_bytes(b"payload") is False
    assert bundle.bundle_id == same_bundle.bundle_id
    assert bundle.geometry is None
    with pytest.raises(ValidationError, match="relative_path"):
        ArtifactReference(
            artifact_id="bad",
            relative_path="../secret",
            sha256="d" * 64,
            media_type=None,
        )
    with pytest.raises(ValidationError, match="bundle_id"):
        LabelingBundle.model_validate({**bundle.model_dump(), "bundle_id": "0" * 64})

    with_geometry = bundle.rebuild(
        geometry=(
            WordGeometry(
                word_id=word.word_id,
                word_revision=word.word_revision,
                page_sha256="a" * 64,
                page_head_sha256="f" * 64,
                image_artifact_sha256="b" * 64,
                x0=0,
                y0=0,
                x1=1,
                y1=1,
                transform_id="crop-transform",
                coordinate_space_id="image-v1",
                source_orientation=SourceOrientation.UPRIGHT,
            ),
        ),
        artifacts=_inbound_artifacts(),
        page_geometry=_inbound_page_geometry(),
        model_runs=_inbound_model_runs(),
        coordinate_transforms=_transform_chain(),
    )
    assert with_geometry.geometry is not None
    assert bundle.bundle_id is not None
    with pytest.raises(
        ValidationError, match="inbound page geometry must match bundle"
    ):
        LabelingBundle.model_validate(
            {
                **with_geometry.model_dump(),
                "page_geometry": {
                    **_inbound_page_geometry().model_dump(),
                    "page_sha256": "b" * 64,
                    "image_artifact_sha256": "a" * 64,
                    "page_head_sha256": "b" * 64,
                },
                "geometry": (),
                "bundle_id": None,
            }
        )
    with pytest.raises(ValidationError, match="inbound page and word geometry"):
        LabelingBundle.model_validate(
            {
                **with_geometry.model_dump(),
                "page_geometry": None,
                "bundle_id": None,
            }
        )
    with pytest.raises(ValidationError, match="model run hashes"):
        LabelingBundle.model_validate(
            {
                **with_geometry.model_dump(),
                "model_runs": (
                    {
                        **_inbound_model_runs()[0].model_dump(),
                        "output_artifact_sha256": "0" * 64,
                    },
                    _inbound_model_runs()[1].model_dump(),
                ),
                "bundle_id": None,
            }
        )
    with pytest.raises(ValidationError, match="orientation and crop"):
        LabelingBundle.model_validate(
            {
                **with_geometry.model_dump(),
                "page_geometry": {
                    **_inbound_page_geometry().model_dump(),
                    "transform_ids": ("crop-transform", "orientation-transform"),
                },
                "bundle_id": None,
            }
        )
    with pytest.raises(ValidationError, match="identity crop"):
        LabelingBundle.model_validate(
            {
                **with_geometry.model_dump(),
                "coordinate_transforms": (
                    _transform_chain()[0].model_dump(),
                    {
                        **_transform_chain()[1].model_dump(),
                        "affine": (0.5, 0, 0, 0, 1, 0),
                    },
                ),
                "bundle_id": None,
            }
        )
    correction_bundle = CorrectionBundle(
        bundle_id=None,
        schema_version="0.24.0",
        configuration_hash="e" * 64,
        labeling_bundle_id=bundle.bundle_id,
        corrections=(
            TypographyCorrection(
                correction_id="correction-1",
                word_id=word.word_id,
                revision=1,
                supersedes_id=None,
                base_page_sha256="a" * 64,
                base_image_sha256="b" * 64,
                base_text_sha256=word.text_sha256,
                base_word_revision=0,
                replacement_text_sha256=None,
                replacement_page_sha256=None,
                replacement_image_sha256=None,
                replacement_page_head_sha256=None,
                replacement_word_revision=None,
                taxonomy_version=word.taxonomy_version,
                taxonomy_hash=word.taxonomy_hash,
                grapheme_map_version=word.grapheme_map_version,
                page_head_sha256="f" * 64,
                labeler_id="reviewer-1",
                decision=CorrectionDecision.REJECT_SOURCE,
                replacement=None,
            ),
        ),
    )
    correction_bundle.validate_against(bundle)
    rebuilt_correction_bundle = correction_bundle.rebuild(
        corrections=correction_bundle.corrections
    )
    assert rebuilt_correction_bundle.bundle_id == correction_bundle.bundle_id
    geometry_absent_roundtrip = CorrectionBundle.model_validate(
        correction_bundle.model_dump(mode="json")
    )
    assert geometry_absent_roundtrip.page_geometry is None
    assert geometry_absent_roundtrip.geometry is None
    assert geometry_absent_roundtrip.model_runs == ()
    assert geometry_absent_roundtrip.coordinate_transforms == ()
    assert correction_bundle.bundle_id
    assert ReviewDecision.APPROVED.value == "approved"


def test_artifact_reference_verifies_matching_bytes() -> None:
    payload = b"portable evidence"
    artifact = ArtifactReference(
        artifact_id="evidence",
        relative_path="evidence/source.txt",
        sha256=hashlib.sha256(payload).hexdigest(),
        media_type="text/plain",
    )

    assert artifact.verify_bytes(payload)


def test_declared_replacement_hashes_can_differ_from_inbound_page_and_image() -> None:
    word = _word()
    artifact = ArtifactReference(
        artifact_id="inbound-image",
        relative_path="inbound/page.png",
        sha256="b" * 64,
        media_type="image/png",
    )
    inbound = LabelingBundle(
        bundle_id=None,
        schema_version="0.24.0",
        configuration_hash="e" * 64,
        taxonomy=_taxonomy(),
        page_id="page-1",
        page_sha256="a" * 64,
        image_sha256="b" * 64,
        text_sha256="c" * 64,
        page_head_sha256="f" * 64,
        artifacts=(artifact,),
        words=(word,),
        evidence=(
            Evidence(
                evidence_id="evidence-1",
                artifact_id="inbound-image",
                artifact_sha256="b" * 64,
                byte_start=0,
                byte_end=1,
            ),
        ),
    )
    replacement = word.model_copy(
        update={
            "page_content_sha256": "1" * 64,
            "image_artifact_sha256": "2" * 64,
            "word_revision": 1,
        }
    )
    correction = TypographyCorrection(
        correction_id="replacement-1",
        word_id=word.word_id,
        revision=1,
        supersedes_id=None,
        base_page_sha256="a" * 64,
        base_image_sha256="b" * 64,
        base_text_sha256=word.text_sha256,
        base_word_revision=0,
        replacement_text_sha256=word.text_sha256,
        replacement_page_sha256="1" * 64,
        replacement_image_sha256="2" * 64,
        replacement_page_head_sha256="3" * 64,
        replacement_word_revision=1,
        taxonomy_version=word.taxonomy_version,
        taxonomy_hash=word.taxonomy_hash,
        grapheme_map_version=word.grapheme_map_version,
        page_head_sha256="f" * 64,
        labeler_id="reviewer-1",
        decision=CorrectionDecision.APPROVED_EDIT,
        replacement=replacement,
    )
    correction_bundle = CorrectionBundle(
        bundle_id=None,
        schema_version="0.24.0",
        configuration_hash="e" * 64,
        labeling_bundle_id=inbound.bundle_id or "",
        corrections=(correction,),
        replacement_artifacts=(
            ReplacementArtifact(
                artifact_id="replacement-page",
                relative_path="out/page.json",
                sha256="1" * 64,
                byte_size=1,
                media_type="application/json",
            ),
            ReplacementArtifact(
                artifact_id="replacement-image",
                relative_path="out/page.png",
                sha256="2" * 64,
                byte_size=1,
                media_type="image/png",
            ),
            ReplacementArtifact(
                artifact_id="replacement-head",
                relative_path="out/head.json",
                sha256="3" * 64,
                byte_size=1,
                media_type="application/json",
            ),
        ),
    )

    correction_bundle.validate_against(inbound)
    mismatched = correction.model_copy(update={"replacement_image_sha256": "4" * 64})
    with pytest.raises(ValueError, match="replacement does not match"):
        CorrectionBundle(
            bundle_id=None,
            schema_version="0.24.0",
            configuration_hash="e" * 64,
            labeling_bundle_id=inbound.bundle_id or "",
            corrections=(mismatched,),
            replacement_artifacts=correction_bundle.replacement_artifacts,
        ).validate_against(inbound)


def test_geometry_rejects_nonfinite_coordinates() -> None:
    word = _word()

    with pytest.raises(ValidationError, match="finite"):
        WordGeometry(
            word_id=word.word_id,
            word_revision=word.word_revision,
            page_sha256="a" * 64,
            page_head_sha256="f" * 64,
            image_artifact_sha256="b" * 64,
            x0=float("nan"),
            y0=0,
            x1=1,
            y1=1,
            transform_id="transform-1",
            coordinate_space_id="image-v1",
            source_orientation=SourceOrientation.UPRIGHT,
        )


def test_complete_word_requires_all_required_taxonomy_states() -> None:
    word = _word().model_copy(
        update={
            "label_states": {"italic": LabelState.UNKNOWN, "bold": LabelState.NEGATIVE},
            "spans": (),
        }
    )

    with pytest.raises(ValueError, match="reviewed word"):
        word.validate_taxonomy(_taxonomy())


def test_review_states_distinguish_completed_regular_and_deferred_work() -> None:
    assert {state.value for state in ReviewState} == {
        "unreviewed",
        "reviewed",
        "reviewed_regular",
        "quarantined",
        "deferred",
    }


def test_word_binds_page_image_graphemes_evidence_warnings_and_whole_word_labels() -> (
    None
):
    word = _word()

    assert word.page_content_sha256 == "a" * 64
    assert word.image_artifact_sha256 == "b" * 64
    assert word.grapheme_map_version
    assert word.source_evidence_ids == ("evidence-1",)
    assert word.warnings == ("fixture warning",)
    assert word.whole_word_labels == ("italic",)


def test_artifact_paths_reject_windows_forms() -> None:
    for relative_path in (r"projects\\page.png", "C:/projects/page.png"):
        with pytest.raises(ValidationError, match="relative_path"):
            ArtifactReference(
                artifact_id="bad",
                relative_path=relative_path,
                sha256="d" * 64,
                media_type=None,
            )


def test_bundle_requires_schema_configuration_and_reproducible_geometry_chain() -> None:
    word = _word()
    geometry = WordGeometry(
        word_id=word.word_id,
        word_revision=word.word_revision,
        page_sha256="a" * 64,
        page_head_sha256="f" * 64,
        image_artifact_sha256="b" * 64,
        x0=0,
        y0=0,
        x1=1,
        y1=1,
        transform_id="crop-transform",
        coordinate_space_id="image-v1",
        source_orientation=SourceOrientation.ROTATE_90_CLOCKWISE,
    )
    bundle = LabelingBundle(
        bundle_id=None,
        schema_version="0.24.0",
        configuration_hash="e" * 64,
        taxonomy=_taxonomy(),
        page_id="page-1",
        page_sha256="a" * 64,
        image_sha256="b" * 64,
        text_sha256="c" * 64,
        page_head_sha256="f" * 64,
        artifacts=_inbound_artifacts(),
        words=(word,),
        page_geometry=_inbound_page_geometry(SourceOrientation.ROTATE_90_CLOCKWISE),
        geometry=(geometry,),
        evidence=(
            Evidence(
                evidence_id="evidence-1",
                artifact_id="page-image",
                artifact_sha256="b" * 64,
                byte_start=0,
                byte_end=1,
            ),
        ),
        model_runs=_inbound_model_runs(),
        coordinate_transforms=_transform_chain(SourceOrientation.ROTATE_90_CLOCKWISE),
    )

    assert bundle.schema_version == "0.24.0"
    assert bundle.configuration_hash == "e" * 64
    assert geometry.source_orientation is SourceOrientation.ROTATE_90_CLOCKWISE
    with pytest.raises(ValidationError, match="orientation-stage affine"):
        LabelingBundle.model_validate(
            {
                **bundle.model_dump(),
                "coordinate_transforms": (
                    {
                        **_transform_chain(SourceOrientation.ROTATE_90_CLOCKWISE)[
                            0
                        ].model_dump(),
                        "affine": (1, 0, 0, 0, 1, 0),
                    },
                    _transform_chain(SourceOrientation.ROTATE_90_CLOCKWISE)[
                        1
                    ].model_dump(),
                ),
                "bundle_id": None,
            }
        )
    with pytest.raises(ValidationError, match="transform bounds"):
        LabelingBundle.model_validate(
            {
                **bundle.model_dump(),
                "coordinate_transforms": (
                    _transform_chain(SourceOrientation.ROTATE_90_CLOCKWISE)[
                        0
                    ].model_dump(),
                    {
                        **_transform_chain(SourceOrientation.ROTATE_90_CLOCKWISE)[
                            1
                        ].model_dump(),
                        "source_width": 100,
                    },
                ),
                "bundle_id": None,
            }
        )
    with pytest.raises(ValidationError, match="orientation-stage affine"):
        LabelingBundle.model_validate(
            {
                **bundle.model_dump(),
                "coordinate_transforms": (
                    {
                        **_transform_chain(SourceOrientation.ROTATE_90_CLOCKWISE)[
                            0
                        ].model_dump(),
                        "affine": (0, 1, 0, -1, 0, 0),
                    },
                    _transform_chain(SourceOrientation.ROTATE_90_CLOCKWISE)[
                        1
                    ].model_dump(),
                ),
                "bundle_id": None,
            }
        )


@pytest.mark.parametrize(
    ("orientation", "expected_corners"),
    [
        (
            SourceOrientation.ROTATE_90_CLOCKWISE,
            ((200, 0), (200, 100), (0, 0), (0, 100)),
        ),
        (
            SourceOrientation.ROTATE_90_COUNTERCLOCKWISE,
            ((0, 100), (0, 0), (200, 100), (200, 0)),
        ),
    ],
)
def test_quarter_turn_orientation_affines_map_image_corners_and_validate_chain(
    orientation: SourceOrientation,
    expected_corners: tuple[
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
    ],
) -> None:
    bundle = _inbound_geometry_bundle(orientation)
    transform = bundle.coordinate_transforms[0]
    corners = ((0.0, 0.0), (100.0, 0.0), (0.0, 200.0), (100.0, 200.0))

    mapped_corners = tuple(
        _apply_affine(transform.affine, corner) for corner in corners
    )

    assert mapped_corners == expected_corners
    assert all(0 <= x <= 200 and 0 <= y <= 100 for x, y in mapped_corners)
    assert bundle.page_geometry is not None
    assert bundle.page_geometry.source_orientation is orientation


def test_correction_bundles_require_contiguous_word_revisions() -> None:
    word = _word()
    first = TypographyCorrection(
        correction_id="correction-1",
        word_id=word.word_id,
        revision=1,
        supersedes_id=None,
        base_page_sha256="a" * 64,
        base_image_sha256="b" * 64,
        base_text_sha256=word.text_sha256,
        base_word_revision=0,
        replacement_text_sha256=word.text_sha256,
        replacement_page_sha256=word.page_content_sha256,
        replacement_image_sha256=word.image_artifact_sha256,
        replacement_page_head_sha256="f" * 64,
        replacement_word_revision=1,
        taxonomy_version=word.taxonomy_version,
        taxonomy_hash=word.taxonomy_hash,
        grapheme_map_version=word.grapheme_map_version,
        page_head_sha256="f" * 64,
        labeler_id="reviewer-1",
        decision=CorrectionDecision.APPROVED_EDIT,
        replacement=word,
    )
    second = first.model_copy(
        update={
            "correction_id": "correction-2",
            "revision": 3,
            "supersedes_id": "correction-1",
        }
    )

    with pytest.raises(ValidationError, match="contiguous"):
        CorrectionBundle(
            bundle_id=None,
            schema_version="0.24.0",
            configuration_hash="e" * 64,
            labeling_bundle_id="d" * 64,
            corrections=(first, second),
        )


def test_returned_geometry_requires_bound_models_artifacts_and_current_correction() -> (
    None
):
    word = _word()
    replacement = word.model_copy(
        update={
            "page_content_sha256": "1" * 64,
            "image_artifact_sha256": "2" * 64,
            "word_revision": 1,
        }
    )
    correction = TypographyCorrection(
        correction_id="geometry-correction-1",
        word_id=word.word_id,
        revision=1,
        supersedes_id=None,
        base_page_sha256="a" * 64,
        base_image_sha256="b" * 64,
        base_text_sha256=word.text_sha256,
        base_word_revision=0,
        replacement_text_sha256=word.text_sha256,
        replacement_page_sha256="1" * 64,
        replacement_image_sha256="2" * 64,
        replacement_page_head_sha256="3" * 64,
        replacement_word_revision=1,
        taxonomy_version=word.taxonomy_version,
        taxonomy_hash=word.taxonomy_hash,
        grapheme_map_version=word.grapheme_map_version,
        page_head_sha256="f" * 64,
        labeler_id="reviewer-1",
        decision=CorrectionDecision.APPROVED_EDIT,
        replacement=replacement,
    )
    artifacts = (
        ReplacementArtifact(
            artifact_id="returned-page",
            relative_path="returned/page.json",
            sha256="1" * 64,
            byte_size=1,
            media_type="application/json",
        ),
        ReplacementArtifact(
            artifact_id="returned-image",
            relative_path="returned/page.png",
            sha256="2" * 64,
            byte_size=1,
            media_type="image/png",
        ),
        ReplacementArtifact(
            artifact_id="returned-head",
            relative_path="returned/head.json",
            sha256="3" * 64,
            byte_size=1,
            media_type="application/json",
        ),
        ReplacementArtifact(
            artifact_id="ocr-model",
            relative_path="models/ocr.onnx",
            sha256="4" * 64,
            byte_size=1,
            media_type="application/onnx",
        ),
        ReplacementArtifact(
            artifact_id="ocr-config",
            relative_path="models/ocr-config.json",
            sha256="5" * 64,
            byte_size=1,
            media_type="application/json",
        ),
        ReplacementArtifact(
            artifact_id="ocr-preprocessing",
            relative_path="models/ocr-preprocessing.json",
            sha256="6" * 64,
            byte_size=1,
            media_type="application/json",
        ),
        ReplacementArtifact(
            artifact_id="region-model",
            relative_path="models/region.onnx",
            sha256="7" * 64,
            byte_size=1,
            media_type="application/onnx",
        ),
        ReplacementArtifact(
            artifact_id="region-config",
            relative_path="models/region-config.json",
            sha256="8" * 64,
            byte_size=1,
            media_type="application/json",
        ),
        ReplacementArtifact(
            artifact_id="region-preprocessing",
            relative_path="models/region-preprocessing.json",
            sha256="9" * 64,
            byte_size=1,
            media_type="application/json",
        ),
        ReplacementArtifact(
            artifact_id="source-image",
            relative_path="source/page.png",
            sha256="a" * 64,
            byte_size=1,
            media_type="image/png",
        ),
        ReplacementArtifact(
            artifact_id="ocr-result",
            relative_path="returned/ocr.json",
            sha256="d" * 64,
            byte_size=1,
            media_type="application/json",
        ),
        ReplacementArtifact(
            artifact_id="page-region-result",
            relative_path="returned/page-regions.json",
            sha256="e" * 64,
            byte_size=1,
            media_type="application/json",
        ),
    )
    transforms = (
        CoordinateTransform(
            transform_id="returned-orientation",
            stage=CoordinateTransformStage.ORIENTATION,
            source_space="scan_pixels",
            target_space="oriented_pixels",
            source_coordinate_space_id="scan-v1",
            target_coordinate_space_id="oriented-v1",
            source_orientation=SourceOrientation.UPRIGHT,
            source_artifact_sha256="a" * 64,
            target_artifact_sha256="a" * 64,
            source_width=100,
            source_height=200,
            target_width=100,
            target_height=200,
            crop_recipe="identity",
            crop_recipe_version="1",
            padding_px=0,
            resampling="nearest",
            preprocessing_sha256="6" * 64,
            transform_version="1",
            affine=(1, 0, 0, 0, 1, 0),
        ),
        CoordinateTransform(
            transform_id="returned-crop",
            stage=CoordinateTransformStage.CROP,
            source_space="oriented_pixels",
            target_space="image_pixels",
            source_coordinate_space_id="oriented-v1",
            target_coordinate_space_id="image-v1",
            source_orientation=SourceOrientation.UPRIGHT,
            source_artifact_sha256="a" * 64,
            target_artifact_sha256="2" * 64,
            source_width=100,
            source_height=200,
            target_width=100,
            target_height=200,
            crop_recipe="identity",
            crop_recipe_version="1",
            padding_px=0,
            resampling="nearest",
            preprocessing_sha256="6" * 64,
            transform_version="1",
            affine=(1, 0, 0, 0, 1, 0),
        ),
    )
    model_runs = (
        ModelRun(
            run_id="ocr-run",
            purpose=ModelRunPurpose.OCR,
            model_name="ocr",
            model_version="1",
            input_artifact_sha256="2" * 64,
            output_artifact_sha256="d" * 64,
            model_artifact_sha256="4" * 64,
            config_sha256="5" * 64,
            preprocessing_sha256="6" * 64,
        ),
        ModelRun(
            run_id="region-run",
            purpose=ModelRunPurpose.PAGE_REGION,
            model_name="region",
            model_version="1",
            input_artifact_sha256="2" * 64,
            output_artifact_sha256="e" * 64,
            model_artifact_sha256="7" * 64,
            config_sha256="8" * 64,
            preprocessing_sha256="9" * 64,
        ),
    )
    page_geometry = PageGeometry(
        page_id="page-1",
        page_sha256="1" * 64,
        source_image_artifact_sha256="a" * 64,
        source_image_width=100,
        source_image_height=200,
        image_artifact_sha256="2" * 64,
        page_head_sha256="3" * 64,
        ocr_artifact_sha256="d" * 64,
        page_region_artifact_sha256="e" * 64,
        coordinate_space="image_pixels",
        coordinate_space_id="image-v1",
        source_orientation=SourceOrientation.UPRIGHT,
        transform_ids=("returned-orientation", "returned-crop"),
        ocr_model_run_id="ocr-run",
        page_region_model_run_id="region-run",
        image_width=100,
        image_height=200,
    )
    geometry = WordGeometry(
        word_id=word.word_id,
        word_revision=1,
        page_sha256="1" * 64,
        page_head_sha256="3" * 64,
        image_artifact_sha256="2" * 64,
        x0=0,
        y0=0,
        x1=10,
        y1=10,
        coordinate_space="image_pixels",
        coordinate_space_id="image-v1",
        transform_id="returned-crop",
        source_orientation=SourceOrientation.UPRIGHT,
    )

    bundle = CorrectionBundle(
        bundle_id=None,
        schema_version="0.24.0",
        configuration_hash="e" * 64,
        labeling_bundle_id="d" * 64,
        corrections=(correction,),
        replacement_artifacts=artifacts,
        page_geometry=page_geometry,
        geometry=(geometry,),
        model_runs=model_runs,
        coordinate_transforms=transforms,
    )

    assert bundle.page_geometry == page_geometry
    assert bundle.geometry == (geometry,)
    assert bundle.model_runs == model_runs
    assert bundle.model_runs[0].input_artifact_sha256 == "2" * 64
    restored = CorrectionBundle.model_validate(bundle.model_dump(mode="json"))
    assert restored.bundle_id == bundle.bundle_id

    with pytest.raises(ValidationError, match="model run hashes"):
        CorrectionBundle.model_validate(
            {
                **bundle.model_dump(),
                "model_runs": (
                    {
                        **model_runs[0].model_dump(),
                        "config_sha256": "0" * 64,
                    },
                    model_runs[1].model_dump(),
                ),
                "bundle_id": None,
            }
        )

    with pytest.raises(ValidationError, match="page geometry hashes"):
        CorrectionBundle.model_validate(
            {
                **bundle.model_dump(),
                "page_geometry": {
                    **page_geometry.model_dump(),
                    "page_head_sha256": "0" * 64,
                },
                "geometry": (
                    {
                        **geometry.model_dump(),
                        "page_head_sha256": "0" * 64,
                    },
                ),
                "bundle_id": None,
            }
        )

    with pytest.raises(ValidationError, match="within the returned image"):
        CorrectionBundle.model_validate(
            {
                **bundle.model_dump(),
                "geometry": ({**geometry.model_dump(), "x1": 101},),
                "bundle_id": None,
            }
        )


def test_returned_geometry_rejects_stale_page_head_and_incomplete_chain() -> None:
    with pytest.raises(ValidationError, match="transform IDs"):
        PageGeometry(
            page_id="page-1",
            page_sha256="1" * 64,
            source_image_artifact_sha256="2" * 64,
            source_image_width=100,
            source_image_height=200,
            image_artifact_sha256="2" * 64,
            page_head_sha256="3" * 64,
            ocr_artifact_sha256="4" * 64,
            page_region_artifact_sha256="5" * 64,
            coordinate_space="image_pixels",
            coordinate_space_id="image-v1",
            source_orientation=SourceOrientation.UPRIGHT,
            transform_ids=(),
            ocr_model_run_id="ocr-run",
            page_region_model_run_id="region-run",
            image_width=100,
            image_height=200,
        )


def test_coordinate_transforms_require_explicit_stages() -> None:
    assert "stage" in CoordinateTransform.model_fields


def test_geometry_free_transforms_allow_legacy_missing_stage() -> None:
    legacy_payload = _transform_chain()[0].model_dump()
    del legacy_payload["stage"]

    transform = CoordinateTransform.model_validate(legacy_payload)

    assert transform.stage is None
