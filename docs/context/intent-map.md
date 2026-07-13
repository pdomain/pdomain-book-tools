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

- Benchmark alternative OCR, HTR, and dewarp engines only with reproducible
  historical-document datasets, license review, and comparison against the
  shipped DocTR, Tesseract, textline-disparity, and UVDoc baseline. This
  includes the deferred page-dewarp fork and any renewed DocUNet-style metric
  suite.
- Cluster ground-truth matching fields into `GTMatchMetadata`, or remove Page
  compatibility fields, only after current consumers are inventoried and an
  owner approves the migration. No removal is implied by the current
  architecture record.

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
  whether canonical fixture baselines represent current or desired behavior.
  Evidence: docs/architecture/reorganize-page-pipeline.md and
  docs/architecture/layout-regression-fixture-corpus.md.
- Decide whether glyph-span validation should become automatic and whether
  unknown future annotation kinds need tolerant reading. Evidence:
  docs/architecture/glyph-annotations.md.
- Reconcile the local-upgrade restore recipe, override semantics, and duplicate
  marker contracts before retiring the dev-local spec. Evidence:
  docs/specs/07-dev-local-upgrade-flow.md, Adversarial Review.
- Protect active layout-debug runs with a liveness marker or lock, and test
  cleanup races and suppressed filesystem failures. Evidence:
  docs/architecture/layout-debug-cleanup.md.

## Rejected directions

- Do not maintain a documentation archive tree. Promote durable truth, update
  inbound links, and rely on Git history for retired prose.

## Blocked (waiting on)

None.

## Needs owner decision

- Reconcile the dev-local contract drift before promoting and retiring spec 07.
  The other implemented specs now have architecture replacements.
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
  remove unvalidated visual-similarity voting and reconcile confidence tiers
  and numbering gaps. Evidence:
  docs/specs/2026-05-24-page-order-detection.md, Adversarial Review.
- For scannos, define stable book/occurrence IDs, evidence storage, dual-write
  recovery, collision-safe rule IDs, deduplication, concurrency, and migrations.
  Evidence: docs/specs/2026-05-24-scannos-module.md, Adversarial Review.

## Legacy-unverified sweep

- **Can retire:** every file formerly under docs/archive/; the completed deep
  code/security review; Git history preserves their evidence.
- **Still active:** docs/plans/roadmap.md, docs/process/lint-deviations.md,
  docs/process/writing-style.md, active specs 06a–06c, 09, 10, hyphen n-grams,
  page-order detection, scannos, and the specs index.
- **Still active pending architecture promotion:** implemented spec 07.
- **Superseded:** the original word-reference-lines parent spec, replaced by
  specs 06a, 06b, and 06c.
- **Needs owner review:** none beyond the remaining architecture destinations
  above.
