---
Status: retired
Owner: CT
Created: 2026-07-21
Last verified: 2026-09-19
Kind: issue
Level: I1
---

# drop-cap path forces is_normalized=True and unit-space thresholds

## Agent Index

- **Kind:** issue
- **Status:** retired
- **Level:** I1
- **Last verified:** 2026-09-19
- **Resolution:** Resolved
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

**Resolved (2026-09-19).** Triage confirmed against the current code before
any change: `_MAX_INDENT_DELTA = 0.10` (unit-space) was added directly to a
raw bbox `minX` at what was then dropcap.py:299, and `is_normalized=True` was
hardcoded at what were then lines 454 and 672 — exactly as filed.

1. **More than three constants were affected.** Beyond the named
   `_MAX_INDENT_DELTA`, seven more unit-space literals in
   `pdomain_book_tools/ocr/dropcap.py` were compared against, or added to, raw
   bbox coordinates without domain scaling: `_MIN_INDENT_DELTA`,
   `_MULTI_LINE_INDENT_TOLERANCE`, `_compute_indent_signature`'s
   `body_left_tolerance` (`0.02`) and fallback `standard_indent` (`0.03`),
   `_geometric_gap_candidates`'s `0.005` gap whisker, `_scan_dropcap_cc`'s
   `0.02` pad-y floor and `1.0` page-bottom clamp, and
   `_next_word_attached_to_drop_cap`'s `0.04` max-gap floor. All eight now
   scale by `metrics.coord_w` / `metrics.coord_h` — the same convention
   `reorganize_page_utils.py` already uses at its own `0.08 * coord_width`
   call sites, and the one `dropcap.py` itself already used at its
   `median_h_px = median_word_h * H if metrics.coord_h <= 2.0 else
   median_word_h` line. `_compute_indent_signature` and
   `_geometric_gap_candidates` gained a `metrics: PageMetrics` parameter to
   carry the scale.
2. **A second, related bug in the same function had to be fixed for the
   pixel path to actually reach recovery, not just pass the trigger.**
   `_scan_dropcap_cc`'s crop math (`x1 = int(candidate.gap_minX * W)`, …)
   unconditionally treated its candidate coordinates as normalised `[0, 1]`
   fractions before multiplying by the image's pixel width/height. On a
   pixel-domain page, `candidate.gap_minX` is already a raw pixel value, so
   this produced crop bounds far outside the image and the CC scan always
   returned `None` — a second silent-non-detection failure, one step past
   the one this issue named. Fixed with the same `metrics.coord_w <= 2.0` /
   `metrics.coord_h <= 2.0` domain check already used for `median_h_px`.
3. **`is_normalized` is now derived, never asserted.** `_scan_dropcap_cc`'s
   return value is derived from `metrics.coord_w`/`coord_h`, and converted
   back into the page's own coordinate domain before returning (previously
   it returned a normalised `[0, 1]` fraction unconditionally, which would
   have produced a cap `Word` in a different coordinate domain than every
   other `Word` on a pixel-domain page). The union at the former line 672
   now raises `ValueError` if the two boxes it's unioning disagree on
   `is_normalized` (per this repo's "fail explicitly on mismatch" rule)
   instead of silently forcing `True`, and otherwise uses the existing
   word's own `is_normalized` flag.
4. **Pixel-domain test.** `tests/ocr/test_dropcap.py` had no test exercising
   the pixel path. Added
   `test_filial_duty_cursive_cap_O_recovered_pixel_domain`, which
   deep-rewrites the `chapter-head-filial-duty` DocTR-normalized fixture's
   bounding boxes into pixel-domain coordinates (mimicking
   `Document._tesseract_bbox`'s output) before running it through the same
   `Document.from_dict` → `refine_bounding_boxes` → `reorganize_page` path
   the existing normalized-domain test uses, and asserts the same drop-cap
   recovery. Confirmed failing (0 drop caps recovered, no error — the
   silent-non-detection failure mode this issue describes) against the
   pre-fix code, and passing after the fix.
   `test_credulities_cursive_cap_S_recovered_pixel_domain` was tried first
   using the `chapter-head-credulities` fixture (same as the existing
   normalized test of that name), but that fixture's geometric-trigger
   margin turns out to be razor-thin even in the original normalized
   domain (~0.0001 of page width) — sub-pixel numerical drift from the
   normalized-to-pixel round-trip flips it either way regardless of the
   domain-scaling fix's correctness, so it was dropped in favor of
   `chapter-head-filial-duty`, which has a comfortable margin in both
   domains. The existing normalized-domain tests
   (`test_credulities_cursive_cap_S_recovered`,
   `test_filial_duty_cursive_cap_O_recovered`,
   `test_footnotes_stacked_cursive_cap_unrecovered`,
   `test_body_page_no_false_positive`,
   `test_known_drop_cap_fixture_keeps_cap_as_separate_word`) all still pass
   unchanged, proving the fix doesn't regress the already-working path.

Resolved in commit message
`fix(ocr): scale dropcap coordinate-domain constants and derive is_normalized`.
