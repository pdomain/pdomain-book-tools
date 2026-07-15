---
Status: active
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-13
Kind: context
---

# Intent Map

## Agent Index

- **Kind:** context
- **Status:** active
- **Read when:** deciding whether proposed work is active, deferred, rejected, blocked, or awaiting an owner decision.
- **Search terms:** intent, deferred, rejected, blocked, legacy sweep.

## Active bets

- Complete the active designs in specs 06a–06c, 09, 10, page-order detection,
  scannos, and hyphen n-grams.
- Continue the residual work in docs/plans/roadmap.md.

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
  `.venv/.pdomain-dev-local` for the Python probe) into one shared contract,
  and decide whether an intentional-clobber escape for `make upgrade-deps` is
  wanted — the old advertised `PDOMAIN_DEV_LOCAL=0` escape never worked and its
  message was removed. Evidence: docs/architecture/local-dev-mode.md, Residual
  intent.
- Protect active layout-debug runs with a liveness marker or lock, and test
  cleanup races and suppressed filesystem failures. Evidence:
  docs/architecture/layout-debug-cleanup.md.
- Decide whether large mixed-order PGDP integration tests are wanted. Three
  drafts (`test_pgdp_large_mixed_order_case1/2/3`) were removed 2026-07-15:
  an indentation bug had nested them inside another test so pytest never
  collected them, and their assertions assumed behaviors the pipeline does
  not implement (space-separated footnote markers, trailing `-*`
  end-of-line cleanup, quote conversion for an elision with attached
  footnote digits such as `'Tis[77][88]`). Git history preserves the
  drafts. Evidence: tests/pgdp/test_pgdp_page.py,
  test_fix_footnotes_no_space_before_marker.

## Rejected directions

- Do not maintain a documentation archive tree. Promote durable truth, update
  inbound links, and rely on Git history for retired prose.

## Blocked (waiting on)

None.

## Needs owner decision

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

## Legacy-unverified sweep

- **Can retire:** every file formerly under docs/archive/; the completed deep
  code/security review; Git history preserves their evidence.
- **Still active:** docs/plans/roadmap.md, docs/process/lint-deviations.md,
  active specs 06a–06c, 09, 10, hyphen n-grams, page-order detection, scannos,
  and the specs index.
- **Still active pending architecture promotion:** implemented spec 07.
- **Superseded:** the original word-reference-lines parent spec, replaced by
  specs 06a, 06b, and 06c.
- **Needs owner review:** none beyond the remaining architecture destinations
  above.
