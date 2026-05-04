# Roadmap

Forward-looking work in pd-book-tools. Excludes anything that's better
tracked in a consuming-app roadmap (the layout-fine-tune workflow lives
in [`ocr-container/docs/SPEC-layout-training.md`](../../docs/SPEC-layout-training.md)
because it spans pd-ocr-labeler + pd-ocr-trainer; this file holds the
items that belong specifically in the library).

The items below are carried over from the (now-archived) workspace
docs `PLAN-layout-aware-ocr.md` and `TODO-layout-training.md`. The
phases they originally lived in have shipped (see "Done" at the
bottom); only the residuals remain.

## Open — layout consumption

Items where the layout module exists and is wired up, but the
consumption logic could be sharper. None of these block the
fine-tune workflow; they're independently useful and one of them
(per-type confidence) becomes more relevant once a fine-tune lands
because confidences will distribute differently.

### Per-type confidence thresholds

`drop_layout_regions` and `drop_figure_internal_words` use a single
blanket threshold (`DEFAULT_DROP_CONFIDENCE = 0.7`,
`pd_book_tools/ocr/layout_aware_reorg.py:50`). Two known cases where
that's wrong:

- `figure` regions tend to be confidently detected even when slightly
  misframed; trusting them at 0.5 is fine.
- `header` regions, by contrast, are the noisiest — the model
  occasionally tags running headers that aren't really there. Want
  ≥0.7 before dropping their words.

Proposed shape:

```python
DEFAULT_DROP_CONFIDENCE_BY_TYPE: dict[RegionType, float] = {
    RegionType.figure:    0.50,
    RegionType.header:    0.70,
    RegionType.footer:    0.65,
    RegionType.footnote:  0.65,
    RegionType.abandoned: 0.70,
    # …
}
```

Plumbing: extend `drop_layout_regions(confidence_threshold=…)` to
accept either a `float` (current behaviour) or a `dict[RegionType,
float]`. Same for `drop_figure_internal_words`. Backwards
compatible — existing call sites keep working.

Test surface: a fixture page with a low-confidence header that the
new policy keeps but the old policy dropped, and vice versa.

### Decoration-vs-figure post-classification

PP-DocLayout has no `decoration` class; the adapter maps `seal` →
`RegionType.decoration` and falls back to `image` → `figure` for
ornamental woodcuts (chapter headpieces, fleurons). PLAN open
question 3 sketched a heuristic: "if a `figure` is small (<5 % of
page), positioned at top or bottom, and contains no detected text
words, reclassify as `decoration`."

This belongs in `pd_book_tools/layout/geometry.py` as
`postclassify_decoration(layout, page) -> PageLayout` and runs as a
late pass in `Page.reorganize_page` after `tag_words_with_layout`
(so we know which words fall inside the figure region). Cheap; helps
the illustration extractor downstream pick the right
`type=decoration` for `i_<stem>_NN.png` filenames.

Out of scope until the fine-tune lands — once the model has a
first-class `decoration` head, the heuristic becomes a fallback
rather than the primary classifier.

### Multi-column reading order primitives

PLAN open question 4 noted regions arrive "in roughly
left-right-top-down order" but tied/overlapping regions need stable
sort. Today the geometric reorg path handles two-column body via
`expand_row_blocks` heuristics; layout-aware reorg inherits whatever
order the regions arrive in.

Add `pd_book_tools/layout/geometry.py:region_reading_order(regions)`
that takes a `list[LayoutRegion]` and returns them in stable, cluster
-aware reading order (column detection by x-projection, then
top-to-bottom inside each column). Consumers: `associate_captions`
(so caption-finding respects column structure), and any future
multi-column page-level reorg.

PGDP corpus has very few multi-column body pages so this is not
urgent. List for completeness because the primitive is small and
useful elsewhere.

### Detector failure hardening

PLAN open question 6: adapter raises (model missing, OOM, etc.) →
should log and return an empty `PageLayout`; reorg with empty layout
falls back to the existing geometric path.

Today's `registry.get_detector` propagates exceptions from
`PPDocLayoutPlusLDetector.__init__` (which `from_pretrained` can
raise on network errors, missing weights, OOM during model load).
The construction failure leaks to the caller — fine for `pd-ocr-cli`
which prints and exits, but the planned `pd-prep-for-pgdp` batch
mode shouldn't abort a 400-page run because page 117 happens to OOM
the layout model.

Two-step fix:

1. `registry.get_detector(..., on_error="raise" | "log_and_null")`.
   `"log_and_null"` returns the `NullDetector` and logs once. Default
   stays `"raise"` so existing CLI behaviour is unchanged.
2. Per-page `detect()` failures (mid-batch) are already caught by
   `_TimingDetector` — confirm that with a dedicated test.

## Open — image-processing improvements (no model fine-tune needed)

These are independent of the layout fine-tune. Each addresses a
specific reorg-pipeline weakness called out in the archived
`TODO-layout-training.md`.

### Glyph-size analysis for sidenote detection

Today's `detect_geometric_sidenotes` (in
`pd_book_tools/ocr/layout_aware_reorg.py`) uses x-position alone —
finds narrow margin columns by histogram analysis. Real sidenotes
are usually rendered in a smaller font than the body. Add a glyph-
height pass:

