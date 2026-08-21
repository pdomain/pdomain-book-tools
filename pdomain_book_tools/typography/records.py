from __future__ import annotations

import base64
import binascii
import datetime as dt
import hashlib
import json
import math
import string
from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType
from typing import Annotated, Literal, Self, cast

from pydantic import Field, field_serializer, field_validator, model_validator
from pydantic_core import PydanticCustomError

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.typography.spans import (
    CanonicalModel,
    SourceSlice,
    StyleSpan,
    split_graphemes,
)

_StrictIndex = Annotated[int, Field(strict=True)]
_Probability = Annotated[float, Field(ge=0.0, le=1.0)]


def _validate_sha256(value: str, field_name: str) -> str:
    if len(value) != 64 or any(char not in string.hexdigits for char in value):
        msg = f"{field_name} must be a 64-character hexadecimal SHA-256"
        raise ValueError(msg)
    return value.lower()


def _validate_half_open_range(value: tuple[int, int], field_name: str) -> None:
    start, end = value
    if start < 0 or start >= end:
        msg = f"{field_name} must be a nonempty half-open range"
        raise ValueError(msg)


def _freeze_json(value: object) -> object:
    if isinstance(value, Mapping):
        return _freeze_mapping(cast("Mapping[str, object]", value))
    if isinstance(value, (list, tuple)):
        items = cast("list[object] | tuple[object, ...]", value)
        return tuple(_freeze_json(item) for item in items)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    msg = f"unsupported alignment alternative value: {type(value).__name__}"
    raise ValueError(msg)


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(
        {str(key): _freeze_json(item) for key, item in value.items()}
    )


def _thaw_json(value: object) -> object:
    if isinstance(value, Mapping):
        return _thaw_mapping(cast("Mapping[str, object]", value))
    if isinstance(value, tuple):
        items = cast("tuple[object, ...]", value)
        return [_thaw_json(item) for item in items]
    return value


def _thaw_mapping(value: Mapping[str, object]) -> dict[str, object]:
    return {str(key): _thaw_json(item) for key, item in value.items()}


def _parse_json_object_member_ranges(
    artifact_bytes: bytes,
) -> tuple[dict[str, object], dict[str, tuple[int, int]]]:
    text = artifact_bytes.decode("utf-8")
    decoder = json.JSONDecoder()
    position = 0
    byte_offsets = [0]
    for character in text:
        byte_offsets.append(byte_offsets[-1] + len(character.encode("utf-8")))

    def skip_whitespace(index: int) -> int:
        while index < len(text) and text[index].isspace():
            index += 1
        return index

    position = skip_whitespace(position)
    if position >= len(text) or text[position] != "{":
        msg = "F2 artifact must be a JSON object"
        raise ValueError(msg)
    position += 1
    members: dict[str, object] = {}
    ranges: dict[str, tuple[int, int]] = {}
    position = skip_whitespace(position)
    while position < len(text) and text[position] != "}":
        key_value, position = decoder.raw_decode(text, position)
        if not isinstance(key_value, str):
            msg = "F2 page keys must be JSON strings"
            raise TypeError(msg)
        if key_value in members:
            msg = f"F2 artifact contains duplicate page key {key_value!r}"
            raise ValueError(msg)
        position = skip_whitespace(position)
        if position >= len(text) or text[position] != ":":
            msg = "F2 page key must be followed by a value"
            raise ValueError(msg)
        value_start = skip_whitespace(position + 1)
        member_value, value_end = decoder.raw_decode(text, value_start)
        members[key_value] = member_value
        ranges[key_value] = (byte_offsets[value_start], byte_offsets[value_end])
        position = skip_whitespace(value_end)
        if position < len(text) and text[position] == ",":
            position = skip_whitespace(position + 1)
            if position >= len(text) or text[position] == "}":
                msg = "F2 artifact must not contain a trailing comma"
                raise ValueError(msg)
            continue
        break
    if position >= len(text) or text[position] != "}":
        msg = "F2 artifact must contain a valid JSON object"
        raise ValueError(msg)
    if skip_whitespace(position + 1) != len(text):
        msg = "F2 artifact must not contain trailing data"
        raise ValueError(msg)
    return members, ranges


class ArtifactSource(StrEnum):
    """Artifact origins supported by the typography record contract."""

    PGDP_F2 = "pgdp_f2"
    GUTENBERG = "gutenberg"
    STANDARD_EBOOKS = "standard_ebooks"
    HUMAN = "human"
    SYNTHETIC = "synthetic"


class SourceCoordinateSpace(StrEnum):
    """Coordinate spaces used on the source side of an alignment."""

    RAW_BYTES = "raw_bytes"
    SOURCE_GRAPHEMES = "source_graphemes"
    SOURCE_PAGES = "source_pages"


