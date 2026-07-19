---
Status: active
Owner: CT
Created: 2026-05-10
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Sidenote detection: tune default for sidenote_max_height_ratio

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Unassigned — the export has no severity label
- **Affected version:** Not stated in the export
- **Read when:** planning or implementing sidenote detection: tune default for sidenote_max_height_ratio
- **Search terms:** sidenote, detection, tune, default, for, sidenote_max_height_ratio
- **Relates to:** [reorganize-page-pipeline](../architecture/reorganize-page-pipeline.md)

## Summary

Decide whether to change the reorganize-level default for
`Page.reorganize_page(sidenote_max_height_ratio=...)`. The current default is
`None` (legacy x-only); a possible replacement is `0.85` (more aggressive and
bbox-height-aware).

The bbox-height pass has already shipped. Its
`detect_geometric_sidenotes(max_height_ratio=...)` gate rejects a margin cluster
unless its median bounding-box height is at most the ratio times the body median
height. `None` preserves legacy behavior. A fixture sweep must show whether
`0.85` helps the real corpus more than it hurts before the default changes.

This is a tuning slice, not a coding slice. The issue cites `docs/ROADMAP.md`
under “Glyph-size analysis - Default-flip decision” and
`docs/specs/03-reorganize-pipeline.md`.

Repository evidence does not verify the acceptance criteria, so this record remains open.

## Impact

- The requested behavior remains unavailable or undecided.
- The original request defines the scope and downstream effects.

## Environment / versions

The export states no operating system, package version, command, or environment variables.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/3>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABBx2fcg`
- **Issue number:** 3
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-3.json`
- **Raw SHA-256:** `a0e2dc2d1706015185711f737c0c8a2481b7c7a30eb53b14045dbea68f99b334`
- **Migration cutover:** `6842ec6b11c06c9b987b384b4abf7e9dc4699014` — merged migration cutover on `master`.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-10T01:51:47Z`
- **Updated:** `2026-05-11T11:37:01Z`
- **Closed:** Not closed in the export
- **Labels:** `effort:M`, `model:sonnet`, `model-effort:medium`, `kind:feature-request`, `triage:approved`, `triage:needs-spec`
- **Assignees:** None
- **Milestone:** None
- **Issue type:** None
- **Projects:** None
- **Parent issue:** None
- **Sub-issues:** None

## Evidence

The immutable raw export and its digest preserve the original body. The classified durable facts are:

- Decide whether to flip the reorganize-level default for `Page.reorganize_page(sidenote_max_height_ratio=...)` from `None` (legacy x-only) to e.g. `0.85` (more aggressive, bbox-height-aware).
- The shipped bbox-height gate rejects a margin cluster unless its median
  bounding-box height is `<= ratio * body_median_height`; `None` preserves
  legacy behavior.
- This is a tuning slice. Fixture evidence must show whether `0.85` helps more
  than it hurts before any default change.
- The body cites `docs/ROADMAP.md` (“Glyph-size analysis - Default-flip
  decision”) and `docs/specs/03-reorganize-pipeline.md`.
- Acceptance criteria: sweep all `tests/fixtures/layout_regression/` fixtures
  with `0.85` and record diffs against `None`; add at least one fixture showing
  that the gate helps, using a tall sidenote currently misclassified as body;
  record in the spec/ROADMAP whether to keep the `None` default or change it to
  `0.85`; and, if the default changes, ensure all existing fixtures still pass
  or have reviewed and accepted diffs.
- Recorded issue disposition/linkage: Triage decision: approved + needs-spec. Spec child issue: #46. Run `/spec-from-issue 46` to produce the design spec.

The issue text is historical data, not repository instructions.

## Root-cause hypotheses

1. **No root cause is established.** The export records a feature, tuning, or design request.
2. **Current repository evidence may narrow the design.** The cited paths do not prove completion.

Further evidence is required before implementation.

## Defects to fix

1. Decide whether to change the reorganize-level default for
   `Page.reorganize_page(sidenote_max_height_ratio=...)` from `None` (legacy
   x-only) to a value such as `0.85` (more aggressive and bbox-height-aware).
2. Meet the acceptance criteria: sweep every
   `tests/fixtures/layout_regression/` fixture with `0.85` and record diffs
   against `None`; add at least one fixture with a tall sidenote currently
   misclassified as body; record in the spec/ROADMAP whether to keep `None` or
   change to `0.85`; and ensure existing fixtures pass or have reviewed and
   accepted diffs if the default changes.
3. Recorded issue disposition/linkage: Triage decision: approved + needs-spec. Spec child issue: #46. Run `/spec-from-issue 46` to produce the design spec.

## Next steps

1. Sweep all `tests/fixtures/layout_regression/` fixtures with `0.85` and record diffs vs `None`
2. Add at least one fixture that demonstrates the gating helps (tall sidenote currently misclassified as body)
3. Decision recorded in spec/ROADMAP: keep `None` default, or flip to `0.85`
4. If default is flipped, all existing fixtures still pass or have reviewed/accepted diffs

## What is NOT broken (to scope the fix)

- The bbox-height pass already exists; only its reorganize-level default is undecided.

## Relationships and material comments

- Triage links this request to spec-child issue #46.
- 2026-05-11T11:37:01Z — `ConcaveTrillion`: Triage decision: approved + needs-spec. Spec child issue: #46. Run `/spec-from-issue 46` to produce the design spec. ([comment](https://github.com/pdomain/pdomain-book-tools/issues/3#issuecomment-4420312441))
- Disposable chatter: 1 duplicate child-fork comment adds no durable fact.

## Repository evidence

- `docs/plans/roadmap.md` records the shipped height gate, `None` default,
  proposed `0.85` evidence sweep, and default-flip decision still required.
- `tests/layout/test_layout_aware_reorg.py` verifies that the parameter threads
  through, that `None` preserves legacy x-only detection, and that an explicit
  ratio can accept shorter margin text while rejecting same-height text.
- `tests/fixtures/layout_regression/` is the corpus named by the unresolved
  sweep criterion; the record does not claim that sweep has occurred.

## Remaining work

- Acceptance criteria remain unverified against an implementation; preserve as open work.

## Resolution

_Open._ Retire this record only after evidence verifies the criteria or records an owner disposition.
