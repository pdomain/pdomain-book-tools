---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Download and cache the hyphen n-grams database

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — first-use data acquisition lacks a safe reproducible contract
- **Affected version:** Draft hyphen n-grams design dated 2026-05-24
- **Read when:** implementing the database URL, cache path, integrity checks, version pinning, or first-use races
- **Search terms:** ensure_db, HYPHEN_DB_URL, platformdirs, checksum, atomic download, issue 224
- **Relates to:** [Hyphen n-grams SQLite spec](../specs/2026-05-24-hyphen-ngrams-sqlite.md), [parent issue #210](2026-05-24-gh-210-spec-hyphen-ngrams-sqlite.md)

## Summary

This open task downloads a versioned SQLite database on first use. It caches the database at a `platformdirs` user-data path. The finalized design must verify integrity and recover safely from corruption or concurrent first use.

## Impact

- Users avoid a large mandatory data wheel and pay the roughly 50 MB download cost only when they use the feature.
- Weak pinning or non-atomic writes could break reproducibility or leave a corrupt shared cache.

## Environment / versions

The task targets section 6.3 of the draft 2026-05-24 spec. The export does not name a runtime, package version, or operating system.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/224>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDPjEtg`
- **Issue number:** 224
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-224.json`
- **Raw SHA-256:** `48379cc2395523e8f79222932db4790f2aaa9bf7644bb40532c6aaf590577ed5`
- **Migration cutover:** `6842ec6b11c06c9b987b384b4abf7e9dc4699014` — merged migration cutover on `master`.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-24T18:53:19Z`
- **Updated:** `2026-05-24T18:53:19Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:feature`, `effort:M`, `model:sonnet`, `model-effort:medium`, `status:backlog`
- **Assignees:** None
- **Milestone:** `spec: 2026-05-24-hyphen-ngrams-sqlite (#210)` (open milestone #17; no due date; description names the source spec and spec issue #210)
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The body cites spec section 6.3 and states `Tracks: #210`.
- It requires a versioned GitHub Release asset, `platformdirs` caching, integrity verification, version pinning, and cache hit, miss, and corruption tests.
- The draft URL uses an independent `hyphen-data-{snapshot_date}` tag and `hyphen_ngrams_{snapshot_date}.db` asset.
- The later source review requires checksum verification, locking, atomic replacement, retry and timeout rules, and corruption recovery.
- GitHub asset durability and cross-process first-use races remain residual risks.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **The package has no verified data artifact to acquire.** The review found neither implementation nor a published database.
2. **The draft happy path omits failure safety.** Cache presence alone cannot prove integrity, version, or complete download.

## Defects to fix

1. Pin the asset URL, snapshot identity, expected checksum, and cache layout.
2. Implement timeout, bounded retry, locking, temporary download, atomic replacement, and corruption recovery.
3. Define synchronous first-use behavior and observable failures.

## Next steps

1. Publish a reproducible database and build manifest before pinning download constants.
2. Add cache hit, miss, force, checksum mismatch, interrupted download, corrupt cache, and concurrent first-use tests.

## What is NOT broken (to scope the fix)

- Manual database building remains a separate advanced path.
- The approximate 50 MB size is an estimate, not a verified acceptance result.

## Relationships and material comments

- The task tracks #210 and shares open milestone #17 with #221 through #223 and #225.
- No commit reference or comment was present in the export.

## Repository evidence

- The source spec defines `default_db_path()`, `ensure_db(force=False)`, and `HYPHEN_DB_URL` but only names one cached-path test.
- Its review expands the required failure and concurrency coverage and says no artifact was found.

## Remaining work

- Artifact publication, integrity metadata, safe downloader implementation, cache policy, and failure and concurrency tests remain open.

## Resolution

_Open._ The issue is open, and no evidence supports treating the download mechanism or data artifact as complete.
