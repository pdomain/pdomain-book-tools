from __future__ import annotations

import pytest
from pydantic import ValidationError

from pdomain_book_tools.matching import (
    ArtifactRange,
    MatchAlternative,
    MatchContinuationReference,
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
    MatchSearchEvidence,
    MatchSearchPathEvidence,
    MatchToken,
    canonical_relation_path_bytes,
    match_documents,
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


def _substitution_relation() -> MatchRelation:
    return MatchRelation(
        relation_id=None,
        kind=MatchRelationKind.ONE_TO_ONE,
        source_token_ids=("source-001-line-1-token-1",),
        target_token_ids=("ocr-001-line-1-token-1",),
        operations=(
            MatchOperation(
                kind=MatchOperationKind.SUBSTITUTION,
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


def _continuation_provenance_graph(*, right_fragment_text: str) -> MatchGraph:
    source_ranges = tuple(
        ArtifactRange(
            artifact_id="f2",
            artifact_sha256="a" * 64,
            byte_start=index,
            byte_end=index + 1,
            grapheme_start=index,
            grapheme_end=index + 1,
        )
        for index in range(3)
    )
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
                                token_id="source-token",
                                text="aa*",
                                artifact_ranges=source_ranges,
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
                        tokens=(MatchToken(token_id="target-token", text="aa"),),
                    ),
                ),
            ),
        ),
    )
    relation = MatchRelation(
        kind=MatchRelationKind.ONE_TO_ONE,
        source_token_ids=("source-token",),
        target_token_ids=("target-token",),
        operations=(
            MatchOperation(
                kind=MatchOperationKind.SUBSTITUTION,
                source_grapheme_range=(0, 3),
                target_grapheme_range=(0, 2),
            ),
        ),
        continuation_references=(
            MatchContinuationReference(
                continuation_id="continuation-1",
                evidence_artifact_id="pgdp-continuations",
                evidence_artifact_path="continuations/continuation-1.json",
                evidence_sha256="b" * 64,
                decision="join_without_hyphen",
                left_fragment_token_id="source-token",
                right_fragment_token_id="source-token",
                left_fragment_text="a",
                right_fragment_text=right_fragment_text,
                left_fragment_grapheme_ranges=(source_ranges[0],),
                right_fragment_grapheme_ranges=(source_ranges[1],),
                relation_source_token_ids=("source-token",),
                relation_target_token_ids=("target-token",),
            ),
        ),
    )
    return MatchGraph(
        source_document=source,
        target_document=target,
        policy=MatchPolicy(
            policy_id="matcher-v1",
            version="1",
            low_margin_threshold=0.5,
            max_merge_size=2,
            max_state_count=10,
            max_transition_count=10,
        ),
        best_alternative=MatchAlternative(total_cost=1.0, relations=(relation,)),
        runner_up_alternative=None,
        runner_up_margin=None,
        accepted=True,
        quarantine_reasons=(),
    )


def test_graph_accepts_ordered_continuation_provenance_against_document_tokens() -> (
    None
):
    assert _continuation_provenance_graph(right_fragment_text="a").accepted


def test_graph_rejects_continuation_text_not_present_at_declared_token_range() -> None:
    with pytest.raises(ValidationError, match="continuation provenance"):
        _continuation_provenance_graph(right_fragment_text="b")


def test_graph_content_id_rejects_tampered_continuation_evidence_pin() -> None:
    graph = _continuation_provenance_graph(right_fragment_text="a")
    payload = graph.model_dump(mode="json")
    relation = payload["best_alternative"]["relations"][0]
    relation["relation_id"] = None
    relation["continuation_references"][0]["evidence_sha256"] = "c" * 64
    payload["best_alternative"]["alternative_id"] = None

    with pytest.raises(ValidationError, match="graph_id"):
        MatchGraph.model_validate(payload)


