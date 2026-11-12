---
Status: built
Owner: CT
Created: 2026-11-12
Last verified: 2026-11-12
Kind: architecture
---

# What this library is

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Last verified:** 2026-11-12
- **Read when:** orienting on the package, finding the doc for a shipped behavior, or deciding whether a new module belongs here.
- **Search terms:** architecture index, package map, OCR foundation, book-contracts boundary, prep-for-pgdp boundary.

`pdomain-book-tools` is the imaging and OCR foundation the other `pdomain-*` projects import. It turns a page image into a `Page` tree, corrects geometry, and detects layout regions.

Shared types that need no imaging stack live in `pdomain-book-contracts`.

A PGDP project's stage runner lives in `pdomain-prep-for-pgdp`.

This page is the map of what already ships.

Open work is the [roadmap](../plans/roadmap.md).

## Where the code sits

The installable package is `pdomain_book_tools/`.

| Package | Role |
| --- | --- |
| `ocr/` | `Page`, `Block`, `Word`, DocTR and Tesseract ingress, `reorganize_page` |
| `geometry/` | `Point` and `BoundingBox` |
| `geometry_correction/` | Deskew, dewarp, curvature gate, page-side detection |
| `image_processing/` | The same image algorithms in `cv2_processing/` and `cupy_processing/` |
| `layout/` | Layout detectors and region geometry. `RegionType` is re-exported from contracts |
| `schemas/` | JSON Schema emission for the public models |
| `hf/` | Hugging Face Hub model resolution |
| `matching/`, `typography/`, `pgdp/` | Re-export shims. The implementations live in `pdomain-book-contracts` |
| `utility/` | Timing helpers and Jupyter widgets |

`pdomain-book-contracts` holds the pure-Python types: geometry, layout region types, matching, typography records, glyph annotations, and PGDP round parsers. This library depends on it.

Image operations, OCR engines, and layout models stay here.

The contracts repo states that split in `docs/architecture/00-overview.md`. On this machine that file is `/mnt/work/projects/pdomain/pdomain-book-contracts/docs/architecture/00-overview.md`.

There is no `page_order`, `scannos`, or `hyphen_ngrams` package in this tree.

## How a page moves through the library

**The OCR tree.** `ocr/` holds `Page`, `Block`, and `Word`, and the heuristic pipeline that groups words into rows, classifies bands, and assigns reading order.

The pipeline has to keep the DocTR and Tesseract coordinate domains apart. DocTR emits boxes in normalized `[0, 1]` coordinates. Tesseract emits pixel coordinates.

**Geometry.** `Point`, `BoundingBox`, and `geometry_correction` carry the `is_normalized` flag the OCR tree relies on.

Ingress is supposed to set the flag.

Merge, split, and union raise when two boxes disagree on it.

**Image processing, twice.** `cv2_processing/` and `cupy_processing/` implement the same algorithms. A change to one is unfinished until the other agrees.

The `[gpu]` extra is opt-in.

CPU tests always run.

GPU tests skip when CUDA is absent.

**Layout and wire format.** `layout/` registers detectors, including PP-DocLayout (`pp-doclayout-plus-l` via `transformers`).

`schemas.emit` publishes the public model schemas.

`transformers` is a mandatory dependency.

The old `[layout]` extra never shipped.

The layout regression corpus is `tests/fixtures/layout_regression/`. It is the check that reorganization still produces the expected text.

## Invariants

These are current contracts.

The continued-work plan repeats them as rules for future edits.

- Merge, split, and union fail when `is_normalized` disagrees. They do not coerce.
- `Point`, `BoundingBox`, and the OCR model types keep that flag's meaning.
- A CPU image-processing change includes the GPU twin.
- A public surface change reaches every downstream `pdomain-*` repo.
- Operational persistence, event history, and project ordering belong to pdomain-ops records. They are not fields on `Page`. The model note is [OCR model and schema boundaries](ocr-model-and-schema-boundaries.md).
- The ownership sentence for OCR provenance is in [OCR model and schema boundaries](ocr-model-and-schema-boundaries.md). Where the `Document` value should go is still an owner decision.

## Shipped contracts

Each link is the current description of that behavior.

- [PGDP-aware matcher](pgdp-aware-matcher.md)
- [Reorganize page pipeline](reorganize-page-pipeline.md)
- [Layout regression fixtures](layout-regression-fixture-corpus.md)
- [Geometry correction](geometry-correction.md). Callers also have [the usage note](../usage/geometry-correction.md).
- [OCR page orientation](ocr-page-orientation.md)
- [PP-DocLayout trust boundary](pp-doclayout-trust-boundary.md)
- [Local development mode](local-dev-mode.md)
- [DocTR checkpoint loading](checkpoint-loading-trust-boundary.md)
- [OCR model and schema boundaries](ocr-model-and-schema-boundaries.md)
- [Page serialization](page-serialization.md)
- [Glyph annotations](glyph-annotations.md)
- [Tesseract integration](tesseract-integration.md)
- [Type checking](type-checking.md)
- [Layout debug cleanup](layout-debug-cleanup.md)

How to call the public surface: [Public API](../usage/public-api.md).

## What stays outside this package

A PGDP project pipeline, including the `page_order` numbering stage, `wordcheck` (the scanno tables), and `hyphen_join`, lives in `pdomain-prep-for-pgdp`.

Layout training lives in `pdomain-ocr-training` and `pdomain-ocr-trainer-spa`.

Serializing a detected table into PGDP table syntax is outside this library.

Layout detection of a table region is shipped.

Row, column, and cell structure is still a spec.

The [roadmap](../plans/roadmap.md) lists proposed homes for the page-order detector, a shared scanno library, the hyphen n-gram database, and a table-structure detector.

Those homes are an owner question.

They are not extra packages in this tree.
