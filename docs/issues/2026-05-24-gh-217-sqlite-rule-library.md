---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Add the SQLite scanno rule library

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — shared scanno rules lack a durable queryable store
- **Affected version:** Draft scannos design dated 2026-05-24
- **Read when:** implementing global scanno rule persistence, queries, or default paths
- **Search terms:** RuleLibrary, SQLite, WAL, platformdirs, rules.db, issue 217, issue 209
- **Relates to:** [Scannos module spec](../specs/2026-05-24-scannos-module.md), [parent issue #209](2026-05-24-gh-209-spec-scannos-module.md)

## Summary

This open task implements the global `RuleLibrary` with SQLite, WAL mode, indexed queries, and a default `platformdirs` path. The active spec adds CRUD, statistics, schema-version scaffolding, and a bundled empty database, while its review leaves shared-state risks unresolved.

## Impact

- Scanning and promotion need a durable source of global rules.
- A mutable library shared across tools can leak project-specific judgments unless scope and conflict behavior are defined.

## Environment / versions

The task targets section 6.4 of the draft 2026-05-24 scannos spec. No runtime, SQLite version, package version, or operating system appears in the export.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/217>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDPjBAQ`
- **Issue number:** 217
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-217.json`
- **Raw SHA-256:** `6c00eff2fb40c1faaa96d1f1ec2969f0cb451217b3a4f5894a0827137032c3ff`
- **Migration cutover:** `6842ec6b11c06c9b987b384b4abf7e9dc4699014` — merged migration cutover on `master`.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-24T18:52:55Z`
- **Updated:** `2026-05-24T18:52:55Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:feature`, `effort:M`, `model:sonnet`, `model-effort:medium`, `status:backlog`
- **Assignees:** None
- **Milestone:** `spec: 2026-05-24-scannos-module (#209)` (open milestone #16; no due date; description names the source spec and spec issue #209)
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The body cites spec section 6.4 and states `Tracks: #209`.
- It requests a SQLite `RuleLibrary` in WAL mode, indexes on pattern, scope, and auto, plus load, save, query, and list methods.
- It requests a `platformdirs` default at `~/.local/share/pd-suite/scannos/rules.db` and schema and query-path unit tests.
- The source spec instead shows `~/.local/share/pdomain-suite/scannos/rules.db`, defines CRUD, search, and statistics APIs, and requires schema-version scaffolding and an empty bundled database.
- The spec review requires migrations, statistics-update rules, normalization, and conflicts to be specified before implementation.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **The global rule store has not been implemented.** No durable query path exists for scanno rules.
2. **The storage contract remains internally inconsistent.** The issue and spec disagree on the default application directory and method names.

## Defects to fix

1. Decide the stable default application directory and public method surface.
2. Define schema migration, normalization, statistics, scope, and conflict behavior.
3. Address the reviewed risk of shared mutable state crossing project boundaries.

## Next steps

1. Finalize the parent model and storage contracts.
2. Implement schema creation, WAL mode, versioning, CRUD, queries, statistics, and default-path initialization.
3. Test schema, indexes, query filters, WAL mode, migrations, and concurrent readers.

## What is NOT broken (to scope the fix)

- This task does not implement candidate sidecars, scanning, promotion, or UI.
- The export provides no evidence that a shipped rule database regressed.

## Relationships and material comments

- This task tracks #209 and shares open milestone #16 with #216 and #218 through #220.
- No commit references or comments were present in the export.

## Repository evidence

- The source spec chooses SQLite for relational queries and read-heavy concurrent access.
- Its review says no implementation was found and preserves unresolved storage decisions.

## Remaining work

- Contract decisions, implementation, database initialization, migrations, and tests remain open.

## Resolution

_Open._ The issue is open and no evidence supports treating `RuleLibrary` as implemented.
