---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Add the visual-similarity page-order signal

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — the proposed visual vote lacks an accepted positional model
- **Affected version:** Draft page-order design dated 2026-05-24
- **Read when:** evaluating perceptual hashes or visual evidence for page-order proposals
- **Search terms:** perceptual hash, pHash, imagehash, visual similarity, issue 214
- **Relates to:** [Page-order detection spec](../specs/2026-05-24-page-order-detection.md), [parent issue #208](2026-05-24-gh-208-spec-page-order-detection.md)

## Summary

This open task proposes perceptual hashes for page thumbnails, adjacent comparisons, and swap-restoration candidates. The source spec's later review rejects pair similarity as a swap vote unless a validated positional model is supplied, so implementation must not assume the original algorithm is accepted.

## Impact

- The original design treats visual evidence as a third confidence signal when images are available.
- An unvalidated similarity vote could raise confidence without proving that two pages belong in exchanged positions.

## Environment / versions

The task targets the draft 2026-05-24 page-order spec. No runtime, package version, operating system, or labelled evaluation corpus appears in the export.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/214>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDPi9ag`
- **Issue number:** 214
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-214.json`
- **Raw SHA-256:** `d98924bb484a076bddce5c648c15537167ed4595b7a0373e2909070df980133f`
- **Migration cutover:** `6842ec6b11c06c9b987b384b4abf7e9dc4699014` — merged migration cutover on `master`.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-24T18:52:33Z`
- **Updated:** `2026-05-24T18:52:33Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:feature`, `effort:M`, `model:sonnet`, `model-effort:medium`, `status:backlog`
- **Assignees:** None
- **Milestone:** `spec: 2026-05-24-page-order-detection (#208)` (open milestone #15; no due date; description names the source spec and spec issue #208)
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The body cites the visual-similarity subsection of spec section 7.2 and dependency notes identified there as section 7.4. In the current spec, dependency notes appear under section 7.4.
- It requests a perceptual hash per thumbnail, adjacent-pair comparison, swap-restoration candidates, a decision between `imagehash` and an alternative, and synthetic-thumbnail tests.
- The source spec proposes an 8×8 average hash, with dHash as fallback, and normalized Hamming similarity. It prefers a pure-NumPy implementation unless accuracy evidence justifies `imagehash`.
- The source spec requires CPU operation, determinism across Python versions, optional precomputed thumbnail bytes, and graceful behavior when `image_array` is `None`.
- The 2026-07-13 review says visual pair similarity must not vote for a swap without a validated positional model. It also reports no labelled corpus for precision, recall, or thresholds.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **Visual similarity does not establish position.** Similar pages may be adjacent without being swapped.
2. **No validated visual model or corpus exists.** The proposed threshold and confidence contribution lack evidence.

## Defects to fix

1. Define and validate a positional visual model before using visual data as a vote.
2. Decide the hashing algorithm and dependency only after measuring accuracy and stability.
3. Specify missing-image behavior, thumbnail ownership, and deterministic serialization.
4. Test both useful and misleading visual similarities.

## Next steps

1. Resolve the parent spec's accepted rejection of raw pair similarity.
2. Build or identify a labelled page-order corpus and evaluation criteria.
3. If evidence supports a positional model, implement it with CPU-only deterministic tests.

## What is NOT broken (to scope the fix)

- This task does not require a GPU.
- Missing page images must degrade to other signals rather than fail detection.
- Thumbnail rendering for the downstream route remains an unresolved ownership question.

## Relationships and material comments

- This task tracks #208, depends on the shared types in #211, and would feed aggregation task #215 only after validation.
- No comments were present in the export.

## Repository evidence

- The source spec retains the historical algorithm but its review explicitly records the required correction.
- No implementation, corpus, threshold evaluation, or test result is cited by the export.

## Remaining work

- Positional-model design, corpus evaluation, dependency choice, implementation, and tests remain open.

## Resolution

_Open._ The task remains open, and current evidence does not support implementing raw visual pair similarity as a swap vote.
