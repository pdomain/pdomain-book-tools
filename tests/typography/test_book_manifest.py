from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError

from pdomain_book_tools.typography import (
    BookLabelingManifest,
    BookLabelingPage,
    BookMatchRelationReference,
)
from pdomain_book_tools.typography.review import canonical_json_bytes


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _page(
    *,
    page_index: int,
    page_id: str | None = None,
    labeling_bundle_id: str | None = None,
    relative_path: str | None = None,
    configuration_hash: str | None = None,
    taxonomy_version: str = "typography-v1",
    taxonomy_hash: str | None = None,
    relation_ids: tuple[str, ...] = (),
) -> BookLabelingPage:
    page_name = page_id or f"page-{page_index:03d}"
    return BookLabelingPage(
        page_index=page_index,
        page_id=page_name,
        labeling_bundle_id=labeling_bundle_id or _sha256(f"bundle:{page_name}"),
        materialization_relative_path=relative_path or f"pages/{page_name}.json",
        materialization_sha256=_sha256(f"materialization:{page_name}"),
        configuration_hash=configuration_hash or _sha256(f"configuration:{page_name}"),
        taxonomy_version=taxonomy_version,
        taxonomy_hash=taxonomy_hash or _sha256(f"taxonomy:{taxonomy_version}"),
        relation_ids=relation_ids,
    )


def _manifest(
    *,
    pages: tuple[BookLabelingPage, ...] | None = None,
    relations: tuple[BookMatchRelationReference, ...] = (),
    manifest_id: str | None = None,
) -> BookLabelingManifest:
    return BookLabelingManifest(
        book_id="pgdp:projectID643ab41f2b9e6",
        manifest_id=manifest_id,
        pages=pages or (_page(page_index=0),),
        match_relations=relations,
    )


def _relation(
    *,
    relation_id: str = "join-001-002",
    page_ids: tuple[str, ...] = ("page-000", "page-001"),
    match_graph_id: str | None = None,
    match_graph_relative_path: str = "match-graphs/book-graph.json",
    match_graph_sha256: str | None = None,
) -> BookMatchRelationReference:
    return BookMatchRelationReference(
        relation_id=relation_id,
        page_ids=page_ids,
        match_graph_id=match_graph_id or _sha256("graph-id:book-graph"),
        match_graph_relative_path=match_graph_relative_path,
        match_graph_sha256=match_graph_sha256 or _sha256("graph-bytes:book-graph"),
    )


def test_manifest_has_stable_book_id_and_content_addressed_identity() -> None:
    manifest = _manifest()

    canonical_payload = manifest.model_dump(mode="json")
    canonical_payload.pop("manifest_id")

    assert manifest.book_id == "pgdp:projectID643ab41f2b9e6"
    assert (
        manifest.manifest_id
        == hashlib.sha256(canonical_json_bytes(canonical_payload)).hexdigest()
    )
    assert BookLabelingManifest.from_json_bytes(manifest.to_json_bytes()) == manifest


def test_model_copy_revalidates_and_recomputes_manifest_identity() -> None:
    manifest = _manifest()

    copied = manifest.model_copy(update={"book_id": "gutenberg:123"})

    assert copied.book_id == "gutenberg:123"
    assert copied.manifest_id != manifest.manifest_id


def test_manifest_requires_contiguous_ordered_page_indexes() -> None:
    pages = (_page(page_index=0), _page(page_index=2))

    with pytest.raises(ValidationError, match="contiguous"):
        _manifest(pages=pages)


@pytest.mark.parametrize(
    "relative_path",
    [
        "/pages/001.json",
        "pages\\001.json",
        "C:pages/001.json",
        "./pages/001.json",
        "pages/../001.json",
    ],
)
def test_page_rejects_unsafe_materialization_path(relative_path: str) -> None:
    with pytest.raises(ValidationError, match="safe relative POSIX path"):
        _page(page_index=0, relative_path=relative_path)


def test_manifest_requires_relation_references_to_match_the_affected_pages() -> None:
    relation = _relation()
    pages = (
        _page(page_index=0, relation_ids=(relation.relation_id,)),
        _page(page_index=1),
    )

    with pytest.raises(ValidationError, match="exactly the affected pages"):
        _manifest(pages=pages, relations=(relation,))


def test_manifest_requires_page_relation_ids_to_exist() -> None:
    pages = (_page(page_index=0, relation_ids=("unknown-relation",)),)

    with pytest.raises(ValidationError, match="declared match relations"):
        _manifest(pages=pages)


def test_manifest_allows_one_page_match_relation() -> None:
    relation = _relation(page_ids=("page-000",), relation_id="joined-word:001")
    pages = (_page(page_index=0, relation_ids=(relation.relation_id,)),)

    manifest = _manifest(pages=pages, relations=(relation,))

    assert manifest.match_relations == (relation,)


