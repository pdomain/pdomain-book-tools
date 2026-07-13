---
Status: built
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-13
Kind: architecture
---

# OCR model and schema boundaries

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Read when:** changing Page identity, blob references, unmatched ground
  truth, review metadata, serialization, or public schema emission.
- **Search terms:** Page, page_id, BlobStoreProtocol, GtOrphans,
  ReviewMetadata, schemas emit, Pydantic schema.

## OCR values and lifecycle ownership

`Page`, `Block`, and `Word` are portable OCR content models. `Page.page_id`
provides stable entity identity across copy, scale, equality, and serialization.
Image and thumbnail blob hashes are lazy references; `BlobStoreProtocol` keeps
blob access independent of the operational storage package.

`GtOrphans` preserves unmatched ground-truth lines and words without mixing
them into the block tree. `Page` retains compatibility and content fields used
by current consumers. Operational persistence, event history, application
extensions, and project ordering belong to pdomain-ops records and aggregates,
not this foundation package.

## Review and schema boundary

`ReviewMetadata` is reusable review state on Page, Block, and Word. Ground-truth
matching fields remain separate because review decisions and matching evidence
have different lifecycles.

`pdomain_book_tools.schemas.emit` is the public producer boundary for JSON
schemas. `PUBLIC_MODELS` controls the exported model set, and tests prevent
documented public models from silently disappearing. Consumers should generate
language bindings from these schemas instead of introspecting internal modules.

## Non-goals

This record does not promise removal dates for compatibility fields and does
not define pdomain-ops persistence. A future `GTMatchMetadata` cluster requires
consumer evidence before it changes the current top-level matching fields.

The current JSON reference is
[`page-serialization.md`](page-serialization.md).

## Evidence

- **Code:** `pdomain_book_tools/ocr/page.py`,
  `pdomain_book_tools/ocr/blob_protocol.py`,
  `pdomain_book_tools/ocr/gt_orphans.py`,
  `pdomain_book_tools/ocr/review.py`, `pdomain_book_tools/schemas/emit.py`
- **Tests:** `tests/ocr/test_page.py`, `tests/ocr/test_gt_orphans.py`,
  `tests/ocr/test_review_metadata.py`, `tests/ocr/test_page_pydantic_schema.py`,
  `tests/test_schemas_emit.py`
- **Salvaged sources:**
  `_tbd/ocr-container-docs/archive/plans/2026-05-31-page-split-book-tools.md`,
  `_tbd/ocr-container-docs/archive/plans/2026-05-16-pd-book-tools-review-metadata-and-schemas-emit.md`,
  `_tbd/ocr-container-docs/archive/plans/2026-05-17-pd-book-tools-pydantic-core-schemas.md`
- **Verified:** 2026-07-13 against the current code and focused tests.
