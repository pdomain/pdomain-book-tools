"""Content-addressed portable typography bundle models."""

from __future__ import annotations

import hashlib
import string
from enum import StrEnum
from itertools import pairwise
from pathlib import PurePosixPath
from typing import Annotated, Self

from pydantic import Field, field_validator, model_validator

from pdomain_book_tools.typography.review import (
    REVIEW_CONTRACT_VERSION,
    CorrectionDecision,
    LabelState,
    TypographyCorrection,
    TypographyTaxonomy,
    WordTypography,
    canonical_json_bytes,
    validate_sha256,
)
from pdomain_book_tools.typography.spans import CanonicalModel

_Coordinate = Annotated[float, Field(strict=True, allow_inf_nan=False)]
_StrictIndex = Annotated[int, Field(strict=True, ge=0)]


class SourceOrientation(StrEnum):
    """Orientation of the source image before a geometry transform."""

    UPRIGHT = "upright"
    ROTATE_90_CLOCKWISE = "rotate_90_clockwise"
    ROTATE_180 = "rotate_180"
    ROTATE_90_COUNTERCLOCKWISE = "rotate_90_counterclockwise"


class ArtifactReference(CanonicalModel):
    """Path-safe content-addressed artifact metadata with no filesystem I/O."""

    artifact_id: str
    relative_path: str
    sha256: str
    media_type: str | None = None

    @field_validator("artifact_id")
    @classmethod
    def _require_artifact_id(cls, value: str) -> str:
        if not value.strip():
            msg = "artifact_id must not be empty"
            raise ValueError(msg)
        return value

    @field_validator("relative_path")
    @classmethod
    def _validate_relative_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if (
            not value
            or "\\" in value
            or (len(value) >= 2 and value[0].isalpha() and value[1] == ":")
            or path.is_absolute()
            or ".." in path.parts
            or "." in path.parts
        ):
            msg = "relative_path must be a nonempty safe relative POSIX path"
            raise ValueError(msg)
        return value

    @field_validator("sha256")
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        return validate_sha256(value, "sha256")

    def verify_bytes(self, payload: bytes) -> bool:
        """Return whether in-memory bytes match this artifact's declared hash."""
        return hashlib.sha256(payload).hexdigest() == self.sha256


class ReplacementArtifact(CanonicalModel):
    """Path-safe declared output artifact created by an approved correction."""

    artifact_id: str
    relative_path: str
    sha256: str
    byte_size: Annotated[int, Field(strict=True, ge=0)]
    media_type: str

    @field_validator("artifact_id", "media_type")
    @classmethod
    def _require_value(cls, value: str) -> str:
        if not value.strip():
            msg = "replacement artifact values must not be empty"
            raise ValueError(msg)
        return value

    @field_validator("relative_path")
    @classmethod
    def _validate_relative_path(cls, value: str) -> str:
        ArtifactReference(
            artifact_id="validation",
            relative_path=value,
            sha256="0" * 64,
            media_type=None,
        )
        return value

    @field_validator("sha256")
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        return validate_sha256(value, "sha256")


class ModelRun(CanonicalModel):
    """Reproducibility metadata for a model-generated proposal."""

    run_id: str
    model_name: str
    model_version: str
    config_sha256: str | None = None

    @field_validator("run_id", "model_name", "model_version")
    @classmethod
    def _require_value(cls, value: str) -> str:
        if not value.strip():
            msg = "model run identifiers must not be empty"
            raise ValueError(msg)
        return value

    @field_validator("config_sha256")
    @classmethod
    def _validate_config_hash(cls, value: str | None) -> str | None:
        return validate_sha256(value, "config_sha256") if value is not None else None


class CoordinateTransform(CanonicalModel):
    """Named affine transform between portable coordinate spaces."""

    transform_id: str
    source_space: str
    target_space: str
    source_coordinate_space_id: str
    target_coordinate_space_id: str
    source_orientation: SourceOrientation
    source_artifact_sha256: str
    target_artifact_sha256: str
    crop_recipe: str
    crop_recipe_version: str
    padding_px: Annotated[int, Field(strict=True, ge=0)]
    resampling: str
    preprocessing_sha256: str
    transform_version: str
    affine: tuple[
        _Coordinate, _Coordinate, _Coordinate, _Coordinate, _Coordinate, _Coordinate
    ]

    @field_validator(
        "transform_id",
        "source_space",
        "target_space",
        "source_coordinate_space_id",
        "target_coordinate_space_id",
    )
    @classmethod
    def _require_value(cls, value: str) -> str:
        if not value.strip():
            msg = "coordinate transform values must not be empty"
            raise ValueError(msg)
        return value

    @field_validator(
        "source_artifact_sha256", "target_artifact_sha256", "preprocessing_sha256"
    )
    @classmethod
    def _validate_hash(cls, value: str, info: object) -> str:
        return validate_sha256(value, str(getattr(info, "field_name", "sha256")))

    @field_validator(
        "crop_recipe", "crop_recipe_version", "resampling", "transform_version"
    )
    @classmethod
    def _require_recipe_value(cls, value: str) -> str:
        if not value.strip():
            msg = "transform recipe values must not be empty"
            raise ValueError(msg)
        return value


