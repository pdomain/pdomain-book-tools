"""Immutable, source-neutral contracts for OCR-to-text matching."""

from __future__ import annotations

import hashlib
import json
import math
import string
from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, field_validator, model_validator

from pdomain_book_tools.typography.spans import CanonicalModel

_StrictIndex = Annotated[int, Field(strict=True, ge=0)]


def _content_id(payload: dict[str, object], *, excluded_field: str) -> str:
    """Return a SHA-256 ID for a canonical model payload without its own ID."""
    content = {key: value for key, value in payload.items() if key != excluded_field}
    canonical = json.dumps(
        content,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _validate_identifier(value: str, *, field_name: str) -> str:
    if not value:
        msg = f"{field_name} must not be empty"
        raise ValueError(msg)
    return value


def _validate_sha256(value: str, *, field_name: str) -> str:
    if len(value) != 64 or any(
        character not in string.hexdigits for character in value
    ):
        msg = f"{field_name} must be a 64-character hexadecimal SHA-256"
        raise ValueError(msg)
    return value.lower()


def _validate_content_id(value: str | None, *, expected: str, field_name: str) -> str:
    if value is not None and value != expected:
        msg = f"{field_name} does not match the canonical payload"
        raise ValueError(msg)
    return expected


class MatchOperationKind(StrEnum):
    """A monotonic grapheme edit retained as matching evidence."""

    MATCH = "match"
    SUBSTITUTION = "substitution"
    SOURCE_ONLY_DELETION = "source_only_deletion"
    TARGET_ONLY_INSERTION = "target_only_insertion"


class MatchRelationKind(StrEnum):
    """The cardinality of one immutable physical-token relation."""

    ONE_TO_ONE = "one_to_one"
    SOURCE_TO_FRAGMENTS = "source_to_fragments"
    SOURCES_TO_ONE = "sources_to_one"
    SOURCE_ONLY = "source_only"
    TARGET_ONLY = "target_only"


class MatchQuarantineReason(StrEnum):
    """Reasons a graph is retained for review instead of accepted."""

    TIE = "tie"
    LOW_MARGIN = "low_margin"
    STATE_LIMIT_EXHAUSTED = "state_limit_exhausted"
    TRANSITION_LIMIT_EXHAUSTED = "transition_limit_exhausted"
    UNRESOLVED_CONTINUATION = "unresolved_continuation"


class ArtifactRange(CanonicalModel):
    """One exact nonempty byte and grapheme range in an input artifact."""

    artifact_id: str
    artifact_sha256: str
    byte_start: _StrictIndex
    byte_end: _StrictIndex
    grapheme_start: _StrictIndex
    grapheme_end: _StrictIndex

    @field_validator("artifact_id")
    @classmethod
    def _validate_artifact_id(cls, value: str) -> str:
        return _validate_identifier(value, field_name="artifact_id")

    @field_validator("artifact_sha256")
    @classmethod
    def _validate_artifact_sha256(cls, value: str) -> str:
        return _validate_sha256(value, field_name="artifact_sha256")

    @model_validator(mode="after")
    def _validate_ranges(self) -> Self:
        if self.byte_start >= self.byte_end:
            msg = "artifact byte range must be nonempty and ordered"
            raise ValueError(msg)
        if self.grapheme_start >= self.grapheme_end:
            msg = "artifact grapheme range must be nonempty and ordered"
            raise ValueError(msg)
        return self


class MatchToken(CanonicalModel):
    """A stable physical token and the exact artifacts that supplied its text."""

    token_id: str
    text: str
    artifact_ranges: tuple[ArtifactRange, ...] = ()

    @field_validator("token_id")
    @classmethod
    def _validate_token_id(cls, value: str) -> str:
        return _validate_identifier(value, field_name="token_id")

    @field_validator("text")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        return _validate_identifier(value, field_name="token text")


class MatchLine(CanonicalModel):
    """One ordered physical line of immutable tokens."""

    line_id: str
    tokens: tuple[MatchToken, ...]

    @field_validator("line_id")
    @classmethod
    def _validate_line_id(cls, value: str) -> str:
        return _validate_identifier(value, field_name="line_id")

    @model_validator(mode="after")
    def _validate_tokens(self) -> Self:
        token_ids = tuple(token.token_id for token in self.tokens)
        if len(set(token_ids)) != len(token_ids):
            msg = "token IDs must be unique within a line"
            raise ValueError(msg)
        return self


class MatchPage(CanonicalModel):
    """One ordered physical page of immutable lines."""

    page_id: str
    lines: tuple[MatchLine, ...]

    @field_validator("page_id")
    @classmethod
    def _validate_page_id(cls, value: str) -> str:
        return _validate_identifier(value, field_name="page_id")

    @model_validator(mode="after")
    def _validate_lines(self) -> Self:
        line_ids = tuple(line.line_id for line in self.lines)
        if len(set(line_ids)) != len(line_ids):
            msg = "line IDs must be unique within a page"
            raise ValueError(msg)
        return self


class MatchDocument(CanonicalModel):
    """A source-neutral ordered document with stable page, line, and token IDs."""

    document_id: str
    pages: tuple[MatchPage, ...]
    warnings: tuple[str, ...] = ()

    @field_validator("document_id")
    @classmethod
    def _validate_document_id(cls, value: str) -> str:
        return _validate_identifier(value, field_name="document_id")

    @model_validator(mode="after")
    def _validate_document_ids(self) -> Self:
        page_ids = tuple(page.page_id for page in self.pages)
        line_ids = tuple(line.line_id for page in self.pages for line in page.lines)
        token_ids = tuple(
            token.token_id
            for page in self.pages
            for line in page.lines
            for token in line.tokens
        )
        if len(set(page_ids)) != len(page_ids):
            msg = "page IDs must be unique within a document"
            raise ValueError(msg)
        if len(set(line_ids)) != len(line_ids):
            msg = "line IDs must be unique within a document"
            raise ValueError(msg)
        if len(set(token_ids)) != len(token_ids):
            msg = "token IDs must be unique within a document"
            raise ValueError(msg)
        return self

    def token_ids(self) -> frozenset[str]:
        """Return the stable token IDs contained by this document."""
        return frozenset(
            token.token_id
            for page in self.pages
            for line in page.lines
            for token in line.tokens
        )


class MatchOperation(CanonicalModel):
    """One typed monotonic operation in local source and target grapheme ranges."""

    kind: MatchOperationKind
    source_grapheme_range: tuple[_StrictIndex, _StrictIndex]
    target_grapheme_range: tuple[_StrictIndex, _StrictIndex]

    @model_validator(mode="after")
    def _validate_ranges(self) -> Self:
        source_start, source_end = self.source_grapheme_range
        target_start, target_end = self.target_grapheme_range
        if source_start > source_end or target_start > target_end:
            msg = "match operation grapheme ranges must be ordered"
            raise ValueError(msg)
        source_consumed = source_start < source_end
        target_consumed = target_start < target_end
        if self.kind in {MatchOperationKind.MATCH, MatchOperationKind.SUBSTITUTION}:
            if not (source_consumed and target_consumed):
                msg = "match and substitution operations must consume both sides"
                raise ValueError(msg)
        elif self.kind is MatchOperationKind.SOURCE_ONLY_DELETION:
            if not (source_consumed and not target_consumed):
                msg = "source-only deletion must consume only the source"
                raise ValueError(msg)
        elif self.kind is MatchOperationKind.TARGET_ONLY_INSERTION and not (
            target_consumed and not source_consumed
        ):
            msg = "target-only insertion must consume only the target"
            raise ValueError(msg)
        return self


class MatchRelation(CanonicalModel):
    """An immutable relation between physical source and target token IDs."""

    relation_id: str | None = None
    kind: MatchRelationKind
    source_token_ids: tuple[str, ...]
    target_token_ids: tuple[str, ...]
    operations: tuple[MatchOperation, ...]
    warnings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _validate_relation(self) -> Self:
        self._validate_token_ids()
        self._validate_cardinality()
        expected = _content_id(
            self.model_dump(mode="json"), excluded_field="relation_id"
        )
        object.__setattr__(
            self,
            "relation_id",
            _validate_content_id(
                self.relation_id,
                expected=expected,
                field_name="relation_id",
            ),
        )
        return self

    def _validate_token_ids(self) -> None:
        identifiers = self.source_token_ids + self.target_token_ids
        if any(not token_id for token_id in identifiers):
            msg = "relation token IDs must not be empty"
            raise ValueError(msg)
        if len(set(self.source_token_ids)) != len(self.source_token_ids):
            msg = "source token IDs must be unique within a relation"
            raise ValueError(msg)
        if len(set(self.target_token_ids)) != len(self.target_token_ids):
            msg = "target token IDs must be unique within a relation"
            raise ValueError(msg)

    def _validate_cardinality(self) -> None:
        source_count = len(self.source_token_ids)
        target_count = len(self.target_token_ids)
        expected = {
            MatchRelationKind.ONE_TO_ONE: (source_count == 1 and target_count == 1),
            MatchRelationKind.SOURCE_TO_FRAGMENTS: (
                source_count == 1 and target_count >= 2
            ),
            MatchRelationKind.SOURCES_TO_ONE: (source_count >= 2 and target_count == 1),
            MatchRelationKind.SOURCE_ONLY: (source_count >= 1 and target_count == 0),
            MatchRelationKind.TARGET_ONLY: (source_count == 0 and target_count >= 1),
        }
        if not expected[self.kind]:
            msg = f"{self.kind.value} relation has invalid token cardinality"
            raise ValueError(msg)


class MatchAlternative(CanonicalModel):
    """One complete deterministic graph candidate with immutable relations."""

    alternative_id: str | None = None
    total_cost: float
    relations: tuple[MatchRelation, ...]
    warnings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _validate_alternative(self) -> Self:
        if not math.isfinite(self.total_cost) or self.total_cost < 0:
            msg = "alternative total_cost must be finite and nonnegative"
            raise ValueError(msg)
        relation_ids = tuple(relation.relation_id for relation in self.relations)
        if len(set(relation_ids)) != len(relation_ids):
            msg = "relation IDs must be unique within an alternative"
            raise ValueError(msg)
        expected = _content_id(
            self.model_dump(mode="json"), excluded_field="alternative_id"
        )
        object.__setattr__(
            self,
            "alternative_id",
            _validate_content_id(
                self.alternative_id,
                expected=expected,
                field_name="alternative_id",
            ),
        )
        return self


class MatchPolicy(CanonicalModel):
    """Versioned deterministic costs, bounds, and acceptance settings."""

    policy_id: str
    version: str
    low_margin_threshold: Annotated[float, Field(ge=0.0)]
    max_merge_size: Annotated[int, Field(strict=True, ge=1)]
    max_state_count: Annotated[int, Field(strict=True, ge=1)]
    max_transition_count: Annotated[int, Field(strict=True, ge=1)]
    exact_match_cost: Annotated[float, Field(ge=0.0)] = 0.0
    substitution_cost: Annotated[float, Field(ge=0.0)] = 1.0
    source_only_cost: Annotated[float, Field(ge=0.0)] = 1.0
    target_only_cost: Annotated[float, Field(ge=0.0)] = 1.0
    comparison_normalization_version: str = "1"
    tie_break_rule: str = "canonical_relation_bytes"

    @field_validator(
        "policy_id",
        "version",
        "comparison_normalization_version",
        "tie_break_rule",
    )
    @classmethod
    def _validate_strings(cls, value: str, info: object) -> str:
        field_name = getattr(info, "field_name", "policy field")
        return _validate_identifier(value, field_name=str(field_name))

    @field_validator(
        "low_margin_threshold",
        "exact_match_cost",
        "substitution_cost",
        "source_only_cost",
        "target_only_cost",
    )
    @classmethod
    def _validate_finite_costs(cls, value: float, info: object) -> float:
        if not math.isfinite(value):
            field_name = getattr(info, "field_name", "policy value")
            msg = f"{field_name} must be finite"
            raise ValueError(msg)
        return value


class MatchGraph(CanonicalModel):
    """An immutable match result with canonical identity and review quarantine."""

    graph_id: str | None = None
    source_document: MatchDocument
    target_document: MatchDocument
    policy: MatchPolicy
    best_alternative: MatchAlternative
    runner_up_alternative: MatchAlternative | None
    runner_up_margin: float | None
    accepted: bool
    quarantine_reasons: tuple[MatchQuarantineReason, ...]
    warnings: tuple[str, ...] = ()

    @field_validator("runner_up_margin")
    @classmethod
    def _validate_margin(cls, value: float | None) -> float | None:
        if value is not None and (value < 0 or not math.isfinite(value)):
            msg = "runner_up_margin must be finite and nonnegative when present"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _validate_graph(self) -> Self:
        if (self.runner_up_alternative is None) != (self.runner_up_margin is None):
            msg = "runner-up alternative and margin must be present together"
            raise ValueError(msg)
        if self.accepted and self.quarantine_reasons:
            msg = "accepted graphs cannot contain quarantine reasons"
            raise ValueError(msg)
        if not self.accepted and not self.quarantine_reasons:
            msg = "unaccepted graphs require at least one quarantine reason"
            raise ValueError(msg)
        self._validate_relation_references(self.best_alternative)
        if self.runner_up_alternative is not None:
            self._validate_relation_references(self.runner_up_alternative)
        expected = _content_id(self.model_dump(mode="json"), excluded_field="graph_id")
        object.__setattr__(
            self,
            "graph_id",
            _validate_content_id(
                self.graph_id,
                expected=expected,
                field_name="graph_id",
            ),
        )
        return self

    def _validate_relation_references(self, alternative: MatchAlternative) -> None:
        source_ids = self.source_document.token_ids()
        target_ids = self.target_document.token_ids()
        for relation in alternative.relations:
            unknown_source = set(relation.source_token_ids) - source_ids
            if unknown_source:
                msg = "relation references an unknown source token"
                raise ValueError(msg)
            unknown_target = set(relation.target_token_ids) - target_ids
            if unknown_target:
                msg = "relation references an unknown target token"
                raise ValueError(msg)
