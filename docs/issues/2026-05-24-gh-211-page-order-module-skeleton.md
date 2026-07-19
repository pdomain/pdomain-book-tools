---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Add the page-order module skeleton and proposal types

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — the shared page-order API and result types do not exist
- **Affected version:** Draft page-order design dated 2026-05-24
- **Read when:** creating the page-order package or defining its public result types
- **Search terms:** page_order, SwapProposal, signal result, issue 211, issue 208
- **Relates to:** [Page-order detection spec](../specs/2026-05-24-page-order-detection.md), [parent issue #208](2026-05-24-gh-208-spec-page-order-detection.md)

## Summary

This open task creates the page-order package skeleton, `SwapProposal`, and signal-result types. It implements the file layout and result shape from issue #208, subject to the source spec's accepted review corrections.

## Impact

- Signal tasks #212 through #214 and aggregation task #215 need shared types and package boundaries.
- A premature public shape could ripple into the downstream service because the spec says the route serializes results directly.

## Environment / versions

The task targets the draft 2026-05-24 page-order spec. No runtime, package version, or operating system appears in the export.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/211>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDPi88w`
- **Issue number:** 211
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-211.json`
- **Raw SHA-256:** `d4438e3c827496906457de3592df0e6bfdef493c2a3687a607fd7d66943b9e02`
- **Migration cutover:** `6842ec6b11c06c9b987b384b4abf7e9dc4699014` — merged migration cutover on `master`.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-24T18:52:30Z`
- **Updated:** `2026-05-24T18:52:30Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:feature`, `effort:M`, `model:sonnet`, `model-effort:medium`, `status:backlog`
- **Assignees:** None
- **Milestone:** `spec: 2026-05-24-page-order-detection (#208)` (open milestone #15; no due date; description names the source spec and spec issue #208)
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The body cites spec section 7.1 and section 6 and states `Tracks: #208`.
- It requests `pd_book_tools/page_order/__init__.py`, an `_page_order_impl/` subpackage, a `SwapProposal` dataclass, `high | medium | low` confidence, a typed signals dictionary, and signal-result types.
- The current spec instead proposes `pdomain_book_tools/page_order.py` plus a sibling `_page_order_impl/` directory and describes `signals` values as intentionally untyped `object`. These differences require resolution.
- The spec review requires the proposal shape to align with current `Page.name`, `page_index`, and UUID `page_id` before implementation.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **Shared page-order types have not been established.** Dependent signal and aggregation tasks lack a stable contract.
2. **The issue and spec disagree on layout and typing.** Implementing either version without reconciliation risks an incompatible public API.

## Defects to fix

1. Reconcile the package layout and the historical `pd_book_tools` spelling with the current package name.
2. Define `SwapProposal` fields against current `Page` identifiers.
3. Decide whether signal values remain `object` or use explicit typed signal results.

## Next steps

1. Resolve the parent spec corrections and API discrepancies.
2. Add the agreed package skeleton and dataclasses.
3. Add focused construction, typing, and serialization tests before downstream signal work.

## What is NOT broken (to scope the fix)

- This task does not implement signal algorithms, aggregation, or the downstream route.
- The export provides no evidence that a previously shipped public page-order API regressed.

## Relationships and material comments

- This task tracks #208 and shares open milestone #15 with #212 through #215.
- The timeline references commit `15f67f06c467967ffc86ea9ce8c91de39190002e` on 2026-05-24 at 18:53:37 UTC. The same commit appears in #208 and #215 and records the spec back-reference and decomposition into milestone tasks; it does not show implementation.
- No comments were present in the export.

## Repository evidence

- The source spec's implementation plan describes the intended module family, but its review records unresolved contract corrections.
- No implementation result or resolving commit appears in the issue export or source spec.

## Remaining work

- Contract reconciliation, package creation, result types, and tests remain open.

## Resolution

_Open._ The issue is open and no evidence supports treating the module skeleton or public types as implemented.