@pytest.mark.parametrize(
    ("pages", "relations", "error"),
    [
        (
            (_page(page_index=0), _page(page_index=1, page_id="page-000")),
            (),
            "page IDs must be unique",
        ),
        (
            (
                _page(page_index=0),
                _page(page_index=1, labeling_bundle_id=_sha256("bundle:page-000")),
            ),
            (),
            "labeling bundle IDs must be unique",
        ),
        (
            (_page(page_index=0),),
            (
                _relation(relation_id="relation-1"),
                _relation(relation_id="relation-1"),
            ),
            "relation IDs must be unique",
        ),
    ],
)
def test_manifest_rejects_duplicate_identity_values(
    pages: tuple[BookLabelingPage, ...],
    relations: tuple[BookMatchRelationReference, ...],
    error: str,
) -> None:
    with pytest.raises(ValidationError, match=error):
        _manifest(pages=pages, relations=relations)


def test_manifest_allows_page_configuration_hashes_to_differ() -> None:
    taxonomy_hash = _sha256("taxonomy:typography-v1")
    relation = _relation()
    pages = (
        _page(
            page_index=0,
            configuration_hash=_sha256("configuration:one"),
            taxonomy_hash=taxonomy_hash,
            relation_ids=(relation.relation_id,),
        ),
        _page(
            page_index=1,
            configuration_hash=_sha256("configuration:two"),
            taxonomy_hash=taxonomy_hash,
            relation_ids=(relation.relation_id,),
        ),
    )

    manifest = _manifest(pages=pages, relations=(relation,))

    assert manifest.pages[0].configuration_hash != manifest.pages[1].configuration_hash


def test_manifest_requires_one_taxonomy_identity_across_pages() -> None:
    pages = (
        _page(page_index=0, taxonomy_version="typography-v1"),
        _page(page_index=1, taxonomy_version="typography-v2"),
    )

    with pytest.raises(ValidationError, match="taxonomy identity"):
        _manifest(pages=pages)


def test_manifest_and_nested_pages_are_immutable() -> None:
    manifest = _manifest()

    with pytest.raises(ValidationError, match="frozen"):
        manifest.book_id = "gutenberg:123"
    with pytest.raises(ValidationError, match="frozen"):
        manifest.pages[0].page_id = "other-page"


def test_page_model_copy_revalidates_an_unsafe_materialization_path() -> None:
    page = _page(page_index=0)

    with pytest.raises(ValidationError, match="safe relative POSIX path"):
        page.model_copy(update={"materialization_relative_path": "../outside.json"})


def test_relation_model_copy_revalidates_an_empty_page_relation() -> None:
    relation = _relation()

    with pytest.raises(ValidationError, match="at least one page"):
        relation.model_copy(update={"page_ids": ()})


def test_manifest_revalidates_tampered_nested_page_instances_in_constructor() -> None:
    page = _page(page_index=0)
    object.__setattr__(page, "materialization_relative_path", "../outside.json")

    with pytest.raises(ValidationError, match="safe relative POSIX path"):
        _manifest(pages=(page,))


def test_manifest_model_copy_revalidates_tampered_nested_page_instances() -> None:
    manifest = _manifest()
    page = _page(page_index=0)
    object.__setattr__(page, "materialization_relative_path", "../outside.json")

    with pytest.raises(ValidationError, match="safe relative POSIX path"):
        manifest.model_copy(update={"pages": (page,)})


def test_manifest_revalidates_tampered_nested_relation_instances() -> None:
    relation = _relation()
    pages = (
        _page(page_index=0, relation_ids=(relation.relation_id,)),
        _page(page_index=1, relation_ids=(relation.relation_id,)),
    )
    object.__setattr__(relation, "match_graph_relative_path", "../outside.json")

    with pytest.raises(ValidationError, match="safe relative POSIX path"):
        _manifest(pages=pages, relations=(relation,))


@pytest.mark.parametrize(
    ("field_name", "value", "error"),
    [
        ("match_graph_id", "not-a-sha256", "match_graph_id"),
        ("match_graph_sha256", "not-a-sha256", "match_graph_sha256"),
        (
            "match_graph_relative_path",
            "../match-graphs/book-graph.json",
            "safe relative POSIX path",
        ),
    ],
)
def test_relation_rejects_unpinned_or_unsafe_match_graph_metadata(
    field_name: str,
    value: str,
    error: str,
) -> None:
    payload = _relation().model_dump(mode="json")
    payload[field_name] = value

    with pytest.raises(ValidationError, match=error):
        BookMatchRelationReference.model_validate(payload)


def test_relation_pins_the_graph_and_relation_id_for_lazy_resolution() -> None:
    graph_id = _sha256("canonical-match-graph-content")
    graph_bytes = (
        b'{"graph_id":"'
        + graph_id.encode("ascii")
        + b'","relations":[{"relation_id":"join-001-002"}]}'
    )
    relation = _relation(
        match_graph_id=graph_id,
        match_graph_relative_path="match-graphs/003.json",
        match_graph_sha256=hashlib.sha256(graph_bytes).hexdigest(),
    )

    assert relation.match_graph_id == graph_id
    assert relation.match_graph_relative_path == "match-graphs/003.json"
    assert relation.match_graph_sha256 == hashlib.sha256(graph_bytes).hexdigest()
    assert relation.relation_id == "join-001-002"