class Evidence(CanonicalModel):
    """A precise half-open byte range supporting a label decision."""

    evidence_id: str
    artifact_id: str
    artifact_sha256: str
    byte_start: _StrictIndex
    byte_end: _StrictIndex
    note: str | None = None

    @field_validator("evidence_id", "artifact_id")
    @classmethod
    def _require_identifier(cls, value: str) -> str:
        if not value.strip():
            msg = "evidence identifiers must not be empty"
            raise ValueError(msg)
        return value

    @field_validator("artifact_sha256")
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        return validate_sha256(value, "artifact_sha256")

    @model_validator(mode="after")
    def _validate_range(self) -> Self:
        if self.byte_start >= self.byte_end:
            msg = "evidence must use a nonempty half-open byte range"
            raise ValueError(msg)
        return self


class WordGeometry(CanonicalModel):
    """Optional axis-aligned word geometry in the bundle's declared space."""

    word_id: str
    x0: _Coordinate
    y0: _Coordinate
    x1: _Coordinate
    y1: _Coordinate
    coordinate_space: str = "image_pixels"
    transform_id: str
    source_orientation: SourceOrientation

    @model_validator(mode="after")
    def _validate_bounds(self) -> Self:
        if (
            not self.word_id.strip()
            or not self.coordinate_space.strip()
            or not self.transform_id.strip()
        ):
            msg = "geometry identifiers must not be empty"
            raise ValueError(msg)
        if self.x0 >= self.x1 or self.y0 >= self.y1:
            msg = "geometry must have positive width and height"
            raise ValueError(msg)
        return self


def _bundle_content_id(payload: dict[str, object]) -> str:
    """Hash canonical JSON payload after omitting its self-referential ID."""
    payload_without_id = {
        key: value for key, value in payload.items() if key != "bundle_id"
    }
    return hashlib.sha256(canonical_json_bytes(payload_without_id)).hexdigest()


