---
Status: retired
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# reorganize band classify uses page pixel dims against normalized boxes

## Agent Index

- **Kind:** issue
- **Status:** retired
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Resolved
- **Severity:** High — wrong header/footer geometry under DocTR-normalized OCR
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** changing reorganize_page_utils classify, bands, or coordinate metrics; before re-baselining layout fixtures
- **Search terms:** _classify_row_block, coord_w, normalized, page_height, split_mixed_content_lines, reorganize domain
- **Relates to:** [plan A1 / S1](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** A1 / S1

## Summary

`_classify_row_block` compares row block boxes to `0.12 * page_height` and `0.88 * page_height` without `coord_w` / `coord_h` adaptation used elsewhere. Under DocTR-normalized geometry, near-top is almost always true and near-bottom almost never. A related opposite-polarity bug: `split_mixed_content_lines` uses a bare Y gap of `0.08` that fails on pixel boxes. Confirmed in the 2026-07-21 deep review adversarial pass.

## Impact

- Header/footer/sidenote role classification can be wrong on the common DocTR path.
- Reading-order and band peels can misfire without a hard error.
- Silent correctness failure; fixtures may still look plausible.

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

- [plan A1 / S1](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)
- [reorganize architecture](../architecture/reorganize-page-pipeline.md)

### 1. Decisive observation — band thresholds vs page dims

```bash
rg -n '0\.12 \* page_height|0\.88 \* page_height|_classify_row_block' pdomain_book_tools/ocr/reorganize_page_utils.py
rg -n 'coord_w|coord_h|_coord_dims_from_words' pdomain_book_tools/ocr/reorganize_page_utils.py | head -20
```

`_classify_row_block` (~4129–4161) multiplies raw `page_height` / `page_width`.
Other steps use `_coord_dims_from_words` / `coord_w` / `coord_h` (~129–145).

### 2. Mixed-line Y gap

```bash
rg -n '0\.08' pdomain_book_tools/ocr/reorganize_page_utils.py
```

`split_mixed_content_lines` (~2192) hardcodes Y gap `0.08` (unit-space).
On pixel OCR this almost never clears the preferred-split guard.

### 3. Adversarial confirmation

Challenger confirmed opposite polarity: band thresholds break on normalized
geometry; bare `0.08` breaks on pixel geometry.

## Root-cause hypotheses

1. **(Most likely) Missing coord-domain helper on late-added classify path** — Fits the pattern that Step E adapted and classify did not; dual-domain unit test would confirm.
2. **Intentional pixel-only API never documented** — Unlikely: architecture claims normalized or pixel; fixtures are DocTR-normalized.

## Defects to fix

1. **Band classify thresholds** — scale top/bottom/side checks by `coord_w`/`coord_h` (or `is_normalized`).
2. **Absolute thresholds** — fix mixed-line Y gap and any other bare unit-space constants used against pixel boxes.
3. **Tests** — dual-domain matrix: same synthetic page normalized `[0,1]` vs pixel `W×H`; identical role outcomes.

## Next steps

1. Add dual-domain unit test that fails on current classify behavior.
2. Centralize domain helper; fix classify and mixed-line thresholds.
3. Do not rewrite layout-regression text baselines until this matrix is green (plan B prerequisite).

## What is NOT broken

- Merge/union/intersect still fail-closed on mixed `is_normalized`.
- Layout unit tests for synthetic reorg helpers are separate from this path.
- Corpus text baselines may still pass while roles are wrong if text order coincidentally matches.

## Resolution

**Resolved (2026-07-21).**

1. `_classify_row_block` thresholds use `_coord_dims_for_block` (`coord_w` /
   `coord_h` from `is_normalized` / max-coordinate heuristic), not raw page
   pixel dims.
2. `split_mixed_content_lines` preferred-split Y gap scales as `0.08 * coord_h`
   (optional `page_height`; call site passes `page.height`).
3. Dual-domain unit matrix in
   `tests/ocr/test_reorganize_coord_domain.py` (normalized vs pixel WxH) is
   green.
4. Reviewed re-baseline of 7 layout-regression text fixtures: blank-line
   spacing only (non-blank content identical) after correct band roles.

Resolved in commit message
`fix(ocr): A1 dual-domain reorganize band thresholds` (2026-07-21).
