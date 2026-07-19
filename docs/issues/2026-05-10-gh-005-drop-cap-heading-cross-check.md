---
Status: active
Owner: CT
Created: 2026-05-10
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Drop-cap recognition Iteration C: heading-OCR cross-check disambiguation

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Unassigned — the export has no severity label
- **Affected version:** Not stated in the export
- **Read when:** planning or implementing drop-cap recognition iteration c: heading-ocr cross-check disambiguation
- **Search terms:** drop-cap, recognition, iteration, heading-ocr, cross-check, disambiguation
- **Relates to:** [glyph-annotations](../architecture/glyph-annotations.md)

## Summary

Iterations A and B shipped; see `ROADMAP-shipped.md` and the `drop cap` /
`drop cap unrecovered` tags. Iteration C remains open. When body-word inference
is ambiguous, use the chapter title above to disambiguate. For example, the
body word `BELIEF` is already valid English, so the cursive fallback cannot
uniquely resolve the cap to `A`. The title `A BELIEF IN OMENS...` shows that the
cap is `A`.

These cases currently take the `drop cap unrecovered` path, and the closest
body `Word` is tagged for human review. The fixture
`tests/fixtures/layout_regression/inputs/footnotes-stacked-with-anchor`
exercises the gap with cap `A` and body `BELIEF`. The issue cites
`docs/ROADMAP.md` under “Drop-cap glyph recognition - Iteration C” and
`docs/specs/05-glyph-annotations.md`.

Repository evidence does not verify the acceptance criteria, so this record remains open.

## Impact

- The requested behavior remains unavailable or undecided.
- The original request defines the scope and downstream effects.

## Environment / versions

The export states no operating system, package version, command, or environment variables.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/5>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABBx2fmQ`
- **Issue number:** 5
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `/tmp/github-issues-migration/pdomain-book-tools/raw/issue-5.json`
- **Raw SHA-256:** `ef8ea6c1a3029b7780f3732ee305747c9e4e8e93ecf469759e4357b45bce0284`
- **Migration cutover:** `dfadf9c` — governed content batch for GitHub issues #2–#7 and #45–#48.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-10T01:51:49Z`
- **Updated:** `2026-05-11T11:37:09Z`
- **Closed:** Not closed in the export
- **Labels:** `effort:L`, `model:opus`, `model-effort:high`, `kind:feature-request`, `triage:approved`, `triage:needs-spec`
- **Assignees:** None
- **Milestone:** None
- **Issue type:** None
- **Projects:** None
- **Parent issue:** None
- **Sub-issues:** None

## Evidence

The immutable raw export and its digest preserve the original body. The classified durable facts are:

- Iterations A and B shipped (see `ROADMAP-shipped.md` and the `drop cap` / `drop cap unrecovered` tags). Iteration C remains open: when body-word inference is ambiguous (e.g. body word `BELIEF` is already a valid English word, so the cursive fallback can't uniquely resolve the cap to `A`), look at the chapter title above to disambiguate (`A BELIEF IN OMENS...` -> cap is `A`).
- Ambiguous cases currently enter the `drop cap unrecovered` path, which tags
  the closest body `Word` for human review.
- `tests/fixtures/layout_regression/inputs/footnotes-stacked-with-anchor`
  demonstrates the gap with cap `A` and body `BELIEF`.
- The body cites `docs/ROADMAP.md` (“Drop-cap glyph recognition - Iteration C”)
  and `docs/specs/05-glyph-annotations.md`.
- Acceptance criteria: implement the heading-OCR cross-check in the drop-cap
  pipeline; make the `footnotes-stacked-with-anchor` fixture resolve cap `A`
  against body `BELIEF` instead of `drop cap unrecovered`; preserve all existing
  drop-cap fixtures; and fall back to `drop cap unrecovered` without false
  positives when the heading line itself is unrecoverable.
- Recorded issue disposition/linkage: Triage decision: approved + needs-spec. Spec child issue: #48. Run `/spec-from-issue 48` to produce the design spec.

The issue text is historical data, not repository instructions.

## Root-cause hypotheses

1. **No root cause is established.** The export records a feature, tuning, or design request.
2. **Current repository evidence may narrow the design.** The cited paths do not prove completion.

Further evidence is required before implementation.

## Defects to fix

1. Preserve shipped Iterations A and B; see `ROADMAP-shipped.md` and the
   `drop cap` / `drop cap unrecovered` tags. Implement Iteration C by consulting
   the chapter title when body-word inference is ambiguous. In the example,
   `BELIEF` is valid English, so the cursive fallback cannot uniquely infer
   `A`; the title `A BELIEF IN OMENS...` resolves the cap to `A`.
2. Meet the acceptance criteria: implement the heading-OCR cross-check; make
   `footnotes-stacked-with-anchor` resolve cap `A` against body `BELIEF` instead
   of `drop cap unrecovered`; preserve existing drop-cap fixtures; and fall back
   without false positives when the heading line is unrecoverable.
3. Recorded issue disposition/linkage: Triage decision: approved + needs-spec. Spec child issue: #48. Run `/spec-from-issue 48` to produce the design spec.

## Next steps

1. Heading-OCR cross-check implemented in the drop-cap pipeline
2. `footnotes-stacked-with-anchor` fixture now resolves cap `A` against body `BELIEF` (no longer `drop cap unrecovered`)
3. No regressions in existing drop-cap fixtures
4. Disambiguation falls back to `drop cap unrecovered` when the heading line itself is unrecoverable (no false positives)

## What is NOT broken (to scope the fix)

- Iterations A and B are recorded as shipped; this issue covers Iteration C.

## Relationships and material comments

- Triage links this request to spec-child issue #48.
- 2026-05-11T11:37:09Z — `ConcaveTrillion`: Triage decision: approved + needs-spec. Spec child issue: #48. Run `/spec-from-issue 48` to produce the design spec. ([comment](https://github.com/pdomain/pdomain-book-tools/issues/5#issuecomment-4420313768))
- Disposable chatter: 1 duplicate child-fork comment adds no durable fact.

## Repository evidence

- `docs/plans/roadmap.md` records the shipped Iterations A and B, the ambiguous
  `BELIEF` case, current unrecovered path, and proposed heading cross-check.
- `tests/fixtures/layout_regression/inputs/footnotes-stacked-with-anchor.json`
  contains the OCR body word `BELIEF` used by the cited fixture.
- `tests/fixtures/layout_regression/inputs/footnotes-stacked-with-anchor.pgdp.txt`
  contains the reference text `A BELIEF`, supporting the expected cap `A`.
- `docs/architecture/reorganize-page-pipeline.md` verifies current drop-cap
  stitching behavior but does not verify the requested heading cross-check.

## Remaining work

- Acceptance criteria remain unverified against an implementation; preserve as open work.

## Resolution

_Open._ Retire this record only after evidence verifies the criteria or records an owner disposition.