class TargetCoordinateSpace(StrEnum):
    """Coordinate spaces used on the target side of an alignment."""

    OCR_GRAPHEMES = "ocr_graphemes"
    OCR_TOKENS = "ocr_tokens"
    TARGET_PAGES = "target_pages"


class ArtifactRef(CanonicalModel):
    """Immutable identity and retrieval metadata for one artifact."""

    source: ArtifactSource
    source_url: str | None
    local_path: str
    retrieved_at: dt.datetime
    sha256: str
    version: str
    license_ref: str | None

    @field_validator("sha256")
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        return _validate_sha256(value, "sha256")

    @field_validator("version")
    @classmethod
    def _validate_version(cls, value: str) -> str:
        if not value:
            msg = "version must not be empty"
            raise ValueError(msg)
        return value

    @field_validator("retrieved_at")
    @classmethod
    def _validate_retrieved_at(cls, value: dt.datetime) -> dt.datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            msg = "retrieved_at must include a timezone"
            raise ValueError(msg)
        return value


class TextIdentity(CanonicalModel):
    """Stable work, edition, book, project, and page identity."""

    work_id: str
    edition_id: str
    book_id: str
    project_id: str | None
    pg_ebook_id: _StrictIndex | None
    se_repository: str | None
    page_id: str
    image_artifact: ArtifactRef
    text_artifacts: tuple[ArtifactRef, ...]


class Grapheme(CanonicalModel):
    """One visible grapheme and its exact source byte slices."""

    index: _StrictIndex
    text: str
    source_slices: tuple[SourceSlice, ...]
    normalized_from: str | None

    @field_validator("text")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        if len(split_graphemes(value)) != 1:
            msg = "text must contain exactly one Unicode extended grapheme"
            raise ValueError(msg)
        return value


class OcrTokenRef(CanonicalModel):
    """An OCR token and its projection into canonical grapheme coordinates."""

    token_id: str
    text: str
    confidence: _Probability | None
    bbox: BoundingBox
    line_id: str
    grapheme_start: _StrictIndex
    grapheme_end: _StrictIndex
    alignment_id: str

    @field_validator("bbox", mode="before")
    @classmethod
    def _accept_bbox_instance(cls, value: object) -> object:
        if isinstance(value, BoundingBox):
            return value.to_dict()
        return value

    @model_validator(mode="after")
    def _validate_grapheme_range(self) -> Self:
        _validate_half_open_range(
            (self.grapheme_start, self.grapheme_end), "OCR token grapheme range"
        )
        return self


class AlignmentEvidence(CanonicalModel):
    """Versioned evidence for one source-to-target alignment."""

    alignment_id: str
    method: str
    source_artifact_sha256: str
    target_artifact_sha256: str
    source_coordinate_space: SourceCoordinateSpace
    target_coordinate_space: TargetCoordinateSpace
    source_range: tuple[_StrictIndex, _StrictIndex]
    target_range: tuple[_StrictIndex, _StrictIndex]
    operations: tuple[str, ...]
    score: float
    margin: float | None
    alternatives: tuple[Mapping[str, object], ...]
    accepted: bool

    @field_validator("source_artifact_sha256", "target_artifact_sha256")
    @classmethod
    def _validate_hashes(cls, value: str, info: object) -> str:
        field_name = getattr(info, "field_name", "artifact_sha256")
        return _validate_sha256(value, str(field_name))

    @field_validator("alternatives", mode="after")
    @classmethod
    def _freeze_alternatives(
        cls, alternatives: tuple[Mapping[str, object], ...]
    ) -> tuple[Mapping[str, object], ...]:
        return tuple(_freeze_mapping(alternative) for alternative in alternatives)

    @field_serializer("alternatives")
    def _serialize_alternatives(
        self, alternatives: tuple[Mapping[str, object], ...]
    ) -> list[dict[str, object]]:
        return [_thaw_mapping(alternative) for alternative in alternatives]

    @model_validator(mode="after")
    def _validate_evidence(self) -> Self:
        _validate_half_open_range(self.source_range, "source_range")
        _validate_half_open_range(self.target_range, "target_range")
        if not math.isfinite(self.score):
            msg = "score must be finite"
            raise ValueError(msg)
        if self.margin is not None and not math.isfinite(self.margin):
            msg = "margin must be finite when present"
            raise ValueError(msg)
        return self


