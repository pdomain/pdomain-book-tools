# Reorganize Page Pipeline

> **Status**: Active
> **Last updated**: 2026-05-10
> **Spec-Issue**: ConcaveTrillion/pd-book-tools#27

How `Page.reorganize_page` turns a page of OCR output (a tree of `Block` /
`Line` / `Word` objects) into the ordered, classified block structure used by
`page.text` and downstream consumers.

The goal is to take messy OCR output for a scanned printed book page and
produce reading-order text that respects layout: page headers and page numbers
merge into one line, figure captions stay paired left-then-right rather than
interleaved by Y, body text that wraps around a floated figure flows
correctly, and special blocks (sidenotes, poetry, blockquotes) are tagged.

The implementation lives almost entirely in
[`pd_book_tools/ocr/reorganize_page_utils.py`](../../pd_book_tools/ocr/reorganize_page_utils.py).
`Page.reorganize_page` is a thin orchestration shim that calls named module
functions in pipeline order.

## Guiding principles

1. **Geometry first, content second.** Heuristics use bounding-box positions,
   word and line heights, and gap statistics. Text content is only consulted
   when geometry is ambiguous (e.g. a "FiG." prefix as a tiebreaker).
2. **Generalize, don't memorize.** Heuristics use per-page robust statistics
   (medians, p90) rather than hard-coded thresholds tuned to one page. The
   `PageMetrics` dataclass captures the page-wide stats once at the start and
   feeds every step.
3. **Small named functions.** Each pipeline step is one named function with a
   matching debug-PNG writer.
4. **Explicit step order.** The orchestration in `Page.reorganize_page` reads
   like a numbered outline — every step is a labeled call to a module
   function, and the file follows the same order.
5. **No surprising mutations.** Steps that take a list of lines should not
   mutate it; sorts produce local copies.

## Per-page metrics (`PageMetrics`)

Computed once in `compute_page_metrics(page)`:

| Field | Definition | Used for |
|---|---|---|
| `coord_w`, `coord_h` | `1.0` if word boxes are normalized, else page pixel size | unit-aware thresholds (handles both pixel and `[0, 1]` OCR coords) |
| `median_word_w`, `median_word_h` | medians across all word bboxes | header-band thickness, "is this band a different typeface" |
| `median_line_h` | median line bbox height | inter-line gap thresholds |
| `top_word_min_y`, `bottom_word_max_y` | extreme Y of OCR content | anchors header/footer bands to actual text, not raw image |
| `word_count` | total non-empty words | bail-outs for near-empty pages |

Future expansions (currently planned but not implemented; add when a fixture
demands them):

- `cap_height` — median height of all-caps words (distinguishes header from
  body when a header is uppercase and the body is mixed-case).
- `x_height` — median height of short lowercase words.
- `body_left_x`, `body_right_x` — robust mode of paragraph-line minX/maxX.
- `median_intra_line_gap`, `median_inter_line_gap` — for column-boundary and
  paragraph-break thresholds.

## Pipeline steps

```text
   raw page (Block tree from OCR JSON)
   │
   ▼
 [Step A] refine_bounding_boxes               (image-based bbox tightening)
   │
   ▼
 [Step B] reorganize_lines                    (per existing block)
   │
   ▼
 [Step D] split_mixed_content_lines           + write_step_d_debug_overlay_png
   │
   ▼
 [Step E] extract_top_header_lines / footer    + write_step_e_debug_overlay_png
   │       build_page_header_block / footer
   │
   ▼
 [Step F] compute_text_row_blocks            + write_step_row_blocks_debug_overlay_png
   │       _build_word_seeded_row_blocks       (chooses lower-cost variant)
   │       _row_block_quality
   │
   ▼
 [Step B'] reorganize_lines per row block      (re-merge after grouping)
   │
   ▼
 [Step H] expand_row_blocks                  + write_step_h_debug_overlay_png
   │       expand_floated_flow_row_block
   │       expand_mixed_column_row_block
   │       expand_multi_column_row_block
   │       expand_simple_two_column_row_block
   │
   ▼
 [Step L] classify_and_paragraphize_blocks     + write_step_l_debug_overlay_png
   │       (uses _classify_row_block, then
   │        wrap_special_role_block OR
   │        compute_text_paragraph_blocks)
   │       — Step K paragraph splits run inside this for body blocks
   │
   ▼
 [Step DC] stitch_drop_caps                    + emit_step_dropcap_debug
   │       Tag oversized initial letter with word_components=["drop cap"]
   │       and merge it into the next paragraph's first line.
   │       (Followed by detect_and_stitch_cursive_dropcaps fallback for
   │       cursive / decorative caps DocTR didn't recognise.)
   │
   ▼
 [Final] assemble_final_blocks                 (weave header/footer back in,
                                                 stamp override_page_sort_order)
   │
   ▼
   page.text  ← "\n\n".join(block.text for block in items) + "\n"
```

