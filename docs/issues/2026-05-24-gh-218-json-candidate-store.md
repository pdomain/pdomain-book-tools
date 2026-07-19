---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Add the per-book JSON candidate store

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — per-book scanno review state lacks durable storage
- **Affected version:** Draft scannos design dated 2026-05-24
- **Read when:** implementing candidate sidecars, persistence, or status filtering
- **Search terms:** CandidateStore, JSON sidecar, scanno candidates, per-book, issue 218, issue 209
- **Relates to:** [Scannos module spec](../specs/2026-05-24-scannos-module.md), [parent issue #209](2026-05-24-gh-209-spec-scannos-module.md)

## Summary

This open task implements a per-book JSON `CandidateStore` with load, save, and status-filtered listing. The source spec selects a human-readable UTF-8 array sidecar for V1, but concurrent writes and the array-versus-directory choice remain unresolved.

## Impact

- Book-specific candidates need portable state that travels with each book's output.
- Unsafe full-file writes could lose review decisions when multiple processes update one sidecar.

## Environment / versions

The task targets the section 6 per-book-sidecar decision in the draft 2026-05-24 scannos spec. No runtime, package version, or operating system appears in the export.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/218>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDPjBMA`
- **Issue number:** 218
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-218.json`
- **Raw SHA-256:** `62b925d19580ce5923a0492d0f4f36b3b1613d42d0ec9a422d22c38f64484246`
- **Migration cutover:** Pending — record the immutable merged cutover commit before deleting the GitHub issue.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-24T18:52:56Z`
- **Updated:** `2026-05-24T18:52:57Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:feature`, `effort:M`, `model:sonnet`, `model-effort:medium`, `status:backlog`
- **Assignees:** None
- **Milestone:** `spec: 2026-05-24-scannos-module (#209)` (open milestone #16; no due date; description names the source spec and spec issue #209)
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The body cites the spec's section 6 per-book-sidecar decision and states `Tracks: #209`.
- It requests load, save, and status-filtered candidate listing with unit tests.
- The source spec chooses `<book-id>-scanno-candidates.json`, UTF-8, indentation, full read on open, and an explicit full-file `save()`.
- The source spec expects candidate counts in the low hundreds, making full-file V1 persistence acceptable in its draft.
- Unresolved question Q-SC-1 still weighs one JSON array against one file per candidate, and the review requires concurrent-write behavior before implementation.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **Per-book candidate persistence does not exist.** Review state has no shared sidecar contract.
2. **The draft write model lacks concurrency protection.** Full-file replacement can race without locking or conflict detection.

## Defects to fix

1. Decide the V1 array-file versus per-candidate-file layout.
2. Define atomic writes, concurrent-writer behavior, recovery, and schema evolution.
3. Align candidate identity and evidence fields with the parent spec revision.

## Next steps

1. Resolve Q-SC-1 and the accepted concurrency finding.
2. Implement load, add, get, list, update, and explicit save behavior.
3. Test UTF-8 round trips, human-readable output, status filters, recovery, and write conflicts.

## What is NOT broken (to scope the fix)

- This task does not implement the global SQLite library, scanning, promotion, or UI.
- The export provides no evidence of a regression in an existing sidecar format.

## Relationships and material comments

- This task tracks #209 and shares open milestone #16 with #216, #217, #219, and #220.
- No commit references or comments were present in the export.

## Repository evidence

- The source spec selects JSON because book state should remain portable and git-friendly.
- Its review says no implementation was found and identifies concurrent sidecar writes as unresolved.

## Remaining work

- Layout and concurrency decisions, implementation, persistence behavior, and tests remain open.

## Resolution

_Open._ The issue is open and no evidence supports treating `CandidateStore` as implemented.
