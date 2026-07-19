---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Define the hyphen n-grams protocol and result type

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — the interchangeable client implementations lack a shared typed contract
- **Affected version:** Draft hyphen n-grams design dated 2026-05-24
- **Read when:** defining hyphen frequency result fields, client typing, or lightweight test doubles
- **Search terms:** HyphenNgramsClient, FreqResult, Protocol, dataclass, issue 221
- **Relates to:** [Hyphen n-grams SQLite spec](../specs/2026-05-24-hyphen-ngrams-sqlite.md), [parent issue #210](2026-05-24-gh-210-spec-hyphen-ngrams-sqlite.md)

## Summary

This open task defines the `HyphenNgramsClient` structural protocol and `FreqResult` dataclass. Both production clients and lightweight test doubles must share this contract.

## Impact

- The protocol is the compatibility boundary between Stage 15 callers and JSON or SQLite lookup.
- Field-level tests protect the decade-indexed frequency result shape.

## Environment / versions

The task targets section 6.1 of the draft 2026-05-24 spec. The export does not name a runtime, package version, or operating system.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/221>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDPjENQ`
- **Issue number:** 221
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-221.json`
- **Raw SHA-256:** `e33f25b36cd712d7421f188bf487b45247355ce491ad42fb166889fbd60678a2`
- **Migration cutover:** Pending — record the immutable merged cutover commit before deleting the GitHub issue.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-24T18:53:16Z`
- **Updated:** `2026-05-24T18:53:16Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:feature`, `effort:M`, `model:sonnet`, `model-effort:medium`, `status:backlog`
- **Assignees:** None
- **Milestone:** `spec: 2026-05-24-hyphen-ngrams-sqlite (#210)` (open milestone #17; no due date; description names the source spec and spec issue #210)
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The body cites spec section 6.1 and states `Tracks: #210`.
- `FreqResult` carries `word_a`, `word_b`, and decade-to-relative-frequency maps for hyphenated and joined forms.
- `query` accepts both words plus inclusive `start_year` and `end_year` keyword arguments, defaulting to 1800 and 2000, and returns `FreqResult | None`.
- The source spec requires a plain dict-based test double to satisfy the protocol.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **The shared interface has not been implemented.** The task remains a backlog item. The source-spec review found no implementation.
2. **Downstream compatibility depends on exact structural typing.** An abstract base class or implementation-specific result would conflict with the selected duck-typed design.

## Defects to fix

1. Add the protocol and dataclass under `pdomain_book_tools.hyphen_ngrams`.
2. Add `FreqResult` field tests and structural protocol-conformance tests.

## Next steps

1. Confirm the result fields and year-range behavior against the revised spec.
2. Implement focused tests before the SQLite and JSON clients consume the contract.

## What is NOT broken (to scope the fix)

- This issue does not implement either client, downloading, or corpus extraction.
- It does not report a shipped API regression.

## Relationships and material comments

- The task tracks #210 and shares open milestone #17 with #222 through #225.
- The timeline references planning commit `15f67f06c467967ffc86ea9ce8c91de39190002e` on 2026-05-24 at 18:53:38 UTC. It does not prove implementation.
- No comments were present in the export.

## Repository evidence

- The source spec defines the proposed types and lists result-round-trip and structural protocol tests.
- Its 2026-07-13 review says no implementation was found.

## Remaining work

- Contract finalization, implementation, exports, and tests remain open.

## Resolution

_Open._ The issue is open, and no evidence supports treating the protocol or result type as implemented.
