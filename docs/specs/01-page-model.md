# Page model — `Page.to_dict()` JSON reference

> **Status**: Active
> **Last updated**: 2026-05-10
> **Spec-Issue**: ConcaveTrillion/pd-book-tools#24

This document is the user-facing reference for the JSON form of a
processed page produced by pd-book-tools. It describes what the keys
mean, what the value vocabularies are, and where the format is and
isn't stable. Downstream consumers (`pd-ocr-cli`, `pd-ocr-labeler`,
`pd-prep-for-pgdp`) all read this format back via `Page.from_dict`.

For maintainers: this doc is gated by
[`tests/test_page_model_doc.py`](../../tests/test_page_model_doc.py),
which fails the build if the vocabulary lists below drift from the
authoritative `ClassVar` frozensets on `Block` or the `RegionType`
enum. If a test in that file fails, update the doc and the
allowed-set together.

## Where the format lives in code

- `Page.to_dict()` — `pd_book_tools/ocr/page.py` (around line 2661).
- `Page.from_dict(...)` — same file, around line 3091.
- `Block.to_dict()` / `Block.from_dict()` — `pd_book_tools/ocr/block.py`.
- `Word.to_dict()` / `Word.from_dict()` — `pd_book_tools/ocr/word.py`.
- `BoundingBox.to_dict()` / `BoundingBox.from_dict()` —
  `pd_book_tools/geometry/bounding_box.py`.
- Allowed label vocabularies — `Block.ALLOWED_BLOCK_ROLE_LABELS`,
  `Block.ALLOWED_LINE_ROLE_LABELS`, plus the `*_POSITION_LABELS` siblings
  and the `*_ALIASES` maps that fold legacy strings onto canonical ones.

## The top-level tree

A serialised page is a recursive tree:

```text
Page
└─ items: list[Block]
   └─ items: list[Block | Word]   # blocks may nest; Block.child_type controls which
      └─ ...
         └─ Word                   # leaves
```

Every level except `Word` may carry a `BoundingBox`; words always do.

`Block` is intentionally recursive because different OCR engines emit
different levels of nesting:

- DocTR emits page → block → line → word; pd-book-tools represents this
  as `Block(child_type=BLOCKS) → Block(child_type=BLOCKS, block_category=PARAGRAPH) → Block(child_type=WORDS, block_category=LINE) → Word`.
- Tesseract's nesting flattens to a similar tree via the per-level
  helpers in `pd_book_tools/ocr/cv2_tesseract.py`.
- After `Page.reorganize_page` runs, the canonical shape is
  `Page → Block(PARAGRAPH) → Block(LINE) → Word` — but the data model
  does not enforce a single shape and downstream code MUST traverse
  recursively rather than indexing fixed depths.

`Block.child_type` (`BlockChildType`) is one of:

- `WORDS` — `items` are `Word` instances. Required when
  `block_category == LINE`.
- `BLOCKS` — `items` are nested `Block` instances.

`Block.block_category` (`BlockCategory`) is one of:

- `BLOCK` — generic container (the default).
- `PARAGRAPH` — semantic paragraph; reorg pipeline emits these.
- `LINE` — single line of text; must contain `Word` children.

## Top-level Page fields

`Page.to_dict()` always emits:

- `type` — the literal string `"Page"`. Used to disambiguate node types
  during `from_dict` traversal.
- `width`, `height` — page geometry in pixels.
- `page_index` — zero-based index of the page within its source
  document.
- `bounding_box` — a serialised `BoundingBox` (see below) or `null`
  when the page has no spatial extent recorded.
- `items` — list of serialised `Block`s in reading order.
- `ocr_provenance` — engine / model / parameters used; `null` when no
  OCR was run (e.g. a hand-edited page loaded back via `from_dict`).

Plus these optional metadata fields, emitted only when set (omitted
otherwise to keep the JSON compact):

- `image_path` — original scan path as a string.
- `name` — caller-supplied display name.
- `source` — set when `Page.source != "ocr"` (e.g. `"reflow"`,
  `"manual"`).
