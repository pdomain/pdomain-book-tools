---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Build the hyphen n-grams extraction pipeline

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — no reproducible process produces the local frequency database
- **Affected version:** Draft hyphen n-grams design dated 2026-05-24
- **Read when:** building the Google Books corpus extractor, database snapshot, manifest, normalization rules, or smoke tests
- **Search terms:** build_hyphen_ngrams_db, Google Books Ngrams corpus, two-pass extraction, synthetic corpus, issue 225
- **Relates to:** [Hyphen n-grams SQLite spec](../specs/2026-05-24-hyphen-ngrams-sqlite.md), [parent issue #210](2026-05-24-gh-210-spec-hyphen-ngrams-sqlite.md)

## Summary

This open task builds the corpus extraction script and a tiny end-to-end smoke test. The pipeline must use pinned Google Books Ngrams inputs to produce a reproducible SQLite snapshot. It must do so without materializing the full corpus.

## Impact

- The SQLite client and downloader cannot ship without a verified database artifact and repeatable build process.
- Incorrect pair discovery, normalization, or denominator rules would silently distort frequency comparisons.

## Environment / versions

The task targets sections 6.4 and 8 of the draft 2026-05-24 spec. The export does not name a runtime, package version, or operating system.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/225>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDPjE5A`
- **Issue number:** 225
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-225.json`
- **Raw SHA-256:** `9524b42a9c110afb2d7c96a88560432da404700faf0385752290fff26c380125`
- **Migration cutover:** Pending — record the immutable merged cutover commit before deleting the GitHub issue.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-24T18:53:20Z`
- **Updated:** `2026-05-24T18:53:20Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:feature`, `effort:M`, `model:sonnet`, `model-effort:medium`, `status:backlog`
- **Assignees:** None
- **Milestone:** `spec: 2026-05-24-hyphen-ngrams-sqlite (#210)` (open milestone #17; no due date; description names the source spec and spec issue #210)
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The body cites spec sections 6.4 and 8 and states `Tracks: #210`.
- It names `scripts/build_hyphen_ngrams_db.py`, Google Books Ngrams raw data, hyphen-pair extraction, SQLite output, and a tiny synthetic-corpus smoke test.
- The draft describes 20 compressed English 2-gram files, decade aggregation from 1700 through 2020, relative frequency using total tokens per decade, and an idempotent `--overwrite` path.
- The proposed 30–60 minute build, approximately 20 GB compressed input, approximately 50 MB output, and sub-millisecond lookup remain unverified estimates.
- The later source review requires an explicit two-pass or indexed process, a pinned corpus edition, exact normalization and counting rules, and a reproducible build manifest.
- Corpus licensing and redistribution remain unresolved risks.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **The draft single-scan description cannot reliably count joined forms discovered later.** The accepted review calls for a two-pass or indexed design.
2. **The corpus contract is not pinned precisely enough.** Snapshot identity, input checksums, character rules, case handling, and denominators need exact definitions.

## Defects to fix

1. Define the two-pass or indexed extraction algorithm and resource bounds.
2. Pin source files, corpus edition, checksums, normalization, token filters, decade buckets, and frequency denominators.
3. Emit a build manifest and create the database schema and metadata deterministically.
4. Add parser, aggregation, overwrite, malformed-input, and end-to-end fixture tests.

## Next steps

1. Resolve licensing and redistribution before publishing an artifact.
2. Finalize the extraction contract and build a small fixture before a full corpus run.
3. Record measured duration, disk, output size, and query performance in the manifest or benchmark evidence.

## What is NOT broken (to scope the fix)

- The task does not download the finished database at runtime or implement the query client.
- Full-corpus materialization, lemmatization, diacritic normalization, and corpus refreshes are outside V1 scope.

## Relationships and material comments

- The task tracks #210 and shares open milestone #17 with #221 through #224.
- The timeline references planning commit `15f67f06c467967ffc86ea9ce8c91de39190002e` on 2026-05-24 at 18:53:38 UTC. It does not prove implementation.
- No comments were present in the export.

## Repository evidence

- The source spec contains a five-step pipeline outline and one named ten-row smoke test.
- Its review accepted a two-pass redesign and build-manifest requirements; it found no implementation or data artifact.

## Remaining work

- Algorithm design, corpus pinning, licensing decision, implementation, fixture tests, full build, manifest, benchmarks, and artifact publication remain open.

## Resolution

_Open._ The issue is open, and no evidence supports treating the extraction pipeline or database snapshot as implemented.
