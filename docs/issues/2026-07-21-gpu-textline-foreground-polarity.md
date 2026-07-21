---
Status: retired
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# GPU textline _ensure_foreground polarity diverges from CPU

## Agent Index

- **Kind:** issue
- **Status:** retired
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Resolved
- **Severity:** High — dual-path dewarp binary polarity bug
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** editing textline_dewarp, geometry_correction dewarp, or GPU parity tests
- **Search terms:** _ensure_foreground, textline_dewarp, cupy polarity, text=0 background=255
- **Relates to:** [plan A4 / S3](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** A4 / S3

## Summary

CPU `_ensure_foreground` requires mean < 128 for `{0,255}` binaries before pass-through. GPU accepts any `{0,255}` binary unchanged. Library-standard text=0 / background=255 binaries invert polarity on GPU morphology. Confirmed vs CPU/GPU textline_dewarp modules.

## Impact

- GPU textline dewarp / geometry-correction path can treat paper as ink.
- Default CI never runs cupy tests, so the bug stays green on PRs.
- CPU and GPU results diverge for the same binary input.

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

- [plan A4 / S3](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)

### 1. Decisive observation — CPU vs GPU gate

```bash
rg -n 'mean|_ensure_foreground|0, 255'   pdomain_book_tools/image_processing/cv2_processing/textline_dewarp.py   pdomain_book_tools/image_processing/cupy_processing/textline_dewarp.py
```

CPU (~43–57): `{0,255}` **and** `mean < 128` → pass-through.
GPU (~63–70): any `{0,255}` uint8 returns unchanged (no mean gate).

### 2. Library polarity

Threshold/denoise contract is text=0, background=255. Typical pages have mean ≥ 128
→ CPU re-binarizes; GPU does not.

## Root-cause hypotheses

1. **(Most likely) GPU port omitted the mean check** — Line-for-line comparison shows only the mean gate missing.
2. **Intentional GPU optimization** — No docstring claims divergence; CPU docstring documents the gate.

## Defects to fix

1. **Match CPU gate on GPU** — require mean < 128 for pass-through of `{0,255}` binaries.
2. **Parity tests** — text=0 and text=255 binaries on both backends.

## Next steps

1. Add CPU-side test that encodes the contract (always runs in CI).
2. Fix GPU implementation; add cupy parity tests (skip without CUDA).

## What is NOT broken

- Other cupy modules with array_equal parity (e.g. denoise) are separate.
- CPU textline path behavior is the reference contract.

## Resolution

**Resolved (2026-07-21).** GPU `_ensure_foreground` mean < 128 gate matches CPU; Otsu empty-class weights fixed so thr does not collapse to 255. CPU always-on + cupy parity tests (skip without CUDA).