- `ocr_failed` — boolean; `True` when OCR raised but the page is being
  preserved as a geometry-only artefact.
- `provenance_live_ocr`, `provenance_saved_ocr`, `provenance_saved` —
  audit trail across save/load cycles.
- `rotation_applied` — present when `pd_book_tools/ocr/rotation.py`
  rotated the page during ingestion. See
  [`02-rotation.md`](02-rotation.md) for the rotated-frame coordinate
  convention.

## Block fields

`Block.to_dict()` emits:

- `type` — the literal string `"Block"`.
- `child_type` — `"WORDS"` or `"BLOCKS"`.
- `block_category` — `"BLOCK"`, `"PARAGRAPH"`, or `"LINE"`.
- `block_labels` — caller-controlled freeform labels (no enforced
  vocabulary).
- `block_role_labels` — semantic role; vocabulary below.
- `block_position_labels` — position within the page or column;
  vocabulary below.
- `line_role_labels` — only meaningful when `block_category == LINE`;
  vocabulary below.
- `line_position_labels` — line-level position vocabulary, also LINE-only.
- `baseline` — line-baseline parameters (slope/intercept) when computed
  by `Block.estimate_baseline_from_image`.
- `bounding_box` — serialised `BoundingBox` or `null`.
- `items` — children, all serialised.
- `override_page_sort_order` — when set, forces sort position relative
  to peers.
- `unmatched_ground_truth_words` — populated only by ground-truth
  matching workflows.
- `additional_block_attributes` — open-schema dict for caller use.
- `base_ground_truth_text` — populated only by ground-truth matching
  workflows.

### `block_role_labels` vocabulary

The library validates additions against
`Block.ALLOWED_BLOCK_ROLE_LABELS`. Aliases in
`Block.BLOCK_ROLE_LABEL_ALIASES` (e.g. `"poem"` → `"poetry"`,
`"block quote"` → `"blockquote"`) are normalised on assignment.

Allowed values:

- `paragraph` — body text. The default for blocks that don't carry a
  more specific role.
- `sidenote` — margin gloss; set by the geometric sidenote detector
  (`detect_geometric_sidenotes`) or bubbled up from a layout
  `RegionType.sidenote` region.
- `page header` — running head at the top of the page.
- `page footer` — running foot.
- `page number` — folio/page number.
- `printers mark` — signature, catchword, or printer's ornament.
- `blockquote` — indented quotation.
- `poetry` — verse.
- `recovered` — words the reorg pipeline initially dropped but
  re-attached at the end so the OCR word multiset round-trips. Visible
  to consumers so they can flag, strip, or re-flow them. See
  [`03-reorganize-pipeline.md`](03-reorganize-pipeline.md) for the recovery
  step.
