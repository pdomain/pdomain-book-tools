---
Status: active
Owner: CT
Created: 2026-05-04
Last verified: 2026-11-10
Kind: plan
---

# Roadmap

## Agent Index

- **Kind:** plan
- **Status:** active
- **Last verified:** 2026-11-10
- **Read when:** choosing the next library change, or checking whether a behavior already shipped.
- **Search terms:** roadmap, remaining work, sidenote, drop cap, page order, scannos, hyphen n-grams.

Shipped behavior is an architecture doc. Open work is one line plus its issue or plan.

## Shipped

- [PGDP-aware matcher](../architecture/pgdp-aware-matcher.md)
- [Reorganize page pipeline](../architecture/reorganize-page-pipeline.md)
- [Layout regression fixtures](../architecture/layout-regression-fixture-corpus.md)
- [Geometry correction](../architecture/geometry-correction.md)
- [OCR page orientation](../architecture/ocr-page-orientation.md)
- [PP-DocLayout trust boundary](../architecture/pp-doclayout-trust-boundary.md)
- [Local development mode](../architecture/local-dev-mode.md)
- [DocTR checkpoint loading](../architecture/checkpoint-loading-trust-boundary.md)
- [OCR model and schema boundaries](../architecture/ocr-model-and-schema-boundaries.md)
- [Page serialization](../architecture/page-serialization.md)
- [Glyph annotations](../architecture/glyph-annotations.md)
- [Tesseract integration](../architecture/tesseract-integration.md)
- [Type checking](../architecture/type-checking.md)
- [Layout debug cleanup](../architecture/layout-debug-cleanup.md)

## Remaining work

The [continued-work plan](2026-07-21-continued-work-from-deep-review.md) stays active. Its opening note names the slices the code already proves. The lines below are what is still unfinished.