class LabelingBundle(CanonicalModel):
    """Complete portable review input for a page, optionally with geometry."""

    bundle_id: str | None = None
    schema_version: str
    configuration_hash: str
    taxonomy: TypographyTaxonomy
    page_id: str
    page_sha256: str
    image_sha256: str
    text_sha256: str
    page_head_sha256: str
    artifacts: tuple[ArtifactReference, ...]
    words: tuple[WordTypography, ...]
    geometry: tuple[WordGeometry, ...] | None = None
    evidence: tuple[Evidence, ...] = ()
    model_runs: tuple[ModelRun, ...] = ()
    coordinate_transforms: tuple[CoordinateTransform, ...] = ()

    @field_validator("page_id")
    @classmethod
    def _require_page_id(cls, value: str) -> str:
        if not value.strip():
            msg = "page_id must not be empty"
            raise ValueError(msg)
        return value

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        if value != REVIEW_CONTRACT_VERSION:
            msg = "schema_version must equal the review contract version"
            raise ValueError(msg)
        return value

    @field_validator(
        "configuration_hash",
        "page_sha256",
        "image_sha256",
        "text_sha256",
        "page_head_sha256",
    )
    @classmethod
    def _validate_hash(cls, value: str, info: object) -> str:
        return validate_sha256(value, str(getattr(info, "field_name", "sha256")))

    @model_validator(mode="after")
    def _validate_bundle(self) -> Self:
        for word in self.words:
            word.validate_taxonomy(self.taxonomy)
            if (
                word.page_content_sha256 != self.page_sha256
                or word.image_artifact_sha256 != self.image_sha256
            ):
                msg = "word page and image hashes must match the containing bundle"
                raise ValueError(msg)
        artifact_hashes = {
            artifact.artifact_id: artifact.sha256 for artifact in self.artifacts
        }
        if len(artifact_hashes) != len(self.artifacts):
            msg = "bundle artifact IDs must be unique"
            raise ValueError(msg)
        for item in self.evidence:
            if artifact_hashes.get(item.artifact_id) != item.artifact_sha256:
                msg = "evidence artifact ID and hash must identify a declared artifact"
                raise ValueError(msg)
        evidence_ids = {item.evidence_id for item in self.evidence}
        if any(
            not set(word.source_evidence_ids).issubset(evidence_ids)
            for word in self.words
        ):
            msg = "word source evidence IDs must be declared by the containing bundle"
            raise ValueError(msg)
        if any(
            span.alignment_evidence_id not in evidence_ids
            for word in self.words
            for span in word.spans
        ):
            msg = (
                "span alignment evidence IDs must be declared by the containing bundle"
            )
            raise ValueError(msg)
        word_ids = {word.word_id for word in self.words}
        if len(word_ids) != len(self.words):
            msg = "bundle word IDs must be unique"
            raise ValueError(msg)
        if self.geometry is not None and any(
            item.word_id not in word_ids for item in self.geometry
        ):
            msg = "geometry must reference a declared word"
            raise ValueError(msg)
        transform_ids = {
            transform.transform_id for transform in self.coordinate_transforms
        }
        if self.geometry is not None and any(
            item.transform_id not in transform_ids for item in self.geometry
        ):
            msg = "geometry must reference a declared coordinate transform"
            raise ValueError(msg)
        transforms = {
            transform.transform_id: transform
            for transform in self.coordinate_transforms
        }
        if self.geometry is not None and any(
            transforms[item.transform_id].source_orientation != item.source_orientation
            for item in self.geometry
        ):
            msg = "geometry orientation must match its coordinate transform"
            raise ValueError(msg)
        if self.geometry is not None and any(
            transforms[item.transform_id].target_space != item.coordinate_space
            for item in self.geometry
        ):
            msg = "geometry coordinate space must match its transform target"
            raise ValueError(msg)
        if any(
            transform.target_artifact_sha256 != self.image_sha256
            for transform in self.coordinate_transforms
        ):
            msg = "coordinate transform target artifact must match bundle image"
            raise ValueError(msg)
        artifact_hash_values = set(artifact_hashes.values())
        if any(
            transform.source_artifact_sha256 not in artifact_hash_values
            or transform.target_artifact_sha256 not in artifact_hash_values
            for transform in self.coordinate_transforms
        ):
            msg = "coordinate transforms must reference declared bundle artifacts"
            raise ValueError(msg)
        expected = _bundle_content_id(self.model_dump(mode="json"))
        if self.bundle_id is not None and self.bundle_id != expected:
            msg = "bundle_id does not match the canonical bundle payload"
            raise ValueError(msg)
        object.__setattr__(self, "bundle_id", expected)
        return self

    def rebuild(self, **updates: object) -> Self:
        """Apply updates through validation and derive a new content ID.

        Do not use Pydantic's ``model_copy`` for content-addressed bundles:
        it intentionally skips validation and can preserve a stale ``bundle_id``.
        """
        data = self.model_dump(mode="json")
        data.update(updates)
        data["bundle_id"] = None
        return type(self).model_validate(data)


