---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# table structure TABLE/CELL grid layer (spec 10) not implemented

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** Medium — layout table role only; no structure serialization
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** starting work on I1 (after E) or reading ../specs/10-table-structure.md
- **Search terms:** BlockCategory TABLE CELL, spec 10, TATR, table structure
- **Relates to:** [plan I1 (after E)](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** I1 (after E)

## Summary

BlockCategory is BLOCK|PARAGRAPH|LINE only. No row/col/span fields or TATR step. Layout RegionType.table / role exist. Roadmap "table detection complete" must not be read as structure complete. Blocked on owner decisions for fallbacks. Tracked for plan Theme G–I after decision pack.

## Impact

- Consumers cannot serialize TABLE/CELL grid fields through the page model.
- Layout `RegionType.table` / role tagging exists; **structure** does not.
- PGDP table **syntax** export remains out of scope (roadmap).

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

- [plan I1 (after E)](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)
- [spec](../specs/10-table-structure.md)

### 1. Decisive absence check

```bash
rg -n 'class BlockCategory|TABLE|CELL' pdomain_book_tools/ocr/block.py | head -20
rg -n 'rowspan|colspan|TATR' pdomain_book_tools || true
```

Expected: `BlockCategory` is BLOCK|PARAGRAPH|LINE only; no grid fields. Blocked on Theme E table decisions.

## Root-cause hypotheses

1. **(Most likely) Design complete, implementation intentionally not started** — Matches adversarial "no implementation" and roadmap omission.

## Defects to fix

1. **Implement per revised spec** after Theme E — see I1 (after E).
2. **Do not code from unrevised post-adversarial drafts** without folding review corrections.

## Next steps

1. Keep blocked until Theme E answers land.
2. Revise spec if adversarial redesign is accepted, then implement.

## What is NOT broken

- Layout detection can still emit `table` **regions** / roles.
- Roadmap “table detection complete” means region detection, not structure.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
