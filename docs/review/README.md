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

**Next pick:** H-04 — `page.py` `recompute_bounding_box` undefined, called from
page.py:752/953/967/998. Define it as
`BoundingBox.union([b.bounding_box for b in self._items if b.bounding_box is not None])`.

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
