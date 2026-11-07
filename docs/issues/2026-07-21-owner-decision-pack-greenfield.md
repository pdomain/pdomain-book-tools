---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-11-07
Kind: issue
Level: I1
---

# greenfield specs blocked on unresolved owner decisions

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-11-07
- **Resolution:** Open
- **Severity:** Medium — implementation thrash risk without decision pack
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** starting page-order, scannos, hyphen, reference-lines, char-bbox, or table structure
- **Search terms:** owner decision, Q-RL, greenfield blocked, Theme E
- **Relates to:** [plan E / S11](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** E / S11

## Summary

Active specs 06b/c, 09, 10, page-order, scannos, hyphen still need owner decisions (Q-RL-*, char-bbox polarity, table fallbacks, page-order redesign, scannos IDs, hyphen packaging). Implementing from unrevised drafts re-litigates prior adversarial reviews. Also pick overrides for public-API default, geometry dual-gate, GPU CI strategy, coverage ratchet.

### Page-order filename source (decided 2026-11-07)

The page-order filename signal needs each page's source filename. `Page.name`
exists but defaults to `None`, and no ingestion code sets it.
`Document.source_identifier` holds one value for the whole document, and it is
empty for a multi-image document. Pick one:

1. Ingestion sets `Page.name` to the source filename. Every caller gets the
   signal for free, but this changes what ingestion writes to each page.
2. `detect_out_of_order_pages` takes an optional list of filenames in page
   order. Ingestion stays as it is, but each caller must supply the list.

**Answer: option 2.** The `page_order` stage in prep-for-pgdp runs before OCR,
so no ingested `Page` exists when it runs. See the 2026-11-07 entry in
[decisions](../context/decisions.md). The spec records this as Q-PO-4, and
issue [gh-212](2026-05-24-gh-212-page-order-filename-signal.md) is no longer
blocked on it.

## Impact

- Cannot safely start Themes G–I.
- Wasted implementation if answers reverse design.

## Environment / versions

```text
pdomain-book-tools 0.21.x-dev @ a7bff12
Repo: pdomain/pdomain-book-tools (master)
Found by: 2026-07-21 deep code review (9 specialists + 3 adversarial challenges)
Plan: docs/plans/2026-07-21-continued-work-from-deep-review.md
Findings: docs/research/2026-07-21-deep-code-review-findings.md
```

## Evidence

Related governed docs:

- [plan E / S11](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)
- [intent-map](../context/intent-map.md)

`docs/context/intent-map.md` Needs owner decision section.
Plan Theme E table.
Specs remain active/Draft with adversarial "no implementation" notes.

## Root-cause hypotheses

1. **(Most likely) Decisions deferred while core OCR shipped** — Matches history.

## Defects to fix

1. **Decision workshop** — answer or date-defer each Theme E row with owner.
2. **Update intent-map** after decisions.

## Next steps

1. Schedule S11 workshop; produce dated answers in intent-map/decisions.
2. After decisions, **unblock or update the existing** G–I issue trackers (already filed under `docs/issues/`); do not refile duplicates.

## What is NOT broken

- Theme A–D and F1 can proceed without this pack.
- Specs remain valid design records until revised.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
