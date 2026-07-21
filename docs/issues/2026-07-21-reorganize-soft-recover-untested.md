---
Status: retired
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I2
---

# soft word-recover path never runs in default CI

## Agent Index

- **Kind:** issue
- **Status:** retired
- **Level:** I2
- **Last verified:** 2026-07-21
- **Resolution:** Resolved
- **Severity:** High — untested production soft-recover path (CI-blind)
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** changing reconcile_dropped_words or PD_OCR_REORGANIZE_STRICT behavior
- **Search terms:** PD_OCR_REORGANIZE_STRICT, soft recover, build_recovered_words_block, recovered role
- **Relates to:** [plan A3 / S2](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** A3 / S2

## Summary

Production reorganize default is non-strict: warn, append a `recovered` block, continue. Reconcile tests force `PD_OCR_REORGANIZE_STRICT=1`. The soft path (`reorganize_page_utils` ~973–989) has no CI coverage. Empty-bbox words are filtered before soft recover; any empty-bbox asserts are documentation of that filter, not a separate “recover failure” product path.

## Impact

- Users hit a code path CI never executes.
- Regressions in soft recover ship green.
- Empty-bbox cases are largely filtered before soft recover (`_meaningful_words` / `find_dropped_words`); treat empty-bbox work as document/assert of intentional filter, not a proven permanent-loss path for real drops.

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

- [plan A3 / S2](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)

### 1. Decisive check — tests force strict

```bash
rg -n 'PD_OCR_REORGANIZE_STRICT' tests/ocr/test_reconcile_dropped_words.py
```

Expected: tests set `PD_OCR_REORGANIZE_STRICT=1` (~84, ~118). No case leaves it unset for soft recover.

### 2. Soft path code

Non-strict branch in `reorganize_page_utils.py` ~973–989: stderr warning +
`build_recovered_words_block`. htmlcov marks this branch missing/partial.

## Root-cause hypotheses

1. **(Most likely) Strict-first testing never added the soft counterpart** — Matches test file structure; no alternate non-strict cases found.

## Defects to fix

1. **Non-strict recover test** — forced drop → recovered role, stderr warning, words on page.
2. **Empty-bbox documentation test** — assert intentional filter / documented behavior for bbox-less words (do not invent a “warn then permanent loss” product path unless code is shown to reach it).

## Next steps

1. Add tests with STRICT unset under default pytest markers (`not slow`).
2. Pair with early-return fix (A2) so soft path is reachable from all exits.

## What is NOT broken

- Strict-mode drop detection unit tests are present and useful.
- Default production non-strict policy is intentional; this issue is coverage, not the policy choice.

## Resolution

**Resolved (2026-07-21).** Soft recover covered without STRICT env: recovered role, stderr warning, words on page; empty-bbox filter asserted. Tests: `test_reorganize_early_return_and_soft_recover.py`.
