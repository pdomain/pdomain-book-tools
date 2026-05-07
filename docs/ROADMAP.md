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

### Aspect-ratio control in `rescale_image` (follow-up to R-24)

Commit `9b8f651` (R-24) deprecated the `aspect_ratio` parameter in
both rescale backends because the parameter was accepted but unused —
the function always preserved the source aspect ratio. On reflection,
there *is* a real use case for aspect-ratio-aware rescale: at minimum,
the existing downstream caller
(`pd-prep-for-pgdp/src/pd_prep_for_pgdp/core/pipeline/process_page.py:154`,
which passes `aspect_ratio=cfg.page_h_w_ratio` and which spec
`pd-prep-for-pgdp/specs/06-page-workbench.md:502` documents) was
written assuming the parameter clamps the long side to a target
page-shape ratio. R-24's deprecation closed the silent-no-op
behaviour, but it didn't answer the underlying question: should
rescale support an aspect-ratio option, and if so, with what
semantics?

This entry exists to capture that the next implementing session must
**design the semantics first** — the user has flagged the need but
not pinned the exact shape.

#### Backends affected

- `pd_book_tools/image_processing/cv2_processing/rescale.py` (the
  `rescale_image` function; currently emits `DeprecationWarning` on
  non-default `aspect_ratio`).
- `pd_book_tools/image_processing/cupy_processing/rescale.py`
  (the GPU `rescale_image_gpu` equivalent — same deprecated parameter
  shape).

Both backends must end up with the same public surface; downstream
code branches on availability of cupy, not on a different signature.

#### Rationale — what "aspect-ratio control" might mean

Several distinct features get conflated under "aspect ratio". The
implementing session must decide which one(s) the option actually
covers:

1. **Long-side clamp to a target page shape.** Cap the long side at
   `target_short_side * aspect_ratio` so an unusually tall scan (e.g.
   a page that includes margin junk) gets cropped/clamped down to the
   canonical book-page proportion. This is what
   `pd-prep-for-pgdp` was originally trying to do.
2. **Aspect-preserving resize when only one dimension is supplied.**
   Caller passes `target_width` *or* `target_height` and rescale
   computes the other from the source aspect. Today the only knob is
   `target_short_side`, which already preserves source aspect — so
   this only matters if a `target_long_side` / `target_width` /
   `target_height` knob is added.
3. **Aspect override (stretch / letterbox / crop).** Caller passes a
   target ratio and rescale either stretches, letterboxes (pad), or
   crops to match. This is the most invasive option and the least
   likely to be wanted for OCR pipelines, but flagging it here so it
   gets explicitly ruled in or out.

#### Open questions for the implementing session

Resolve these before writing code:

- **Type of `aspect_ratio`:** float (target H/W or W/H — which?), a
  `(w, h)` tuple, or an enum like
  `Literal["preserve", "stretch", "letterbox", "crop", "clamp_long_side"]`?
  Pure float is what the deprecated param was; an enum better
  expresses the actual semantic decisions above.
- **Interaction with existing `target_short_side`:** if both
  `target_short_side` and an aspect-ratio override are passed, which
  wins? Does aspect-ratio control imply a different primary
  dimension knob (e.g. `target_long_side`)?
- **Naming vs. R-24:** R-24's deprecation warning fires on any
  non-default `aspect_ratio` value. Re-introducing the same parameter
  name with different semantics would surprise callers who saw the
  warning and dropped the keyword. Options:
  - Pick a new parameter name (e.g. `aspect_mode`,
    `target_aspect_ratio`, `long_side_clamp`) and leave R-24's
    deprecation in place until a future major removes it.
  - Reuse `aspect_ratio` but bump a major version and document the
    semantic change in CHANGELOG.
  Recommend the new-name path unless there's a strong reason to
  reuse.
- **Default behaviour:** the current default
  (`_ASPECT_RATIO_DEFAULT = 1.65`) is silently no-op. Whatever the
  new option is, its default must continue to preserve source aspect
  exactly so existing callers don't shift output silently.
- **Downstream coordination:** any new option needs a paired update in
  `pd-prep-for-pgdp/core/pipeline/process_page.py` and its
  `specs/06-page-workbench.md` entry — flag this in the implementing
  session's hand-off so the downstream agent picks it up promptly
  rather than living on the deprecation warning indefinitely.
- **Both backends in lock-step:** whichever signature lands must ship
  in the cv2 *and* cupy backends in the same change. Drifting them
  re-creates the original R-24 confusion.

#### Reference

- Commit `9b8f651` — R-24, the deprecation that motivated this
  follow-up.
- `docs/review/refactors.md` — R-24 entry (search for "R-24") explains
  why deprecation was chosen over implementation last time.
- `pd-prep-for-pgdp/src/pd_prep_for_pgdp/core/pipeline/process_page.py:154`
  — the live downstream caller still passing `aspect_ratio=...`.