Steps C, J, and M from the original design are folded in implicitly:

- **Step C** (assign words to baseline-rows) is performed inside
  `build_word_seeded_row_blocks`'s line-bucketing pass.
- **Step J** (reading order) is the natural output ordering of
  `expand_row_blocks` — left column emitted before right column, narrow
  wrapped flow before its caption, etc.
- **Step M** (block tree → text) is `Page.text`, which simply joins the items.

The previous design also exposed Step 1a/1b/1c "seed-region growth" debug
overlays, computed by an independent word-grouping algorithm. That code
path was vestigial — the result was never consumed by the pipeline, only
visualised — and dominated debug-on test runtime by a factor of ~250×.
It was removed; if you need to inspect word grouping today, the row-block
debug PNG (`stepF`) is the live equivalent.

Each step (D, E, F, H, K, L) writes a debug PNG into
`tests/fixtures/layout_regression/debug/<case>/` when the
`PD_OCR_LAYOUT_DEBUG=1` environment variable is set. The regression test
enables this automatically. An auto-generated `index.html` lets you scroll
through the per-step overlays in a browser.

## Step descriptions

### Step A — refine bounding boxes

Image-based tightening of OCR bounding boxes. Existing functionality on
`Page.refine_bounding_boxes`; not part of this module.

### Step B — re-merge OCR-fragmented lines

`reorganize_lines(block)` walks pairwise through the block's lines and fuses
two adjacent `LINE` children when:

- Their Y bands overlap by at least `0.4 * mean_height`.
- Their X bands don't overlap by more than `0.1 * line.width` (they're not
  the same line OCR'd twice).
- Their heights differ by less than 50 % (drop-cap tolerance).
- Their per-word height ratio is below 1.20 OR the X gap between them is less
  than 2 % of coord-width (style-shift guard, prevents merging a caption into
  body text).
- Their X gap is less than 10 % of the median line width in the block.

Runs once before row-block grouping (on each existing OCR block), and once
per row block after Step F as a refinement pass.

### Step D — split mixed-content lines

`split_mixed_content_lines(paragraphs, page_width)` scans for OCR lines that
were stitched together from two visually distinct streams (e.g. the bottom of
a figure caption + the start of the wrapped body line). When a line has
neighbors that are markedly narrower than the page-median line width, it
tries `split_line_by_gap_and_word_height`:

- Find the largest intra-line word gap. If it's narrower than 2.2 % of
  coord-width, no split.
