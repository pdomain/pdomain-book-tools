"""Immutable, source-neutral contracts for OCR-to-text matching."""

from __future__ import annotations

import hashlib
import json
import math
import string
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Self, override

from pydantic import Field, field_validator, model_validator

from pdomain_book_tools.typography.spans import CanonicalModel, split_graphemes

if TYPE_CHECKING:
    from collections.abc import Mapping

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

    @override
    def model_copy(
        self,
        *,
        update: Mapping[str, object] | None = None,
        deep: bool = False,
    ) -> Self:
        """Return a revalidated copy that always recomputes its content ID."""
        del deep
        payload = {**self.model_dump(), **(update or {}), "relation_id": None}
        return type(self).model_validate(payload)

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

    @override
    def model_copy(
        self,
        *,
        update: Mapping[str, object] | None = None,
        deep: bool = False,
    ) -> Self:
        """Return a revalidated copy that always recomputes its content ID."""
        del deep
        payload = {**self.model_dump(), **(update or {}), "alternative_id": None}
        return type(self).model_validate(payload)

    @model_validator(mode="after")
    def _validate_alternative(self) -> Self:
        if not math.isfinite(self.total_cost) or self.total_cost < 0:
            msg = "alternative total_cost must be finite and nonnegative"
            raise ValueError(msg)
        relation_ids = tuple(relation.relation_id for relation in self.relations)
        if len(set(relation_ids)) != len(relation_ids):
            msg = "relation IDs must be unique within an alternative"
            raise ValueError(msg)
        source_token_ids = tuple(
            token_id
            for relation in self.relations
            for token_id in relation.source_token_ids
        )
        if len(set(source_token_ids)) != len(source_token_ids):
            msg = "source tokens can appear only once within an alternative"
            raise ValueError(msg)
        target_token_ids = tuple(
            token_id
            for relation in self.relations
            for token_id in relation.target_token_ids
        )
        if len(set(target_token_ids)) != len(target_token_ids):
            msg = "target tokens can appear only once within an alternative"
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

    @override
    def model_copy(
        self,
        *,
        update: Mapping[str, object] | None = None,
        deep: bool = False,
    ) -> Self:
        """Return a revalidated copy that always recomputes its content ID."""
        del deep
        payload = {**self.model_dump(), **(update or {}), "graph_id": None}
        return type(self).model_validate(payload)

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
        self._validate_runner_up_integrity()
        if self.accepted and self.quarantine_reasons:
            msg = "accepted graphs cannot contain quarantine reasons"
            raise ValueError(msg)
        if not self.accepted and not self.quarantine_reasons:
            msg = "unaccepted graphs require at least one quarantine reason"
            raise ValueError(msg)
        self._validate_margin_acceptance()
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
        source_tokens = _tokens_by_id(self.source_document)
        target_tokens = _tokens_by_id(self.target_document)
        source_ids = frozenset(source_tokens)
        target_ids = frozenset(target_tokens)
        for relation in alternative.relations:
            unknown_source = set(relation.source_token_ids) - source_ids
            if unknown_source:
                msg = "relation references an unknown source token"
                raise ValueError(msg)
            unknown_target = set(relation.target_token_ids) - target_ids
            if unknown_target:
                msg = "relation references an unknown target token"
                raise ValueError(msg)
            self._validate_relation_operations(
                relation,
                source_grapheme_count=_relation_grapheme_count(
                    relation.source_token_ids, source_tokens
                ),
                target_grapheme_count=_relation_grapheme_count(
                    relation.target_token_ids, target_tokens
                ),
            )
        self._validate_alternative_coverage_and_order(
            alternative,
            source_token_order=_token_order(self.source_document),
            target_token_order=_token_order(self.target_document),
        )

    def _validate_runner_up_integrity(self) -> None:
        runner_up = self.runner_up_alternative
        margin = self.runner_up_margin
        if runner_up is None or margin is None:
            return
        if runner_up.alternative_id == self.best_alternative.alternative_id:
            msg = "runner-up alternative must differ from the best alternative"
            raise ValueError(msg)
        if runner_up.total_cost < self.best_alternative.total_cost:
            msg = "runner-up cost cannot be lower than best cost"
            raise ValueError(msg)
        expected_margin = runner_up.total_cost - self.best_alternative.total_cost
        if margin != expected_margin:
            msg = "runner-up margin must equal runner-up cost minus best cost"
            raise ValueError(msg)

    def _validate_margin_acceptance(self) -> None:
        margin = self.runner_up_margin
        if margin is None:
            return
        required_reasons: list[MatchQuarantineReason] = []
        if margin == 0:
            required_reasons.append(MatchQuarantineReason.TIE)
        if margin < self.policy.low_margin_threshold:
            required_reasons.append(MatchQuarantineReason.LOW_MARGIN)
        for reason in required_reasons:
            if self.accepted:
                msg = f"accepted graph must quarantine {reason.value.replace('_', ' ')}"
                raise ValueError(msg)
            if reason not in self.quarantine_reasons:
                msg = f"graph quarantine reasons must include {reason.value.replace('_', ' ')}"
                raise ValueError(msg)

    @staticmethod
    def _validate_alternative_coverage_and_order(
        alternative: MatchAlternative,
        *,
        source_token_order: tuple[str, ...],
        target_token_order: tuple[str, ...],
    ) -> None:
        relation_source_tokens = tuple(
            token_id
            for relation in alternative.relations
            for token_id in relation.source_token_ids
        )
        relation_target_tokens = tuple(
            token_id
            for relation in alternative.relations
            for token_id in relation.target_token_ids
        )
        if set(relation_source_tokens) != set(source_token_order):
            msg = "complete alternative must cover every source token exactly once"
            raise ValueError(msg)
        if set(relation_target_tokens) != set(target_token_order):
            msg = "complete alternative must cover every target token exactly once"
            raise ValueError(msg)
        if relation_source_tokens != source_token_order:
            msg = "relations must follow physical source document order"
            raise ValueError(msg)
        if relation_target_tokens != target_token_order:
            msg = "relations must follow physical target document order"
            raise ValueError(msg)

    @staticmethod
    def _validate_relation_operations(
        relation: MatchRelation,
        *,
        source_grapheme_count: int,
        target_grapheme_count: int,
    ) -> None:
        previous_source_end = 0
        previous_target_end = 0
        for operation in relation.operations:
            source_start, source_end = operation.source_grapheme_range
            target_start, target_end = operation.target_grapheme_range
            if source_start < previous_source_end or target_start < previous_target_end:
                msg = "relation operations must be monotonic and non-overlapping"
                raise ValueError(msg)
            if source_start > previous_source_end:
                msg = "relation operations must partition source graphemes without gaps"
                raise ValueError(msg)
            if target_start > previous_target_end:
                msg = "relation operations must partition target graphemes without gaps"
                raise ValueError(msg)
            if source_end > source_grapheme_count:
                msg = "relation operation source grapheme range exceeds its tokens"
                raise ValueError(msg)
            if target_end > target_grapheme_count:
                msg = "relation operation target grapheme range exceeds its tokens"
                raise ValueError(msg)
            previous_source_end = source_end
            previous_target_end = target_end
        if previous_source_end != source_grapheme_count:
            msg = "relation operations must partition source graphemes exactly"
            raise ValueError(msg)
        if previous_target_end != target_grapheme_count:
            msg = "relation operations must partition target graphemes exactly"
            raise ValueError(msg)


def _tokens_by_id(document: MatchDocument) -> dict[str, MatchToken]:
    """Return the document's stable tokens keyed by ID for graph validation."""
    return {
        token.token_id: token
        for page in document.pages
        for line in page.lines
        for token in line.tokens
    }


def _relation_grapheme_count(
    token_ids: tuple[str, ...], tokens_by_id: Mapping[str, MatchToken]
) -> int:
    """Count Unicode graphemes in the relation's declared physical-token order."""
    return sum(
        len(split_graphemes(tokens_by_id[token_id].text)) for token_id in token_ids
    )


def _token_order(document: MatchDocument) -> tuple[str, ...]:
    """Return stable token IDs in the document's physical reading order."""
    return tuple(
        token.token_id
        for page in document.pages
        for line in page.lines
        for token in line.tokens
    )
