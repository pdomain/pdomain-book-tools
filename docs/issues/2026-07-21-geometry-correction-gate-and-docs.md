---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# geometry_correction dual gate and docs disagree; grid map_points unsupported

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** Medium — dual-gate/docs mismatch; false keypoint remap claims
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** editing geometry_correction pipeline, transforms, or usage docs
- **Search terms:** geometry_correction dual gate, map_points grid, UVDoc skip, SuppliedPageSide
- **Relates to:** [plan C4 / S7](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** C4 / S7

## Summary

Regime only selects dewarp backend name; curvature `recommended == "dewarp"` enables dewarp. Docs often read as if regime alone gates expensive dewarp. Grid transforms raise on `map_points` while usage docs advertise keypoint mapping. Missing backend leaves `dewarp_res is None` (omit). conf=0 from textline dewarp still applies an identity transform (no-op success), not a skip. Usage backend table already marks `gutter_shadow` default; only the page-side **hint** paragraph wrongly names `SuppliedPageSide`.

## Impact

- Callers may believe dewarp ran, keypoints remapped, or a non-identity warp applied when the result was omit or identity no-op.
- OCR boxes are not remapped after image correction → frame mismatch if assumed.

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

- [plan C4 / S7](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)
- [geometry-correction architecture](../architecture/geometry-correction.md)
- [geometry-correction usage](../usage/geometry-correction.md)

### 1. Decisive observation

```bash
rg -n 'recommended|dewarp|_select_dewarp|map_points|SuppliedPageSide|gutter_shadow' \
  pdomain_book_tools/geometry_correction/pipeline.py \
  pdomain_book_tools/geometry_correction/transforms.py \
  docs/usage/geometry-correction.md | head -40
```

Pipeline ~68–101: regime names backend; curvature enables. Grid `map_points`
NotImplemented ~154–167. Usage: keypoint remap claims; hint paragraph ~97
wrongly cites SuppliedPageSide while table lists gutter_shadow default.

## Root-cause hypotheses

1. **(Most likely) Docs written for intended design; code kept dual signals** — Fits residual mismatch pattern.

## Defects to fix

1. **Align docs and code** on dual gate (or change code to match docs).
2. **map_points** — implement for grid or stop advertising.
3. **Surface outcomes** — missing backend omit vs conf=0 identity no-op must both be explicit to callers (do not lump as “skip”).
4. **Usage hint paragraph** — fix SuppliedPageSide wording; keep table’s gutter_shadow default.

## Next steps

1. Owner pick: docs-only vs code change for gate (plan Theme E override).
2. Until then, fix false claims in usage/architecture.

## What is NOT broken

- Image-only pipeline still runs deskew/dewarp backends when gates pass.
- Protocol/registry structure is sound.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
