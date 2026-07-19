---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Specify the scannos rule and candidate module

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — all downstream Stage 13 scanno slices depend on an unresolved shared contract
- **Affected version:** Draft scannos design dated 2026-05-24
- **Read when:** defining or implementing shared scanno rules, candidates, storage, scanning, or promotion
- **Search terms:** scannos, ScannoRule, ScannoCandidate, RuleLibrary, CandidateStore, issue 209
- **Relates to:** [Scannos module spec](../specs/2026-05-24-scannos-module.md)

## Summary

This open issue defines a shared scanno model, storage layer, and API. The draft proposes a SQLite global rule library, per-book JSON candidate sidecars, and atomic promotion with an evidence trail. Its accepted design review findings must be resolved before implementation.

## Impact

- The issue gates `pdomain-prep-for-pgdp` Stage 13 slices S13-A through S13-D.
- The proposed schema would be shared by `pdomain-prep-for-pgdp` and future `pdomain-*` tools.
- The named UI consumers are `pdomain-ui/.../wf05b/scanno-configure.jsx`, `wf05b/scanno-promote.jsx`, and `wf05b/DISCUSSION.md`.

## Environment / versions

The issue targets the draft 2026-05-24 scannos spec. No runtime, package version, operating system, or launch command appears in the export.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/209>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDPi4Zw`
- **Issue number:** 209
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-209.json`
- **Raw SHA-256:** `b02f1735b12241792a13b2ed800d64fb7dde2bdf5be9ef54371b6763d9fe1892`
- **Migration cutover:** `6842ec6b11c06c9b987b384b4abf7e9dc4699014` — merged migration cutover on `master`.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-24T18:52:00Z`
- **Updated:** `2026-05-24T18:52:00Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:spec`, `status:backlog`
- **Assignees:** None
- **Milestone:** None
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The body names `docs/specs/2026-05-24-scannos-module.md` as its spec.
- It requests `pd_book_tools.scannos` as the owner of the data model, storage, and API for scanner-error-correction rules and candidates.
- It specifies a SQLite `RuleLibrary`, a per-book JSON sidecar `CandidateStore`, and an atomic `promote()` transaction that moves a candidate into a rule with an evidence trail.
- The source spec uses the current package spelling `pdomain_book_tools.scannos`, expands the model and APIs, and retains four unresolved design questions.
- The source spec's 2026-07-13 adversarial review found no implementation. It requires stable book and occurrence identifiers, normalized evidence, dual-write recovery, collision-safe IDs, corrected matching semantics, and defined concurrency and migration behavior.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **The shared scanno contract has not been finalized.** The active spec still carries accepted corrections and owner decisions.
2. **Cross-store promotion needs a recovery design.** SQLite and JSON cannot share one transaction, despite the issue's atomic-promotion wording.

## Defects to fix

1. Reconcile the historical `pd_book_tools` spelling with the current package name.
2. Fold the accepted design-review corrections into an evidence-backed spec revision.
3. Resolve identity, evidence, dual-write recovery, normalization, conflict, migration, and concurrency behavior.
4. Establish seed-data and real-book evaluation evidence before claiming useful detection quality.

## Next steps

1. Revise the source spec and decide its unresolved V1 questions.
2. Define safe failure and recovery behavior for promotion across SQLite and JSON.
3. Then execute child tasks #216 through #220 in dependency order.

## What is NOT broken (to scope the fix)

- The issue does not report a regression in an existing scannos API.
- The source spec excludes UI implementation, multi-user collaboration, online sync, and V1 regex scanning.

## Relationships and material comments

- Child work is tracked by #216, #217, #218, #219, and #220. The GitHub API export does not encode them as sub-issues; their bodies each say `Tracks: #209`.
- The timeline references commit `15f67f06c467967ffc86ea9ce8c91de39190002e` on 2026-05-24 at 18:53:37 UTC. The same commit appears in #216 and #220 and records the spec back-reference and task decomposition; it is planning provenance, not implementation evidence.
- No comments were present in the export.

## Repository evidence

- The governed source spec remains active and labels its own status as Draft.
- Its adversarial-review section says no implementation was found as of 2026-07-13.
- Accepted corrections and unresolved ideas are preserved in `docs/context/intent-map.md` pending an evidence-backed revision.

## Remaining work

- Spec revision, owner decisions, model and storage implementation, scanning and promotion APIs, tests, downstream routes, and UI integration remain open.

## Resolution

_Open._ The GitHub issue is open, the source spec is still a draft, and current evidence does not support completion.
