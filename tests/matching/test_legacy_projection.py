"""Tests for opt-in projection of immutable matches onto legacy OCR pages."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.matching import (
    LegacyDocumentSide,
    MatchDocument,
    MatchLine,
    MatchPage,
    MatchPolicy,
    MatchToken,
    legacy_page_to_match_document,
    match_documents,
    project_match_graph_onto_page,
)
from pdomain_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pdomain_book_tools.ocr.page import Page
from pdomain_book_tools.ocr.word import Word

if TYPE_CHECKING:
    from collections.abc import Sequence


def _page(lines_of_words: Sequence[Sequence[str]]) -> Page:
    """Build a page with deterministic, non-normalized word geometry."""
    lines: list[Block] = []
    for line_index, word_texts in enumerate(lines_of_words):
        words = [
            Word(
                text=text,
                bounding_box=BoundingBox.from_ltrb(
                    word_index * 20,
                    line_index * 20,
                    word_index * 20 + 16,
                    line_index * 20 + 16,
                    is_normalized=False,
                ),
            )
            for word_index, text in enumerate(word_texts)
        ]
        lines.append(
            Block(
                items=words,
                block_category=BlockCategory.LINE,
                child_type=BlockChildType.WORDS,
            )
        )
    return Page(width=400, height=400, page_index=7, blocks=lines)


def _source_document(*texts: str) -> MatchDocument:
    """Build a simple immutable source document."""
    return MatchDocument(
        document_id="ground-truth",
        pages=(
            MatchPage(
                page_id="ground-truth:page:0",
                lines=(
                    MatchLine(
                        line_id="ground-truth:page:0:line:0",
                        tokens=tuple(
                            MatchToken(
                                token_id=f"ground-truth:page:0:line:0:word:{index}",
                                text=text,
                            )
                            for index, text in enumerate(texts)
                        ),
                    ),
                ),
            ),
        ),
    )


def _policy() -> MatchPolicy:
    """Return a bounded policy for one-page projection examples."""
    return MatchPolicy(
        policy_id="legacy-projection-test",
        version="1",
        low_margin_threshold=0.5,
        max_merge_size=2,
        max_state_count=100,
        max_transition_count=100,
    )


def test_graph_retains_original_page_topology_before_legacy_projection() -> None:
    """Building a graph must not collapse physical OCR words before projection."""
    page = _page((("hel", "lo"),))
    target = legacy_page_to_match_document(page, document_id="ocr-page")
    graph = match_documents(_source_document("hello"), target, policy=_policy())

    assert graph.accepted
    assert graph.best_alternative.relations[0].target_token_ids == (
        "ocr-page:page:7:line:0:word:0",
        "ocr-page:page:7:line:0:word:1",
    )
    assert [word.text for word in page.lines[0].words] == ["hel", "lo"]
    assert len(page.lines[0].words) == 2


def test_projection_combines_target_fragments_with_typed_physical_evidence() -> None:
    """Opt-in projection retains old combined-word behavior after graph matching."""
    page = _page((("hel", "lo"),))
    target = legacy_page_to_match_document(page, document_id="ocr-page")
    graph = match_documents(_source_document("hello"), target, policy=_policy())

    result = project_match_graph_onto_page(
        page,
        graph,
        document_id="ocr-page",
        page_side=LegacyDocumentSide.TARGET,
    )

    assert result.mutated_relation_ids == (
        graph.best_alternative.relations[0].relation_id,
    )
    assert [word.text for word in page.lines[0].words] == ["hello"]
    word = page.lines[0].words[0]
    assert word.ground_truth_text == "hello"
    assert word.ground_truth_match_keys["match_graph_id"] == graph.graph_id
    assert word.ground_truth_match_keys["match_source_token_ids"] == (
        "ground-truth:page:0:line:0:word:0",
    )
    assert word.ground_truth_match_keys["match_target_token_ids"] == (
        "ocr-page:page:7:line:0:word:0",
        "ocr-page:page:7:line:0:word:1",
    )
    assert word.ground_truth_match_keys["match_projection_mutation"] == (
        "combined_page_fragments"
    )
    assert word.ground_truth_match_keys["match_type"] == (
        "difflib-line-replace-word-replace-combined"
    )
    assert word.review is None
    assert word.typography_annotations is None


def test_projection_does_not_combine_manual_split_words() -> None:
    """A manual legacy split remains physical even when the graph joins it."""
    page = _page((("hel", "lo"),))
    page.lines[0].words[0].ground_truth_match_keys = {"split": True}
    target = legacy_page_to_match_document(page, document_id="ocr-page")
    graph = match_documents(_source_document("hello"), target, policy=_policy())

    result = project_match_graph_onto_page(
        page,
        graph,
        document_id="ocr-page",
        page_side=LegacyDocumentSide.TARGET,
    )

    assert result.mutated_relation_ids == ()
    assert result.skipped_relation_ids == (
        graph.best_alternative.relations[0].relation_id,
    )
    assert [word.text for word in page.lines[0].words] == ["hel", "lo"]
    assert page.lines[0].words[0].ground_truth_text == "hello"
    assert page.lines[0].words[1].ground_truth_text == ""


def test_projection_keeps_one_ocr_word_for_sources_to_one_relation() -> None:
    """A logical source join projects onto one OCR word without a topology change."""
    page = _page((("firefly",),))
    target = legacy_page_to_match_document(page, document_id="ocr-page")
    graph = match_documents(_source_document("fire", "fly"), target, policy=_policy())

    result = project_match_graph_onto_page(
        page,
        graph,
        document_id="ocr-page",
        page_side=LegacyDocumentSide.TARGET,
    )

    assert result.mutated_relation_ids == ()
    assert [word.text for word in page.lines[0].words] == ["firefly"]
    word = page.lines[0].words[0]
    assert word.ground_truth_text == "firefly"
    assert word.ground_truth_match_keys["match_source_token_ids"] == (
        "ground-truth:page:0:line:0:word:0",
        "ground-truth:page:0:line:0:word:1",
    )


def test_projection_uses_stable_ids_for_multiple_page_lines() -> None:
    """A relation retains its page-line identity for every physical page line."""
    page = _page((("caption",), ("body",)))
    target = legacy_page_to_match_document(page, document_id="ocr-page")
    source = MatchDocument(
        document_id="ground-truth",
        pages=(
            MatchPage(
                page_id="ground-truth:page:0",
                lines=(
                    MatchLine(
                        line_id="ground-truth:page:0:line:caption",
                        tokens=(
                            MatchToken(
                                token_id="ground-truth:page:0:line:caption:word:0",
                                text="caption",
                            ),
                        ),
                    ),
                    MatchLine(
                        line_id="ground-truth:page:0:line:body",
                        tokens=(
                            MatchToken(
                                token_id="ground-truth:page:0:line:body:word:0",
                                text="body",
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    graph = match_documents(source, target, policy=_policy())

    _ = project_match_graph_onto_page(
        page,
        graph,
        document_id="ocr-page",
        page_side=LegacyDocumentSide.TARGET,
    )

    first, second = (line.words[0] for line in page.lines)
    assert first.ground_truth_match_keys["match_target_token_ids"] == (
        "ocr-page:page:7:line:0:word:0",
    )
    assert second.ground_truth_match_keys["match_target_token_ids"] == (
        "ocr-page:page:7:line:1:word:0",
    )


def test_projection_requires_the_original_page_document_before_mutation() -> None:
    """Projection refuses a page whose physical token topology no longer matches."""
    page = _page((("hel", "lo"),))
    target = legacy_page_to_match_document(page, document_id="ocr-page")
    graph = match_documents(_source_document("hello"), target, policy=_policy())
    page.lines[0].words[0].text = "help"

    with pytest.raises(ValueError, match="does not match"):
        project_match_graph_onto_page(
            page,
            graph,
            document_id="ocr-page",
            page_side=LegacyDocumentSide.TARGET,
        )
