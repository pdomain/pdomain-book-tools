---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Test the complete scanno promotion flow

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — the cross-store promotion workflow lacks end-to-end verification
- **Affected version:** Draft scannos design dated 2026-05-24
- **Read when:** testing scanno scanning, promotion, concurrency, idempotency, or conflicts
- **Search terms:** scanno integration test, promotion flow, evidence trail, concurrency, issue 220, issue 209
- **Relates to:** [Scannos module spec](../specs/2026-05-24-scannos-module.md), [parent issue #209](2026-05-24-gh-209-spec-scannos-module.md)

## Summary

This open task adds an end-to-end promotion-flow test and supporting unit coverage. The requested flow scans a synthetic page, promotes one candidate, and verifies the global rule and evidence trail, including concurrency, repeat promotion, and conflict warnings.

## Impact

- This test is the integration gate for the model, SQLite, JSON, scanning, and promotion tasks.
- Without negative-path coverage, partial cross-store writes or double-counted evidence could pass unnoticed.

## Environment / versions

The task targets sections 7 and 8 of the draft 2026-05-24 scannos spec. No runtime, package version, or operating system appears in the export.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/220>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDPjBhw`
- **Issue number:** 220
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-220.json`
- **Raw SHA-256:** `7a263b955bfc53abb8451fcf6250e5170112f25f348f7d34c169b5a27a6b4c7f`
- **Migration cutover:** `6842ec6b11c06c9b987b384b4abf7e9dc4699014` — merged migration cutover on `master`.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-24T18:52:59Z`
- **Updated:** `2026-05-26T09:22:38Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:feature`, `effort:M`, `model:sonnet`, `model-effort:medium`, `status:backlog`
- **Assignees:** None
- **Milestone:** `spec: 2026-05-24-scannos-module (#209)` (open milestone #16; no due date; description names the source spec and spec issue #209)
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The body cites spec sections 7 and 8 and states `Tracks: #209`.
- It requires a synthetic-page flow that creates candidates, promotes one, and verifies the rule and evidence trail in the global library.
- It explicitly requires coverage for concurrency, repeat-promotion idempotency, and conflict warnings.
- The source spec lists 13 named unit tests for model round trips, rule persistence and search, WAL mode, candidate persistence, literal and word-final scans, empty rules, promotion creation and idempotency, candidate status, and the default library path.
- The source spec review requires recovery behavior, normalized evidence, collision-safe identity, statistics rules, conflicts, migrations, and concurrent sidecar writes before implementation.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **The integration surface is unimplemented.** No complete promotion path exists to test.
2. **The draft tests do not yet cover all accepted design corrections.** Recovery and concurrent sidecar failure paths need explicit cases.

## Defects to fix

1. Convert each finalized model, storage, scanning, and promotion contract into focused tests.
2. Add cross-store failure injection and recovery assertions.
3. Define observable conflict warnings and concurrency outcomes before asserting them.

## Next steps

1. Complete the revised contracts and implementations from #216 through #219.
2. Add the 13 named source-spec tests and the requested end-to-end flow.
3. Add concurrency, conflict, repeat-promotion, partial-write, and recovery cases.

## What is NOT broken (to scope the fix)

- The issue does not report a failing existing test or shipped behavior regression.
- UI integration and real-book quality evaluation are separate from this synthetic integration test.

## Relationships and material comments

- This task tracks #209 and shares open milestone #16 with #216 through #219.
- The timeline references commit `15f67f06c467967ffc86ea9ce8c91de39190002e` on 2026-05-24 at 18:53:37 UTC. It records planning decomposition, not implementation.
- No comments were present in the export.

## Repository evidence

- The source spec contains the named test plan but says no implementation was found.
- Its residual risks include shared-library leakage and the absence of seed-data or real-book quality evidence.

## Remaining work

- Implementation prerequisites, unit tests, integration tests, and concurrency and recovery coverage remain open. Real-book evaluation remains separate follow-up work under the parent spec.

## Resolution

_Open._ The issue is open and no evidence supports treating the promotion-flow tests as implemented.
