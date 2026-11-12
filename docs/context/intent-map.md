---
Status: active
Owner: CT
Created: 2026-07-13
Last verified: 2026-11-12
Kind: context
---

# Intent Map

## Agent Index

- **Kind:** context
- **Status:** active
- **Last verified:** 2026-11-12
- **Read when:** deciding whether proposed work is active, deferred, rejected, blocked, or awaiting an owner decision.
- **Search terms:** intent, deferred, rejected, blocked, legacy sweep.

## Active bets

- Finish the library lines in the [roadmap](../plans/roadmap.md). That file is the only remaining-work list. The [issue index](../issues/README.md) points at it. Shipped behavior is the [architecture index](../architecture/README.md).
- Keep the [continued-work plan](../plans/2026-07-21-continued-work-from-deep-review.md) until its unfinished themes are done. Shipped slices are named at the top of that plan. Theme G waits on the home question in the roadmap.
- Build reference lines and character boxes in this library only after the owner decisions below are answered. Page-order, scannos, hyphen n-grams, and the table detector also wait on the home question in the roadmap. The specs are:
  [specs 06a](../specs/06a-word-reference-lines-audit.md),
  [06b](../specs/06b-word-reference-lines-api.md),
  [06c](../specs/06c-word-reference-lines-testing.md),
  [09](../specs/09-char-bbox-extraction.md),
  [10](../specs/10-table-structure.md),
  [page-order detection](../specs/2026-05-24-page-order-detection.md),
  [scannos](../specs/2026-05-24-scannos-module.md), and
  [hyphen n-grams](../specs/2026-05-24-hyphen-ngrams-sqlite.md).

## Deferred work

- Benchmark alternative OCR, HTR, and dewarp engines only when the work uses
  reproducible historical-document datasets. The work must include license
  review and comparison against the shipped DocTR, Tesseract,
  textline-disparity, and UVDoc baseline. This condition applies to the
  deferred page-dewarp fork and any renewed DocUNet-style metric suite.
- Cluster ground-truth matching fields into `GTMatchMetadata`, or remove Page
  compatibility fields, only after two conditions are met. Current consumers
  must be inventoried, and an owner must approve the migration. The current
  architecture record does not imply removal.

- Add a dirty flag for Page.items and Block.items sorting only if profiling
  shows repeated reads are material. Preserve the mutation-site coverage in
  tests/ocr/test_items_resort_l23.py. Evidence: retired review item L-23 in Git
  history for docs/archive/research/older/bugs-low.md.
- Decide whether a non-canonical DocTR Git URL should activate local-dev mode
  when a concrete fork-pin workflow needs it. Evidence: docs/plans/roadmap.md.
- Add a versioned, complete Page JSON schema and downstream compatibility gate
  before retiring the page-model spec. Evidence:
  docs/architecture/page-serialization.md.
- Decide whether rotation probes need a durable audit/event surface, then back
  threshold and timing claims with a reproducible benchmark. Evidence:
  docs/architecture/ocr-page-orientation.md.
- Close or explicitly accept the five strict-xfail layout baselines, and define
  whether canonical fixture baselines represent current behavior or desired
  behavior.
  Evidence: docs/architecture/reorganize-page-pipeline.md and
  docs/architecture/layout-regression-fixture-corpus.md.
- Decide whether glyph-span validation should become automatic and whether
  unknown future annotation kinds need tolerant reading. Evidence:
  docs/architecture/glyph-annotations.md.
- Consolidate the duplicate local-dev marker contracts
  (`.venv/.pdomain-local-mode` for the shell scripts,
  `.venv/.pdomain-dev-local` for the Python probe) into one shared contract.
  Decide whether an intentional-clobber escape for `make upgrade-deps` is
  wanted. The old advertised `PDOMAIN_DEV_LOCAL=0` escape never worked, and its
  message was removed. Evidence: docs/architecture/local-dev-mode.md, Residual
  intent.
- Protect active layout-debug runs with a liveness marker or lock, and test
  cleanup races and suppressed filesystem failures. Evidence:
  docs/architecture/layout-debug-cleanup.md.
