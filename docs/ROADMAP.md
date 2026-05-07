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

### Glyph-size analysis for sidenote detection — partial

Bbox-height pass shipped: `detect_geometric_sidenotes` now accepts
`max_height_ratio: float | None = None`. When set (e.g. `0.8`), a
margin cluster is rejected unless its median bbox height is
`<= max_height_ratio * body_median_height` (body sample excludes
words already in either margin cluster, so a tall sidenote can't
pull the median up). Default `None` preserves legacy x-only
behaviour.

Reorganize-level pass-through shipped:
`Page.reorganize_page(sidenote_max_height_ratio=…)` threads through
to Step Layout-1b. Default `None` preserves legacy behaviour; callers
opt in by passing a float. A pd-ocr-cli flag remains a downstream
follow-up tracked in that repo's roadmap; it can wire straight onto
this kwarg without further changes here.

Still open:

- **Default-flip decision.** Whether to flip the reorganize-level
  default from `None` to e.g. `0.85` (more aggressive) needs tuning
  on real fixtures. No fixture today regresses with the current
  `None` default; flipping the default needs evidence that
  `0.85`-style gating helps the corpus more than it hurts. Don't
  pick this slice without a fixture pass first.
- **Image-projection refinement.** Bbox heights are coarse for OCR
  output that bundles ascenders/descenders inconsistently. The
  PLAN sketched a horizontal-projection pass on the cropped image
  to estimate true x-height per word. Worth doing only if a fixture
  shows bbox-height alone misclassifying.

### Drop-cap glyph recognition — Iteration C (queued)

Iterations A and B shipped (see the archive table below). The
remaining open piece is the multi-letter heading-OCR cross-check: when
body-word inference is ambiguous (e.g. body word "BELIEF" is already
a valid English word, so the cursive fallback can't uniquely resolve
the cap to "A"), look at the chapter title above to disambiguate
("A BELIEF IN OMENS…" → cap is "A"). Today these cases land in the
``"drop cap unrecovered"`` failure path and the closest body Word is
tagged for human review.

The fixture that exercises this gap is
`tests/fixtures/layout_regression/inputs/footnotes-stacked-with-anchor`
(cap "A", body "BELIEF" — currently unrecovered).

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

## Open — developer tooling

### dev-local-aware `upgrade-deps` flow — partial

Detection + guard shipped: `scripts/check_dev_local.py` reports
dev-local mode (sibling pd-* editables, `[gpu]` extra installed,
`.venv/.pd-dev-local` marker, or `PD_DEV_LOCAL=1` env var) with
exit-code contract (0 canonical / 1 dev-local) and a `--quiet`
mode for Makefile branching. `make upgrade-deps` now refuses with
a pointer to `make upgrade-deps-local` when dev-local is detected;
`make upgrade-deps-local` runs the canonical sync then re-applies
the `[gpu]` extra via `make sync-gpu`. Spec
[`docs/planning/dev-local-upgrade-flow-spec.md`](planning/dev-local-upgrade-flow-spec.md).

`make dev-local` recipe shipped: runs `sync-gpu` (which applies the
`[gpu]` extra when an NVIDIA GPU is auto-detected) and writes the
`.venv/.pd-dev-local` marker via `scripts/write_dev_local_marker.py`.
Lifecycle is anchored to the venv — `make remove-venv` deletes the
marker automatically. Downstream `pd-*` repos can now tell users
"run `make dev-local` in pd-book-tools first" with a stable contract.

Still open:

- **Doctr-from-git signal.** Whether `python-doctr` installed from a
  non-canonical URL (a contributor's fork rather than
  `mindee/doctr.git`) should auto-flag dev-local without a marker
  file. The current detector only inspects `uv pip list --format=json`,
  which doesn't expose the install URL — a probe would have to read
  doctr's `direct_url.json` from dist-info. Design question: which
  URLs count as "non-canonical" given pyproject already pins doctr
  from `mindee/doctr.git` (so canonical installs leave a `vcs_info`
  block too). Deferred until a concrete fork-pin workflow needs it.

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
| Aspect-ratio control in `rescale_image` (R-24 follow-up) | ✅ Dropped entirely — `aspect_ratio` parameter removed from `rescale_image`, `rescale_image_gpu`, and `np_uint8_rescale_image`. Aspect-shape applied downstream via `map_content_onto_scaled_canvas`, not at rescale time. New `long_side_clamp` option deferred until a fixture demonstrates need. Breaking change; downstream `pd-prep-for-pgdp/core/pipeline/process_page.py` caller must drop the kwarg. |
| Drop-cap glyph recognition — Iteration A (cursive fallback) | ✅ Shipped. New module `pd_book_tools/ocr/dropcap.py` exposes `detect_and_stitch_cursive_dropcaps(blocks, image, metrics)` for caps DocTR mis-read or skipped entirely (decorative serif / italic). Geometric indent trigger → `cv2.connectedComponentsWithStats` scan → body-word lexicon lookup. Recovers `S`/`O` on credulities/filial-duty fixtures; tags closest body Word `"drop cap unrecovered"` (with `logger.warning`) when letter inference is ambiguous (e.g. `BELIEF` case in `footnotes-stacked-with-anchor`). |
| Drop-cap glyph recognition — Iteration B (tag rationalization + Step DC unification) | ✅ Shipped. (1) The iteration-A `"drop cap inferred"` tag was consolidated away — synthesised caps are signalled by `ocr_confidence=None` instead, so `ALLOWED_COMPONENTS` carries just `"drop cap"` and `"drop cap unrecovered"`. (2) `pd_book_tools/ocr/dropcap.py` now owns BOTH the block-cap geometric stitcher and the cursive fallback under a unified `detect_and_stitch_drop_caps(blocks, image, metrics)` entry point; `reorganize_page_utils.stitch_drop_caps` is preserved as a one-line shim for the historical name. (3) The empty-string-join rendering contract on `Block.text` (cap "S" + body "tudies" → "Studies", not "S tudies") and the structural shape (cap is its own Word, body Word untouched) are pinned by `tests/ocr/test_block.py` (4 cases) and `tests/ocr/test_dropcap.py` (parametrized over preface-with-drop-cap / chapter-head-credulities / chapter-head-filial-duty). Layout-regression sweep unchanged: 26 pass + 5 xfail (no rendered-text deltas). |

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
