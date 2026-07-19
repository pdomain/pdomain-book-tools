---
Status: active
Owner: CT
Created: 2026-07-15
Last verified: 2026-07-19
Kind: process
Level: I1
---

# Issues

## Agent Index

- **Kind:** process
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Read when:** filing a bug / defect / investigation report, or looking up an
  open issue's status, evidence, or resolution.
- **Search terms:** issues folder, bug report, defect report, issue template,
  issue lifecycle, kind issue.

## Purpose

`docs/issues/` holds **governed, evidence-bearing issue reports** for bugs,
silent failures, regressions, and investigations. These reports provide a
durable, citable record instead of a throwaway chat summary. Each report is a
docgraph node, so readers can retrieve it and link to it from specs, plans, or
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
  `draft → active → implemented → retired`. Express the *issue's* resolution state
  as a separate **`Resolution:`** line in the Agent Index (`Open` / `Resolved` /
  `Won't fix` / `Duplicate`) and a final `## Resolution` section. Map the governed
  `Status:`:
  - **Open** → `Status: active`.
  - **Resolved / Won't fix / Duplicate** → `Status: retired`, routed through
    `doc-retirer`, with the resolving commit/spec linked in `## Resolution`.
- **Link it (no orphans):** reference every new issue from a governed doc — by
  default an **Open issues** bullet in `docs/context/intent-map.md`, or a Risk in
  `docs/context/current-state.md`. This `README` also links the live issues below,
  which satisfies the no-orphan rule.
- **Stage + reindex:** under `mode = "git"` a new doc is invisible until
  `git add`ed; stage it, then `docgraph reindex` and `docgraph check --strict` the
  same turn (a new `dangling` blocks completion).
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

## Open issues

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
- [#191 — Require strict image validation for untrusted inputs](2026-05-22-gh-191-strict-image-validation.md)
- [#201 — Add advisory static-testing scanners](2026-05-22-gh-201-advisory-static-scanners.md)
- [#208 — Specify page-order detection](2026-05-24-gh-208-spec-page-order-detection.md)
- [#211 — Add the page-order module skeleton and proposal types](2026-05-24-gh-211-page-order-module-skeleton.md)
- [#212 — Add the filename-sequence page-order signal](2026-05-24-gh-212-page-order-filename-signal.md)
- [#213 — Add the OCR page-number page-order signal](2026-05-24-gh-213-page-order-ocr-signal.md)
- [#214 — Add the visual-similarity page-order signal](2026-05-24-gh-214-page-order-visual-signal.md)
- [#215 — Aggregate page-order signals behind the public API](2026-05-24-gh-215-page-order-aggregation.md)
- [#226 — Verify release of predictor batch-size keyword arguments](2026-05-29-gh-226-release-batch-predictor-kwargs.md)

## Resolved issues

- *None yet.*
