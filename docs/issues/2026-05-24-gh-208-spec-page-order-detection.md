---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Specify page-order detection

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — page-order detection remains unimplemented and its design has unresolved corrections
- **Affected version:** Draft page-order design dated 2026-05-24
- **Read when:** designing or implementing page-order detection or its downstream Stage 11 route
- **Search terms:** page order, SwapProposal, detect_out_of_order_pages, issue 208, Stage 11, S11-B
- **Relates to:** [Page-order detection spec](../specs/2026-05-24-page-order-detection.md)

## Summary

The open issue requests page-order detection based on filename sequence, OCR page numbers, and perceptual-hash visual similarity. The draft spec proposes `SwapProposal` results with high, medium, or low confidence, but its 2026-07-13 review found no implementation and identified design corrections that remain unresolved.

## Impact

- The proposed detector is meant to supply confident swap pairs for human review.
- The work gates the downstream `pdomain-prep-for-pgdp` Stage 11 slice S11-B and its `/projects/:id/page-order` route.
- The named UI consumer is the `SwapRow` design in `pdomain-ui`, but the historical issue uses older `pd-*` repository names and paths.

## Environment / versions

The issue and source spec describe planned work, not a completed runtime environment. The source spec was created on 2026-05-24 and last verified on 2026-07-13.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/208>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDPi4UA`
- **Issue number:** 208
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-208.json`
- **Raw SHA-256:** `70039bbf70d4e8abf0ac7e2c7536e274030b01a9d1c02479a46238d0e07c83ce`
- **Migration cutover:** Pending — record the immutable merged cutover commit before deleting the GitHub issue.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-24T18:51:59Z`
- **Updated:** `2026-05-24T18:51:59Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:spec`, `status:backlog`
- **Assignees:** None
- **Milestone:** None
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The issue points to `docs/specs/2026-05-24-page-order-detection.md` as its source spec.
- The issue requests `pd_book_tools.page_order.detect_out_of_order_pages()` with three-signal voting and `SwapProposal` output. The current spec instead names `pdomain_book_tools.page_order`, so the historical API spelling requires reconciliation.
- The spec assigns filename sequence, OCR-extracted page number, and perceptual-hash visual similarity as the proposed signals.
- The spec makes pairwise swaps a V1 goal and excludes multi-page cycles, duplex or recto-verso detection, automatic application, and downstream router integration.
- The spec requires CPU operation, deterministic hashing, graceful degradation when images or OCR are unavailable, and a pure detector when page image arrays are already loaded.
- The 2026-07-13 adversarial review found no implementation. It required alignment with current `Page` fields and normalized role labels, rejected visual pair similarity as a swap vote without a validated positional model, and called for reconciled confidence tiers and numbering-gap or front-matter rules.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **The original draft does not match current model contracts.** Its API and signal assumptions need an evidence-backed revision before implementation.
2. **The proposed confidence model lacks validation.** No labelled corpus establishes precision, recall, thresholds, or safe high-confidence behavior.

## Defects to fix

1. Reconcile the requested API name and data model with current `pdomain_book_tools` types.
2. Resolve the accepted review findings before treating the original three-signal design as implementable.
3. Define page-number gaps, front matter, arbitrary moves, and cycle behavior precisely.
4. Establish evaluation evidence for confidence tiers and thresholds.

## Next steps

1. Revise the source spec against current `Page`, OCR role, and image-cache behavior.
2. Decide whether a validated positional visual model replaces the rejected pair-similarity vote.
3. Resolve the three open questions about incremental merging, hashing dependencies, and thumbnail ownership.
4. Then execute child tasks #211 through #215 in dependency order.

## What is NOT broken (to scope the fix)

- The issue does not report a regression in an existing page-order API.
- The source spec explicitly leaves swap application and the FastAPI route to downstream consumers.

## Relationships and material comments

- Child work is tracked by #211, #212, #213, #214, and #215. The GitHub API export does not encode them as sub-issues; their bodies each say `Tracks: #208`.
- The timeline references commit `15f67f06c467967ffc86ea9ce8c91de39190002e` on 2026-05-24 at 18:53:37 UTC. The same commit appears in #211 and #215, linking the spec back-reference and task decomposition; this is planning provenance, not implementation evidence.
- No comments were present in the export.

## Repository evidence

- The governed source spec remains active and labels its own status as Draft.
- Its adversarial-review section says no implementation was found as of 2026-07-13.
- The spec preserves accepted corrections and unresolved ideas in `docs/context/intent-map.md` rather than claiming completion.

## Remaining work

- Spec revision, owner decisions, signal implementation, aggregation, tests, downstream route integration, and UI integration remain open.

## Resolution

_Open._ The GitHub issue is open, the source spec is still a draft, and the current evidence does not support completion.
