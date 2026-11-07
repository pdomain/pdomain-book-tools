---
Status: built
Owner: CT
Created: 2026-07-13
Last verified: 2026-11-06
Kind: architecture
---

# OCR model and schema boundaries

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Last verified:** 2026-11-06
- **Read when:** changing Page identity, blob references, unmatched ground
  truth, review metadata, serialization, or public schema emission.
- **Search terms:** Page, page_id, BlobStoreProtocol, GtOrphans,
  ReviewMetadata, schemas emit, Pydantic schema.

## OCR values and lifecycle ownership

`Page`, `Block`, and `Word` are portable OCR content models. `Page.page_id`
keeps entity identity stable during copying, scaling, equality checks, and
serialization. Blob hashes are lazy references to images and thumbnails.
`BlobStoreProtocol` keeps blob access independent of the operational storage
package.

`GtOrphans` preserves unmatched ground-truth lines and words without adding
them to the block tree. `Page` retains the compatibility and content fields
that current consumers use. Operational persistence, event history,
application extensions, and project ordering belong to pdomain-ops records and
aggregates. They do not belong to this foundation package.

## Review and schema boundary

`ReviewMetadata` provides reusable review state on Page, Block, and Word.
Ground-truth matching fields remain separate. Review decisions and matching
evidence have different lifecycles.

`pdomain_book_tools.schemas.emit` is the public producer boundary for JSON
schemas. `PUBLIC_MODELS` controls which models it exports. Tests prevent
documented public models from silently disappearing. Consumers should generate
language bindings from these schemas instead of inspecting internal modules.

## Word merge keeps the rest of the line

`Block.merge_adjacent_words` merges two adjacent words and leaves every other word's `ground_truth_text` alone. `Word.merge` concatenates the pair's ground truth onto the survivor. `merge_word_left` and `merge_word_right` call the same method. `split_word_at_fraction` still clears ground truth for the whole line, because a split does not say which half owns the old transcription.

## Non-goals

This record does not promise removal dates for compatibility fields. It also
does not define pdomain-ops persistence. A future `GTMatchMetadata` cluster
requires consumer evidence before it can change the current top-level matching
fields.

The current JSON reference is
[`page-serialization.md`](page-serialization.md).

## Evidence

- **Code:** `pdomain_book_tools/ocr/block.py` (`merge_adjacent_words`, `split_word_at_fraction`), `pdomain_book_tools/ocr/page.py`,
  `pdomain_book_tools/ocr/blob_protocol.py`,
  `pdomain_book_tools/ocr/gt_orphans.py`,
  `pdomain_book_tools/ocr/review.py`, `pdomain_book_tools/schemas/emit.py`
- **Tests:** `tests/ocr/test_block_coverage2.py` (`test_merge_words_right_success`), `tests/ocr/test_page.py`, `tests/ocr/test_gt_orphans.py`,
  `tests/ocr/test_review_metadata.py`, `tests/ocr/test_page_pydantic_schema.py`,
  `tests/test_schemas_emit.py`
- **Salvaged sources:**
  `_tbd/ocr-container-docs/archive/plans/2026-05-31-page-split-book-tools.md`,
  `_tbd/ocr-container-docs/archive/plans/2026-05-16-pd-book-tools-review-metadata-and-schemas-emit.md`,
  `_tbd/ocr-container-docs/archive/plans/2026-05-17-pd-book-tools-pydantic-core-schemas.md`
- **Verified:** 2026-11-06 against `Block.merge_adjacent_words`, which returns after `Word.merge` and does not clear the line. The 2026-07-13 schema facts still hold. `test_merge_words_right_success` checks the merge result, not the sibling ground-truth values.
