# Roadmap

Forward-looking work in pdomain-book-tools. Excludes anything that's better
tracked in a consuming-app roadmap (the layout-fine-tune workflow lives
in [`ocr-container/docs/SPEC-layout-training.md`](../../docs/SPEC-layout-training.md)
because it spans pdomain-ocr-labeler-spa + pdomain-ocr-training; this file holds the
items that belong specifically in the library).

The items below are carried over from the (now-archived) workspace
docs `PLAN-layout-aware-ocr.md` and `TODO-layout-training.md`. The
phases they originally lived in have shipped; only the residuals remain.

> Shipped items live in [`ROADMAP-shipped.md`](ROADMAP-shipped.md).

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

This belongs in `pdomain_book_tools/layout/geometry.py` as
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
opt in by passing a float. A pdomain-ocr-cli flag remains a downstream
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
`pdomain_book_tools/ocr/rotation.py`. Documented in
`docs/specs/02-rotation.md`. **No further work tracked here.**

## Open — developer tooling

### dev-local-aware `upgrade-deps` flow — partial

Detection + guard shipped: `scripts/check_dev_local.py` reports
dev-local mode (sibling pdomain-* editables, `[gpu]` extra installed,
`.venv/.pdomain-dev-local` marker, or `PDOMAIN_DEV_LOCAL=1` env var) with
exit-code contract (0 canonical / 1 dev-local) and a `--quiet`
mode for Makefile branching. `make upgrade-deps` now refuses with
a pointer to `make upgrade-deps-local` when dev-local is detected;
`make upgrade-deps-local` runs the canonical sync then re-applies
the `[gpu]` extra via `make sync-gpu`. Spec
[`docs/specs/07-dev-local-upgrade-flow.md`](specs/07-dev-local-upgrade-flow.md).

`make dev-local` recipe shipped: runs `sync-gpu` (which applies the
`[gpu]` extra when an NVIDIA GPU is auto-detected) and writes the
`.venv/.pdomain-dev-local` marker via `scripts/write_dev_local_marker.py`.
Lifecycle is anchored to the venv — `make remove-venv` deletes the
marker automatically. Downstream `pdomain-*` repos can now tell users
"run `make dev-local` in pdomain-book-tools first" with a stable contract.

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