- The two halves must show a height ratio of at least 1.20 (or 1.02 if the
  caller hinted at a preferred split-X from the previous line's split).
- Content tiebreakers (right side starts lowercase, or left side ends in `-`
  or `,`) are used only to suppress unwanted splits, never to drive them.

### Step E — page header / page footer extraction

`extract_top_header_lines(lines, metrics)` peels the topmost band off the
line set as the page header. The band qualifies when:

1. The topmost line's `minY` is within `near_top_factor * coord_h` of the
   top of the page (default 12 %).
2. Every header line fits within a band of height
   `band_factor * median_word_h` starting at the topmost minY (default 1.5).
3. There is a clear vertical gap of at least `min_gap_factor * median_word_h`
   (default 0.7) between the band's bottom and the next non-header line.

`build_page_header_block(header_lines)` then collapses every word in the band
into a single LINE sorted by `minX`, packed into a PARAGRAPH and BLOCK with
`block_role_labels=["page header"]`. This is what merges
`"EARLY HERBALS" + "177"` into the single line `EARLY HERBALS 177` even when
the X gap between them is far wider than any normal word gap.

`extract_bottom_footer_lines` is the symmetric mirror.

The header/footer words are removed from the body pool before Step F runs.

### Step F — vertical row-block grouping

Two grouping strategies run; `_row_block_quality` picks the better one:

- `compute_text_row_blocks(body_lines)` — splits the page on inter-line Y
  gaps that exceed `tolerance + max(std * 0.75, median_h * 0.025)`. A
  side-by-side column band is detected by `overlap_x_amount(prev, curr) <= 0`
  and *suppresses* the split, so caption columns stay in one row block for
  Step H to handle.
- `_build_word_seeded_row_blocks(body_words)` — connected-component grouping
  on the words themselves with X/Y expansion thresholds. Robust when OCR's
  paragraph boundaries are noisy.

`_row_block_quality` scores by counting suspicious lines (very short, single
word, Y backtracks). The pipeline keeps the lower-scoring variant.

### Step H — column / floated-figure expansion

`expand_row_blocks(page, row_blocks, debug_squeezed_lines)` iterates every
row block and dispatches to one of:

| Detected shape | Handler | Output |
|---|---|---|
| Floated figure with wrapped body flow | `expand_floated_flow_row_block` | merged main flow (pre-band + band-body + left-rest + right-rest + post-band) followed by left-caption sidenote |
| Two narrow columns + spanning body | `expand_mixed_column_row_block` | two sub-shapes: (a) floated figure layout where spanning lines start above the columns: `body_before+right` → `left_caption` → `body_after`; or (b) standard side-by-side captions: `left → right → trailing_body` |
| 3+ columns | `expand_multi_column_row_block` | merged via `_merge_isolated_columns_into_flow` (left-to-right by median X) |
| Simple two-column | `expand_simple_two_column_row_block` | merged left-then-right |
| Single column | pass-through | original row block |

The floated-figure detector (`_detect_floated_flow_span`) requires:

- The row block's lines fall into two horizontally-disjoint clusters of
  squeezed (narrow) lines.
- The right cluster's median X is more than 14 % of coord-width to the right
  of the left cluster.
- At least one cluster is offset by at least 7 % of coord-width from the body
  margins.
- The squeezed clusters' Y range spans at least 3 line heights.
- At least 2 left-cluster lines fall inside the right-cluster's Y band.

The mixed-column detector (`_detect_mixed_column_split`) is more permissive
and catches the common shape of side-by-side captions followed by full-width
body.

### Step K — paragraph splits within a row block

`compute_text_paragraph_blocks(lines)` walks the row block's lines and
emits paragraph breaks when:

- The previous line's `maxX` is left of the right-tolerance band, **or**
- The current line's `minX` is right of the left-tolerance band (typical
  paragraph indent), **and**
- Several content rules don't suppress the break (lowercase continuation,
  same-band wrapped narrow lines, returning-to-margin after a wrap).

Runs only on row blocks classified as ordinary body (Step L handles special
blocks).

### Step L — classify special blocks

`classify_and_paragraphize_blocks(page, expanded_row_blocks)` calls
`_classify_row_block` with page-level stats (median line width, OCR Y extent,
body X extent). Possible classifications:

- **page header** — block is in the top 12 % of both image and OCR content
  AND has ≤3 lines.
- **page footer** — symmetric for the bottom.
- **sidenote left / right** — block bbox is entirely outside the body X
  extent (left of `body_minX - 2 % page_width` or right of `body_maxX + 2 %`).
- **poetry** — block lines are markedly narrower than median, left-indented,
  with high right-edge variance.
- **blockquote** — same as poetry but right edges are tight.
- **None (body)** — fall through to Step K paragraph splitting.