- For each candidate sidenote word, estimate median glyph height from
  its OCR bbox plus a horizontal projection on the cropped image.
- Compare against the page's body-text median height.
- Promote to `layout:sidenote` only if the candidate's height is
  ≤80 % of the body median.

Where it goes: `pd_book_tools/ocr/layout_aware_reorg.py`, alongside
`detect_geometric_sidenotes`. Pure image-processing — no new model
weights, no new dependencies.

Helps where the sidenote column overlaps the body's x-range (a
narrow body protrusion that's not a sidenote) or where the body
itself has sidenote-like protrusions.

### Drop-cap glyph recognition for cursive caps

The geometric drop-cap stitcher in `reorganize_page_utils.py` works
on plain block caps (R-style) but fails on cursive caps (S/O/A
glyphs in `chapter-head-credulities`, `chapter-head-filial-duty`,
`footnotes-stacked-with-anchor`). The DocTR recogniser doesn't pick
the cursive S as a letter; it ends up as gibberish or skipped.

Approach: a small image-processing pass that **detects the oversized
initial glyph** (large connected component at the start of the first
body paragraph after a chapter heading) and **stitches its character
into the next OCR word**. The character can be guessed from the
chapter-title text (a chapter starting "STUDIES IN…" likely has an
"S" drop cap) without needing OCR on the glyph.

Where it goes: `pd_book_tools/ocr/dropcap.py` (new module) called
from `Page.reorganize_page` after the geometric drop-cap stitcher
fails to find a hit. Tests against the three known regression
fixtures listed above.

### Multi-column body detection enhancements

Once glyph-size data exists (above), the column-detection in
`expand_row_blocks` can become sidenote-aware: the geometric column
splitter shouldn't break on a sidenote that produces a narrow third
column. Currently rare in the PGDP corpus, so this is a follow-up to
the glyph-size work, not standalone.

## Open — page handling

### Page rotation — already shipped

The PLAN's "open follow-up" on page-rotation detection (sideways
plates, upside-down scans, the Peutinger map fixture) shipped as
`pd_book_tools/ocr/rotation.py`. Documented in
`docs/architecture/rotation.md`. **No further work tracked here.**

## Done (archived from PLAN-layout-aware-ocr.md)

The original phases all shipped. Cross-referenced for anyone reading
the old plan:

| Phase | Status |
|---|---|
| Phase 1 — `pd_book_tools.layout` module (`types`, `detector`, `_mappings`, `registry`, `geometry`, `adapters/pp_doclayout`) | ✅ Shipped. `visualize.py` added as a bonus debug helper. |
| Phase 2 — Layout-aware `Page.reorganize_page(layout=…)` with `tag_words_with_layout`, `drop_layout_regions`, `drop_figure_internal_words`, `bubble_block_roles_from_layout`, `associate_captions`, `emit_caption_block`, `detect_geometric_sidenotes` | ✅ Shipped. See `pd_book_tools/ocr/layout_aware_reorg.py`. |
| Phase 3 — `pd-ocr-cli` flags (`--layout-model`, `--layout-checkpoint`, `--layout-confidence`, `--layout-debug`, `--extract-illustrations`) | ✅ Shipped. The CLI defaults to `pp-doclayout-plus-l`; `--layout-model none` opts out. The `-la` short flag from the original plan was dropped because the model selector subsumes it. |
| Phase 4 — `pd-prep-for-pgdp` integration (specs reference `pd_book_tools.layout`, `ProjectConfig.layout_checkpoint` exists) | ✅ Shipped (spec-level). |
| Page rotation detection follow-up | ✅ Shipped as `pd_book_tools/ocr/rotation.py`. |
| Confidence-threshold-blanket-vs-per-type design question | 🟡 Listed above as an open item. |
| Decoration-vs-figure post-classify heuristic | 🟡 Listed above as an open item. |
| Multi-column reading order primitive | 🟡 Listed above as an open item. |
| Detector-failure fallback hardening | 🟡 Listed above as an open item. |
| Caption association distance (`max_gap_px` knob) | ✅ Shipped via `caption_for_figure(max_gap_px=…)` in `pd_book_tools/layout/geometry.py`. |
| Performance instrumentation (`PageLayout.inference_ms`) | ✅ Shipped via `_TimingDetector` wrapper in `registry.py`. |
| Optional `[layout]` install extra | ❌ Not shipped — `transformers` was promoted to mandatory `dependencies`. The install footprint is ~40 MB on top of DocTR; users get layout out of the box. The original plan's `pd_book_tools[layout]` extra never shipped. Documented here so future readers don't go looking for it. |

## Out of scope (still)

- **Training PP-DocLayout from scratch.** The model's pretrained
  corpus already includes ancient books; fine-tuning is plenty.
- **Custom architectures (DocLayout-YOLO, DocLayNet-DETR, DiT).**
  RT-DETR is a solid baseline; swapping architectures buys little
  for the engineering cost.
- **Cross-book transfer learning** beyond what fine-tuning provides.
- **Table-to-PGDP-table syntax.** Detecting tables is in;
  serialising into PGDP table syntax stays manual.
- **Cross-page figure stitching** (foldout maps spanning two pages).
- **Layout-aware OCR crops** (different recognition models per
  region type — handwriting / fraktur / running text). Real
  improvement, separate effort, not on this roadmap.
