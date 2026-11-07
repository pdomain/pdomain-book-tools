---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-11-07
Kind: issue
Level: I2
---

# BoundingBox.center and contains_point weaken is_normalized discipline

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I2
- **Last verified:** 2026-11-07
- **Resolution:** Open
- **Severity:** Medium — silent flag loss / mixed-space contains
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** editing BoundingBox coordinate semantics (now in pdomain-book-contracts)
- **Search terms:** BoundingBox.center, contains_point, is_normalized, unit-square pixel
- **Relates to:** [plan C3 / S7](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** C3 / S7

## Summary

`BoundingBox.center` rebuilds `Point(x,y)` without the box flag (re-infers). `contains_point` does not require matching normalization unlike union/intersect. Unit-square pixel boxes can mislabel centers. Low call-site count but violates project rules.

## Impact

- Subtle coordinate bugs if callers use center/contains across domains.
- Inconsistent with fail-closed merge APIs.

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

- [plan C3 / S7](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)

### 1. Decisive observation

```bash
rg -n 'def center|def contains_point|_require_same_coords' \
  .venv/lib/python3.13/site-packages/pdomain_book_contracts/geometry/bounding_box.py
```

`BoundingBox` moved to `pdomain-book-contracts` (0.2.0 installed);
`pdomain_book_tools/geometry/bounding_box.py` only re-exports it. In that
package, `center` (~247) builds `Point` without the box flag, and
`contains_point` (~540) has no domain check. Union and intersect use
`_require_same_coords` (~552+). The fix therefore lands in the contracts repo.

## Root-cause hypotheses

1. **(Most likely) Older helpers never updated when fail-closed merge landed** — Likely.

## Defects to fix

1. **center** — pass `is_normalized=self.is_normalized`.
2. **contains_point** — fail-closed on mismatch.
3. **Tests** — unit-square pixel boxes; mixed-space contains raises.

## Next steps

1. Fix center + contains_point; add unit tests.
2. Audit scale/four-point helpers for the same class of bug.

## What is NOT broken

- union/intersect/iou fail-closed paths are tested and correct.
- center is rarely used outside tests today (small blast radius).

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
