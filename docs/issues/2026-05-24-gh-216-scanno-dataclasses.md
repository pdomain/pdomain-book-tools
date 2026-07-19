---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Define the scanno rule and candidate dataclasses

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — every scanno storage and API task depends on stable model types
- **Affected version:** Draft scannos design dated 2026-05-24
- **Read when:** defining `ScannoRule`, `ScannoCandidate`, or their serialization contract
- **Search terms:** ScannoRule, ScannoCandidate, dataclass, round trip, issue 216, issue 209
- **Relates to:** [Scannos module spec](../specs/2026-05-24-scannos-module.md), [parent issue #209](2026-05-24-gh-209-spec-scannos-module.md)

## Summary

This open task defines `ScannoRule` and `ScannoCandidate` dataclasses with field-level tests. The source spec also requires stable `to_dict` and `from_dict` round trips, but its accepted review findings require identity and evidence changes before the model is safe to implement.

## Impact

- `RuleLibrary`, `CandidateStore`, `scan_page()`, and `promote()` depend on these types.
- A premature schema would create incompatible SQLite, JSON, and downstream UI contracts.

## Environment / versions

The task targets sections 6.1 and 6.2 of the draft 2026-05-24 scannos spec. No runtime, package version, or operating system appears in the export.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/216>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDPjA5A`
- **Issue number:** 216
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-216.json`
- **Raw SHA-256:** `3053765037b7caf6eaa47e55d0e63a7bca10322ce6f1c839255acfb4310af9f8`
- **Migration cutover:** `6842ec6b11c06c9b987b384b4abf7e9dc4699014` — merged migration cutover on `master`.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-24T18:52:54Z`
- **Updated:** `2026-05-24T18:52:54Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:feature`, `effort:M`, `model:sonnet`, `model-effort:medium`, `status:backlog`
- **Assignees:** None
- **Milestone:** `spec: 2026-05-24-scannos-module (#209)` (open milestone #16; no due date; description names the source spec and spec issue #209)
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The body cites spec sections 6.1 and 6.2 and states `Tracks: #209`.
- It enumerates rule fields for identity, pattern, suggestion, match type, scope, automatic application, statistics, contributors, timestamps, conflict, and note.
- It enumerates candidate fields for identity, token, suggestion, source, hits, pages, confidence, status, first-seen time, and note.
- The source spec requires `to_dict` and `from_dict` identity tests for both types.
- The spec review requires collision-safe immutable IDs plus stable book and occurrence identifiers and a normalized evidence schema.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **The base scanno entities do not exist.** Dependent storage and behavior lack a stable serialization contract.
2. **The draft schema lacks reviewed identity and evidence fields.** Implementing it unchanged would preserve known design gaps.

## Defects to fix

1. Reconcile `firstSeen` in the issue with `first_seen` in the Python-oriented source spec.
2. Replace recommended slug identity with collision-safe immutable identity.
3. Add the reviewed book, occurrence, and evidence fields before freezing serialization.

## Next steps

1. Revise the parent spec's model contracts.
2. Implement both dataclasses with deep-copy-safe `to_dict` and `from_dict` round trips.
3. Add field validation and field-level unit tests.

## What is NOT broken (to scope the fix)

- This task does not implement SQLite, JSON persistence, scanning, promotion, or downstream UI.
- The export contains no evidence of a regression in shipped model classes.

## Relationships and material comments

- This task tracks #209 and shares open milestone #16 with #217 through #220.
- The timeline references commit `15f67f06c467967ffc86ea9ce8c91de39190002e` on 2026-05-24 at 18:53:37 UTC. It records planning decomposition, not implementation.
- No comments were present in the export.

## Repository evidence

- The source spec's implementation sequence begins with these dataclasses.
- The spec's review says no implementation was found and requires model corrections first.

## Remaining work

- Contract revision, dataclass implementation, validation, serialization, and tests remain open.

## Resolution

_Open._ The issue is open and no evidence supports treating the dataclasses as implemented.
