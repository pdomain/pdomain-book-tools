---
Status: active
Owner: CT
Created: 2026-05-04
Last verified: 2026-11-12
Kind: plan
---

# Roadmap

## Agent Index

- **Kind:** plan
- **Status:** active
- **Last verified:** 2026-11-12
- **Read when:** choosing the next library change, or checking which proposed module should live in another repo.
- **Search terms:** roadmap, remaining work, separate repo, page order, scannos, hyphen n-grams, table structure.

This is the only remaining-work list.

The [issue index](../issues/README.md) points here.

The [continued-work plan](2026-07-21-continued-work-from-deep-review.md) is the sequence for the library items.

Shipped behavior is the [architecture index](../architecture/README.md).

Glyph schema emission and Block tuple restore are fixed. The provenance-ownership sentence is in the [OCR model note](../architecture/ocr-model-and-schema-boundaries.md) (`e2c9a79`, 2026-11-10). Where the `Document` provenance value should go stays an owner decision in the continued-work plan.

These commits from `fix/roadmap-no-owner-items` are on master. Their retirement records are in [decisions](../context/decisions.md).

- OCR ingress states `is_normalized` (`04da801`, 2026-11-10).
- Grid `map_points` and `PipelineResult.dewarp_outcome` (`a094ed7` and `39cdd9a`, 2026-11-10). GPU use of grid `map_points` is unverified.
- The public-API test pins the documented names (`eb4df23`, 2026-11-10).
- Reorganize branch tables cover the B4 priority paths (`eeb9a82`, 2026-11-10). Splitting that module stays optional.
- Unused `opencv-cuda` is removed from the `[gpu]` extra (`b868a2a`, 2026-11-10).
- Floated-caption thresholds use the line-box coordinate width. The same vertical gap splits in pixels and when that geometry is normalized. Tail absorption uses that width too. A mix of coordinate flags raises. One left-edge pixel mark does not switch the width to 1. `tests/ocr/test_reorganize_branch_tables.py`.
- Geometric sidenote detection tags a margin cluster on a normalized page, including unit boxes whose flag is unset. The domain is the page's shared coordinate flag, and a mix raises. The 1-pixel gap floor stays on pixel pages. A word that already has a layout tag other than text keeps that tag. Locked reorganize baselines still pass, and the five strict xfails stay xfail. `tests/layout/test_layout_aware_reorg.py` and `tests/ocr/test_reorganize_page_utils_grouping.py`.
- `encode_bgr_image_as_png` raises `ValueError` when `cv2.imencode` reports failure. `tests/image_processing/cv2_processing/test_encoding.py`.

## Open work in this library

These items change code or docs that already live here.

### Reorganize and geometry

- Five strict-xfail baselines still define those cases in CI. They are reading-order failures, and `plate-rio-harbour-photo` and `plate-service-on-board` want opposite results from nearly the same geometry. [xfail baselines](../issues/2026-07-21-reorganize-known-failing-baselines-xfail.md). Plan theme B3. The unverified attempt stays on `fix/caption-reading-order` (`ed54ecd`, 2026-09-19). Blocker: conflicting baselines.
- The broader scale/four-point helper audit remains unverified. `BoundingBox.center` flag preservation and fail-closed `contains_point` now ship in consumed contracts 0.3.1. See [geometry coordinate domains](../architecture/geometry-coordinate-domains.md). Plan theme C3 retains the residual audit.
- Drop-cap Iteration C, the heading cross-check, is unbuilt. [Iteration C](../issues/2026-07-21-dropcap-iteration-c-heading-crosscheck.md), [gh-005](../issues/2026-05-10-gh-005-drop-cap-heading-cross-check.md), [gh-048](../issues/2026-05-11-gh-048-spec-drop-cap-heading-cross-check.md). Plan theme F1. Blocker: no supporting fixture.
- The sidenote height-ratio default is still `None` until a fixture pass. [gh-003](../issues/2026-05-10-gh-003-sidenote-height-ratio-default.md), [gh-046](../issues/2026-05-11-gh-046-spec-sidenote-height-ratio-default.md). Plan theme F2. Blocker: no supporting fixture.
- Sidenote x-height image projection is unbuilt. [gh-004](../issues/2026-05-10-gh-004-sidenote-projection-x-height.md), [gh-047](../issues/2026-05-11-gh-047-spec-sidenote-projection-x-height.md). Blocker: no supporting fixture.
- Row-block expansion is not sidenote-aware. [gh-006](../issues/2026-05-10-gh-006-sidenote-aware-row-blocks.md), [gh-049](../issues/2026-05-11-gh-049-spec-sidenote-aware-row-blocks.md). Blocker: no supporting fixture.
- Decoration-versus-figure post-classification waits on a fine-tune. [gh-002](../issues/2026-05-10-gh-002-decoration-figure-post-classification.md), [gh-045](../issues/2026-05-11-gh-045-spec-decoration-figure-post-classification.md). Plan theme F3. Training stays in the training repos named under out of scope. Blocker: another repo.

