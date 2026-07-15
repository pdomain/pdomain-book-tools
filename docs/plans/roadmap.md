---
Status: active
Owner: CT
Created: 2026-05-04
Last verified: 2026-07-13
Kind: plan
---

# Roadmap

This roadmap tracks forward-looking work that belongs specifically in
pdomain-book-tools. It excludes work better tracked in a consuming app's
roadmap. For example, the layout-fine-tune workflow lives in the workspace
layout-training specification because it spans pdomain-ocr-labeler-spa +
pdomain-ocr-training.

The items below come from the now-archived workspace docs
`PLAN-layout-aware-ocr.md` and `TODO-layout-training.md`. Their original phases
have shipped. Only the remaining work appears here.

> Git history preserves shipped roadmap items removed from this live plan.

## Open — layout consumption

The layout module exists and is wired up, but its consumption logic could be
sharper. None of these items block the fine-tune workflow. They are useful on
their own. One item, per-type confidence, becomes more relevant after a
fine-tune lands because confidences will distribute differently.

### Decoration-vs-figure post-classification

PP-DocLayout has no `decoration` class. The adapter maps `seal` →
`RegionType.decoration`. For ornamental woodcuts such as chapter headpieces and
fleurons, it falls back to `image` → `figure`. PLAN open question 3 sketched a
heuristic: "if a `figure` is small (<5 % of page), positioned at top or bottom,
and contains no detected text words, reclassify as `decoration`."

Add `postclassify_decoration(layout, page) -> PageLayout` to
`pdomain_book_tools/layout/geometry.py`. Run it as a late pass in
`Page.reorganize_page`, after `tag_words_with_layout`, so the pass knows which
words fall inside the figure region. This cheap change helps the downstream
illustration extractor choose the correct `type=decoration` for
`i_<stem>_NN.png` filenames.

This work is out of scope until the fine-tune lands. Once the model has a
first-class `decoration` head, the heuristic becomes a fallback instead of the
primary classifier.

## Open — image-processing improvements (no model fine-tune needed)

These are independent of the layout fine-tune. Each addresses a
specific reorg-pipeline weakness called out in the archived
`TODO-layout-training.md`.

### Glyph-size analysis for sidenote detection — partial

Bbox-height support has shipped: `detect_geometric_sidenotes` now accepts
`max_height_ratio: float | None = None`. When set (e.g. `0.8`), a
margin cluster is rejected unless its median bbox height is
`<= max_height_ratio * body_median_height` (body sample excludes
words already in either margin cluster. This exclusion prevents a tall sidenote
from raising the median. The default `None` preserves legacy x-only behaviour.

The reorganize-level pass-through has also shipped:
`Page.reorganize_page(sidenote_max_height_ratio=…)` threads through
to Step Layout-1b. Default `None` preserves legacy behaviour; callers
opt in by passing a float. A pdomain-ocr-cli flag remains a downstream
follow-up in that repo's roadmap. It can connect directly to this kwarg without
further changes here.

Still open:

- **Default-flip decision.** Whether to flip the reorganize-level
  default from `None` to e.g. `0.85` (more aggressive) needs tuning
  with real fixtures. No fixture today regresses with the current
  `None` default. Flipping the default needs evidence that
  `0.85`-style gating helps the corpus more than it hurts. Do not pick this
  slice without running a fixture pass first.
- **Image-projection refinement.** Bbox heights are coarse for OCR
  output that bundles ascenders and descenders inconsistently. The
  PLAN sketched a horizontal-projection pass on the cropped image
  to estimate true x-height per word. Worth doing only if a fixture
  shows bbox-height alone misclassifying.

### Drop-cap glyph recognition — Iteration C (queued)

Iterations A and B shipped (see the archive table below). The remaining work is
the multi-letter heading-OCR cross-check. When body-word inference is ambiguous,
use the chapter title above to disambiguate it. For example, the body word
"BELIEF" is already valid English, so the cursive fallback cannot uniquely
resolve the cap to "A". The title "A BELIEF IN OMENS…" shows that the cap is
"A". Today, these cases enter the ``"drop cap unrecovered"`` failure path, and
the closest body Word is tagged for human review.

The fixture that exercises this gap is
`tests/fixtures/layout_regression/inputs/footnotes-stacked-with-anchor`
(cap "A", body "BELIEF" — currently unrecovered).

### Multi-column body detection enhancements

Once the glyph-size data described above exists, column detection in
`expand_row_blocks` can become sidenote-aware. The geometric column splitter
should not break on a sidenote that creates a narrow third column. This case is
currently rare in the PGDP corpus, so it is a follow-up to the glyph-size work,
not standalone work.

## Open — page handling

### Page rotation — already shipped

The PLAN's "open follow-up" for page-rotation detection has shipped as
`pdomain_book_tools/ocr/rotation.py`. Documented in
`../architecture/ocr-page-orientation.md`. It covers sideways plates,
upside-down scans, and the Peutinger map fixture. **No further work tracked here.**

## Open — developer tooling

### dev-local-aware `upgrade-deps` flow — partial

Detection and the guard have shipped. `scripts/check_dev_local.py` reports
dev-local mode (sibling pdomain-* editables, `[gpu]` extra installed,
`.venv/.pdomain-dev-local` marker, or `PDOMAIN_DEV_LOCAL=1` env var) with
exit-code contract (0 canonical / 1 dev-local) and a `--quiet`
mode for Makefile branching. When it detects dev-local mode, `make upgrade-deps`
now refuses to run and points to `make upgrade-deps-local`.
`make upgrade-deps-local` runs the canonical sync, then reapplies
the `[gpu]` extra via `make sync-gpu`. Spec
[`docs/specs/07-dev-local-upgrade-flow.md`](../specs/07-dev-local-upgrade-flow.md).

The `make dev-local` recipe has shipped. It runs `sync-gpu`, which applies the
`[gpu]` extra when an NVIDIA GPU is auto-detected) and writes the
`.venv/.pdomain-dev-local` marker via `scripts/write_dev_local_marker.py`.
Its lifecycle is tied to the venv: `make remove-venv` deletes the marker
automatically. Downstream `pdomain-*` repos can now give users a stable
instruction: "run `make dev-local` in pdomain-book-tools first".

