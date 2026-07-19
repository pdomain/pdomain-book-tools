---
Status: active
Owner: CT
Created: 2026-05-24
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Add the OCR page-number page-order signal

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — printed page numbers cannot yet contribute to swap proposals
- **Affected version:** Draft page-order design dated 2026-05-24
- **Read when:** extracting printed page numbers from OCR for page-order analysis
- **Search terms:** OCR page number, arabic, roman, footer, header, issue 213
- **Relates to:** [Page-order detection spec](../specs/2026-05-24-page-order-detection.md), [parent issue #208](2026-05-24-gh-208-spec-page-order-detection.md)

## Summary

This open task reads pre-extracted OCR text, parses Arabic and Roman page numbers, and reports sequence anomalies. It must return per-page signal results and include unit tests.

## Impact

- Printed numbering can corroborate filename-based page-order anomalies after OCR and reorganization.
- Incorrect front-matter or gap handling could create false swap proposals even when extraction succeeds.

## Environment / versions

The task targets the draft 2026-05-24 page-order spec. No runtime, package version, or operating system appears in the export.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/213>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDPi9Ow`
- **Issue number:** 213
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-213.json`
- **Raw SHA-256:** `26fd772c15d27c6148907335d1a8e39a928cb55de5523db206ad880ce2a59c25`
- **Migration cutover:** Pending — record the immutable merged cutover commit before deleting the GitHub issue.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-24T18:52:32Z`
- **Updated:** `2026-05-24T18:52:32Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:feature`, `effort:M`, `model:sonnet`, `model-effort:medium`, `status:backlog`
- **Assignees:** None
- **Milestone:** `spec: 2026-05-24-page-order-detection (#208)` (open milestone #15; no due date; description names the source spec and spec issue #208)
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The body cites the OCR page-number subsection of spec section 7.2 and states `Tracks: #208`.
- It explicitly requests Arabic and Roman page-number parsing from pre-extracted OCR text.
- The source spec currently describes bare integers in header or footer blocks, within the plausible range `1` through `len(pages) * 2`. It does not specify Roman parsing, so the issue adds a material requirement that the spec must reconcile.
- The source spec review requires normalized page-role labels and explicit handling for numbering gaps and front matter.
- The test plan requires pages with no OCR blocks to omit this signal without crashing.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **No OCR numbering signal exists.** The detector cannot compare printed numbers with page position.
2. **The extraction contract is inconsistent.** The issue includes Roman numerals while the draft algorithm only defines bare integers.

## Defects to fix

1. Reconcile Arabic and Roman parsing with the source spec.
2. Read current normalized header and footer roles from the current OCR model.
3. Define plausible ranges, gaps, front matter, ambiguity, missing OCR, and multiple candidates.
4. Return the agreed signal-result type with positive and negative tests.

## Next steps

1. Resolve the parent spec's numbering and role-label corrections.
2. Write tests for Arabic, Roman, absent, ambiguous, and anomalous page numbers.
3. Implement the signal against current OCR entities and feed it to task #215.

## What is NOT broken (to scope the fix)

- This task does not run OCR; it consumes text already stored on pages.
- Pages without OCR must remain valid inputs and simply lack this signal.

## Relationships and material comments

- This task tracks #208, depends on the shared types in #211, and feeds aggregation task #215.
- No comments were present in the export.

## Repository evidence

- The source spec preserves the OCR signal as planned work, while its review records required model and numbering corrections.
- No implementation or test result is cited by the export.

## Remaining work

- Parsing policy, role selection, anomaly semantics, implementation, and tests remain open.

## Resolution

_Open._ The task remains open, and the issue/spec discrepancy about Roman page numbers is unresolved.