### API, schema, and packaging

- Heavy OCR dependencies are still mandatory. [gh-161](../issues/2026-05-21-gh-161-optional-ocr-dependencies.md). Blocker: explicit deferral.
- Checkpoint loading still lacks size, checksum, and safetensors limits. [gh-165](../issues/2026-05-22-gh-165-checkpoint-hardening.md). The shipped baseline is [DocTR checkpoint loading](../architecture/checkpoint-loading-trust-boundary.md). Blocker: explicit deferral.
- Strict image validation for untrusted inputs is open. [gh-191](../issues/2026-05-22-gh-191-strict-image-validation.md). Blocker: explicit deferral.
- OCR entry points have no progress callback. [progress hook](../issues/2026-08-08-ocr-progress-hook.md). Blocker: explicit deferral.
- A DocTR fork pin does not flag local-dev mode. [gh-007](../issues/2026-05-10-gh-007-dev-local-doctr-fork-pin.md). Deferred until a fork-pin workflow needs it. Blocker: explicit deferral.
- Advisory static scanners are not added. [gh-201](../issues/2026-05-22-gh-201-advisory-static-scanners.md). Keep this as a dev check in this repo. Blocker: explicit deferral.
- Coverage and process ratchet choices in plan theme J have no separate issue file. They stay in the continued-work plan. Blocker: explicit deferral.

### Geometry that stays here after the owner answers the specs

Build word reference lines and per-character boxes here after the decisions in the specs.

Word reference lines and per-character boxes are OCR geometry on word crops.

This package owns the word model and the image algorithms.

The labeler is the caller (`pdomain-ocr-labeler-spa`, CharFixer).

A separate repo would split the word crop away from the word.

- The word-reference-lines API is unbuilt beyond the baseline helpers. [tracker](../issues/2026-07-21-word-reference-lines-api-unbuilt.md). Plan theme H1. Specs [06a](../specs/06a-word-reference-lines-audit.md), [06b](../specs/06b-word-reference-lines-api.md), [06c](../specs/06c-word-reference-lines-testing.md). Blocker: owner decision.
- Character bounding-box extraction is unbuilt. [tracker](../issues/2026-07-21-char-bbox-extraction-unbuilt.md), [spec 09](../specs/09-char-bbox-extraction.md). Plan theme H2. Blocker: owner decision.
- Table `TABLE`/`CELL` fields on the page model stay with this library when they are built. The detector is a different home, in the next section. [tracker](../issues/2026-07-21-table-structure-unbuilt.md), [spec 10](../specs/10-table-structure.md). Plan theme I, slice A. Blocker: owner decision.

The decision pack that blocks H and I is [owner decisions](../issues/2026-07-21-owner-decision-pack-greenfield.md). Plan theme E.

Q-PO-4, the page-order filename source, is already answered in [decisions](../context/decisions.md) (2026-11-07).

## Homes still to choose

These designs were written here as stages of `pdomain-prep-for-pgdp`.

That repo now runs its own stages.

