---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Add the SQLite hyphen n-grams client

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — deterministic local hyphen-pair lookup is unavailable
- **Affected version:** Draft hyphen n-grams design dated 2026-05-24
- **Read when:** implementing the hyphen-pair database schema, query client, frequency normalization, or concurrency behavior
- **Search terms:** SqliteClient, hyphen_pairs, decade frequency, WAL, issue 222
- **Relates to:** [Hyphen n-grams SQLite spec](../specs/2026-05-24-hyphen-ngrams-sqlite.md), [parent issue #210](2026-05-24-gh-210-spec-hyphen-ngrams-sqlite.md)

## Summary

This open task adds the SQLite schema and implements `SqliteClient` behind `HyphenNgramsClient`. Tests use a small fixture database. They must cover hits, misses, year ranges, and the finalized concurrency mode.

## Impact

- Local lookup removes the runtime network dependency from the primary path.
- Incorrect normalization, schema, or connection behavior could produce misleading frequency comparisons or unsafe multi-process reads.

## Environment / versions

The task targets section 6.2 of the draft 2026-05-24 spec. The export does not name a runtime, package version, or operating system.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/222>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDPjEWQ`
- **Issue number:** 222
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-222.json`
- **Raw SHA-256:** `82575ebe87e4d0411c4fef28a5b75b371654defb0e3b3e27a930996d250f03c8`
- **Migration cutover:** `6842ec6b11c06c9b987b384b4abf7e9dc4699014` — merged migration cutover on `master`.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-24T18:53:17Z`
- **Updated:** `2026-05-24T18:53:17Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:feature`, `effort:M`, `model:sonnet`, `model-effort:medium`, `status:backlog`
- **Assignees:** None
- **Milestone:** `spec: 2026-05-24-hyphen-ngrams-sqlite (#210)` (open milestone #17; no due date; description names the source spec and spec issue #210)
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The body cites spec section 6.2 and states `Tracks: #210`.
- The issue asks for decade-bucketed hyphen and joined frequencies from 1700 through 2020.
- The source schema instead stores one row per word pair and decade, with relative frequencies and metadata for schema version and corpus snapshot date.
- The client must make a parameterized query and return `FreqResult | None`.
- The draft requires standard-library `sqlite3`, concurrent read-only use, and WAL mode, while the later review requires an explicit safe read-only design instead of assuming WAL is suitable.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **The deterministic local implementation is unbuilt.** The source review found no implementation or database artifact.
2. **The draft concurrency contract needs revision.** A distributed read-only database may not safely support the draft WAL assumption in every location.

## Defects to fix

1. Finalize the schema and exact-match, range-filtered query semantics.
2. Define relative-frequency calculation and corpus metadata precisely.
3. Implement safe read-only multi-process connection behavior and fixture-based tests.

## Next steps

1. Resolve the schema wording and WAL/read-only design before implementation.
2. Add hit, miss, year-range, metadata, normalization, and concurrency tests.

## What is NOT broken (to scope the fix)

- Downloading, caching, JSON fallback, and corpus extraction are separate tasks.
- The issue does not report corruption in an existing database.

## Relationships and material comments

- The task tracks #210 and shares open milestone #17 with #221 and #223 through #225.
- No commit reference or comment was present in the export.

## Repository evidence

- The source spec contains the proposed schema and four named SQLite client tests.
- Its review requires pinned normalization and safer read-only behavior; it found no implementation.

## Remaining work

- Schema finalization, client implementation, fixture construction, and positive and negative tests remain open.

## Resolution

_Open._ The issue is open, and no evidence supports treating the SQLite client as implemented.
