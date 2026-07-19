---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Add the filename-sequence page-order signal

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — filename order cannot yet contribute to swap proposals
- **Affected version:** Draft page-order design dated 2026-05-24
- **Read when:** implementing filename parsing or page-order anomaly detection
- **Search terms:** filename sequence, IMG_0042, non-monotonic, page order, issue 212
- **Relates to:** [Page-order detection spec](../specs/2026-05-24-page-order-detection.md), [parent issue #208](2026-05-24-gh-208-spec-page-order-detection.md)

## Summary

This open task extracts integer sequences from common filenames and flags non-monotonic page order. It must return per-page signal results and include unit tests with synthetic `Page` objects.

## Impact

- Filename sequence is intended to remain available when OCR or image data is missing.
- Filename-only evidence has no corroboration, so the parent design assigns it low confidence when it is the sole signal.

## Environment / versions

The task targets the draft 2026-05-24 page-order spec. No runtime, package version, or operating system appears in the export.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/212>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDPi9GQ`
- **Issue number:** 212
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-212.json`
- **Raw SHA-256:** `101652e8ec889bce4f7024d5efbd6cd1c1cf3e7ebe836bc5f4030592bcb70339`
- **Migration cutover:** `6842ec6b11c06c9b987b384b4abf7e9dc4699014` — merged migration cutover on `master`.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-24T18:52:31Z`
- **Updated:** `2026-05-24T18:52:31Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:feature`, `effort:M`, `model:sonnet`, `model-effort:medium`, `status:backlog`
- **Assignees:** None
- **Milestone:** `spec: 2026-05-24-page-order-detection (#208)` (open milestone #15; no due date; description names the source spec and spec issue #208)
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The body cites the filename subsection of spec section 7.2 and states `Tracks: #208`.
- It gives `IMG_0042.jpg → 42` as the representative extraction and requests detection of non-monotonic ordering.
- The source spec narrows extraction to the last continuous digit run in the basename. It proposes comparing sorted and list positions with a configurable tolerance that defaults to two positions.
- The source spec also requires no crash and no filename signal when names contain no digits.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **No filename signal implementation exists.** The proposed detector cannot use numeric source-name order.
2. **Sequence semantics need sharper rules.** Duplicate numbers, gaps, front matter, and the relationship between `Page.name` and the spec's older `source_path` assumption remain unresolved.

## Defects to fix

1. Define filename parsing against the current `Page` model.
2. Specify duplicates, gaps, missing digits, tolerance, and non-monotonic anomalies.
3. Return the agreed signal-result type and cover ordered, swapped, and nonnumeric cases.

## Next steps

1. Resolve the parent spec's model and numbering corrections.
2. Write failing synthetic-page tests for the agreed edge cases.
3. Implement the pure filename signal and connect it to task #215 only after its contract is stable.

## What is NOT broken (to scope the fix)

- This task does not parse OCR, compute visual hashes, or aggregate confidence.
- Numeric filenames are not guaranteed; the design requires graceful absence rather than an error.

## Relationships and material comments

- This task tracks #208, depends on the shared types in #211, and feeds aggregation task #215.
- No comments were present in the export.

## Repository evidence

- The current source spec preserves the filename signal as planned work and records unresolved front-matter and numbering-gap rules.
- No implementation or test result is cited by the export.

## Remaining work

- Parsing rules, anomaly semantics, implementation, and unit tests remain open.

## Resolution

_Open._ The task and its parent spec remain open, with no evidence of an implemented filename signal.