- Decide whether large mixed-order PGDP integration tests are wanted. Three
  drafts (`test_pgdp_large_mixed_order_case1/2/3`) were removed 2026-07-15.
  An indentation bug had nested them inside another test, so pytest never
  collected them. Their assertions assumed behaviors the pipeline does not
  implement (space-separated footnote markers, trailing `-*`
  end-of-line cleanup, quote conversion for an elision with attached
  footnote digits such as `'Tis[77][88]`). Git history preserves the
  drafts. Evidence: tests/pgdp/test_pgdp_page.py,
  test_fix_footnotes_no_space_before_marker.

## Rejected directions

- Do not maintain a documentation archive tree. Promote durable truth, update
  inbound links, and rely on Git history for retired prose.

## Blocked (waiting on)

None.

## Open issues

The open list is the [roadmap](../plans/roadmap.md). The [issue index](../issues/README.md) repeats it. The [continued-work plan](../plans/2026-07-21-continued-work-from-deep-review.md) holds the unfinished theme sequence.

## Needs owner decision

- Choose a home for the page-order detector, the scanno store, the hyphen n-gram client, and the table-structure detector. The roadmap recommends prep-for-pgdp for the first three (scannos stays with `wordcheck` until a second consumer exists) and a separate model package for the table detector, with `TABLE`/`CELL` fields staying on the page model here. Evidence: [roadmap](../plans/roadmap.md) section "Homes still to choose"; prep-for-pgdp intent map (wordcheck is the scanno stage; `scannocheck` is rejected); [page-order filename decision](decisions.md) on 2026-11-07.
- Resolve the word-reference-lines coordinate, persistence, heuristic, mapping,
  font-fixture, and property-test contracts before implementation. Evidence:
  docs/specs/06b-word-reference-lines-api.md and
  docs/specs/06c-word-reference-lines-testing.md, Adversarial Review.
- For character extraction, resolve mask polarity, placeholder/component
  invariants, confidence, coverage, crop dimensions, morphology, and Unicode
  failure behavior. Evidence: docs/specs/09-char-bbox-extraction.md,
  Adversarial Review.
- For table structure, define word fallback, line grouping, rendering, detector
  mapping, table-region replacement, and sparse-span validation. Evidence:
  docs/specs/10-table-structure.md, Adversarial Review.
- For hyphen n-grams, choose a two-pass/indexed builder and specify corpus
  identity, normalization, secure atomic download, locking, and read-only
  SQLite behavior. Evidence:
  docs/specs/2026-05-24-hyphen-ngrams-sqlite.md, Adversarial Review.
- Redesign page-order evidence around current Page fields and normalized roles;
  remove unvalidated visual-similarity voting. Reconcile confidence tiers and
  numbering gaps. Evidence:
  docs/specs/2026-05-24-page-order-detection.md, Adversarial Review.
- For scannos, define stable book/occurrence IDs, evidence storage, dual-write
  recovery, collision-safe rule IDs, deduplication, concurrency, and migrations.
  Evidence: docs/specs/2026-05-24-scannos-module.md, Adversarial Review.
- Resolve migrated owner-decision records through the
  [issue index](../issues/README.md). A closed GitHub source does not close the local file.
- GPU and slow-path CI. [gpu-slow-ci-strategy](../issues/2026-07-21-gpu-slow-ci-strategy.md) describes GitHub workflows removed in `67a714b`. This pass did not prove that a replacement gate was chosen or built.
- Five workspace repos and CI. [actions-disabled](../issues/2026-08-08-actions-disabled-five-repos.md) is cross-repo. This pass did not prove those repositories now run CI.

## Legacy-unverified sweep

- **Can retire:** every file formerly under docs/archive/; the completed deep
  code/security review; Git history preserves their evidence.
- **Still active:** docs/architecture/README.md, docs/plans/roadmap.md,
  docs/plans/2026-07-21-continued-work-from-deep-review.md,
  docs/process/lint-deviations.md, active specs 06a–06c, 09, 10, hyphen
  n-grams, page-order detection, scannos, and the specs index. The PGDP-aware
  matcher spec and plan were promoted on 2026-11-06.
- **Superseded:** the original word-reference-lines parent spec, replaced by
  specs 06a, 06b, and 06c.
- **Needs owner review:** none beyond the remaining architecture destinations
  above.
