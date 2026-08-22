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
    relation = BookMatchRelationReference(
        relation_id="join-001-002",
        page_ids=("page-000", "page-001"),
    )
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
                BookMatchRelationReference(
                    relation_id="relation-1", page_ids=("page-000", "page-001")
                ),
                BookMatchRelationReference(
                    relation_id="relation-1", page_ids=("page-000", "page-001")
                ),
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
    relation = BookMatchRelationReference(
        relation_id="join-001-002",
        page_ids=("page-000", "page-001"),
    )
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
