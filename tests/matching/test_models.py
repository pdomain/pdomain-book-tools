from __future__ import annotations

import pytest
from pydantic import ValidationError

from pdomain_book_tools.matching import (
    ArtifactRange,
    MatchAlternative,
    MatchDocument,
    MatchGraph,
    MatchLine,
    MatchOperation,
    MatchOperationKind,
    MatchPage,
    MatchPolicy,
    MatchQuarantineReason,
    MatchRelation,
    MatchRelationKind,
    MatchToken,
)


def _source_document() -> MatchDocument:
    return MatchDocument(
        document_id="source-book",
        pages=(
            MatchPage(
                page_id="source-001",
                lines=(
                    MatchLine(
                        line_id="source-001-line-1",
                        tokens=(
                            MatchToken(
                                token_id="source-001-line-1-token-1",
                                text="Saint",
                                artifact_ranges=(
                                    ArtifactRange(
                                        artifact_id="f2",
                                        artifact_sha256="a" * 64,
                                        byte_start=8,
                                        byte_end=13,
                                        grapheme_start=0,
                                        grapheme_end=5,
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )


def _target_document() -> MatchDocument:
    return MatchDocument(
        document_id="ocr-book",
        pages=(
            MatchPage(
                page_id="ocr-001",
                lines=(
                    MatchLine(
                        line_id="ocr-001-line-1",
                        tokens=(
                            MatchToken(
                                token_id="ocr-001-line-1-token-1",
                                text="SAINT",
                                artifact_ranges=(
                                    ArtifactRange(
                                        artifact_id="ocr",
                                        artifact_sha256="b" * 64,
                                        byte_start=41,
                                        byte_end=46,
                                        grapheme_start=0,
                                        grapheme_end=5,
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )


def _relation() -> MatchRelation:
    return MatchRelation(
        relation_id=None,
        kind=MatchRelationKind.ONE_TO_ONE,
        source_token_ids=("source-001-line-1-token-1",),
        target_token_ids=("ocr-001-line-1-token-1",),
        operations=(
            MatchOperation(
                kind=MatchOperationKind.MATCH,
                source_grapheme_range=(0, 5),
                target_grapheme_range=(0, 5),
            ),
        ),
    )


def _graph() -> MatchGraph:
    return MatchGraph(
        graph_id=None,
        source_document=_source_document(),
        target_document=_target_document(),
        policy=MatchPolicy(
            policy_id="pgdp-aware-v1",
            version="1.0.0",
            low_margin_threshold=1.0,
            max_merge_size=2,
            max_state_count=100,
            max_transition_count=200,
        ),
        best_alternative=MatchAlternative(
            alternative_id=None,
            total_cost=0.0,
            relations=(_relation(),),
        ),
        runner_up_alternative=None,
        runner_up_margin=None,
        accepted=True,
        quarantine_reasons=(),
    )


def test_documents_preserve_order_and_require_globally_stable_token_ids() -> None:
    document = MatchDocument.model_validate(
        {
            "document_id": "book",
            "pages": [
                {
                    "page_id": "page-2",
                    "lines": [
                        {
                            "line_id": "page-2-line-2",
                            "tokens": [
                                {
                                    "token_id": "page-2-line-2-token-1",
                                    "text": "second",
                                    "artifact_ranges": [],
                                },
                            ],
                        },
                        {
                            "line_id": "page-2-line-3",
                            "tokens": [
                                {
                                    "token_id": "page-2-line-3-token-1",
                                    "text": "third",
                                    "artifact_ranges": [],
                                },
                            ],
                        },
                    ],
                },
                {
                    "page_id": "page-10",
                    "lines": [
                        {
                            "line_id": "page-10-line-1",
                            "tokens": [
                                {
                                    "token_id": "page-10-line-1-token-1",
                                    "text": "tenth",
                                    "artifact_ranges": [],
                                },
                            ],
                        },
                    ],
                },
            ],
        }
    )

    assert tuple(page.page_id for page in document.pages) == ("page-2", "page-10")
    assert tuple(line.line_id for line in document.pages[0].lines) == (
        "page-2-line-2",
        "page-2-line-3",
    )
    assert isinstance(document.pages, tuple)
    with pytest.raises(ValidationError, match="token IDs must be unique"):
        MatchDocument.model_validate(
            {
                **document.model_dump(),
                "pages": (
                    document.pages[0],
                    MatchPage(
                        page_id="page-11",
                        lines=(
                            MatchLine(
                                line_id="page-11-line-1",
                                tokens=(
                                    MatchToken(
                                        token_id="page-2-line-2-token-1",
                                        text="duplicate",
                                        artifact_ranges=(),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            }
        )


def test_artifact_ranges_reject_unordered_or_empty_ranges() -> None:
    with pytest.raises(ValidationError, match="byte range must be nonempty"):
        ArtifactRange(
            artifact_id="f2",
            artifact_sha256="a" * 64,
            byte_start=3,
            byte_end=3,
            grapheme_start=1,
            grapheme_end=2,
        )
    with pytest.raises(ValidationError, match="grapheme range must be nonempty"):
        ArtifactRange(
            artifact_id="f2",
            artifact_sha256="a" * 64,
            byte_start=3,
            byte_end=4,
            grapheme_start=2,
            grapheme_end=1,
        )


@pytest.mark.parametrize(
    ("kind", "source_token_ids", "target_token_ids"),
    [
        (MatchRelationKind.ONE_TO_ONE, ("source",), ("target-1", "target-2")),
        (MatchRelationKind.SOURCE_TO_FRAGMENTS, ("source",), ("target",)),
        (MatchRelationKind.SOURCES_TO_ONE, ("source",), ("target",)),
        (MatchRelationKind.SOURCE_ONLY, (), ()),
        (MatchRelationKind.TARGET_ONLY, (), ()),
    ],
)
def test_relations_enforce_their_declared_cardinality(
    kind: MatchRelationKind,
    source_token_ids: tuple[str, ...],
    target_token_ids: tuple[str, ...],
) -> None:
    with pytest.raises(ValidationError):
        MatchRelation(
            relation_id=None,
            kind=kind,
            source_token_ids=source_token_ids,
            target_token_ids=target_token_ids,
            operations=(),
        )


def test_graph_ids_are_canonical_and_graph_relations_reference_its_documents() -> None:
    graph = _graph()
    rebuilt = MatchGraph.model_validate(graph.model_dump())

    assert graph.graph_id == rebuilt.graph_id
    assert graph.graph_id is not None
    assert len(graph.graph_id) == 64
    with pytest.raises(ValidationError, match="unknown source token"):
        MatchGraph.model_validate(
            {
                **graph.model_dump(),
                "graph_id": None,
                "best_alternative": {
                    **graph.best_alternative.model_dump(),
                    "alternative_id": None,
                    "relations": (
                        {
                            **graph.best_alternative.relations[0].model_dump(),
                            "relation_id": None,
                            "source_token_ids": ("not-in-source",),
                        },
                    ),
                },
            }
        )


def test_nested_collections_are_deeply_immutable() -> None:
    source_ranges = [
        ArtifactRange(
            artifact_id="f2",
            artifact_sha256="a" * 64,
            byte_start=0,
            byte_end=5,
            grapheme_start=0,
            grapheme_end=5,
        ),
    ]
    tokens = [
        MatchToken.model_validate(
            {
                "token_id": "source-token",
                "text": "Saint",
                "artifact_ranges": source_ranges,
            }
        ),
    ]
    line = MatchLine.model_validate({"line_id": "source-line", "tokens": tokens})
    source_ranges.clear()
    tokens.clear()

    assert line.tokens[0].artifact_ranges[0].artifact_id == "f2"
    with pytest.raises(ValidationError):
        line.tokens[0].text = "changed"
    with pytest.raises(ValidationError):
        line.tokens = line.tokens
    with pytest.raises(ValidationError):
        line.tokens[0].artifact_ranges = ()


def test_unaccepted_graph_requires_a_explicit_quarantine_reason() -> None:
    graph = _graph()
    with pytest.raises(ValidationError, match="quarantine reason"):
        MatchGraph.model_validate(
            {
                **graph.model_dump(),
                "graph_id": None,
                "accepted": False,
                "quarantine_reasons": (),
            }
        )
    quarantined = MatchGraph.model_validate(
        {
            **graph.model_dump(),
            "graph_id": None,
            "accepted": False,
            "quarantine_reasons": (MatchQuarantineReason.TIE,),
        }
    )
    assert quarantined.accepted is False


def test_graph_rejects_operations_that_overlap_or_exceed_token_graphemes() -> None:
    graph = _graph()
    overlapping_relation = MatchRelation(
        relation_id=None,
        kind=MatchRelationKind.ONE_TO_ONE,
        source_token_ids=("source-001-line-1-token-1",),
        target_token_ids=("ocr-001-line-1-token-1",),
        operations=(
            MatchOperation(
                kind=MatchOperationKind.MATCH,
                source_grapheme_range=(0, 3),
                target_grapheme_range=(0, 3),
            ),
            MatchOperation(
                kind=MatchOperationKind.MATCH,
                source_grapheme_range=(2, 5),
                target_grapheme_range=(3, 5),
            ),
        ),
    )
    with pytest.raises(ValidationError, match="monotonic"):
        MatchGraph(
            graph_id=None,
            source_document=graph.source_document,
            target_document=graph.target_document,
            policy=graph.policy,
            best_alternative=MatchAlternative(
                alternative_id=None,
                total_cost=0.0,
                relations=(overlapping_relation,),
            ),
            runner_up_alternative=None,
            runner_up_margin=None,
            accepted=True,
            quarantine_reasons=(),
        )

    out_of_bounds_relation = MatchRelation(
        relation_id=None,
        kind=MatchRelationKind.ONE_TO_ONE,
        source_token_ids=("source-001-line-1-token-1",),
        target_token_ids=("ocr-001-line-1-token-1",),
        operations=(
            MatchOperation(
                kind=MatchOperationKind.MATCH,
                source_grapheme_range=(0, 6),
                target_grapheme_range=(0, 5),
            ),
        ),
    )
    with pytest.raises(ValidationError, match="source grapheme range"):
        MatchGraph(
            graph_id=None,
            source_document=graph.source_document,
            target_document=graph.target_document,
            policy=graph.policy,
            best_alternative=MatchAlternative(
                alternative_id=None,
                total_cost=0.0,
                relations=(out_of_bounds_relation,),
            ),
            runner_up_alternative=None,
            runner_up_margin=None,
            accepted=True,
            quarantine_reasons=(),
        )


def test_graph_rejects_accepted_ties_and_below_policy_margins() -> None:
    graph = _graph()
    runner_up = MatchAlternative(
        alternative_id=None,
        total_cost=1.0,
        relations=graph.best_alternative.relations,
    )
    with pytest.raises(ValidationError, match="tie"):
        MatchGraph(
            graph_id=None,
            source_document=graph.source_document,
            target_document=graph.target_document,
            policy=graph.policy,
            best_alternative=graph.best_alternative,
            runner_up_alternative=runner_up,
            runner_up_margin=0.0,
            accepted=True,
            quarantine_reasons=(),
        )
    with pytest.raises(ValidationError, match="low margin"):
        MatchGraph(
            graph_id=None,
            source_document=graph.source_document,
            target_document=graph.target_document,
            policy=graph.policy,
            best_alternative=graph.best_alternative,
            runner_up_alternative=runner_up,
            runner_up_margin=0.5,
            accepted=True,
            quarantine_reasons=(),
        )
    with pytest.raises(ValidationError, match="tie"):
        MatchGraph(
            graph_id=None,
            source_document=graph.source_document,
            target_document=graph.target_document,
            policy=graph.policy,
            best_alternative=graph.best_alternative,
            runner_up_alternative=runner_up,
            runner_up_margin=0.0,
            accepted=False,
            quarantine_reasons=(MatchQuarantineReason.LOW_MARGIN,),
        )
    with pytest.raises(ValidationError, match="low margin"):
        MatchGraph(
            graph_id=None,
            source_document=graph.source_document,
            target_document=graph.target_document,
            policy=graph.policy,
            best_alternative=graph.best_alternative,
            runner_up_alternative=runner_up,
            runner_up_margin=0.5,
            accepted=False,
            quarantine_reasons=(MatchQuarantineReason.TIE,),
        )


def test_alternatives_reject_source_or_target_token_reuse() -> None:
    source = MatchDocument(
        document_id="source",
        pages=(
            MatchPage(
                page_id="source-page",
                lines=(
                    MatchLine(
                        line_id="source-line",
                        tokens=(
                            MatchToken(
                                token_id="source-1", text="abc", artifact_ranges=()
                            ),
                            MatchToken(
                                token_id="source-2", text="def", artifact_ranges=()
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    target = MatchDocument(
        document_id="target",
        pages=(
            MatchPage(
                page_id="target-page",
                lines=(
                    MatchLine(
                        line_id="target-line",
                        tokens=(
                            MatchToken(
                                token_id="target-1", text="abc", artifact_ranges=()
                            ),
                            MatchToken(
                                token_id="target-2", text="def", artifact_ranges=()
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    source_reused = (
        MatchRelation(
            relation_id=None,
            kind=MatchRelationKind.ONE_TO_ONE,
            source_token_ids=("source-1",),
            target_token_ids=("target-1",),
            operations=(
                MatchOperation(
                    kind=MatchOperationKind.MATCH,
                    source_grapheme_range=(0, 3),
                    target_grapheme_range=(0, 3),
                ),
            ),
        ),
        MatchRelation(
            relation_id=None,
            kind=MatchRelationKind.ONE_TO_ONE,
            source_token_ids=("source-1",),
            target_token_ids=("target-2",),
            operations=(
                MatchOperation(
                    kind=MatchOperationKind.MATCH,
                    source_grapheme_range=(0, 3),
                    target_grapheme_range=(0, 3),
                ),
            ),
        ),
    )
    with pytest.raises(ValidationError, match="source tokens can appear only once"):
        MatchAlternative(alternative_id=None, total_cost=0.0, relations=source_reused)

    target_reused = (
        source_reused[0],
        MatchRelation(
            relation_id=None,
            kind=MatchRelationKind.ONE_TO_ONE,
            source_token_ids=("source-2",),
            target_token_ids=("target-1",),
            operations=(
                MatchOperation(
                    kind=MatchOperationKind.MATCH,
                    source_grapheme_range=(0, 3),
                    target_grapheme_range=(0, 3),
                ),
            ),
        ),
    )
    with pytest.raises(ValidationError, match="target tokens can appear only once"):
        MatchAlternative(alternative_id=None, total_cost=0.0, relations=target_reused)

    assert source.token_ids() == {"source-1", "source-2"}
    assert target.token_ids() == {"target-1", "target-2"}


def test_every_match_contract_is_deeply_immutable_after_mutable_input_conversion() -> (
    None
):
    source_range = [0, 5]
    target_range = [0, 5]
    operation = MatchOperation.model_validate(
        {
            "kind": MatchOperationKind.MATCH,
            "source_grapheme_range": source_range,
            "target_grapheme_range": target_range,
        }
    )
    source_range[0] = 4
    target_range[0] = 4
    operations = [operation]
    relation = MatchRelation.model_validate(
        {
            "relation_id": None,
            "kind": MatchRelationKind.ONE_TO_ONE,
            "source_token_ids": ["source-001-line-1-token-1"],
            "target_token_ids": ["ocr-001-line-1-token-1"],
            "operations": operations,
        }
    )
    operations.clear()
    relations = [relation]
    alternative = MatchAlternative.model_validate(
        {
            "alternative_id": None,
            "total_cost": 0.0,
            "relations": relations,
        }
    )
    relations.clear()
    source_pages = [_source_document().pages[0]]
    document = MatchDocument.model_validate(
        {"document_id": "immutable-source", "pages": source_pages}
    )
    source_pages.clear()
    graph_warnings = ["review later"]
    graph = MatchGraph.model_validate(
        {
            "graph_id": None,
            "source_document": _source_document(),
            "target_document": _target_document(),
            "policy": _graph().policy,
            "best_alternative": alternative,
            "runner_up_alternative": None,
            "runner_up_margin": None,
            "accepted": True,
            "quarantine_reasons": [],
            "warnings": graph_warnings,
        }
    )
    graph_warnings.clear()

    assert operation.source_grapheme_range == (0, 5)
    assert relation.operations == (operation,)
    assert alternative.relations == (relation,)
    assert document.pages[0].page_id == "source-001"
    assert graph.warnings == ("review later",)
    for model, field_name, replacement in (
        (operation, "kind", MatchOperationKind.SUBSTITUTION),
        (relation, "warnings", ("changed",)),
        (alternative, "total_cost", 1.0),
        (_graph().policy, "version", "changed"),
        (document, "warnings", ("changed",)),
        (graph, "accepted", False),
    ):
        with pytest.raises(ValidationError):
            setattr(model, field_name, replacement)
