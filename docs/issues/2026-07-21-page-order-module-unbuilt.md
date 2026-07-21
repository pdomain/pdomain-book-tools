---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# page-order module specified but not implemented

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** Medium — Stage 11 prep-for-pgdp blocked on missing module
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** starting work on G1 (after E) or reading ../specs/2026-05-24-page-order-detection.md
- **Search terms:** page_order, SwapProposal, detect_out_of_order_pages, #208
- **Relates to:** [plan G1 (after E)](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** G1 (after E)

## Summary

Spec and issue cluster #211–#215 / #208 describe `detect_out_of_order_pages` and `SwapProposal`. No `pdomain_book_tools.page_order` package exists. Blocked on owner redesign (drop unvalidated visual-sim as swap vote). Tracked for plan Theme G–I after decision pack.

## Impact

- **prep-for-pgdp Stage 11** cannot call an in-repo `detect_out_of_order_pages` / `SwapProposal` API.
- App-layer reimplementation risks diverging confidence models across tools.
- Not a runtime regression in current OCR reorganize paths.

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

- [plan G1 (after E)](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)
- [spec](../specs/2026-05-24-page-order-detection.md)

### 1. Decisive absence check

```bash
ls pdomain_book_tools/page_order 2>&1 || true
rg -n 'detect_out_of_order_pages|SwapProposal' pdomain_book_tools || true
```

Expected: no package directory; symbols only in docs/specs.
Blocked on Theme E page-order redesign decisions.

## Root-cause hypotheses

1. **(Most likely) Design complete, implementation intentionally not started** — Matches adversarial "no implementation" and roadmap omission.

## Defects to fix

1. **Implement per revised spec** after Theme E — see G1 (after E).
2. **Do not code from unrevised post-adversarial drafts** without folding review corrections.

## Next steps

1. Keep blocked until Theme E answers land.
2. Revise spec if adversarial redesign is accepted, then implement.

## What is NOT broken

- Page already exposes `page_id` / name and header/footer **roles** usable by a future module.
- This issue tracks missing Stage-11 product surface, not a silent OCR failure.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
