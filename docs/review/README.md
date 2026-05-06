# Code Review: pd-book-tools

Full library review conducted May 2026 using 7 parallel agents, one per module group.
~130 issues documented across 4 files.

## Files

| File | Contents |
|------|----------|
| [bugs-high.md](bugs-high.md) | 21 critical bugs — data corruption, definite crashes, wrong output |
| [bugs-medium.md](bugs-medium.md) | 30 medium-severity bugs — incorrect behavior on realistic inputs |
| [bugs-low.md](bugs-low.md) | 40 low-severity bugs — edge-case failures, misleading errors, minor correctness |
| [refactors.md](refactors.md) | 30 refactor opportunities — structural, design, and API improvements |

## Highest-priority fixes

Start here before anything else:

1. **H-01** `encoding.py` — PNG channel swap (all image previews have wrong colors)
2. **H-02** `pgdp_results.py` — unescaped `.` in 13 diacritic regexes (silent data corruption)
3. **H-03** `ipynb_widgets.py` — malformed HTML output (missing tags)
4. **H-04** `page.py` — `recompute_bounding_box` undefined → `AttributeError` on all editing ops
5. **H-05** `bounding_box.py` — `_vertical_crop` coordinate-system flip for pixel-space boxes
6. **H-06** `word.py` — `crop_bottom`/`crop_top` can store `None` as `bounding_box`
7. **H-07** `block.py` — `mean_ocr_confidence` crashes after any `Word.split()`
8. **H-08** `block.py` — `Block.from_dict` calls `BoundingBox.from_dict(None)`
9. **H-12** `document.py` — DocTR `original_text` indexes by character, not page
10. **H-14/15/16** `threshold.py` — Cupy Otsu off-by-one, crash on uniform images, wrong return type

## Loop progress

Durable state for the `/loop` bug-fix run, so a fresh session can resume without
remembering prior turns. Update this when an iteration completes (after the
`docs(review): mark H-XX fixed` commit).

**Fixed so far:**

- H-01 `encoding.py` BGR/RGB swap — fix `702d402`, doc mark `b4f1140`
- H-02 `pgdp_results.py` unescaped diacritic `.` regexes — fix `6b1ff5b`, doc mark `466d1df`
- H-03 `ipynb_widgets.py` malformed HTML (operator-precedence) — fix `1f26286`, doc mark `e0da955`
- H-04 `page.py` `Page.recompute_bounding_box` was reported missing but was
  actually implemented in commit `2248366` (April 2025); review was stale —
  regression-locked via test in fix `bd4ece9`, doc mark `24b97f0`
- H-05 `bounding_box.py` `_vertical_crop` discarded `original_is_normalized`
  and always normalized output — fix `2327d2f`, doc mark `<pending>`
- H-06 `word.py` `crop_bottom` / `crop_top` overwrote `self.bounding_box`
  with `None` on the blank-ROI warning path — fix `645c825`, doc mark `<pending>`
- H-07 `block.py` `Block.mean_ocr_confidence` raised `TypeError` because
  `ocr_confidence_scores()` can contain `None` after any `Word.split()` —
  fix `42da1ac`, doc mark `<pending>`
- H-08 `block.py` `Block.from_dict` called `BoundingBox.from_dict(None)`
  when deserializing a block whose `bounding_box` was serialized as JSON
  `null` — fix `3163feb`, doc mark `<pending>`. Note: `Page.from_dict`
  already had the equivalent guard, so the review's parenthetical claim
  about `Page.from_dict` was partly stale.
- H-12 `document.py` `from_doctr_result` passed `doctr_result.render()`
  (a single `str`) as `original_text`, which `from_doctr_output` then
  indexed by `page_idx` — yielding one character per page since `str` is
  a `Sequence[str]`. Existing test mocked `render.return_value` as a
  list, masking the bug. Fixed to pass
  `[page.render() for page in doctr_result.pages]`. — fix `06f22c3`,
  doc mark `<pending>`
- H-14 `image_processing/cupy_processing/threshold.py` `otsu_binary_thresh`
  defined `weight2 = weight1[-1] - weight1` (exclusive suffix sum), which
  combined with `weight2[1:]` / `mean2[1:]` in the variance expression
  excluded bin `k+1` from both classes and biased the threshold high on
  realistic bimodal images. Switched to
  `weight2 = cp.flip(cp.cumsum(cp.flip(hist)))` (inclusive suffix sum,
  matching `skimage.filters.threshold_otsu`). Verified live with cupy and
  skimage: pre-fix threshold ~0.55, fixed and skimage both ~0.42 on
  overlapping Gaussian clusters. — fix `2e1b2be`, doc mark `<pending>`
- H-15 `image_processing/cupy_processing/threshold.py` `otsu_binary_thresh`
  on uniform-valued images. The reviewed crash (`ValueError: max must be
  larger than min` from `cp.histogram(..., range=(min, max))`) no longer
  reproduces on cupy 14.x — the histogram call now silently produces a
  bogus single-bin distribution over an arbitrary [-0.5, 0.5]-style edge
  span, so `cp.argmax` of an all-zero between-class variance returns 0
  and the function emits a meaningless threshold (~`-0.498`) and an
  all-1.0 mask for an all-zero input. Added an early return when
  `min_val == max_val` that emits an all-zero binary mask, matching
  skimage/cv2 semantics (uniform image's Otsu threshold is the uniform
  value itself; strict-`>` binarization is therefore all-zero). Review
  was partly stale on the symptom but the underlying defect (no uniform
  guard) was real. — fix `92d7c32`, doc mark `<pending>`

**Next pick:** H-16 — `pd_book_tools/image_processing/cupy_processing/threshold.py`
lines 49–52 (Cupy `otsu_binary_thresh` returns `float32` 0.0/1.0 while
the cv2 version returns `uint8` 0/255 — pipelines switching backends
get a silently incompatible dtype/range). Last of the threshold.py
cluster, same file as H-14/H-15 so the regression-test infrastructure
is already in place. H-13 (`doctr_support.py` `Path.exists` unbound
class method) remains deferred per the "Highest-priority fixes"
ordering — README top-10 jumps from H-12 to H-14/15/16.

**Workflow per iteration** (one bug per commit, no push):

1. Verify bug still present in the production code.
2. Write a failing test that reproduces the symptom from the review doc.
3. Implement minimal fix; re-run test; run module test suite for regressions.
4. Commit `fix(<module>): <one-line>` referencing the review ID in the body.
5. Edit `docs/review/bugs-*.md`: prepend `[FIXED in <short-sha>]` and wrap the
   heading text in `~~...~~` (matching H-01..H-03 format).
6. Update **Fixed so far** and **Next pick** in this README.
7. Commit `docs(review): mark H-XX fixed`.

## Modules reviewed

- `pd_book_tools/geometry/` — bounding_box.py, point.py
- `pd_book_tools/hf/` — download.py, models.py
- `pd_book_tools/image_processing/cv2_processing/` — all 16 source files
- `pd_book_tools/image_processing/cupy_processing/` — all 15 source files
- `pd_book_tools/layout/` — types, detector, registry, geometry, mappings, visualize, adapters
- `pd_book_tools/ocr/` — all 14 source files including ground_truth_matching helpers
- `pd_book_tools/pgdp/` — pgdp_results.py
- `pd_book_tools/utility/` — ipynb_widgets.py, timing.py
- `pyproject.toml` — dependency declarations
