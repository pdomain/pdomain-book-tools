---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Add scanno scanning and promotion APIs

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — scanno rules cannot produce or promote review candidates
- **Affected version:** Draft scannos design dated 2026-05-24
- **Read when:** implementing `scan_page()` matching or candidate-to-rule promotion
- **Search terms:** scan_page, promote, literal, word-final, idempotent, issue 219, issue 209
- **Relates to:** [Scannos module spec](../specs/2026-05-24-scannos-module.md), [parent issue #209](2026-05-24-gh-209-spec-scannos-module.md)

## Summary

This open task implements literal and word-final page scanning plus idempotent candidate promotion. Promotion spans SQLite rule state and a JSON candidate sidecar, so the draft's atomic-transaction wording requires explicit compensating or recovery behavior.

## Impact

- Without scanning, global rules cannot create per-book review candidates.
- Without safe promotion, accepted local evidence cannot update the global library reliably.
- A partial dual write could leave a promoted rule and an unpromoted candidate, or the reverse.

## Environment / versions

The task targets section 6.3 of the draft 2026-05-24 scannos spec. No runtime, package version, or operating system appears in the export.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/219>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDPjBXg`
- **Issue number:** 219
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-219.json`
- **Raw SHA-256:** `8964bc624705c837474efadcb1c8f185d1709ea738ba11659033d006730c7bd5`
- **Migration cutover:** Pending — record the immutable merged cutover commit before deleting the GitHub issue.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-24T18:52:58Z`
- **Updated:** `2026-05-24T18:52:58Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:feature`, `effort:M`, `model:sonnet`, `model-effort:medium`, `status:backlog`
- **Assignees:** None
- **Milestone:** `spec: 2026-05-24-scannos-module (#209)` (open milestone #16; no due date; description names the source spec and spec issue #209)
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The body cites spec section 6.3 and states `Tracks: #209`.
- It requests `scan_page(page, rules)` for literal and word-final matching that produces `ScannoCandidate` objects.
- It requests an atomic, idempotent `promote(candidate)` operation that moves a candidate into a global rule, with unit tests for both APIs.
- The source spec's fuller API passes a `RuleLibrary` to `scan_page()` and passes the candidate, `CandidateStore`, `RuleLibrary`, contributor, and optional auto flag to `promote()`.
- The source spec defines literal matching as a lowercased exact `Word.text` match and word-final matching as a suffix test, but its review says the example is incorrect.
- The review requires normalized matching, deduplication, statistics rules, conflict handling, and compensating or recovery behavior for the SQLite/JSON dual write.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **Scanning and promotion behavior has not been implemented.** The storage tasks alone cannot deliver the workflow.
2. **The atomicity claim exceeds the chosen stores' shared guarantees.** A SQLite transaction cannot atomically commit a separate JSON file.

## Defects to fix

1. Define normalization, case handling, word-final semantics, deduplication, and candidate identity.
2. Specify idempotency keys and exact hit, book, contributor, and conflict updates.
3. Define rollback, compensation, or restart-safe recovery for partial promotion.

## Next steps

1. Finalize the model and storage contracts in tasks #216 through #218.
2. Revise matching and promotion semantics against the accepted review findings.
3. Implement both APIs with negative-path and recovery tests.

## What is NOT broken (to scope the fix)

- V1 excludes regex scanning and document-wide `scan_document()` aggregation.
- This task does not implement the downstream FastAPI routes or React UI.

## Relationships and material comments

- This task tracks #209 and shares open milestone #16 with #216 through #218 and #220.
- No commit references or comments were present in the export.

## Repository evidence

- The source spec defines the draft API and implementation sequence but preserves material corrections for revision.
- Its review says no implementation was found as of 2026-07-13.

## Remaining work

- Contract revision, matching, promotion recovery, implementation, and tests remain open.

## Resolution

_Open._ The issue is open and no evidence supports treating scanning or promotion as implemented.
