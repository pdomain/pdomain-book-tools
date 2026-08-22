---
Status: active
Owner: CT
Created: 2026-08-22
Last verified: 2026-08-22
Kind: plan
---

# PGDP-aware Matcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

## Goal

Build a pure shared matcher that preserves OCR tokens and reconstructs PGDP physical continuations with exact evidence.

## Architecture

Add immutable match document and graph models in book-tools. Then add a document-level PGDP continuation adapter and bounded monotonic engine. Keep legacy mutation behind a compatibility projection. Source-data and SPA integration use separate follow-up plans after the shared release.

## Tech Stack

Python 3.13, Pydantic v2, existing typography grapheme alignment, pytest, ruff, basedpyright.

## Global Constraints

- Never mutate source documents or OCR token topology in the matching core.
- Preserve exact source ranges and deterministic identities.
- Quarantine ties, low margins, exhausted search bounds, and unresolved continuations.
- Keep PGDP decoding source-specific and the matcher source-neutral.
- Keep corpus bytes and generated book artifacts outside Git.

---

### Task 1: Immutable match contracts

**Files:** `pdomain_book_tools/matching/models.py`, `pdomain_book_tools/matching/__init__.py`, `tests/matching/test_models.py`

- [ ] Write failing tests for stable token IDs, ordered pages and lines, exact artifact ranges, relation validation, canonical graph IDs, rejected unordered ranges, and deep immutability of every nested container.
- [ ] Run `uv run pytest tests/matching/test_models.py -q` and confirm imports fail.
- [ ] Implement frozen models with tuples and immutable mappings for source ranges, tokens, lines, pages, documents, operations, alternatives, relations, and graphs.
- [ ] Run focused tests, ruff, and basedpyright.
- [ ] Commit `feat: add immutable matching contracts`.

### Task 2: Reversible PGDP continuation evidence

**Files:** `pdomain_book_tools/matching/pgdp_continuations.py`, `pdomain_book_tools/matching/models.py`, `tests/matching/test_pgdp_continuations.py`

- [ ] Write failing tests for the five real continuation patterns, asymmetric markers, nonadjacent joins, orphan markers, F2/P3 round conflicts, and empty-fragment quarantine.
- [ ] Run the focused tests and confirm the decoder is absent.
- [ ] Implement document-level decoding with exact ranges, surface fragments, logical candidates, marker evidence, and explicit quarantine reasons.
- [ ] Prove F2 and P3 bytes remain unchanged and every output grapheme maps to an input range.
- [ ] Run focused gates and commit `feat: decode pgdp continuations reversibly`.

### Task 3: Pure monotonic token matcher

**Files:** `pdomain_book_tools/matching/engine.py`, `pdomain_book_tools/matching/models.py`, `tests/matching/test_engine.py`

- [ ] Write failing tests for exact, source-to-fragments, sources-to-one-token, insert, delete, ties, low margins, exhausted search bounds, deterministic tie-breaks, punctuation, and Unicode ranges.
- [ ] Run the focused tests and confirm the engine is absent.
- [ ] Implement a versioned bounded dynamic program that retains best and runner-up paths, emits explicit quarantine on ties, low margins, or exhausted bounds, and never mutates inputs.
- [ ] Project accepted continuation evidence onto physical OCR relations without collapsing boxes or IDs.
- [ ] Run focused gates and commit `feat: add provenance preserving token matcher`.

### Task 4: Legacy compatibility projection

**Files:** `pdomain_book_tools/matching/legacy_projection.py`, `pdomain_book_tools/ocr/ground_truth_matching.py`, `tests/matching/test_legacy_projection.py`, `tests/ocr/test_ground_truth_matching.py`

- [ ] Pin visible-hyphen, missing-hyphen, combined-word, manual-split, and displaced-line behavior.
- [ ] Add failing tests proving the pure graph retains original topology before projection.
- [ ] Implement an opt-in projection that writes legacy fields and typed evidence.
- [ ] Run legacy and new suites together.
- [ ] Commit `refactor: project match graphs onto legacy pages`.

### Task 5: Real evidence and release gate

**Files:** `tests/fixtures/matching/pgdp-continuations.json`, `tests/matching/test_real_pgdp_evidence.py`, `CHANGELOG.md`

- [ ] Add metadata-only real fixtures with hashes, page keys, minimal fragments, and byte ranges.
- [ ] Test deterministic decoding, matching, and exact range preservation.
- [ ] Run `make ci AI=1`.
- [ ] Run spec compliance and code quality reviews and resolve every finding.
- [ ] Commit `test: cover real pgdp continuation evidence` and prepare a book-tools release.

### Task 6: Shared book labeling manifest

**Files:** `pdomain_book_tools/typography/book_manifest.py`, `pdomain_book_tools/typography/__init__.py`, `tests/typography/test_book_manifest.py`

- [ ] Write failing tests for stable book identity, canonical manifest identity, contiguous page order, confined paths, unique page/bundle/relation IDs, page relation references, and one taxonomy identity.
- [ ] Run the focused tests and confirm the models are absent.
- [ ] Implement frozen `BookLabelingPage`, `BookMatchRelationReference`, and `BookLabelingManifest` models without filesystem access.
- [ ] Test that page configuration hashes may differ and that canonical bytes reproduce the manifest ID.
- [ ] Run focused gates and commit `feat: add book labeling manifest contract`.

## Verification

Run every focused gate after its task and `make ci AI=1` before release. Complete spec compliance review before code quality review. Resolve all findings before merging.