- Five strict-xfail figure-noise baselines still define those cases in CI. [xfail baselines](../issues/2026-07-21-reorganize-known-failing-baselines-xfail.md). Plan theme B3.
- `BoundingBox.center` and `contains_point` still weaken the `is_normalized` rule. The fix belongs in `pdomain-book-contracts`. [geometry flags](../issues/2026-07-21-geometry-primitive-flag-hygiene.md). Plan theme C3.
- HEIF and AVIF load and write failures are fixed, and `opencv-cuda` is removed. `encode_bgr_image_as_png` still discards the `cv2.imencode` success flag. [image I/O](../issues/2026-07-21-image-io-heif-write-failures.md). Plan theme C5.
- The floated-caption split never fires on pages with normalized coordinates. [floated caption](../issues/2026-11-10-floated-caption-thresholds-ignore-normalized-coords.md).
- Greenfield specs are blocked on owner decisions. [decision pack](../issues/2026-07-21-owner-decision-pack-greenfield.md). Plan theme E.
- Drop-cap Iteration C, the heading cross-check, is unbuilt. [Iteration C](../issues/2026-07-21-dropcap-iteration-c-heading-crosscheck.md), [gh-005](../issues/2026-05-10-gh-005-drop-cap-heading-cross-check.md), [gh-048](../issues/2026-05-11-gh-048-spec-drop-cap-heading-cross-check.md). Plan theme F1.
- Decoration-versus-figure post-classification waits on a fine-tune. [gh-002](../issues/2026-05-10-gh-002-decoration-figure-post-classification.md), [gh-045](../issues/2026-05-11-gh-045-spec-decoration-figure-post-classification.md). Plan theme F3.
- The sidenote height-ratio default is still `None` until a fixture pass. [gh-003](../issues/2026-05-10-gh-003-sidenote-height-ratio-default.md), [gh-046](../issues/2026-05-11-gh-046-spec-sidenote-height-ratio-default.md). Plan theme F2.
- Sidenote x-height image projection is unbuilt. [gh-004](../issues/2026-05-10-gh-004-sidenote-projection-x-height.md), [gh-047](../issues/2026-05-11-gh-047-spec-sidenote-projection-x-height.md).
- Row-block expansion is not sidenote-aware. [gh-006](../issues/2026-05-10-gh-006-sidenote-aware-row-blocks.md), [gh-049](../issues/2026-05-11-gh-049-spec-sidenote-aware-row-blocks.md).
- A DocTR fork pin does not flag local-dev mode. [gh-007](../issues/2026-05-10-gh-007-dev-local-doctr-fork-pin.md). Deferred until a fork-pin workflow needs it.
- The page-order module is specified and unbuilt. [tracker](../issues/2026-07-21-page-order-module-unbuilt.md), [gh-208](../issues/2026-05-24-gh-208-spec-page-order-detection.md), [gh-211](../issues/2026-05-24-gh-211-page-order-module-skeleton.md), [gh-212](../issues/2026-05-24-gh-212-page-order-filename-signal.md), [gh-213](../issues/2026-05-24-gh-213-page-order-ocr-signal.md), [gh-214](../issues/2026-05-24-gh-214-page-order-visual-signal.md), [gh-215](../issues/2026-05-24-gh-215-page-order-aggregation.md). Plan theme G1.
- The scannos module is specified and unbuilt. [tracker](../issues/2026-07-21-scannos-module-unbuilt.md), [gh-209](../issues/2026-05-24-gh-209-spec-scannos-module.md), [gh-216](../issues/2026-05-24-gh-216-scanno-dataclasses.md), [gh-217](../issues/2026-05-24-gh-217-sqlite-rule-library.md), [gh-218](../issues/2026-05-24-gh-218-json-candidate-store.md), [gh-219](../issues/2026-05-24-gh-219-scanno-scan-promote-api.md), [gh-220](../issues/2026-05-24-gh-220-scanno-promotion-tests.md). Plan theme G2.
- The hyphen n-grams client is specified and unbuilt. [tracker](../issues/2026-07-21-hyphen-ngrams-unbuilt.md), [gh-210](../issues/2026-05-24-gh-210-spec-hyphen-ngrams-sqlite.md), [gh-221](../issues/2026-05-24-gh-221-hyphen-ngrams-protocol.md), [gh-222](../issues/2026-05-24-gh-222-hyphen-ngrams-sqlite-client.md), [gh-223](../issues/2026-05-24-gh-223-hyphen-ngrams-json-api-client.md), [gh-224](../issues/2026-05-24-gh-224-hyphen-ngrams-download.md), [gh-225](../issues/2026-05-24-gh-225-hyphen-ngrams-extraction.md). Plan theme G3.
- The word-reference-lines API is unbuilt beyond the baseline helpers. [tracker](../issues/2026-07-21-word-reference-lines-api-unbuilt.md). Plan theme H1. Specs [06a](../specs/06a-word-reference-lines-audit.md), [06b](../specs/06b-word-reference-lines-api.md), [06c](../specs/06c-word-reference-lines-testing.md).
- Character bounding-box extraction is unbuilt. [tracker](../issues/2026-07-21-char-bbox-extraction-unbuilt.md), [spec 09](../specs/09-char-bbox-extraction.md). Plan theme H2.
- Table TABLE/CELL structure is unbuilt. [tracker](../issues/2026-07-21-table-structure-unbuilt.md), [spec 10](../specs/10-table-structure.md). Plan theme I1.
- Heavy OCR dependencies are still mandatory. [gh-161](../issues/2026-05-21-gh-161-optional-ocr-dependencies.md).
- Checkpoint loading still lacks size, checksum, and safetensors limits. [gh-165](../issues/2026-05-22-gh-165-checkpoint-hardening.md). The shipped baseline is the checkpoint architecture doc above.
- Strict image validation for untrusted inputs is open. [gh-191](../issues/2026-05-22-gh-191-strict-image-validation.md).
- Advisory static scanners are not added. [gh-201](../issues/2026-05-22-gh-201-advisory-static-scanners.md).
- OCR entry points have no progress callback. [progress hook](../issues/2026-08-08-ocr-progress-hook.md).
- Two issue-record sets still describe the same clusters. [duplicate records](../issues/2026-08-07-duplicate-issue-records-after-rebase.md).
- GPU and slow-path CI strategy. The issue describes GitHub workflows removed in `67a714b`. Whether a replacement gate is wanted is undecided. [GPU CI](../issues/2026-07-21-gpu-slow-ci-strategy.md). Plan theme C6.
- Five workspace repos have had no CI since 2026-07-12. [actions disabled](../issues/2026-08-08-actions-disabled-five-repos.md).
- Seven pdomain repos still point agents at the retired ocr-container-meta tracker. [agent pointers](../issues/2026-11-07-agent-docs-point-at-retired-meta-repo.md).

## Still out of scope

- Training PP-DocLayout from scratch. Fine-tuning is the planned path, and it lives outside this repo.
- Replacing RT-DETR with DocLayout-YOLO, DocLayNet-DETR, or DiT.
- Cross-book transfer learning beyond fine-tuning.
- Serialising tables into PGDP table syntax. Layout detection of table regions is shipped. TABLE/CELL structure is the open spec 10 item above.
- Stitching a figure across a page boundary.
- Running a different recognition model per region type.

## Goal

Track unfinished work that belongs in this library. Point shipped behavior at `docs/architecture/` instead of retelling it here.

## Architecture

Remaining work extends `Page.reorganize_page`, the layout-regression corpus, geometry correction, and the unbuilt page-order, scannos, hyphen n-gram, reference-line, character-box, and table-structure modules. Shipped contracts stay in the architecture docs linked above.

## Tech Stack

The open items use PP-DocLayout and `PageLayout`, OCR boxes, the layout-regression fixtures, and the existing pytest suite. Local-dev detection stays in the repository scripts and Make targets.

## Global Constraints

Do not flip the sidenote height default without a fixture pass. Keep decoration post-classification waiting until a fine-tune provides a decoration class. Do not start the page-order, scannos, hyphen n-gram, reference-line, character-box, or table-structure implementations until the owner decision pack is answered. Keep the out-of-scope list above out of this repo.