Still open:

- **Doctr-from-git signal.** Whether `python-doctr` installed from a
  non-canonical URL (a contributor's fork rather than
  `mindee/doctr.git`) should auto-flag dev-local without a marker
  file. The current detector only inspects `uv pip list --format=json`,
  which does not expose the install URL. A probe would have to read
  doctr's `direct_url.json` from dist-info. Design question: which
  URLs count as "non-canonical" given pyproject already pins doctr
  from `mindee/doctr.git` (so canonical installs leave a `vcs_info`
  block too). This work is deferred until a concrete fork-pin workflow needs it.

## Out of scope (still)

- **Training PP-DocLayout from scratch.** The model's pretrained
  corpus already includes ancient books. Fine-tuning is enough.
- **Custom architectures (DocLayout-YOLO, DocLayNet-DETR, DiT).**
  RT-DETR is a solid baseline. Swapping architectures buys little
  for the engineering cost.
- **Cross-book transfer learning** beyond what fine-tuning provides.
- **Table-to-PGDP-table syntax.** Table detection is complete, but
  serialising into PGDP table syntax stays manual.
- **Cross-page figure stitching** (foldout maps spanning two pages).
- **Layout-aware OCR crops** (different recognition models per
  region type — handwriting / fraktur / running text). This would be a real
  improvement, but it is a separate effort and is not on this roadmap.

## Goal

Track only forward-looking work that belongs in the `pdomain-book-tools`
library, carrying forward residual layout, image-processing, page-handling, and
developer-tooling work after the original phases shipped. Exclude work owned by
consuming applications or cross-repository training workflows.

## Architecture

Extend the existing `Page.reorganize_page` pipeline with late layout
post-classification and optional sidenote refinements, and keep drop-cap
recovery in the OCR reorganization path. Keep local-development detection in
repository scripts and Make targets, with downstream CLI wiring and
cross-repository training outside this plan.

## Tech Stack

The roadmap builds on PP-DocLayout and `PageLayout`/`RegionType` layout
types, OCR bounding boxes and cropped-image projection analysis,
layout-regression fixtures, and the Python scripts, uv environment metadata,
and Make targets used by the local-development workflow.

## Global Constraints

Do not flip the sidenote-height default without a real-fixture pass, and add
image-projection refinement only when a fixture demonstrates that bounding-box
height is insufficient. Keep decoration post-classification deferred until
fine-tuning lands, preserve legacy behavior by default, and retain the listed
model-training, architecture-swap, cross-book, table-serialization, cross-page,
and layout-aware OCR exclusions.
