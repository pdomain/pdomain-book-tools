---
Status: active
Owner: CT
Created: 2026-07-15
Last verified: 2026-07-21
Kind: process
Level: I1
---

# Issues

## Agent Index

- **Kind:** process
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Read when:** filing a bug / defect / investigation report, or looking up an
  open issue's status, evidence, or resolution.
- **Search terms:** issues folder, bug report, defect report, issue template,
  issue lifecycle, kind issue.

## Purpose

`docs/issues/` holds **governed, evidence-bearing issue reports** for bugs,
silent failures, regressions, and investigations. These reports provide a
durable, citable record instead of a throwaway chat summary. Each report is a
docgraph node. Readers can retrieve it and link to it from specs, plans, or
context documents. The repository carries the record instead of per-machine
harness memory.

## Convention

- **Location:** `docs/issues/`
- **Filename:** `YYYY-MM-DD-short-slug.md` (creation date + a terse kebab slug).
- **Metadata:** YAML frontmatter **and** a matching `## Agent Index` block. Keep
  frontmatter `Status:` and Agent Index `Status:` identical — a mismatch trips a
  `field_conflict` (→ `status-reconciler`).
  - `Kind: issue`
  - `Level:` informational scope — `I1` repo-wide, `I2` narrow/local.
  - `Status:` governed lifecycle, **not** the issue's open/closed state (see below).
- **Issue state vs governed status:** the docgraph lifecycle is
  `draft → active → implemented → retired`. Express the *issue's* resolution
  state separately. Add a **`Resolution:`** line to the Agent Index (`Open` /
  `Resolved` / `Won't fix` / `Duplicate`) and a final `## Resolution` section.
  Map the governed `Status:`:
  - **Open** → `Status: active`.
  - **Resolved / Won't fix / Duplicate** → route through `doc-retirer`, which
    **deletes** the report. Promote any specific a reader still needs into the
    architecture or process doc that owns it, repoint inbound references at the
    resolving commit, drop the pointer below, and append a tombstone to
    `docs/context/decisions.md`. Git history keeps the report, so no resolved
    file stays in the tree and there is no resolved index to maintain.
- **Link it (no orphans):** reference every new issue from a governed doc — by
  default an **Open issues** bullet in `docs/context/intent-map.md`, or a Risk in
  `docs/context/current-state.md`. This `README` also links the live issues below,
  which satisfies the no-orphan rule.
- **Stage + reindex:** under `mode = "git"`, a new doc is invisible until it is
  `git add`ed. In the same turn, stage it, run `docgraph reindex`, and run
  `docgraph check --strict`. A new `dangling` blocks completion.
- **Template:** copy `TEMPLATE.md` in this folder. It is index-excluded (a
  top-of-file `<!-- docgraph: ignore -->` marker), so **do not markdown-link to
  it** from a governed doc — the link would dangle. Refer to it by path / inline
  code.

## Recommended structure

Use this section order:

1. Summary
2. Impact
3. Environment/versions
4. Evidence, including reproduction and diagnosis with commands and output
5. Ranked root-cause hypotheses
6. Defects to fix
7. Recommended next steps
8. What is NOT broken, which scopes the fix
9. Resolution

Lead with the **smallest decisive evidence**, separate **observation** from
**hypothesis**, and always include a **What is NOT broken** section.

## Two record sets live here

This folder carries records from two independent efforts, both still live:

- **Active issue files** — the 43 records migrated out of the GitHub tracker in
  July 2026, named `YYYY-MM-DD-gh-NNN-*.md`. They keep their original issue
  number as provenance.
- **Open issues** — the reports filed by the 2026-07-21 deep code review, named
  `2026-07-21-*.md` and mapped to themes in the continued-work plan, plus any
  report filed since under the same dated convention.

Twenty-four of the 43 migrated records describe the same six work clusters as
four open deep-review reports and two deferred plan items, so the two counts
below overlap. Reconciling them is tracked in
[duplicate issue records after rebase](./2026-08-07-duplicate-issue-records-after-rebase.md).
Until that lands, check both lists before filing a new report.

## Active issue files

This index covers all 43 active governed Git records: 33 migrated from open
sources and 10 retained for residual work or owner decisions. Their GitHub
source copies were deleted after migration. These files remain active until
their own work is resolved.

