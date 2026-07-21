---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# drop-cap path forces is_normalized=True and unit-space thresholds

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** Medium — pixel OCR trees get wrong drop-cap geometry
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** editing ocr/dropcap.py or stitching drop caps in reorganize
- **Search terms:** dropcap is_normalized, CC bbox, stitch drop cap pixel
- **Relates to:** [plan C2 / S6](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** C2 / S6

## Summary

Drop-cap CC and stitch paths write boxes with forced `is_normalized=True` and use unit-space indent thresholds. On pixel/Tesseract pages, geometric trigger thresholds (~0.025 unit-space) typically make the path **silently non-detect first**; mixed-flag or nonsense boxes apply only if the path is still entered. Fixtures today are DocTR-normalized, so the gap is under-tested.

## Impact

- Tesseract + drop-cap primarily fails to recover (silent non-detection) under unit thresholds on pixel pages.
- If the path still runs, mixed-norm / forced-True boxes remain a secondary risk.
- Iteration C work on the same module should not inherit this trap.

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

- [plan C2 / S6](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)

### 1. Decisive observation

```bash
rg -n 'is_normalized=True|0\.025|metrics.coord' pdomain_book_tools/ocr/dropcap.py | head -30
rg -n 'pixel|is_normalized|Tesseract' tests/ocr/test_dropcap.py || true
```

Thresholds ~81–95; CC ~444–454 and stitch ~667–672 force True. No pixel-domain
dropcap tests.

## Root-cause hypotheses

1. **(Most likely) Written only against DocTR fixtures** — Matches fixture corpus.

## Defects to fix

1. **Derive flag** from page content / metrics; never force True on pixel trees.
2. **Scale thresholds** by coord domain.
3. **Pixel unit page** in tests.

## Next steps

1. Add pixel synthetic page test that fails today.
2. Fix dropcap domain handling.

## What is NOT broken

- Normalized DocTR drop-cap happy paths (preface fixture) still work.
- Drop-cap A/B algorithms themselves are shipped; this is domain correctness.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
