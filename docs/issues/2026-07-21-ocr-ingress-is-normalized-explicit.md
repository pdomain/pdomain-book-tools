---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# DocTR and Tesseract OCR ingress omit explicit is_normalized flags

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** Medium — coordinate inference at engine boundary
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** changing document.py OCR adapters or BoundingBox factories
- **Search terms:** is_normalized, from_nested_float, from_ltwh, document.py OCR
- **Relates to:** [plan C1 / S6](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** C1 / S6

## Summary

DocTR builds boxes via `from_nested_float(...)` and Tesseract via `from_ltwh(...)` without explicit `is_normalized`. Inference usually works but tiny pixel boxes wholly in [0,1] can be mislabeled. Conflicts with project rule to preserve coordinate systems explicitly.

## Impact

- Latent mis-label of coordinate domain on edge geometry.
- Amplifies reorganize domain bugs when flags are wrong at creation.

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

- [plan C1 / S6](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)

### 1. Decisive observation

```bash
rg -n 'from_nested_float|from_ltwh|is_normalized' pdomain_book_tools/ocr/document.py | head -40
```

DocTR path ~554–566 and Tesseract ~917–924 omit explicit `is_normalized`.
`BoundingBox._build` infers when the flag is omitted.

## Root-cause hypotheses

1. **(Most likely) Historical convenience before explicit flags were required** — Fits age of adapters vs later geometry rules.

## Defects to fix

1. **DocTR → is_normalized=True** always.
2. **Tesseract → is_normalized=False** always.
3. **Tests** — assert flags on synthetic engine outputs.

## Next steps

1. Set flags at both ingress sites; add unit asserts.

## What is NOT broken

- Typical DocTR [0,1] and large Tesseract pixels still infer correctly today.
- Downstream merge/union fail-closed when flags disagree.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
