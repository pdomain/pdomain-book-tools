---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Aggregate page-order signals behind the public API

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — consumers have no public page-order detector or confidence aggregation
- **Affected version:** Draft page-order design dated 2026-05-24
- **Read when:** implementing confidence voting, the public detector, or end-to-end page-order tests
- **Search terms:** detect_out_of_order_pages, voting, confidence, integration test, issue 215
- **Relates to:** [Page-order detection spec](../specs/2026-05-24-page-order-detection.md), [parent issue #208](2026-05-24-gh-208-spec-page-order-detection.md)

## Summary

This open task aggregates the page-order signals into `SwapProposal` objects and exposes `detect_out_of_order_pages`. Its confidence rules and function shape depend on unresolved parent-spec corrections and the outcomes of tasks #211 through #214.

## Impact

- The downstream Stage 11 route cannot call the proposed library API until aggregation and public exports exist.
- Incorrect voting could overstate confidence and encourage unsafe bulk application of proposed swaps.

## Environment / versions

The task targets the draft 2026-05-24 page-order spec. No runtime, package version, or operating system appears in the export.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/215>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDPi9kA`
- **Issue number:** 215
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-215.json`
- **Raw SHA-256:** `941141390c66c0a22b07c7dc468c31bec70f6bb767e32579a925ccccd335d31a`
- **Migration cutover:** Pending — record the immutable merged cutover commit before deleting the GitHub issue.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-24T18:52:34Z`
- **Updated:** `2026-05-24T18:52:34Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:feature`, `effort:M`, `model:sonnet`, `model-effort:medium`, `status:backlog`
- **Assignees:** None
- **Milestone:** `spec: 2026-05-24-page-order-detection (#208)` (open milestone #15; no due date; description names the source spec and spec issue #208)
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The body cites spec section 6, section 7.3, and section 8 and states `Tracks: #208`.
- It requests three-signal voting, `SwapProposal` confidence tiers, the public `detect_out_of_order_pages(pages: list[Page]) -> list[SwapProposal]` API, and an integration test with known synthetic swaps.
- The source spec proposes `high` for three of three available signals or two of two when the third is unavailable. It proposes `medium` for two of three and `low` for one available anomaly signal.
- The same spec says two agreeing signals with the third unavailable are both high and medium in different passages. Its review therefore requires confidence-tier reconciliation.
- The review also rejects unvalidated visual pair similarity as a vote and requires alignment with current `Page` fields, numbering rules, and normalized OCR roles.
- The full spec test plan covers ordered input, one filename swap, missing digits, OCR swaps, missing OCR, similar and dissimilar images, all confidence tiers, missing images, and `dataclasses.asdict` JSON serialization.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **Dependent signals and shared types are unfinished.** Aggregation has no stable inputs or outputs.
2. **The confidence table is internally inconsistent.** Implementing it literally would assign different tiers to the same two-of-two condition.

## Defects to fix

1. Reconcile confidence semantics and remove unsupported visual votes.
2. Finalize the public signature, optional cache and threshold parameters, result ordering, and exports.
3. Define behavior for missing signals, cycles, arbitrary moves, gaps, and front matter.
4. Cover positive, negative, degradation, serialization, and deterministic-order cases.

## Next steps

1. Complete the parent spec revision and task #211.
2. Implement and validate the accepted signals from #212 through #214.
3. Write failing integration and confidence-boundary tests.
4. Implement aggregation and expose the agreed public API.

## What is NOT broken (to scope the fix)

- This task does not auto-apply swaps or implement the downstream FastAPI route.
- The heavy synchronous work belongs in a downstream thread pool unless a separate async wrapper is explicitly designed.
- V1 excludes multi-page cycles under the original draft, though the review flags that limit as a residual risk.

## Relationships and material comments

- This task tracks #208 and aggregates outputs from #212, #213, and any accepted outcome of #214 using types from #211.
- It shares open milestone #15 with the other implementation tasks.
- The timeline references commit `15f67f06c467967ffc86ea9ce8c91de39190002e` on 2026-05-24 at 18:53:37 UTC. The same commit appears in #208 and #211 and records the spec back-reference and milestone decomposition; it does not show implementation.
- No comments were present in the export.

## Repository evidence

- The source spec defines the intended test matrix and public surface but labels itself Draft.
- Its 2026-07-13 review reports no implementation and records unresolved confidence and signal corrections.

## Remaining work

- Dependency completion, confidence design, public API implementation, integration tests, downstream route integration, and UI integration remain open.

## Resolution

_Open._ The task is open and cannot be completed faithfully until its dependencies and parent-spec corrections are resolved.