class CorrectionBundle(CanonicalModel):
    """Content-addressed corrections attached to a labeling bundle."""

    bundle_id: str | None = None
    schema_version: str
    configuration_hash: str
    labeling_bundle_id: str
    corrections: tuple[TypographyCorrection, ...]
    replacement_artifacts: tuple[ReplacementArtifact, ...] = ()

    @field_validator("labeling_bundle_id")
    @classmethod
    def _require_labeling_bundle_id(cls, value: str) -> str:
        if len(value) != 64 or any(char not in string.hexdigits for char in value):
            msg = "labeling_bundle_id must be a 64-character hexadecimal content ID"
            raise ValueError(msg)
        return value.lower()

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        if value != REVIEW_CONTRACT_VERSION:
            msg = "schema_version must equal the review contract version"
            raise ValueError(msg)
        return value

    @field_validator("configuration_hash")
    @classmethod
    def _validate_configuration_hash(cls, value: str) -> str:
        return validate_sha256(value, "configuration_hash")

    @model_validator(mode="after")
    def _validate_bundle(self) -> Self:
        correction_ids = {correction.correction_id for correction in self.corrections}
        if len(correction_ids) != len(self.corrections):
            msg = "correction IDs must be unique"
            raise ValueError(msg)
        replacement_ids = {
            artifact.artifact_id for artifact in self.replacement_artifacts
        }
        if len(replacement_ids) != len(self.replacement_artifacts):
            msg = "replacement artifact IDs must be unique"
            raise ValueError(msg)
        corrections_by_word: dict[str, list[TypographyCorrection]] = {}
        for correction in self.corrections:
            corrections_by_word.setdefault(correction.word_id, []).append(correction)
        for revisions in corrections_by_word.values():
            ordered = sorted(revisions, key=lambda item: item.revision)
            expected_revisions = tuple(range(1, len(ordered) + 1))
            if tuple(item.revision for item in ordered) != expected_revisions:
                msg = "correction revisions must be contiguous from 1 for each word"
                raise ValueError(msg)
            if any(
                current.supersedes_id != previous.correction_id
                for previous, current in pairwise(ordered)
            ):
                msg = "correction supersedes_id must reference the preceding word revision"
                raise ValueError(msg)
            if any(
                current.base_page_sha256 != previous.effective_page_sha256
                or current.base_image_sha256 != previous.effective_image_sha256
                or current.base_text_sha256 != previous.effective_text_sha256
                or current.base_word_revision != previous.effective_word_revision
                or current.page_head_sha256 != previous.effective_page_head_sha256
                for previous, current in pairwise(ordered)
            ):
                msg = "successor correction bases must equal predecessor replacements"
                raise ValueError(msg)
        expected = _bundle_content_id(self.model_dump(mode="json"))
        if self.bundle_id is not None and self.bundle_id != expected:
            msg = "bundle_id does not match the canonical bundle payload"
            raise ValueError(msg)
        object.__setattr__(self, "bundle_id", expected)
        return self

    def validate_against(self, labeling_bundle: LabelingBundle) -> None:
        """Verify every correction is bound to one exact labeling bundle."""
        if self.labeling_bundle_id != labeling_bundle.bundle_id:
            msg = "correction bundle does not reference the supplied labeling bundle"
            raise ValueError(msg)
        words = {word.word_id: word for word in labeling_bundle.words}
        for correction in self.corrections:
            word = words.get(correction.word_id)
            if word is None:
                msg = "correction word_id is absent from labeling bundle"
                raise ValueError(msg)
            if correction.revision == 1 and (
                correction.base_page_sha256 != labeling_bundle.page_sha256
                or correction.base_image_sha256 != labeling_bundle.image_sha256
                or correction.base_text_sha256 != word.text_sha256
                or correction.base_word_revision != word.word_revision
                or correction.taxonomy_version != labeling_bundle.taxonomy.version
                or correction.taxonomy_hash != labeling_bundle.taxonomy.taxonomy_hash
                or correction.grapheme_map_version != word.grapheme_map_version
                or correction.page_head_sha256 != labeling_bundle.page_head_sha256
            ):
                msg = "correction base hashes do not match labeling bundle and word"
                raise ValueError(msg)
            if correction.replacement is not None:
                correction.replacement.validate_taxonomy(labeling_bundle.taxonomy)
                if correction.decision is CorrectionDecision.REVIEWED_REGULAR and any(
                    correction.replacement.label_states.get(label.value)
                    is not LabelState.NEGATIVE
                    for label in labeling_bundle.taxonomy.labels
                    if label.required_for_completion
                ):
                    msg = "reviewed_regular correction requires all required labels negative"
                    raise ValueError(msg)
                declared_hashes = {
                    artifact.sha256 for artifact in self.replacement_artifacts
                }
                if not {
                    correction.replacement_page_sha256,
                    correction.replacement_image_sha256,
                    correction.replacement_page_head_sha256,
                }.issubset(declared_hashes):
                    msg = "approved correction replacement hashes require declared artifacts"
                    raise ValueError(msg)
                if (
                    correction.replacement.page_content_sha256
                    != correction.replacement_page_sha256
                    or correction.replacement.image_artifact_sha256
                    != correction.replacement_image_sha256
                    or correction.replacement.word_revision
                    != correction.replacement_word_revision
                ):
                    msg = "replacement does not match correction or labeling bundle provenance"
                    raise ValueError(msg)

    def rebuild(self, **updates: object) -> Self:
        """Apply updates through validation and derive a new content ID.

        Do not use Pydantic's ``model_copy`` for content-addressed bundles:
        it intentionally skips validation and can preserve a stale ``bundle_id``.
        """
        data = self.model_dump(mode="json")
        data.update(updates)
        data["bundle_id"] = None
        return type(self).model_validate(data)
