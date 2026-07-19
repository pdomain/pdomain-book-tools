---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Add the JSON API fallback client

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — callers need a compatible fallback when the local database is unavailable
- **Affected version:** Draft hyphen n-grams design dated 2026-05-24
- **Read when:** migrating the Google Books JSON client, defining fallback behavior, retries, or downstream compatibility
- **Search terms:** JsonApiClient, Google Books JSON, throttle retry, fallback, issue 223
- **Relates to:** [Hyphen n-grams SQLite spec](../specs/2026-05-24-hyphen-ngrams-sqlite.md), [parent issue #210](2026-05-24-gh-210-spec-hyphen-ngrams-sqlite.md)

## Summary

This open task moves the unofficial Google Books JSON lookup behind the shared `HyphenNgramsClient` protocol. It remains a fallback for users who cannot or do not want to download the SQLite database.

## Impact

- A protocol-compatible fallback preserves Stage 15 behavior during the SQLite transition.
- The endpoint is unofficial, rate-limited, internet-dependent, and subject to removal, so it cannot be the stable primary path.

## Environment / versions

The task targets the JSON fallback decision in section 6 of the draft 2026-05-24 spec. The export does not name a runtime, package version, or operating system.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/223>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDPjEgQ`
- **Issue number:** 223
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-223.json`
- **Raw SHA-256:** `fc141b22706d4395c4c77d84198579b581d193ee408b88c6a4cdb0683c368be9`
- **Migration cutover:** Pending — record the immutable merged cutover commit before deleting the GitHub issue.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-24T18:53:18Z`
- **Updated:** `2026-05-24T18:53:18Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:feature`, `effort:M`, `model:sonnet`, `model-effort:medium`, `status:backlog`
- **Assignees:** None
- **Milestone:** `spec: 2026-05-24-hyphen-ngrams-sqlite (#210)` (open milestone #17; no due date; description names the source spec and spec issue #210)
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The body cites the JSON fallback decision in spec section 6 and states `Tracks: #210`.
- It requires the unofficial Google Books JSON endpoint, the shared protocol, throttle-aware retry behavior, and mocked-network tests.
- The source spec says the implementation currently lives in `pdomain-prep-for-pgdp` and needs a deprecation shim when moved.
- The later source review lists API fallback drift as a residual risk.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **The fallback remains outside the shared package.** The migration and downstream re-export require coordinated API compatibility.
2. **The throttle-aware retry contract is underspecified.** Retry limits and throttle signals need explicit mocked-network tests.

## Defects to fix

1. Implement or migrate `JsonApiClient` behind the protocol.
2. Define throttle-aware retry behavior and its mocked-network tests.
3. Coordinate the downstream deprecation shim.

## Next steps

1. Inspect and test the existing downstream implementation before moving it.
2. Add mocked success and failure cases without requiring network access.
3. Preserve the old import path through the planned shim when this package releases the client.

## What is NOT broken (to scope the fix)

- This issue does not make the JSON endpoint the primary long-term source.
- SQLite lookup, database download, and corpus extraction are separate tasks.

## Relationships and material comments

- The task tracks #210 and shares open milestone #17 with #221, #222, #224, and #225.
- No commit reference or comment was present in the export.

## Repository evidence

- The source spec defines the fallback role and one interface test but leaves migration timing as open question Q-HN-4.
- Its review found no implementation in this repository.

## Remaining work

- Existing-code inspection, failure-contract design, implementation, mocked tests, and downstream shim coordination remain open.

## Resolution

_Open._ The issue is open, and no evidence supports treating the JSON fallback migration as implemented.
