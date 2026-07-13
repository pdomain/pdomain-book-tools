---
Status: built
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-13
Kind: architecture
---

# Page serialization

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Read when:** consuming or changing the serialized `Page`, `Block`, `Word`, or `BoundingBox` tree.
- **Search terms:** Page to_dict, Page from_dict, page JSON, recursive OCR tree, page_id, bounding box normalization.

## Current structure

`Page.to_dict()` serializes a recursive OCR tree. A Page contains Blocks; a Block contains either Words or nested Blocks according to `child_type`; Words are leaves. `Block.from_dict()` selects the child deserializer from that value. The model permits more than one nesting shape, so consumers traverse recursively instead of assuming fixed depths.

`PageLayout` and `LayoutRegion` are separate detector-output types. They are inputs to layout-aware reorganization and are not embedded in the Page serialization tree.

## Page fields

`Page.to_dict()` always emits `type`, `page_id`, `width`, `height`, `page_index`, `bounding_box`, and `items`. `type` is `"Page"`; `page_id` is the UUID string for the Page entity; `bounding_box` is a serialized box or `null`; and `items` is a list of serialized Blocks.

The serializer emits `page_labels`, `name`, `review`, `image_blob_hash`, and `thumbnail_blob_hash` only when they are not `None`. It emits `gt_orphans` only when the value exists and is not empty. It does not emit `ocr_provenance`, `image_path`, `rotation_applied`, or `source`.

`Page.from_dict()` reconstructs nested Blocks and optional metadata. It restores a serialized UUID or creates a new UUID when older input has no `page_id`; a non-string, non-UUID `page_id` raises `TypeError`. JSON list entries used for orphan-line tuples are restored to tuples.

## Child serialization

`Block.to_dict()` records its child type, block category, label collections, baseline, bounding box, serialized children, sort override, ground-truth matching data, additional attributes, and optional review metadata. `Block.from_dict()` defaults a missing child type to `WORDS` for compatibility and recursively loads the declared child kind.

`Word.to_dict()` records text, bounding box, OCR confidence, labels and components, baseline, ground-truth matching fields, and optional review and glyph annotations. `Word.from_dict()` requires text and bounding-box data and supplies compatibility defaults for optional collections.

`BoundingBox.to_dict()` records `top_left`, `bottom_right`, and `is_normalized`. Each corner also carries `is_normalized`. `BoundingBox.from_dict()` accepts older data without the box-level flag and passes the available normalization state through `Point` and `BoundingBox` construction. Normalized and pixel coordinates remain distinct; serialization does not coerce between them.

## Vocabulary ownership

Allowed block-role, block-position, line-role, and line-position labels live on `Block`. Word-component labels live in `ocr/label_normalization.py`. Layout-region vocabulary lives in `layout/types.py`. Those code definitions are authoritative; adding a vocabulary value requires updating its documentation drift test.

## Evidence

- `pdomain_book_tools/ocr/page.py`: `Page` fields, `Page.to_dict`, and `Page.from_dict`.
- `pdomain_book_tools/ocr/block.py`: `Block.to_dict`, `Block.from_dict`, `BlockChildType`, and `BlockCategory`.
- `pdomain_book_tools/ocr/word.py`: `Word.to_dict` and `Word.from_dict`.
- `pdomain_book_tools/geometry/bounding_box.py`: `BoundingBox.to_dict` and `BoundingBox.from_dict`.
- `pdomain_book_tools/ocr/label_normalization.py`: word-component vocabulary.
- `pdomain_book_tools/layout/types.py`: `PageLayout`, `LayoutRegion`, and `RegionType`.
- `tests/test_page_model_doc.py`: vocabulary coverage, current minimal Page fields, explicit absence of removed Page fields, and canonical-API mentions.
- `tests/ocr/test_page_pydantic_schema.py`: Page schema behavior.
- `tests/test_page_behavior_pin.py`: pinned Page behavior.
- `tests/ocr/test_glyph_annotations.py`: optional Word glyph-annotation serialization and legacy loading.

## Residual intent

A versioned, complete Page JSON Schema and a downstream compatibility gate remain deferred in `docs/context/intent-map.md`. This architecture document records the current Python serialization behavior; it does not promise cross-version or cross-repository compatibility beyond the cited implementation and tests.
