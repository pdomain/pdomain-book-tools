---
Status: active
Owner: CT
Created: 2026-07-15
Last verified: 2026-11-06
Kind: process
Level: I1
---

# Issues

## Agent Index

- **Kind:** process
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-11-06
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

## Cross-cut workspace items live here

Items affecting several `pdomain-*` repos are filed in this folder and linked
from the repos they affect. `ConcaveTrillion/ocr-container-meta` is no longer
the home for that work. Repo-local defects stay in their own repo.

## Remaining work

Open work is one line plus the path of its issue or plan. The same list is the [roadmap](../plans/roadmap.md). Shipped behavior is linked from that roadmap to `docs/architecture/`. This file does not keep a second history of closed reports.

- Five strict-xfail figure-noise baselines still define those cases in CI. [xfail baselines](2026-07-21-reorganize-known-failing-baselines-xfail.md). Plan theme B3 in the [continued-work plan](../plans/2026-07-21-continued-work-from-deep-review.md).
- Reorganize branch coverage is still thin on plate noise, column strategy, and floated captions. [branch coverage](2026-07-21-reorganize-branch-unit-coverage.md). Plan theme B4.
- DocTR and Tesseract ingress still omit an explicit `is_normalized` flag. [OCR ingress](2026-07-21-ocr-ingress-is-normalized-explicit.md). Plan theme C1.
- `BoundingBox.center` and `contains_point` still weaken the `is_normalized` rule. [geometry flags](2026-07-21-geometry-primitive-flag-hygiene.md). Plan theme C3.
- Grid `map_points` is unsupported, and `PipelineResult` cannot tell a dewarp skip from an identity no-op. The docs are fixed. [geometry gate](2026-07-21-geometry-correction-gate-and-docs.md). Plan theme C4.
- HEIF and AVIF load and write failures are fixed. The `opencv-cuda` dependency-honesty part is not. [image I/O](2026-07-21-image-io-heif-write-failures.md). Plan theme C5.
- The public API page now matches the README, but `tests/test_public_api.py` does not pin the added names. [public API](2026-07-21-public-api-surface-policy.md). Plan theme D1.
- No doc yet says which model owns provenance; the glyph schema emit and Block tuple restore are fixed. [schema emit](2026-07-21-schema-emit-and-path-hygiene.md). Plan theme D2.
- Greenfield specs are blocked on owner decisions. [decision pack](2026-07-21-owner-decision-pack-greenfield.md). Plan theme E.
- Drop-cap Iteration C, the heading cross-check, is unbuilt. [Iteration C](2026-07-21-dropcap-iteration-c-heading-crosscheck.md), [gh-005](2026-05-10-gh-005-drop-cap-heading-cross-check.md), [gh-048](2026-05-11-gh-048-spec-drop-cap-heading-cross-check.md). Plan theme F1.
- Decoration-versus-figure post-classification waits on a fine-tune. [gh-002](2026-05-10-gh-002-decoration-figure-post-classification.md), [gh-045](2026-05-11-gh-045-spec-decoration-figure-post-classification.md). Plan theme F3.
- The sidenote height-ratio default is still `None` until a fixture pass. [gh-003](2026-05-10-gh-003-sidenote-height-ratio-default.md), [gh-046](2026-05-11-gh-046-spec-sidenote-height-ratio-default.md). Plan theme F2.
- Sidenote x-height image projection is unbuilt. [gh-004](2026-05-10-gh-004-sidenote-projection-x-height.md), [gh-047](2026-05-11-gh-047-spec-sidenote-projection-x-height.md).
- Row-block expansion is not sidenote-aware. [gh-006](2026-05-10-gh-006-sidenote-aware-row-blocks.md), [gh-049](2026-05-11-gh-049-spec-sidenote-aware-row-blocks.md).
- A DocTR fork pin does not flag local-dev mode. [gh-007](2026-05-10-gh-007-dev-local-doctr-fork-pin.md).
- The page-order module is specified and unbuilt. [tracker](2026-07-21-page-order-module-unbuilt.md), [gh-208](2026-05-24-gh-208-spec-page-order-detection.md), [gh-211](2026-05-24-gh-211-page-order-module-skeleton.md), [gh-212](2026-05-24-gh-212-page-order-filename-signal.md), [gh-213](2026-05-24-gh-213-page-order-ocr-signal.md), [gh-214](2026-05-24-gh-214-page-order-visual-signal.md), [gh-215](2026-05-24-gh-215-page-order-aggregation.md). Plan theme G1.
- The scannos module is specified and unbuilt. [tracker](2026-07-21-scannos-module-unbuilt.md), [gh-209](2026-05-24-gh-209-spec-scannos-module.md), [gh-216](2026-05-24-gh-216-scanno-dataclasses.md), [gh-217](2026-05-24-gh-217-sqlite-rule-library.md), [gh-218](2026-05-24-gh-218-json-candidate-store.md), [gh-219](2026-05-24-gh-219-scanno-scan-promote-api.md), [gh-220](2026-05-24-gh-220-scanno-promotion-tests.md). Plan theme G2.
- The hyphen n-grams client is specified and unbuilt. [tracker](2026-07-21-hyphen-ngrams-unbuilt.md), [gh-210](2026-05-24-gh-210-spec-hyphen-ngrams-sqlite.md), [gh-221](2026-05-24-gh-221-hyphen-ngrams-protocol.md), [gh-222](2026-05-24-gh-222-hyphen-ngrams-sqlite-client.md), [gh-223](2026-05-24-gh-223-hyphen-ngrams-json-api-client.md), [gh-224](2026-05-24-gh-224-hyphen-ngrams-download.md), [gh-225](2026-05-24-gh-225-hyphen-ngrams-extraction.md). Plan theme G3.
- The word-reference-lines API is unbuilt beyond the baseline helpers. [tracker](2026-07-21-word-reference-lines-api-unbuilt.md). Plan theme H1.
- Character bounding-box extraction is unbuilt. [tracker](2026-07-21-char-bbox-extraction-unbuilt.md). Plan theme H2.
- Table TABLE/CELL structure is unbuilt. [tracker](2026-07-21-table-structure-unbuilt.md). Plan theme I1.
- Heavy OCR dependencies are still mandatory. [gh-161](2026-05-21-gh-161-optional-ocr-dependencies.md).
- Checkpoint loading still lacks size, checksum, and safetensors limits. [gh-165](2026-05-22-gh-165-checkpoint-hardening.md).
- Strict image validation for untrusted inputs is open. [gh-191](2026-05-22-gh-191-strict-image-validation.md).
- Advisory static scanners are not added. [gh-201](2026-05-22-gh-201-advisory-static-scanners.md).
- OCR entry points have no progress callback. [progress hook](2026-08-08-ocr-progress-hook.md).
- Two issue-record sets still describe the same clusters. [duplicate records](2026-08-07-duplicate-issue-records-after-rebase.md).
- GPU and slow-path CI strategy. The issue describes GitHub workflows removed in `67a714b`. Whether a replacement gate is wanted is undecided. [GPU CI](2026-07-21-gpu-slow-ci-strategy.md). Plan theme C6.
- Five workspace repos have had no CI since 2026-07-12. [actions disabled](2026-08-08-actions-disabled-five-repos.md).

Coverage and process ratchet choices in plan theme J have no separate issue file. They stay in the continued-work plan.