This package has no `page_order`, `scannos`, or `hyphen_ngrams` code.

Start them only after the owner picks the home. Blocker: owner decision.

The recommendation under each item is the one to take unless the owner says otherwise.

### Page-order detector: put it in prep-for-pgdp

The spec detects swapped scans from filenames, OCR page numbers, and a visual hash.

On 2026-11-07 the owner decided two things: `detect_out_of_order_pages` takes an optional list of source filenames in the current page order, and ingestion does not set `Page.name`.

Prep's `page_order` stage depends on `source` and `text_zones`, not on `ocr`.

Prep already has that stage at `core/pipeline/steps/page_order.py`.

The step writes `stages/page_order/output.json`.

Numbering runs live in `stages/page_order/runs.json`, which is the numbering store.

Folio detection is deferred there as issue W3.9.

Recommendation: extend that stage in `pdomain-prep-for-pgdp`. A new repo needs a second caller. The 2026-11-07 review found that ocr-cli and the labeler do not run this stage.

Records, still open until that move is accepted: [tracker](../issues/2026-07-21-page-order-module-unbuilt.md), [spec](../specs/2026-05-24-page-order-detection.md), [gh-208](../issues/2026-05-24-gh-208-spec-page-order-detection.md), [gh-211](../issues/2026-05-24-gh-211-page-order-module-skeleton.md), [gh-212](../issues/2026-05-24-gh-212-page-order-filename-signal.md), [gh-213](../issues/2026-05-24-gh-213-page-order-ocr-signal.md), [gh-214](../issues/2026-05-24-gh-214-page-order-visual-signal.md), [gh-215](../issues/2026-05-24-gh-215-page-order-aggregation.md). Plan theme G1.

### Scanno library: keep it in prep until a second consumer exists

Prep's intent map keeps `wordcheck` as the scanno stage and records a removed `scannocheck` stage as rejected.

System and project scanno tables already run in prep (`scanno_seed.py`, `wordcheck`).

Research is `docs/research/findings-scannos.md` in prep.

"Global hyphen/scanno library management" is deferred in prep.

The book-tools spec is a SQLite rule library, a per-book JSON candidate store, and a promote API. That is a proofreading store.

Recommendation: improve `wordcheck` in prep. Add a shared library repo only when a second program needs the same database. This OCR package should not grow that store.

Records: [tracker](../issues/2026-07-21-scannos-module-unbuilt.md), [spec](../specs/2026-05-24-scannos-module.md), [gh-209](../issues/2026-05-24-gh-209-spec-scannos-module.md), [gh-216](../issues/2026-05-24-gh-216-scanno-dataclasses.md), [gh-217](../issues/2026-05-24-gh-217-sqlite-rule-library.md), [gh-218](../issues/2026-05-24-gh-218-json-candidate-store.md), [gh-219](../issues/2026-05-24-gh-219-scanno-scan-promote-api.md), [gh-220](../issues/2026-05-24-gh-220-scanno-promotion-tests.md). Plan theme G2.

### Hyphen n-gram database: put the client next to hyphen-join

This spec downloads Google Books n-gram hyphen pairs into SQLite and looks them up.

The decision pack sizes that asset at about 50 MB.

Prep already has a `hyphen_join` stage, which rejoins line-end hyphens.

The database is the evidence that stage can consult.

The database is a download, a lock, and a corpus identity.

The database does not use `Page`.

Recommendation: build the client in `pdomain-prep-for-pgdp` beside `hyphen_join`, as a proof inside the one caller. Split a data package after a second caller needs the file.

Records: [tracker](../issues/2026-07-21-hyphen-ngrams-unbuilt.md), [spec](../specs/2026-05-24-hyphen-ngrams-sqlite.md), [gh-210](../issues/2026-05-24-gh-210-spec-hyphen-ngrams-sqlite.md), [gh-221](../issues/2026-05-24-gh-221-hyphen-ngrams-protocol.md), [gh-222](../issues/2026-05-24-gh-222-hyphen-ngrams-sqlite-client.md), [gh-223](../issues/2026-05-24-gh-223-hyphen-ngrams-json-api-client.md), [gh-224](../issues/2026-05-24-gh-224-hyphen-ngrams-download.md), [gh-225](../issues/2026-05-24-gh-225-hyphen-ngrams-extraction.md). Plan theme G3.