- `pd-prep-for-pgdp/specs/06-page-workbench.md:502` — downstream spec
  expecting aspect-ratio-aware rescale.

## Open — page handling

### Page rotation — already shipped

The PLAN's "open follow-up" on page-rotation detection (sideways
plates, upside-down scans, the Peutinger map fixture) shipped as
`pd_book_tools/ocr/rotation.py`. Documented in
`docs/architecture/rotation.md`. **No further work tracked here.**

## Open — developer tooling

### dev-local-aware `upgrade-deps` flow

`make upgrade-deps` ends in `uv sync --group dev`, which silently
clobbers any dev-local venv state — editable sibling pd-* checkouts,
`[gpu]` extras, doctr-from-git overrides — back to the canonical
published / CPU baseline. Workspace-wide standardization across all
`pd-*` repos. Spec lives in
[`docs/planning/dev-local-upgrade-flow-spec.md`](planning/dev-local-upgrade-flow-spec.md).

Foundation-library angle: this repo also defines the **detection
contract** consumed by every downstream `pd-*` repo — they probe
`uv pip show pd-book-tools` for an `Editable project location:`
field. Once `make dev-local` lands here it MUST install
`pd-book-tools` (and any sibling pd-* checkouts) editably so that
field actually appears; a non-editable shortcut would silently break
detection in every consumer.

Implementation pass (separate change): add `_check_dev_local`,
guard `upgrade-deps`, add `upgrade-deps-local`, optionally introduce
`make dev-local` + `.venv/.pd-dev-local` marker. Pre-existing
`make sync-gpu` (Makefile:87) already does conditional `--extra gpu`
syncing on GPU autodetect; the dev-local detection should compose
with it cleanly.

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
| Confidence-threshold-blanket-vs-per-type design question | ✅ Shipped via `drop_layout_regions(confidence_threshold=...)` / `drop_figure_internal_words(confidence_threshold=...)` accepting either a `float` (legacy single-bar) or a `dict[RegionType, float]` (per-type). `DEFAULT_DROP_CONFIDENCE_BY_TYPE` exposes a sensible default policy (figure 0.50, header 0.70, footer/footnote 0.65, abandoned 0.70). Types not listed in caller's dict fall back to `DEFAULT_DROP_CONFIDENCE`. |
| Decoration-vs-figure post-classify heuristic | 🟡 Listed above as an open item. |
| Multi-column reading order primitive | ✅ Shipped via `pd_book_tools/layout/geometry.py:region_reading_order`. Detects column gaps via a left-to-right sweep on `L`, sorts each column top-to-bottom, concatenates left-to-right. Falls back to legacy (T, L) for single-column input or layouts where a region spans across detected column boundaries (e.g. a full-width header). No silent drops. |
| Detector-failure fallback hardening | ✅ Shipped via `get_detector(..., on_error="raise" \| "log_and_null")`. Default `"raise"` preserves CLI fail-fast; `"log_and_null"` memoises a `NullDetector` so batch callers (pd-prep-for-pgdp) survive transient build failures (network, OOM, missing weights, unknown key). Per-page `detect()` failures still propagate to the caller. |
| Opt-in suppression of placeholder illustration blocks | ✅ Shipped via `Page.reorganize_page(emit_illustration_placeholders=...)` threading through `associate_captions(..., emit_placeholders=...)`. Default `True` preserves PGDP-bound behaviour; plain-text consumers (pd-ocr-cli `.txt` output) can pass `False` to skip the geometry-only placeholder block. Caption words are still relocated into a caption-roled block in either mode (no silent OCR-word drops). pd-ocr-cli flag wiring tracked in that repo's roadmap. |
| Caption association distance (`max_gap_px` knob) | ✅ Shipped via `caption_for_figure(max_gap_px=…)` in `pd_book_tools/layout/geometry.py`. |
| Performance instrumentation (`PageLayout.inference_ms`) | ✅ Shipped via `_TimingDetector` wrapper in `registry.py`. |
| Custom-detector extensibility for downstream fine-tunes | ✅ Shipped via `register_detector` / `unregister_detector` in `pd_book_tools/layout/registry.py` (R-25). Lets pd-ocr-trainer plug a custom adapter under its own key without modifying the built-in chain. |
| Optional `[layout]` install extra | ❌ Not shipped — `transformers` was promoted to mandatory `dependencies`. The install footprint is ~40 MB on top of DocTR; users get layout out of the box. The original plan's `pd_book_tools[layout]` extra never shipped. Documented here so future readers don't go looking for it. |
| Page-model / OCR JSON output format reference | ✅ Shipped at [`docs/architecture/page-model.md`](architecture/page-model.md). Doc-vs-code drift gated by `tests/test_page_model_doc.py` (vocabulary lists must match `Block.ALLOWED_*_LABELS` and `RegionType` enum). pd-ocr-cli docs can now redirect format questions here. |

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
