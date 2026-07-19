---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Specify the hyphen n-grams SQLite migration

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — Stage 15 lacks its planned deterministic local frequency source
- **Affected version:** Draft hyphen n-grams design dated 2026-05-24
- **Read when:** designing or implementing hyphen-pair frequency lookup, local data distribution, or the Stage 15 SQLite migration
- **Search terms:** hyphen n-grams, SQLite migration, Google Books Ngrams, Stage 15, issue 210
- **Relates to:** [Hyphen n-grams SQLite spec](../specs/2026-05-24-hyphen-ngrams-sqlite.md)

## Summary

This open spec replaces an unofficial Google Books JSON endpoint with deterministic local SQLite lookup. It retains JSON as a fallback. The spec gates the `pdomain-prep-for-pgdp` Stage 15 SQLite migration and decomposes into issues #221 through #225.

## Impact

- Runtime JSON lookup is rate-limited, internet-dependent, and subject to removal without notice.
- The proposed local database would support reproducible, sub-millisecond lookups, but its size, build duration, and latency remain estimates.

## Environment / versions

The task targets the draft spec dated 2026-05-24 and the Stage 15 design handoff. The export does not name a runtime, package version, or operating system.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/210>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDPi4iw`
- **Issue number:** 210
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-210.json`
- **Raw SHA-256:** `e03bb0b0d5aa16fdbffef16f0ddbdc2f8997b636afc8c28d7e5a34a5895ddf10`
- **Migration cutover:** Pending — record the immutable merged cutover commit before deleting the GitHub issue.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-24T18:52:01Z`
- **Updated:** `2026-05-24T18:52:01Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:spec`, `status:backlog`
- **Assignees:** None
- **Milestone:** None
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The issue names `docs/specs/2026-05-24-hyphen-ngrams-sqlite.md` as its source spec.
- It requests a `HyphenNgramsClient` protocol, a pre-indexed `SqliteClient`, and an unofficial-endpoint `JsonApiClient` fallback.
- It selects download-on-first-use from a versioned GitHub Release asset and local caching through `platformdirs`.
- It says the work gates Decision #2 of the Stage 15 design handoff and cites `pd-ui/docs/templates/design_handoff_pd_ui/wf05/NOTES.md` as its design source.
- The source spec retains manual database building as an advanced path and excludes Stage 15 FastAPI routes, lemmatization, diacritic normalization, and offline corpus updates from V1.
- The 2026-07-13 spec review found no implementation or data artifact.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **The unofficial endpoint cannot provide a stable local contract.** Its rate limits, runtime network dependency, and removal risk motivate the adapter and SQLite design.
2. **The draft extraction and distribution contracts remain incomplete.** Corpus pinning, normalization, licensing, integrity, locking, atomic download, recovery, and read-only concurrency still need evidence-backed decisions.

## Defects to fix

1. Finalize the protocol and result contract.
2. Define and implement the SQLite schema, query behavior, and safe read-only concurrency.
3. Implement the JSON fallback, versioned download, cache integrity, and corruption recovery.
4. Build and verify a reproducible extraction pipeline and distributable database artifact.

## Next steps

1. Resolve the spec review findings and open questions before implementation.
2. Complete issues #221 through #225 with the source spec as the design authority.
3. Publish and benchmark a pinned database snapshot before relying on size, duration, or latency estimates.

## What is NOT broken (to scope the fix)

- The issue does not report a regression in shipped package behavior.
- Stage 15 FastAPI routes belong to `pdomain-prep-for-pgdp`, not this package.
- Community-maintained hyphen-pair data is outside V1 scope.

## Relationships and material comments

- Issues #221 through #225 cite this issue and the source spec; GitHub exposes no parent/sub-issue API relationships.
- The timeline contains five cross-references and references planning commit `15f67f06c467967ffc86ea9ce8c91de39190002e` on 2026-05-24 at 18:53:37 UTC. It does not prove implementation.
- No comments were present in the export.

## Repository evidence

- The source spec defines the module layout, schema, download convention, extraction outline, implementation sequence, and ten named tests.
- Its adversarial review records unresolved design corrections and says no implementation or data artifact was found.

## Remaining work

- The protocol, clients, downloader, extraction pipeline, database snapshot, distribution proof, tests, and downstream migration remain open.

## Resolution

_Open._ The issue is open, and no repository evidence supports treating the migration as implemented.
