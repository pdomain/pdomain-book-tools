---
Status: active
Owner: CT
Created: 2026-05-11
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Specify sidenote-aware row-block expansion

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Unassigned — the export has no severity label
- **Affected version:** Not stated in the export
- **Read when:** designing or decomposing sidenote-aware `expand_row_blocks` work
- **Search terms:** expand_row_blocks, sidenote, multi-column, spec, issue 49
- **Relates to:** [Sidenote-aware row-block expansion](2026-05-10-gh-006-sidenote-aware-row-blocks.md)

## Summary

This open record tracks design and decomposition for parent issue #6. The
historical workflow expected a design specification and child implementation
issues, but the exported specification field remains blank.

The design must prevent a sidenote from creating a spurious third column. Real
two-column splitting and the layout-regression fixture suite must keep passing.

## Impact

- Parent issue #6 needs design work before implementation.
- The work must follow the glyph-size and sidenote-tuning slice.

## Environment / versions

The export states no operating system, package version, command, or environment variables.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/49>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABB3sToQ`
- **Issue number:** 49
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-49.json`
- **Raw SHA-256:** `a48c62febdaae3cc0bd9be097eb3feb46223c1f09d05b60a7a489ce9a2fcf885`
- **Migration cutover:** `6842ec6b11c06c9b987b384b4abf7e9dc4699014` — merged migration cutover on `master`.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-11T11:36:19Z`
- **Updated:** `2026-05-11T11:37:12Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:spec`, `status:backlog`, `triage:proposed-by-agent`
- **Assignees:** None
- **Milestone:** None
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The body says `Tracks: #6` twice; the repeated line adds no separate fact.
- The historical parent URL was `https://github.com/ConcaveTrillion/pd-book-tools/issues/6`.
- The planned `/spec-from-issue 277940NEW` step would create
  `docs/specs/NN-<slug>.md` and a draft pull request.
- The planned `/decompose-spec docs/specs/NN-<slug>.md` step would create a
  per-spec milestone and child issues. Suitable children would receive
  `bot:ship-issue-ready`.
- The 2026-05-11 backlog triage approved a specification because the feature
  needed design work and was not a one-pull-request tracking chore.
- The body says this issue inherits effort and model labels from its parent.
- The specification field was still blank in the export.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **No defect cause is asserted.** This is an open design child for a feature request.

## Defects to fix

1. Produce the design specification for parent issue #6.
2. Decompose the accepted design into implementation work.

## Next steps

1. Draft a governed specification from parent record [#6](2026-05-10-gh-006-sidenote-aware-row-blocks.md) and current repository evidence.
2. Record the accepted specification path here.
3. Decompose the accepted design through the repository's current planning process.

## What is NOT broken (to scope the fix)

- The export rules out no adjacent behavior.

## Relationships and material comments

- Tracks parent issue [#6](2026-05-10-gh-006-sidenote-aware-row-blocks.md).
- No comments were present in the export.

## Repository evidence

- `docs/issues/2026-05-10-gh-006-sidenote-aware-row-blocks.md` preserves the
  parent request, dependencies, and acceptance criteria.
- `docs/plans/roadmap.md` supports the claim that `expand_row_blocks` should
  become sidenote-aware after glyph-size data exists.
- No repository evidence supplied the missing specification path.

## Remaining work

- Design, acceptance verification, and decomposition remain unresolved.

## Resolution

_Open._ Retire this record only after evidence verifies the criteria or records an owner disposition.