- `illustration` — geometry-only block representing a figure region.
  Carries `bounding_box` but `items: []`. Emission is gated by
  `Page.reorganize_page(emit_illustration_placeholders=...)`; pass
  `False` for plain-text consumers (e.g. pd-ocr-cli's `.txt` output)
  that don't want placeholder blocks.
- `decoration` — ornamental woodcut, fleuron, or chapter headpiece.
  Same geometry-only emission rules as `illustration`.
- `caption` — figure / illustration caption text. Always preserves
  caption words (no silent drops) regardless of placeholder emission.
- `figure` — text inside a figure region (rare; usually replaced by
  `illustration` after the reorg pipeline).
- `table` — tabular region; pd-book-tools detects but does not
  serialise into PGDP table syntax (manual step).
- `footnote` — note text at the bottom of the page.
- `title`, `section`, `list`, `formula` — layout-derived roles bubbled
  up from `RegionType.title` / `.section` / `.list` / `.formula` by
  `bubble_block_roles_from_layout`.
- `artefact` — non-text region detected by the OCR engine (DocTR's
  `artefacts`: stamps, barcodes, QR codes, unclassified blobs). Carries
  geometry only; `items` is empty. Preserves the page's full inventory
  of detected regions instead of silently discarding non-text ones.

### `block_position_labels` vocabulary

Allowed values: `top`, `bottom`, `left`, `right`, `center`,
`margin left`, `margin right`. Multiple labels can be set on one block
(e.g. `["top", "left"]`).

### `line_role_labels` vocabulary

Allowed values (LINE-category blocks only):

- `body line` — default for body-text lines.
- `heading line` — chapter / section headings.
- `verse line` — line of poetry.
- `blockquote line` — line within a blockquote.
- `header line` — line of a page header.
- `footer line` — line of a page footer.
- `footnote line` — line of a footnote.
- `caption line` — line of a caption.
- `page number line` — line carrying a page number.

Aliases in `Block.LINE_ROLE_LABEL_ALIASES` (`"body"` → `"body line"`,
etc.) are normalised on assignment.

### `line_position_labels` vocabulary

Allowed values: `top`, `bottom`, `left`, `right`, `center`,
`column left`, `column right`. The `column left` / `column right`
values flag lines on the boundary of a detected multi-column layout.

## Word fields

`Word.to_dict()` emits:

- `type` — the literal string `"Word"`.
- `text` — the recognised text.
- `bounding_box` — serialised `BoundingBox`.
- `ocr_confidence` — engine confidence for this word, or `null`.
- `word_labels` — caller-controlled freeform labels. The reorg
  pipeline's `layout:*` tags (e.g. `layout:figure`, `layout:sidenote`)
  live here. See
  [`pd_book_tools/ocr/layout_aware_reorg.py`](../../pd_book_tools/ocr/layout_aware_reorg.py)
  for the `layout:` prefix convention used by
  `tag_words_with_layout`.
- `text_style_labels` — italic / bold / small-caps style hints (when
  detected).
- `text_style_label_scopes` — start/end scope markers for ranged style
  spans.
- `word_components` — sub-word component tags. Allowed values are
  defined by `ALLOWED_COMPONENTS` in
  [`pd_book_tools/ocr/label_normalization.py`](../../pd_book_tools/ocr/label_normalization.py):
  `superscript`, `subscript`, `footnote marker`, `drop cap`,
  `drop cap unrecovered`. The drop-cap tags are set by Step DC of the
  reorganize pipeline (see
  [`pd_book_tools/ocr/dropcap.py`](../../pd_book_tools/ocr/dropcap.py)):
  - `drop cap` — this Word *is* the decorative initial glyph (e.g. the
    oversized "R" in "READER!"). It is kept as its own Word at the
    front of the body line, with its own bounding box and OCR
    confidence (or `null` confidence for synthesised caps recovered by
    the cursive fallback). `Block.text` keys on this tag to fuse the
    cap to the next body Word with the empty string separator — so cap
    "S" + body "tudies" renders as `Studies`, not `S tudies`. Only the
    immediately following Word in the same line is fused; subsequent
    Words still get the default space separator.
  - `drop cap unrecovered` — set on the closest body Word when the
    geometric trigger detected a drop cap but the letter inference
    couldn't resolve it (e.g. body word is already a valid English
    word like `BELIEF`, so single-letter prepend lookup is ambiguous).
    Surfaced for downstream tooling / labelers to flag for human
    review. This tag does NOT trigger the empty-string-join rendering
    contract — the OCR text is preserved as-is and rendered with the
    default space separator.
- `baseline` — per-word baseline parameters when computed.
- `ground_truth_text` / `ground_truth_bounding_box` /
  `ground_truth_match_keys` — populated only by ground-truth matching
  workflows.

## BoundingBox fields

`BoundingBox.to_dict()` emits a nested object with `top_left`,
`bottom_right`, and `is_normalized`. Each corner is `{x, y,
is_normalized}` — both the box and its corners carry the normalisation
flag because some legacy serialised forms omitted the box-level flag,
and `from_dict` infers from the corners when the box-level flag is
absent.

`is_normalized` semantics:

- `true` — coordinates are in `[0, 1]` relative to the page (DocTR's
  native frame).
- `false` — coordinates are absolute pixel values.
- `null` — inferred from the actual coordinate values at construction
  time. New code should set this explicitly.

## Layout vs page model — two separate trees