def test_search_evidence_requires_at_least_one_state() -> None:
    graph = match_documents(
        _source_document(),
        _target_document(),
        policy=MatchPolicy(
            policy_id="matcher-v1",
            version="1",
            low_margin_threshold=0.5,
            max_merge_size=2,
            max_state_count=10,
            max_transition_count=10,
        ),
    )
    assert graph.search_evidence is not None
    with pytest.raises(ValidationError, match="state_count"):
        MatchSearchEvidence.model_validate(
            {**graph.search_evidence.model_dump(), "state_count": 0}
        )


def test_graph_rejects_search_evidence_that_disagrees_with_best_path() -> None:
    graph = match_documents(
        _source_document(),
        _target_document(),
        policy=MatchPolicy(
            policy_id="matcher-v1",
            version="1",
            low_margin_threshold=0.5,
            max_merge_size=2,
            max_state_count=10,
            max_transition_count=10,
        ),
    )
    assert graph.search_evidence is not None
    assert graph.search_evidence.best_complete_path is not None
    contradictory_path = MatchSearchPathEvidence.model_validate(
        {
            **graph.search_evidence.best_complete_path.model_dump(),
            "total_cost": 1.0,
        }
    )
    contradictory_evidence = MatchSearchEvidence.model_validate(
        {
            **graph.search_evidence.model_dump(),
            "best_complete_path": contradictory_path.model_dump(),
        }
    )

    with pytest.raises(ValidationError, match="best complete search path"):
        MatchGraph.model_validate(
            {
                **graph.model_dump(),
                "search_evidence": contradictory_evidence.model_dump(),
            }
        )


def test_graph_accepts_exhausted_search_without_a_complete_path() -> None:
    graph = match_documents(
        _source_document(),
        _target_document(),
        policy=MatchPolicy(
            policy_id="matcher-v1",
            version="1",
            low_margin_threshold=0.5,
            max_merge_size=2,
            max_state_count=1,
            max_transition_count=10,
        ),
    )

    assert not graph.accepted
    assert graph.search_evidence is not None
    assert graph.search_evidence.best_complete_path is None
    assert MatchGraph.model_validate(graph.model_dump()).graph_id == graph.graph_id