Special blocks get a thin wrapper via `wrap_special_role_block`. Body blocks
get full paragraph splitting via `compute_text_paragraph_blocks`.

### Step DC — drop-cap detection and stitching

`stitch_drop_caps(blocks, metrics)` walks each body BLOCK's paragraphs and
detects the oversized initial letter ("drop cap") that opens the first body
paragraph after a chapter heading. A paragraph qualifies as a drop cap when:

- It is a single-word paragraph (one LINE child, one visible Word).
- The word's height is at least `1.8 * median_word_h`.
- The word's text is 1–2 visible characters (handles OCR oddities like
  ``R'`` where the apostrophe is part of the same OCR token).

The next paragraph's first line is checked for a body word that:

- Sits to the right of the drop-cap centre (centroid comparison; small
  X-overlap is allowed because OCR can place the body word's left edge
  slightly inside the drop-cap glyph's bbox — up to 25% of cap width).
- Has its `minY` near the drop cap's `minY` (within `~1.5 * median_word_h`),
  i.e. shares the top baseline with the cap.

When detected:

1. The cap word's `word_components` get `"drop cap"` appended (using the
   existing `Word.word_components` schema; the label flows through to the
   labeler / training exports).
2. The cap word is moved to the front of the target line.
3. The cap word's text is trimmed to its first character — OCR
   commonly grabs an extra glyph alongside the oversized cap (a smudge,
   a stylistic flourish, or in the test4 case an apostrophe-like
   artifact). Trimming gives the labeler / GT matcher a clean cap-letter
   token and lets the rendered text read as one correct word
   (``"R"`` + ``"EADER!"`` → ``"READER!"`` instead of ``"R'EADER!"``).
4. The now-empty single-word paragraph is dropped from the block.

The cap and body word stay as two distinct ``Word`` objects in the line
so downstream tooling can reason about them separately:

- ``Word.text`` for the cap = the single initial letter (``"R"``).
- ``Word.bounding_box`` for the cap = the full cap-glyph bbox (large).
- ``Word.text`` for the body = the rest of the original word
  (``"EADER!"``).
- ``Block.text`` joins them with no separator because the cap carries
  ``word_components=["drop cap"]``, see :class:`Block`.

Ground-truth matching therefore sees two ``Word`` elements ``R`` and
``EADER!`` to align against the GT word ``READER!``: the matcher splits
the GT word's first character to the drop-cap word and the remainder to
the body word, and the cap's ``"drop cap"`` component flag survives the
match.

Special-role blocks (page header, footer, sidenote, poetry, blockquote,
recovered, page number, printers mark) are skipped — drop caps only appear
at the start of body paragraphs.

This decouples drop-cap handling from the OCR model. Two equally valid
approaches exist:

1. **Train the OCR model to read a drop cap as one word** — produces
   ``"READER!"`` directly. Requires labelled data and does not survive a
   model swap.
2. **Treat the cap as two words and stitch geometrically** — what this step
   does. Robust to model changes, easy to inspect (the `"drop cap"`
   component is a structured tag rather than baked-in text), and the
   downstream consumer can decide whether to render the cap differently.

We use approach 2.

#### Step DC fallback — cursive / decorative caps (`pd_book_tools.ocr.dropcap`)

`stitch_block_drop_caps` (the block-cap path) requires the OCR model
to have *recognised* the cap glyph as a 1–2 character Word.
Decorative serif / italic caps break that assumption — DocTR returns
either a stray ``"-"`` token or nothing at all where the cap glyph
sits. The unified Step DC entry point
`detect_and_stitch_drop_caps(blocks, image, metrics)` runs the
block-cap path first and then the cursive fallback
`detect_and_stitch_cursive_dropcaps(blocks, image, metrics)` for caps
the block-cap path missed. The fallback runs a small image-processing
and lexicon inference pipeline (geometric indent trigger →
`cv2.connectedComponentsWithStats` scan in the gap region →
single-letter prepend lookup against an embedded common-word
lexicon). Recovered caps carry the ``"drop cap"`` tag (so
`Block.text`'s empty-string-join rule fuses the cap to the next body
Word). Synthesised caps carry ``ocr_confidence=None`` as the
synthetic-origin signal for downstream tooling / training pipelines.
Unrecoverable cases are tagged ``"drop cap unrecovered"`` on the
closest body Word with a `logger.warning` — never silently dropped.
The unrecovered tag does NOT trigger the empty-string-join rule;
those Words render with the default space separator.