`PageLayout` and `LayoutRegion` (defined in
`pd_book_tools/layout/types.py`) are a **separate** structure from the
page model. They describe what a layout detector saw on the page and
are consumed by `Page.reorganize_page(layout=...)` as a hint — they
are NOT part of `Page.to_dict()` output.

If you're loading a serialised page and looking for layout regions,
you won't find them: only the *consequences* of layout consumption are
preserved in the page tree (per-word `layout:*` tags, bubbled
`block_role_labels`, geometry-only illustration / decoration
placeholder blocks).

`RegionType` enum values (the layout vocabulary, distinct from
`block_role_labels`):

- `text`, `title`, `section`, `list`, `table`, `figure`, `decoration`,
  `caption`, `header`, `footer`, `footnote`, `formula`, `abandoned`,
  `sidenote`.

The mapping `RegionType` → `block_role_labels` is defined by
`_REGION_TO_BLOCK_ROLE` in
[`pd_book_tools/ocr/layout_aware_reorg.py`](../../pd_book_tools/ocr/layout_aware_reorg.py)
(roughly: `text` → `paragraph`, `header` → `page header`, `footer` →
`page footer`, the rest pass through unchanged). `RegionType.abandoned`
intentionally has no block-role mapping; it exists so layout-derived
regions that the model flags as abandoned can be dropped or ignored
without poisoning the page tree.

## Role labels are advisory, not formatting

pd-book-tools attaches role labels but does **not** render them into
`Page.text`. Turning labels into PGDP markup, `[Illustration: …]`
strings, footnote anchors, etc. is the consuming app's job:

- `pd-prep-for-pgdp` does the PGDP mapping from `block_role_labels`.
- `pd-ocr-cli`'s `.txt` output is plain reading-order text and ignores
  most role labels.

Don't expect the library to do downstream formatting for you.

## No-silent-drop policy

When `Page.reorganize_page` runs without `drop_layout_words=True` (the
default), the OCR word multiset round-trips end-to-end:
`validate_word_preservation` checks that every pre-pipeline word is
still present somewhere in the post-pipeline output, possibly relocated
into a `recovered` block. Footnote / header / footer / abandoned
regions are role-labelled but never dropped, regardless of any flag.
This holds even when layout regions are passed in.

## Stability

The format is currently **informal**. Concretely:

- Field-name additions are routine and do not constitute a breaking
  change. New consumers should use `dict.get(...)` with sensible
  defaults rather than hard-indexing.
- Field removals and renames have happened during reorg refactors.
  Pin a known-good `pd-book-tools` version in downstream projects if
  you depend on a specific field shape.
- The vocabularies listed above
  (`ALLOWED_BLOCK_ROLE_LABELS`, etc.) are append-only in practice but
  not contractually frozen. The doc-vs-code drift gate in
  `tests/test_page_model_doc.py` catches additions; treat it as the
  signal that this doc needs updating.

There is no JSON schema file, no version-negotiation protocol, and no
guarantee of round-trip stability across pd-book-tools major versions.
Those are separate efforts and are out of scope here.

## See also

- [`03-reorganize-pipeline.md`](03-reorganize-pipeline.md) — what the reorg
  pipeline does between `Page.from_doctr_result` and the final tree
  this doc describes.
- [`02-rotation.md`](02-rotation.md) — how `rotation_applied` interacts with
  the page coordinate frame.
- `pd-prep-for-pgdp/specs/` — how `block_role_labels` map to PGDP
  markup downstream.

## TL;DR

Not yet captured during the B3 mechanical migration.

## Context

Not yet captured during the B3 mechanical migration.

## Constraints

Not yet captured during the B3 mechanical migration.

## Decision

Not yet captured during the B3 mechanical migration.

## Contract / Acceptance

Not yet captured during the B3 mechanical migration.

## Trade-offs considered

Not yet captured during the B3 mechanical migration.

## Consequences

Not yet captured during the B3 mechanical migration.

## Open questions

Not yet captured during the B3 mechanical migration.

## References

Not yet captured during the B3 mechanical migration.