def test_graph_rejects_equal_cost_runner_up_before_canonical_best_path() -> None:
    first = MatchAlternative(total_cost=0.0, relations=(_relation(),))
    second = MatchAlternative(total_cost=0.0, relations=(_substitution_relation(),))
    ordered = tuple(
        sorted(
            (first, second),
            key=lambda alternative: canonical_relation_path_bytes(
                alternative.relations
            ),
        )
    )

    with pytest.raises(ValidationError, match="canonical ordering"):
        MatchGraph(
            source_document=_source_document(),
            target_document=_target_document(),
            policy=MatchPolicy(
                policy_id="pgdp-aware-v1",
                version="1.0.0",
                low_margin_threshold=0.0,
                max_merge_size=2,
                max_state_count=100,
                max_transition_count=200,
            ),
            best_alternative=ordered[1],
            runner_up_alternative=ordered[0],
            runner_up_margin=0.0,
            accepted=False,
            quarantine_reasons=(MatchQuarantineReason.TIE,),
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
    distinct_path_relation = _substitution_relation()
    tie_runner_up = MatchAlternative(
        alternative_id=None,
        total_cost=0.0,
        relations=(distinct_path_relation,),
    )
    low_margin_runner_up = MatchAlternative(
        alternative_id=None,
        total_cost=0.5,
        relations=(distinct_path_relation,),
    )
    with pytest.raises(ValidationError, match="tie"):
        MatchGraph(
            graph_id=None,
            source_document=graph.source_document,
            target_document=graph.target_document,
            policy=graph.policy,
            best_alternative=graph.best_alternative,
            runner_up_alternative=tie_runner_up,
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
            runner_up_alternative=low_margin_runner_up,
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
            runner_up_alternative=tie_runner_up,
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
            runner_up_alternative=low_margin_runner_up,
            runner_up_margin=0.5,
            accepted=False,
            quarantine_reasons=(MatchQuarantineReason.TIE,),
        )


def test_graph_rejects_runner_up_that_differs_only_by_alternative_metadata() -> None:
    graph = _graph()
    metadata_only_runner_up = MatchAlternative(
        alternative_id=None,
        total_cost=0.0,
        relations=graph.best_alternative.relations,
        warnings=("different metadata",),
    )

    with pytest.raises(ValidationError, match="runner-up path must differ"):
        MatchGraph(
            graph_id=None,
            source_document=graph.source_document,
            target_document=graph.target_document,
            policy=graph.policy,
            best_alternative=graph.best_alternative,
            runner_up_alternative=metadata_only_runner_up,
            runner_up_margin=0.0,
            accepted=False,
            quarantine_reasons=(
                MatchQuarantineReason.TIE,
                MatchQuarantineReason.LOW_MARGIN,
            ),
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


def test_content_addressed_model_copies_recompute_all_ids() -> None:
    graph = _graph()
    relation = graph.best_alternative.relations[0]
    copied_relation = relation.model_copy(
        update={"relation_id": relation.relation_id, "warnings": ("changed",)}
    )
    copied_alternative = graph.best_alternative.model_copy(
        update={
            "alternative_id": graph.best_alternative.alternative_id,
            "total_cost": 1.0,
        }
    )
    copied_graph = graph.model_copy(
        update={"graph_id": graph.graph_id, "warnings": ("changed",)}
    )

    assert copied_relation.relation_id != relation.relation_id
    assert copied_alternative.alternative_id != graph.best_alternative.alternative_id
    assert copied_graph.graph_id != graph.graph_id


def test_graph_enforces_runner_up_identity_cost_and_exact_margin() -> None:
    graph = _graph()
    runner_up = MatchAlternative(
        alternative_id=None,
        total_cost=1.0,
        relations=(_substitution_relation(),),
    )
    accepted_graph = MatchGraph(
        graph_id=None,
        source_document=graph.source_document,
        target_document=graph.target_document,
        policy=graph.policy,
        best_alternative=graph.best_alternative,
        runner_up_alternative=runner_up,
        runner_up_margin=1.0,
        accepted=True,
        quarantine_reasons=(),
    )
    assert accepted_graph.accepted is True

    with pytest.raises(ValidationError, match="runner-up path must differ"):
        MatchGraph(
            graph_id=None,
            source_document=graph.source_document,
            target_document=graph.target_document,
            policy=graph.policy,
            best_alternative=graph.best_alternative,
            runner_up_alternative=graph.best_alternative,
            runner_up_margin=1.0,
            accepted=True,
            quarantine_reasons=(),
        )
    with pytest.raises(ValidationError, match="runner-up cost cannot be lower"):
        MatchGraph(
            graph_id=None,
            source_document=graph.source_document,
            target_document=graph.target_document,
            policy=graph.policy,
            best_alternative=runner_up,
            runner_up_alternative=graph.best_alternative,
            runner_up_margin=0.0,
            accepted=False,
            quarantine_reasons=(MatchQuarantineReason.TIE,),
        )
    with pytest.raises(ValidationError, match="runner-up margin must equal"):
        MatchGraph(
            graph_id=None,
            source_document=graph.source_document,
            target_document=graph.target_document,
            policy=graph.policy,
            best_alternative=graph.best_alternative,
            runner_up_alternative=runner_up,
            runner_up_margin=0.5,
            accepted=False,
            quarantine_reasons=(MatchQuarantineReason.LOW_MARGIN,),
        )


def test_graph_requires_operations_to_partition_relation_graphemes_exactly() -> None:
    graph = _graph()
    gapped_relation = MatchRelation(
        relation_id=None,
        kind=MatchRelationKind.ONE_TO_ONE,
        source_token_ids=("source-001-line-1-token-1",),
        target_token_ids=("ocr-001-line-1-token-1",),
        operations=(
            MatchOperation(
                kind=MatchOperationKind.MATCH,
                source_grapheme_range=(0, 2),
                target_grapheme_range=(0, 2),
            ),
            MatchOperation(
                kind=MatchOperationKind.MATCH,
                source_grapheme_range=(3, 5),
                target_grapheme_range=(3, 5),
            ),
        ),
    )
    with pytest.raises(ValidationError, match="partition source graphemes"):
        MatchGraph(
            graph_id=None,
            source_document=graph.source_document,
            target_document=graph.target_document,
            policy=graph.policy,
            best_alternative=MatchAlternative(
                alternative_id=None,
                total_cost=0.0,
                relations=(gapped_relation,),
            ),
            runner_up_alternative=None,
            runner_up_margin=None,
            accepted=True,
            quarantine_reasons=(),
        )

    source_only_document = MatchDocument(
        document_id="source-only",
        pages=(
            MatchPage(
                page_id="source-only-page",
                lines=(
                    MatchLine(
                        line_id="source-only-line",
                        tokens=(
                            MatchToken(
                                token_id="source-only-token",
                                text="e\u0301",
                                artifact_ranges=(),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    empty_target_document = MatchDocument(
        document_id="empty-target",
        pages=(MatchPage(page_id="empty-target-page", lines=()),),
    )
    source_only_relation = MatchRelation(
        relation_id=None,
        kind=MatchRelationKind.SOURCE_ONLY,
        source_token_ids=("source-only-token",),
        target_token_ids=(),
        operations=(
            MatchOperation(
                kind=MatchOperationKind.SOURCE_ONLY_DELETION,
                source_grapheme_range=(0, 1),
                target_grapheme_range=(0, 0),
            ),
        ),
    )
    source_only_graph = MatchGraph(
        graph_id=None,
        source_document=source_only_document,
        target_document=empty_target_document,
        policy=graph.policy,
        best_alternative=MatchAlternative(
            alternative_id=None,
            total_cost=1.0,
            relations=(source_only_relation,),
        ),
        runner_up_alternative=None,
        runner_up_margin=None,
        accepted=True,
        quarantine_reasons=(),
    )
    assert source_only_graph.accepted is True


def test_graph_requires_complete_ordered_document_token_coverage() -> None:
    source_document = MatchDocument(
        document_id="source",
        pages=(
            MatchPage(
                page_id="source-page",
                lines=(
                    MatchLine(
                        line_id="source-line",
                        tokens=(
                            MatchToken(
                                token_id="source-1", text="one", artifact_ranges=()
                            ),
                            MatchToken(
                                token_id="source-2", text="two", artifact_ranges=()
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    target_document = MatchDocument(
        document_id="target",
        pages=(
            MatchPage(
                page_id="target-page",
                lines=(
                    MatchLine(
                        line_id="target-line",
                        tokens=(
                            MatchToken(
                                token_id="target-1", text="one", artifact_ranges=()
                            ),
                            MatchToken(
                                token_id="target-2", text="two", artifact_ranges=()
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    relation_one = MatchRelation(
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
    )
    relation_two = MatchRelation(
        relation_id=None,
        kind=MatchRelationKind.ONE_TO_ONE,
        source_token_ids=("source-2",),
        target_token_ids=("target-2",),
        operations=(
            MatchOperation(
                kind=MatchOperationKind.MATCH,
                source_grapheme_range=(0, 3),
                target_grapheme_range=(0, 3),
            ),
        ),
    )
    policy = _graph().policy
    with pytest.raises(ValidationError, match="cover every source token"):
        MatchGraph(
            graph_id=None,
            source_document=source_document,
            target_document=target_document,
            policy=policy,
            best_alternative=MatchAlternative(
                alternative_id=None,
                total_cost=0.0,
                relations=(relation_one,),
            ),
            runner_up_alternative=None,
            runner_up_margin=None,
            accepted=True,
            quarantine_reasons=(),
        )
    with pytest.raises(ValidationError, match="physical source document order"):
        MatchGraph(
            graph_id=None,
            source_document=source_document,
            target_document=target_document,
            policy=policy,
            best_alternative=MatchAlternative(
                alternative_id=None,
                total_cost=0.0,
                relations=(relation_two, relation_one),
            ),
            runner_up_alternative=None,
            runner_up_margin=None,
            accepted=True,
            quarantine_reasons=(),
        )
