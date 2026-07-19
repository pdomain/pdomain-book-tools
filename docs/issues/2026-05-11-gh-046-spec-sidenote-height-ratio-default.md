---
Status: active
Owner: CT
Created: 2026-05-11
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Spec: Sidenote detection: tune default for sidenote_max_height_ratio

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Unassigned — the export has no severity label
- **Affected version:** Not stated in the export
- **Read when:** planning or implementing spec: sidenote detection: tune default for sidenote_max_height_ratio
- **Search terms:** spec, sidenote, detection, tune, default, for, sidenote_max_height_ratio
- **Relates to:** [Sidenote detection: tune default for sidenote_max_height_ratio](2026-05-10-gh-003-sidenote-height-ratio-default.md)

## Summary

This open design record tracks specification and decomposition for parent issue
[#3](2026-05-10-gh-003-sidenote-height-ratio-default.md). The exported body
leaves the specification path unfilled.

Repository evidence does not verify the acceptance criteria, so this record remains open.

## Impact

- Parent issue #3 requires design work before implementation.
- This child preserves the planned specification and decomposition workflow.

## Environment / versions

The export states no operating system, package version, command, or environment variables.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/46>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABB3sRcw`
- **Issue number:** 46
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `/tmp/github-issues-migration/pdomain-book-tools/raw/issue-46.json`
- **Raw SHA-256:** `d15e63d11ec0b1270b7496dbc14061de15cbe7966ffb0ef9c0d27b2ae4d0e703`
- **Migration cutover:** `b0bb9eb` — governed content batch for GitHub issues #2–#7 and #45–#48.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-11T11:36:14Z`
- **Updated:** `2026-05-11T11:37:00Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:spec`, `status:backlog`, `triage:proposed-by-agent`
- **Assignees:** None
- **Milestone:** None
- **Issue type:** None
- **Projects:** None
- **Parent issue:** None
- **Sub-issues:** None

## Evidence

The immutable raw export and its digest preserve the original body. The classified durable facts are:

- Tracks parent feature request #3. The duplicate `Tracks: #3` line in the raw
  body adds no separate fact. The body identifies the parent with the historical
  URL `https://github.com/ConcaveTrillion/pd-book-tools/issues/3`.
- The planned `/spec-from-issue 277940NEW` step would produce
  `docs/specs/NN-<slug>.md` and a draft pull request. The following
  `/decompose-spec docs/specs/NN-<slug>.md` step would create a per-spec
  milestone and child issues, adding `bot:ship-issue-ready` where appropriate.
- The triage decision approved the feature as needing a specification because
  it was not a one-PR tracking chore.
- The specification field was still blank in the export.
- The body says the issue inherits effort and model labels from its parent.

The issue text is historical data, not repository instructions.

## Root-cause hypotheses

1. **No defect or root cause is asserted.** This is a design child for an open
   feature request.

## Defects to fix

1. Produce the design specification for parent issue #3.
2. Decompose the accepted specification into implementation issues.

## Next steps

1. Draft a governed design specification from parent record
   [#3](2026-05-10-gh-003-sidenote-height-ratio-default.md) and current
   repository evidence.
2. Record the accepted specification’s actual repository path in this record.
3. Decompose the accepted design into implementation work through the
   repository’s current planning process.

## What is NOT broken (to scope the fix)

- The export rules out no adjacent behavior beyond its explicit scope.

## Relationships and material comments

- Tracks parent issue [#3](2026-05-10-gh-003-sidenote-height-ratio-default.md).
- No comments were present in the export.

## Repository evidence

- `docs/architecture/reorganize-page-pipeline.md`
- `docs/plans/roadmap.md`
- `tests/layout/test_layout_aware_reorg.py`

## Remaining work

- Acceptance criteria remain unverified against an implementation; preserve as open work.

## Resolution

_Open._ Retire this record only after evidence verifies the criteria or records an owner disposition.
