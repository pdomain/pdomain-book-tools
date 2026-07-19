---
Status: active
Owner: CT
Created: 2026-05-10
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Multi-column body detection: make expand_row_blocks sidenote-aware

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Unassigned — the export has no severity label
- **Affected version:** Not stated in the export
- **Read when:** planning or implementing multi-column body detection: make expand_row_blocks sidenote-aware
- **Search terms:** multi-column, body, detection, make, expand_row_blocks, sidenote-aware
- **Relates to:** [reorganize-page-pipeline](../architecture/reorganize-page-pipeline.md)

## Summary

Make `expand_row_blocks` column detection sidenote-aware once glyph-size data
exists; see the sidenote tuning and projection issues. A sidenote that produces
a narrow third column should not break the geometric column splitter.

The case is rare in the PGDP corpus. This work follows the glyph-size work and
must not start before the sidenote tuning slice ships. The issue cites
`docs/ROADMAP.md` under “Multi-column body detection enhancements” and
`docs/specs/03-reorganize-pipeline.md`.

Repository evidence does not verify the acceptance criteria, so this record remains open.

## Impact

- The requested behavior remains unavailable or undecided.
- The original request defines the scope and downstream effects.

## Environment / versions

The export states no operating system, package version, command, or environment variables.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/6>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABBx2ftA`
- **Issue number:** 6
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-6.json`
- **Raw SHA-256:** `481f1667f06cf6ac2c71f5756f8678fbfba3ed2ab8211f6e9ddaa0199374e419`
- **Migration cutover:** `dfadf9c` — governed content batch for GitHub issues #2–#7 and #45–#48.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-10T01:51:50Z`
- **Updated:** `2026-05-11T11:37:13Z`
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

- Once the glyph-size data exists (see the sidenote tuning and projection issues), `expand_row_blocks` column detection should become sidenote-aware: the geometric column splitter shouldn't break on a sidenote that produces a narrow third column.
- The case is rare in the PGDP corpus and is a follow-up to the glyph-size
  work, not standalone work. It must not be selected before the sidenote tuning
  slice ships.
- The body cites `docs/ROADMAP.md` (“Multi-column body detection enhancements”)
  and `docs/specs/03-reorganize-pipeline.md`.
- Acceptance criteria: make `expand_row_blocks` consume sidenote tags from
  layout/glyph-size data; add a fixture in which a page with body text and a
  sidenote does not split into a spurious third column; retain correct splitting
  for a real two-column page; and prevent regressions across the
  layout-regression fixture suite.
- Recorded issue disposition/linkage: Triage decision: approved + needs-spec. Spec child issue: #49. Run `/spec-from-issue 49` to produce the design spec.

The issue text is historical data, not repository instructions.

## Root-cause hypotheses

1. **No root cause is established.** The export records a feature, tuning, or design request.
2. **Current repository evidence may narrow the design.** The cited paths do not prove completion.

Further evidence is required before implementation.

## Defects to fix

1. Make `expand_row_blocks` column detection sidenote-aware once glyph-size data
   exists; see the sidenote tuning and projection issues. Do not let a sidenote
   that produces a narrow third column break the geometric column splitter.
2. Meet the acceptance criteria: consume sidenote tags from layout/glyph-size
   data; add a fixture in which body text plus a sidenote does not create a
   spurious third column; retain correct splitting for a real two-column page;
   and prevent regressions across the layout-regression fixture suite.
3. Recorded issue disposition/linkage: Triage decision: approved + needs-spec. Spec child issue: #49. Run `/spec-from-issue 49` to produce the design spec.

## Next steps

1. `expand_row_blocks` consumes sidenote tags from layout/glyph-size data
2. Fixture: a page with body + sidenote does NOT split into a spurious third column
3. Fixture: a real two-column page still splits correctly
4. No regressions across the layout-regression fixture suite

## What is NOT broken (to scope the fix)

- Real two-column splitting must continue to work.

## Relationships and material comments

- Prerequisites: [#3 — tune the sidenote height-ratio default](2026-05-10-gh-003-sidenote-height-ratio-default.md)
  and [#4 — image-projection x-height refinement](2026-05-10-gh-004-sidenote-projection-x-height.md).
- Triage links this request to spec-child
  [#49](https://github.com/pdomain/pdomain-book-tools/issues/49). No local #49
  record exists yet.
- 2026-05-11T11:37:13Z — `ConcaveTrillion`: Triage decision: approved + needs-spec. Spec child issue: #49. Run `/spec-from-issue 49` to produce the design spec. ([comment](https://github.com/pdomain/pdomain-book-tools/issues/6#issuecomment-4420314452))
- Disposable chatter: 1 duplicate child-fork comment adds no durable fact.

## Repository evidence

- `docs/plans/roadmap.md` records the sidenote-aware `expand_row_blocks`
  follow-up, the narrow-third-column failure mode, and its dependency on
  glyph-size work.
- `docs/architecture/reorganize-page-pipeline.md` verifies that the current
  pipeline builds and expands row blocks and separately routes sidenotes; it
  does not claim that row-block expansion consumes sidenote tags.

## Remaining work

- Acceptance criteria remain unverified against an implementation; preserve as open work.

## Resolution

_Open._ Retire this record only after evidence verifies the criteria or records an owner disposition.