### Table-structure detector: a separate model package

Spec 10 adds `TABLE` and `CELL` fields on the page model, then a post-OCR detector (TATR, with geometry derived from deepdoctection).

Slice A, the fields and serialization, belongs with the page model in this library.

The detector is another neural model.

PP-DocLayout already ships here through `transformers`, which is a mandatory dependency.

The `[layout]` extra never shipped.

A TATR detector added in this package would be another model on that same install.

A separate package keeps those weights off this library.

Recommendation: keep slice A here. Put the detector in its own package that writes those fields, so this library can stay installable without TATR weights.

Records are the table tracker and spec 10 linked above. Plan theme I, after slice A.

## Tracker items outside the library

These files live in this repo because cross-repo notes were filed here. They are not features of the OCR library.

- GPU and slow-path CI. The issue describes GitHub workflows removed in `67a714b`. Whether a replacement gate is wanted is undecided. [GPU CI](../issues/2026-07-21-gpu-slow-ci-strategy.md). Plan theme C6. Blocker: owner decision.
- Five workspace repos have had no CI since 2026-07-12. [actions disabled](../issues/2026-08-08-actions-disabled-five-repos.md). Blocker: another repo.
- Seven pdomain repos still point agents at the retired ocr-container-meta tracker. [agent pointers](../issues/2026-11-07-agent-docs-point-at-retired-meta-repo.md). Blocker: another repo.
- Two issue-record sets still describe the same clusters. [duplicate records](../issues/2026-08-07-duplicate-issue-records-after-rebase.md). Blocker: explicit deferral.

## Still out of scope

- Training PP-DocLayout from scratch. Fine-tuning is the planned path, in `pdomain-ocr-training` and `pdomain-ocr-trainer-spa`.
- Replacing RT-DETR with DocLayout-YOLO, DocLayNet-DETR, or DiT.
- Cross-book transfer learning beyond fine-tuning.
- Serialising tables into PGDP table syntax. Layout detection of table regions is shipped. `TABLE`/`CELL` structure is spec 10.
- Stitching a figure across a page boundary.
- Running a different recognition model per region type.
- Restoring operational provenance onto the `Page` JSON tree.
- A second scanno stage beside prep's `wordcheck`.

## Goal

Track unfinished work that belongs in this library, and name the home for work that belongs somewhere else. Point shipped behavior at [the architecture index](../architecture/README.md).

## Architecture

The library map, package boundaries, and invariants are [What this library is](../architecture/README.md).

Open library work extends `Page.reorganize_page`, the layout-regression corpus, geometry correction, checkpoint loading, and the public schema.

Reference lines and character boxes extend `ocr/` and `image_processing/` after the spec decisions.

Page-order, scannos, and hyphen n-grams are absent from the tree. Their proposed homes are above.

## Tech Stack

Open library items use PP-DocLayout and `PageLayout`, OCR boxes, the layout-regression fixtures, and pytest with `-n auto`.

Local-dev detection stays in the repository scripts and Just recipes.

DocTR emits normalized coordinates, and Tesseract emits pixel coordinates.

Image processing is OpenCV on CPU and CuPy under the optional `[gpu]` extra.

`transformers` is mandatory.

Gates are ruff, basedpyright, and `just ci`.

## Global Constraints

- Do not flip the sidenote height default without a fixture pass.
- Keep decoration post-classification waiting until a fine-tune provides a decoration class.
- Do not start page-order, scannos, hyphen n-grams, reference lines, character boxes, or table structure until the owner decision pack is answered.
- For page-order, scannos, hyphen n-grams, and the table detector, the home question above is part of that pack.
- Keep the out-of-scope list out of this repo.