Both paths produce the same structural shape: the cap is its own
``Word`` at the front of the body line, and the body Word that
follows is untouched (NOT prepended with the cap letter). The
``Block.text`` empty-string-join rule fuses the rendered output —
cap "S" + body "tudies" renders as `Studies`, not `S tudies`.

See the ROADMAP entry "Drop-cap glyph recognition for cursive /
decorative caps" for the design history (Iteration A: cursive
fallback shipped; Iteration B: tag rationalization + Step DC
unification shipped).

### Final assembly

`assemble_final_blocks(page_header_block, body_blocks, page_footer_block)`
weaves the page-header band (extracted in Step E) at the front and the
page-footer band at the back, then stamps `override_page_sort_order` on each
top-level block so the page's sort-by-Y doesn't reorder them.

## Working with new fixtures

When a new printed-book page exposes a layout the existing heuristics
mishandle:

1. Drop the inputs into `tests/fixtures/layout_regression/inputs/<case>.{json,png}`.
2. Bootstrap a baseline with the dump helper:

   ```bash
   python tests/fixtures/layout_regression/dump_reorganize_output.py <case>
     > tests/fixtures/layout_regression/expected_text/baseline/<case>.reorganize.txt
   ```

3. Eyeball the dump against the source PNG and edit the baseline by hand to
   what you actually want.
4. Add `<case>` to the `@pytest.mark.parametrize` list in
   `tests/ocr/test_reorganize_page_utils_grouping.py`.
5. Run the test. On failure, the diff lands in
   `expected_text/diff/<case>.reorganize.diff.txt` and the per-step PNGs in
   `debug/<case>/`. Open `debug/<case>/index.html` in a browser to scroll
   through the pipeline state.
6. Identify which step is producing the wrong output (read the diff against
   the per-step PNGs), then audit that step's heuristic constants. Prefer
   tightening or relaxing the dynamic thresholds (`band_factor`,
   `near_top_factor`, gap multipliers, etc.) before adding content rules.

The `debug/`, `expected_text/current/`, and `expected_text/diff/` directories
are gitignored — only `inputs/` and `expected_text/baseline/` belong in
source control.

## Adding a new pipeline step

1. Implement the step as a module-level function in
   `reorganize_page_utils.py` taking `page` (or just lines/words) and
   returning the transformed structure. No state on `Page`.
2. Add a debug PNG writer (`write_step_X_debug_overlay_png`) and an emitter
   (`emit_step_X_debug`) following the existing patterns.
3. Hook the call into `Page.reorganize_page`'s outline body.
4. Run the regression suite. The new step's PNG will start showing up in
   `debug/<case>/` and `index.html` will pick it up automatically.

## Historical fixture-driven decisions

The existing heuristics were shaped by these specific failures from the
initial three-page fixture set:

- **test1** — `EARLY HERBALS` (centered) + `177` (right-aligned) on the same
  baseline. Drove Step E: a generic geometry-first header-band peel that
  collapses all words inside the band into one logical line, no matter how
  wide the gap between them. Fig. 72 (left) and Fig. 73 (right) caption
  columns were also being interleaved by Y; the side-by-side caption shape
  in `expand_mixed_column_row_block` emits left-column-first, right-second.
- **test2** — `178 FROM MAGIC TO SCIENCE` header (page number + title with a
  large gap), and body that wraps around a left-side figure. Drove the
  floated-figure-with-spanning-body sub-shape inside
  `expand_mixed_column_row_block`: when spanning lines start *above* the
  column region, output is `body_before+right_column → left_caption →
  body_after` rather than reading by Y.
- **test3** — `EARLY HERBALS 179` header where each piece OCR'd into a
  separate paragraph. Same Step E header-band peel handles it.

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
