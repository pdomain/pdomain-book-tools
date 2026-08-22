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
