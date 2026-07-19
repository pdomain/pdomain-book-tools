---
Status: active
Owner: CT
Created: 2026-05-11
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Spec: Sidenote detection: image-projection-based x-height refinement

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Unassigned — the export has no severity label
- **Affected version:** Not stated in the export
- **Read when:** planning or implementing spec: sidenote detection: image-projection-based x-height refinement
- **Search terms:** spec, sidenote, detection, image-projection-based, x-height, refinement
- **Relates to:** [Sidenote detection: image-projection-based x-height refinement](2026-05-10-gh-004-sidenote-projection-x-height.md)

## Summary

This open design record tracks specification and decomposition for parent issue
[#4](2026-05-10-gh-004-sidenote-projection-x-height.md). The exported body
leaves the specification path unfilled.

Repository evidence does not verify the acceptance criteria, so this record remains open.

## Impact

- Parent issue #4 requires design work before implementation.
- This child preserves the planned specification and decomposition workflow.

## Environment / versions

The export states no operating system, package version, command, or environment variables.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/47>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABB3sSGg`
- **Issue number:** 47
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-47.json`
- **Raw SHA-256:** `110b143a1ca11042b5fb1e4bf3b22d24e6ce1c9313d204f65a720f19d991c1a3`
- **Migration cutover:** `6842ec6b11c06c9b987b384b4abf7e9dc4699014` — merged migration cutover on `master`.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-11T11:36:16Z`
- **Updated:** `2026-05-11T11:37:04Z`
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

- Tracks parent feature request #4. The duplicate `Tracks: #4` line in the raw
  body adds no separate fact. The body identifies the parent with the historical
  URL `https://github.com/ConcaveTrillion/pd-book-tools/issues/4`.
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

1. Produce the design specification for parent issue #4.
2. Decompose the accepted specification into implementation issues.

## Next steps

1. Draft a governed design specification from parent record
   [#4](2026-05-10-gh-004-sidenote-projection-x-height.md) and current
   repository evidence.
2. Record the accepted specification’s actual repository path in this record.
3. Decompose the accepted design into implementation work through the
   repository’s current planning process.

## What is NOT broken (to scope the fix)

- The export rules out no adjacent behavior beyond its explicit scope.

## Relationships and material comments

- Tracks parent issue [#4](2026-05-10-gh-004-sidenote-projection-x-height.md).
- No comments were present in the export.

## Repository evidence

- `docs/architecture/reorganize-page-pipeline.md`
- `docs/plans/roadmap.md`
- `tests/geometry_correction/test_deskew_projection.py`

## Remaining work

- Acceptance criteria remain unverified against an implementation; preserve as open work.

## Resolution

_Open._ Retire this record only after evidence verifies the criteria or records an owner disposition.