class TypographyPageRecord(CanonicalModel):
    """Canonical version 1.0 typography record for one source page."""

    schema_version: Literal["1.0"]
    identity: TextIdentity
    original_f2_artifact_base64: str | None
    original_f2_artifact_sha256: str | None
    f2_page_key: str | None
    f2_page_value_lexical_byte_range: tuple[_StrictIndex, _StrictIndex] | None
    f2_decoded_page_utf8_sha256: str | None
    parsed_text: str
    graphemes: tuple[Grapheme, ...]
    ocr_tokens: tuple[OcrTokenRef, ...]
    style_spans: tuple[StyleSpan, ...]
    structural_context: tuple[str, ...]
    parser_warnings: tuple[str, ...]
    alignments: tuple[AlignmentEvidence, ...]
    project_comments_artifact: ArtifactRef | None
    guideline_version: str

    @field_validator("original_f2_artifact_sha256", "f2_decoded_page_utf8_sha256")
    @classmethod
    def _validate_optional_hashes(cls, value: str | None, info: object) -> str | None:
        if value is None:
            return None
        field_name = getattr(info, "field_name", "sha256")
        return _validate_sha256(value, str(field_name))

    @model_validator(mode="after")
    def _validate_record(self) -> Self:
        if self.f2_page_value_lexical_byte_range is not None:
            _validate_half_open_range(
                self.f2_page_value_lexical_byte_range,
                "f2_page_value_lexical_byte_range",
            )
        self._validate_f2_artifact()
        expected_indices = tuple(range(len(self.graphemes)))
        actual_indices = tuple(grapheme.index for grapheme in self.graphemes)
        if actual_indices != expected_indices:
            msg = "grapheme indices must be contiguous and start at zero"
            raise ValueError(msg)
        if "".join(grapheme.text for grapheme in self.graphemes) != self.parsed_text:
            msg = "graphemes must reconstruct parsed_text exactly"
            raise ValueError(msg)
        if any(span.end > len(self.graphemes) for span in self.style_spans):
            msg = "style span end cannot exceed the page grapheme count"
            raise ValueError(msg)
        alignment_ids = {alignment.alignment_id for alignment in self.alignments}
        if len(alignment_ids) != len(self.alignments):
            msg = "alignment_id values must be unique within a page record"
            raise ValueError(msg)
        for token in self.ocr_tokens:
            if token.grapheme_end > len(self.graphemes):
                msg = "OCR token grapheme range cannot exceed the page grapheme count"
                raise ValueError(msg)
            if token.alignment_id not in alignment_ids:
                msg = "OCR token alignment_id must reference a supplied alignment"
                raise ValueError(msg)
        return self

    def _validate_f2_artifact(self) -> None:
        values = (
            self.original_f2_artifact_base64,
            self.original_f2_artifact_sha256,
            self.f2_page_key,
            self.f2_page_value_lexical_byte_range,
            self.f2_decoded_page_utf8_sha256,
        )
        if all(value is None for value in values):
            return
        if any(value is None for value in values):
            msg = "F2 artifact fields must be either all present or all absent"
            raise ValueError(msg)
        encoded = self.original_f2_artifact_base64
        expected_hash = self.original_f2_artifact_sha256
        if encoded is None or expected_hash is None:
            msg = "F2 artifact identity is incomplete"
            raise ValueError(msg)
        try:
            artifact_bytes = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as error:
            msg = "original_f2_artifact_base64 must be valid base64"
            raise ValueError(msg) from error
        if hashlib.sha256(artifact_bytes).hexdigest() != expected_hash:
            msg = "original_f2_artifact_sha256 does not match the decoded artifact"
            raise ValueError(msg)
        if not any(
            artifact.sha256 == expected_hash
            for artifact in self.identity.text_artifacts
        ):
            msg = "original F2 artifact must appear in identity.text_artifacts"
            raise ValueError(msg)
        lexical_range = self.f2_page_value_lexical_byte_range
        page_key = self.f2_page_key
        decoded_page_hash = self.f2_decoded_page_utf8_sha256
        if lexical_range is None or page_key is None or decoded_page_hash is None:
            msg = "F2 page evidence is incomplete"
            raise ValueError(msg)
        start, end = lexical_range
        if end > len(artifact_bytes):
            msg = "f2_page_value_lexical_byte_range exceeds the F2 artifact"
            raise ValueError(msg)
        try:
            lexical_value: object = json.loads(artifact_bytes[start:end])
            document, member_ranges = _parse_json_object_member_ranges(artifact_bytes)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            msg = "F2 lexical value range must identify a valid JSON string"
            raise ValueError(msg) from error
        if not isinstance(lexical_value, str):
            raise PydanticCustomError(
                "f2_page_value_type",
                "F2 lexical value range must identify a JSON string",
            )
        if page_key not in document:
            msg = "f2_page_key must identify a page in the F2 artifact"
            raise ValueError(msg)
        if member_ranges[page_key] != lexical_range:
            msg = "F2 lexical byte range must identify the selected f2_page_key"
            raise ValueError(msg)
        if document[page_key] != lexical_value:
            msg = "F2 lexical value does not match f2_page_key"
            raise ValueError(msg)
        if hashlib.sha256(lexical_value.encode()).hexdigest() != decoded_page_hash:
            msg = "decoded page hash does not match the F2 lexical value"
            raise ValueError(msg)