- [#43 — Verify the external disposition of the style-review subprocess failure](2026-05-11-gh-043-style-review-detect-subprocess-failure.md)
- [#54 — Decide whether monthly grooming remains part of the workspace workflow](2026-05-17-gh-054-monthly-grooming.md)
- [#65 — Verify the external decompose-spec flag implementation](2026-05-17-gh-065-decompose-spec-flags.md)
- [#77 — Verify the parent workspace-agent definition claim](2026-05-17-gh-077-workspace-agent-definitions.md)
- [#94 — Verify the full-power pd-ui agent definition](2026-05-17-gh-094-pd-ui-agent-definition.md)
- [#95 — Verify the read-only pd-ui-docs agent definition](2026-05-17-gh-095-pd-ui-docs-agent-definition.md)
- [#96 — Verify the full-power pd-ocr-ops agent definition](2026-05-17-gh-096-pd-ocr-ops-agent-definition.md)
- [#97 — Verify the read-only pd-ocr-ops-docs agent definition](2026-05-17-gh-097-pd-ocr-ops-docs-agent-definition.md)
- [#98 — Verify the workspace agent routing table](2026-05-17-gh-098-workspace-routing-table.md)
- [#2 — Decoration-vs-figure post-classification heuristic](2026-05-10-gh-002-decoration-figure-post-classification.md)
- [#3 — Tune the sidenote height-ratio default](2026-05-10-gh-003-sidenote-height-ratio-default.md)
- [#4 — Refine sidenote x-height with image projection](2026-05-10-gh-004-sidenote-projection-x-height.md)
- [#5 — Disambiguate drop caps with a heading cross-check](2026-05-10-gh-005-drop-cap-heading-cross-check.md)
- [#6 — Make row-block expansion sidenote-aware](2026-05-10-gh-006-sidenote-aware-row-blocks.md)
- [#7 — Detect a DocTR fork pin in dev-local mode](2026-05-10-gh-007-dev-local-doctr-fork-pin.md)
- [#45 — Specify decoration-vs-figure post-classification](2026-05-11-gh-045-spec-decoration-figure-post-classification.md)
- [#46 — Specify the sidenote height-ratio default](2026-05-11-gh-046-spec-sidenote-height-ratio-default.md)
- [#47 — Specify image-projection x-height refinement](2026-05-11-gh-047-spec-sidenote-projection-x-height.md)
- [#48 — Specify the drop-cap heading cross-check](2026-05-11-gh-048-spec-drop-cap-heading-cross-check.md)
- [#49 — Specify sidenote-aware row-block expansion](2026-05-11-gh-049-spec-sidenote-aware-row-blocks.md)
- [#161 — Make heavy OCR dependencies optional](2026-05-21-gh-161-optional-ocr-dependencies.md)
- [#165 — Complete checkpoint-loading hardening](2026-05-22-gh-165-checkpoint-hardening.md)
- [#191 — Require strict image validation for untrusted inputs](2026-05-22-gh-191-strict-image-validation.md)
- [#201 — Add advisory static-testing scanners](2026-05-22-gh-201-advisory-static-scanners.md)
- [#208 — Specify page-order detection](2026-05-24-gh-208-spec-page-order-detection.md)
- [#209 — Specify the scannos rule and candidate module](2026-05-24-gh-209-spec-scannos-module.md)
- [#210 — Specify the hyphen n-grams SQLite migration](2026-05-24-gh-210-spec-hyphen-ngrams-sqlite.md)
- [#211 — Add the page-order module skeleton and proposal types](2026-05-24-gh-211-page-order-module-skeleton.md)
- [#212 — Add the filename-sequence page-order signal](2026-05-24-gh-212-page-order-filename-signal.md)
- [#213 — Add the OCR page-number page-order signal](2026-05-24-gh-213-page-order-ocr-signal.md)
- [#214 — Add the visual-similarity page-order signal](2026-05-24-gh-214-page-order-visual-signal.md)
- [#215 — Aggregate page-order signals behind the public API](2026-05-24-gh-215-page-order-aggregation.md)
- [#216 — Define the scanno rule and candidate dataclasses](2026-05-24-gh-216-scanno-dataclasses.md)
- [#217 — Add the SQLite scanno rule library](2026-05-24-gh-217-sqlite-rule-library.md)
- [#218 — Add the per-book JSON candidate store](2026-05-24-gh-218-json-candidate-store.md)
- [#219 — Add scanno scanning and promotion APIs](2026-05-24-gh-219-scanno-scan-promote-api.md)
- [#220 — Test the complete scanno promotion flow](2026-05-24-gh-220-scanno-promotion-tests.md)
- [#221 — Define the hyphen n-grams protocol and result type](2026-05-24-gh-221-hyphen-ngrams-protocol.md)
- [#222 — Add the SQLite hyphen n-grams client](2026-05-24-gh-222-hyphen-ngrams-sqlite-client.md)
- [#223 — Add the JSON API fallback client](2026-05-24-gh-223-hyphen-ngrams-json-api-client.md)
- [#224 — Download and cache the hyphen n-grams database](2026-05-24-gh-224-hyphen-ngrams-download.md)
- [#225 — Build the hyphen n-grams extraction pipeline](2026-05-24-gh-225-hyphen-ngrams-extraction.md)
- [#226 — Verify release of predictor batch-size keyword arguments](2026-05-29-gh-226-release-batch-predictor-kwargs.md)

## Open issues

- **[High]** [five strict-xfail figure-noise baselines leave product gaps green in CI](./2026-07-21-reorganize-known-failing-baselines-xfail.md) — plan `B3 / S5`
- **[Medium]** [docs/issues/ carries two record sets that describe the same work twice](./2026-08-07-duplicate-issue-records-after-rebase.md) — reconcile the two lists above
- **[Medium]** [reorganize_page_utils branch coverage thin on high-risk heuristics](./2026-07-21-reorganize-branch-unit-coverage.md) — plan `B4`
- **[Medium]** [DocTR and Tesseract OCR ingress omit explicit is_normalized flags](./2026-07-21-ocr-ingress-is-normalized-explicit.md) — plan `C1 / S6`
- **[Medium]** [drop-cap path forces is_normalized=True and unit-space thresholds](./2026-07-21-dropcap-coordinate-domain.md) — plan `C2 / S6`
- **[Medium]** [BoundingBox.center and contains_point weaken is_normalized discipline](./2026-07-21-geometry-primitive-flag-hygiene.md) — plan `C3 / S7`
- **[Medium]** [geometry_correction dual gate and docs disagree; grid map_points unsupported](./2026-07-21-geometry-correction-gate-and-docs.md) — plan `C4 / S7`
- **[Medium]** [HEIF/AVIF identify then fail on cv2 load; writes ignore imwrite success](./2026-07-21-image-io-heif-write-failures.md) — plan `C5 / S8`
- **[Medium]** [default CI never runs GPU or @slow model paths](./2026-07-21-gpu-slow-ci-strategy.md) — plan `C6 / S8b`
- **[Medium]** [PP-DocLayout registry rejects security kwargs; captions ignore above side](./2026-07-21-layout-registry-knobs-caption-above.md) — plan `C7 / S8b`
- **[Medium]** [public-api.md is narrower than taught Document/hf/geometry_correction surface](./2026-07-21-public-api-surface-policy.md) — plan `D1 / S9`
- **[Medium]** [schema emit incomplete for glyphs; public-api path drift; Block GT tuples](./2026-07-21-schema-emit-and-path-hygiene.md) — plan `D2 / S9`
- **[Medium]** [greenfield specs blocked on unresolved owner decisions](./2026-07-21-owner-decision-pack-greenfield.md) — plan `E / S11`
- **[Medium]** [drop-cap Iteration C missing heading cross-check for ambiguous lexicon](./2026-07-21-dropcap-iteration-c-heading-crosscheck.md) — plan `F1 / S10`
- **[Medium]** [page-order module specified but not implemented](./2026-07-21-page-order-module-unbuilt.md) — plan `G1 (after E)`
- **[Medium]** [scannos module specified but not implemented](./2026-07-21-scannos-module-unbuilt.md) — plan `G2 (after E)`
- **[Medium]** [hyphen n-grams client and SQLite asset not implemented](./2026-07-21-hyphen-ngrams-unbuilt.md) — plan `G3 (after E)`
- **[Medium]** [word reference lines API (06b/c) not implemented beyond baseline helpers](./2026-07-21-word-reference-lines-api-unbuilt.md) — plan `H1 (after E)`
- **[Medium]** [char-bbox extraction (spec 09) not implemented](./2026-07-21-char-bbox-extraction-unbuilt.md) — plan `H2 (after E)`
- **[Medium]** [table structure TABLE/CELL grid layer (spec 10) not implemented](./2026-07-21-table-structure-unbuilt.md) — plan `I1 (after E)`
- **[Medium]** [OCR entry points report no progress, so callers can only show a spinner](./2026-08-08-ocr-progress-hook.md) — requested by `pdomain-ocr-labeler-spa`

## Deferred plan items (no dedicated issue file)

- **F2** sidenote height default — after B1 evidence only (plan Theme F2).
- **F3** decorations postclassify — until fine-tune policy allows (plan Theme F3).
- **Theme J** coverage/process hygiene — ongoing after A/B; ratchet choices in Theme E.

## Where resolved work is recorded

- [default mode not baselined](./2026-07-21-reorganize-default-mode-not-baselined.md) — plan `B2 / S5` (2026-07-21)
- [layout regression harness without layout=](./2026-07-21-layout-regression-harness-without-layout.md) — plan `B1 / S4` (2026-07-21)
- [GPU textline _ensure_foreground polarity diverges from CPU](./2026-07-21-gpu-textline-foreground-polarity.md) — plan `A4 / S3` (2026-07-21)
- [soft word-recover path never runs in default CI](./2026-07-21-reorganize-soft-recover-untested.md) — plan `A3 / S2` (2026-07-21)
- [early-return skips word reconciliation](./2026-07-21-reorganize-early-return-skips-reconcile.md) — plan `A2 / S2` (2026-07-21)
- [README OCR orientation examples](./2026-07-21-readme-ocr-orientation-examples.md) — plan `A5 / S0` (2026-07-21)
- [roadmap / intent-map backlog sync](./2026-07-21-roadmap-intent-map-backlog-sync.md) — plan `D3 / S0` (2026-07-21)
- [reorganize band classify coordinate-domain thresholds](./2026-07-21-reorganize-coord-domain-thresholds.md) — plan `A1 / S1` (2026-07-21)

These reports are resolved but still in the tree. Under the current rule each
one is deleted once anything durable is promoted and a tombstone is written to
`docs/context/decisions.md`; git history keeps the report.
