---
Status: active
Owner: CT
Created: 2026-05-28
Last verified: 2026-07-13
Kind: spec
---

# Spec: Table Structure (rows / columns / cells) in the OCR model

> **Status**: Draft
> **Last updated**: 2026-05-28
> **Spec-Issue**: _(none yet)_

This spec adds a table-structure layer to the OCR page model. The layer takes
a table region that layout detection already flagged, recovers its row /
column / cell grid with a TATR-style structure detector, and assigns the
existing OCR `Word`s into a recursive tree. The tree reuses the model's own
`Block` idiom and has the shape `TABLE → CELL → LINE → Word`.

This is the **structure** layer only. PGDP table-syntax emission and any
table training pipeline are downstream or future work. See §3 and §9.

Related specs:

- `Spec: 01-page-model` defines the `Page` / `Block` / `Word` JSON form and
  the `block_role_labels` vocabulary. `"table"` already lives in that
  vocabulary, and this spec extends it.
- `Spec: 03-reorganize-pipeline` defines the reading-order pipeline. A
  recovered `TABLE` block must be placed into that pipeline.

---

## 1. TL;DR

1. Add `TABLE` and `CELL` members to `BlockCategory`
   (`pdomain_book_tools/ocr/block.py:43`). Shape:
   `TABLE (child_type=BLOCKS) → CELL (child_type=BLOCKS) → LINE (child_type=WORDS) → Word`.
2. Add four optional grid fields to `Block`: `row`, `col`, `rowspan`, and
   `colspan`, each defaulting to `None`. They are meaningful only on
   `CELL`-category blocks. Thread them through the **five** serialization and
   reconstruction sites in §4, or they are silently dropped.
3. Add a category-aware sort branch so a `TABLE` orders its `CELL` children
   **row-major by `(row, col)`** instead of the current bbox top-left sort
   (`block.py:317`). Add a `TABLE` / `CELL` rendering branch to `Block.text`
   (`block.py:508`).
4. Add a new **post-OCR** structure step that runs after words exist. A TATR
   detector adapter, built on HuggingFace transformers and the existing torch
   stack, emits row / column / spanning-cell boxes per table region.
   Pure-numpy geometry, with concepts ported from deepdoctection (Apache-2.0),
   assigns existing words to cells. The resulting `TABLE` block is placed in
   the page's reading order.
5. Hold the **no-silent-drop invariant**: every OCR `Word` ends up assigned to
   a cell or placed somewhere on the page. Words are never deleted during
   table assembly, including under spanning-cell logic. See §6.6 for the
   authoritative statement.

---

## 2. Context

### 2.1 What exists today

The OCR page model is already recursive and category-tagged:

- `Block` stores children in `_items: list[Word | Block]` (`block.py:162`).
  The `BlockChildType` enum `{WORDS, BLOCKS}` (`block.py:38`) switches between
  the two child shapes.
- A block's semantic role is the `BlockCategory` enum, today
  `{BLOCK, PARAGRAPH, LINE}` (`block.py:43`).
- A LINE is a `Block` with `block_category=LINE` and `child_type=WORDS`. A
  strict construction guard at `block.py:194-201` enforces this: a LINE whose
  `child_type` is set and is not `WORDS` raises `ValueError`. The guard is
  **LINE-only**. `PARAGRAPH` and `BLOCK` are not validated, and neither is any
  new category that uses `BLOCKS`.
- Only `Word` is a separate `@dataclass` (`word.py:55-56`). It carries its
  bbox, `ocr_confidence: float | None` (`word.py:87`), and ground-truth
  fields.
- `Block` is a hand-written class with **identity equality**, not a dataclass
  or pydantic model. See the note at `block.py:158-160`. New attributes
  therefore cannot perturb equality.

Tables are already a first-class layout concept downstream of detection:

- `"table"` is a member of `ALLOWED_BLOCK_ROLE_LABELS` (`block.py:82`).
- The role is stamped onto top-level blocks during layout by
  `bubble_block_roles_from_layout`
  (`pdomain_book_tools/ocr/layout_aware_reorg.py:634`), which the page
  pipeline calls at `page.py:3213`.

So the page model can already say "this region is a table." It cannot yet say
"this table has 4 rows and 3 columns, and this word lives in row 2, column 1."
That gap is what this spec closes.

### 2.2 The ML stack we already have

This repo's layout detection is built on torch and HuggingFace transformers.
The current detector is an RT-DETR layout model, the fork
`CT2534/PP-DocLayout_plus-L`. It is wired through `PPDocLayoutPlusLDetector`
(`pdomain_book_tools/layout/adapters/pp_doclayout.py:119`) and registered
behind the `LayoutDetector` Protocol
(`pdomain_book_tools/layout/detector.py:43`) via the registry's
`register_detector` (`pdomain_book_tools/layout/registry.py:257`).

The stack is already DETR-family plus transformers. So a TATR-style table
**structure** detector drops into the same adapter and registry pattern with
no new heavyweight dependency. The model is HuggingFace
`microsoft/table-transformer-structure-recognition`, a DETR model trained on
PubTables-1M. We explicitly **avoid** the classic deepdoctection
Cascade-R-CNN / Detectron2 route, which would add an incompatible detection
framework.

### 2.3 Why deepdoctection, and how we use it

We evaluated the deepdoctection project (Apache-2.0) for table-aware OCR. Its
table reconstruction has two separable halves:

- A **detector** half, the Detectron2 Cascade-R-CNN. We reject this half and
  use TATR instead.
- A **pure-geometry** half in `pipe/segment.py` and `pipe/order.py`. This is
  box-math that turns detected row / column / spanning-cell boxes plus a set
  of word boxes into a filled cell grid. It is plain intersection and span
  reasoning with no ML.

The decision is to **reimplement the pure-geometry half** as plain numpy box
math, with attribution per §9.4, and to depend on TATR for the boxes. We
borrow concepts, not code.

---

## 3. Goals / Non-Goals

### Goals

- Represent table structure (rows, columns, cells, spans) inside the existing
  `Block` model using its own idiom, with no parallel data structure.
- Recover that structure from already-flagged `"table"` regions in a post-OCR
  step, assigning the existing OCR `Word`s to cells.
- Round-trip the structure losslessly through `to_dict`, `from_dict`, pydantic
  validation, and `scale`.
- Place recovered tables correctly in page reading order.
- Hold the no-silent-drop invariant for words during assembly.

### Non-Goals (out of scope)

- **PGDP table-syntax emission.** Turning the recovered grid into PGDP
  `|`-delimited markup lives **downstream in `pdomain-ocr-cli`**, not here.
  This repo produces the table _structure_; PGDP rendering is a separate
  downstream slice.
- **Rich-text / HTML table rendering.** `Block.text` gains only a plain-text
  grid rendering branch. Any structured emission (HTML, markdown, PGDP) is a
  downstream consumer's job, reading the grid fields.
- **Training on table data.** Fine-tuning the structure detector and capturing
  human-corrected grids is a separate future cross-repo plan. §9.5 flags it
  but does not design it.
- **Nested tables**, meaning a table inside a cell. These are out of scope for
  the initial slices. The recursive model can represent them later without a
  schema change.

---

## 4. Constraints

- **Five-site field threading (hard hazard).** Every new `Block` field must be
  added to all five of these sites:
  - `__init__` (`block.py:164`)
  - the `scale` reconstructor (`block.py:1009`), which must forward **all**
    metadata; see the existing field list at `block.py:1017-1034`
  - `to_dict` (`block.py:1047`)
  - `from_dict` (`block.py:1073`)
  - the pydantic core-schema `typed_dict_schema` (`block.py:1276`, inside
    `__get_pydantic_core_schema__` at `block.py:1255`)

  Omitting a field from `to_dict`, `from_dict`, or the pydantic schema
  silently drops it. This is a known repo hazard. See the agent-memory note
  _"Pydantic schema must list all fields; scale() must forward all metadata."_
  The grid fields must appear at all five sites and ship with explicit
  round-trip tests.
- **Identity equality is preserved.** `Block` uses identity equality
  (`block.py:158-160`), so adding optional fields cannot break existing
  equality-based tests.
- **The LINE guard must not be widened.** The strict guard
  (`block.py:194-201`) fires only for LINE. Both `CELL` and `TABLE` use
  `child_type=BLOCKS`, so neither trips the guard, and the happy path needs
  **no new guard**. An optional defensive guard for `CELL` / `TABLE` shapes is
  an open question; see §9.3.
- **Coordinate-system discipline.** Per repo rules, never silently coerce
  coordinate systems. TATR runs on a **cropped** table image. Its box outputs
  must be mapped back into page coordinates before assignment, and
  `is_normalized` semantics must be preserved end-to-end.
- **No-silent-drop invariant.** Words are never deleted during table assembly.
  This is a standing workspace rule for this repo's reorganize and OCR code.
  §6.6 holds the authoritative statement.

---

## 5. Options Considered

### 5.1 Data model: how to represent cells

**Option A — TABLE / CELL as new `BlockCategory` members (chosen).** Reuse the
recursive `Block` tree:
`TABLE (BLOCKS) → CELL (BLOCKS) → LINE (WORDS) → Word`. Grid coordinates ride
on the `CELL` block as optional fields. This fits the model's existing idiom,
serializes through the existing machinery, and inherits reading-order and text
rendering with small targeted branches.

**Option B — a separate `Table` dataclass parallel to `Block` (rejected).** It
duplicates serialization, scaling, reading-order, and text logic. Every
downstream consumer would need a second traversal path.

**Option C — store grid metadata only in `additional_block_attributes`
(rejected).** This is the existing free-form dict at `block.py:178`. It is
rejected for the structural fields: the dict is untyped, invisible to the
pydantic schema, and easy to drop. The free-form dict stays available for
genuinely ad-hoc detector metadata, such as raw confidence scores.

### 5.2 Structure detector

- **TATR via HF transformers (chosen).** It is DETR-family, matches the
  existing torch stack, and registers like `pp_doclayout.py`.
- **deepdoctection Cascade-R-CNN / Detectron2 (rejected).** It is an
  incompatible detection framework and a heavy new dependency.

### 5.3 Cell-assignment geometry

- **Port deepdoctection's pure box-math as numpy functions (chosen).** It
  needs no ML, is unit-testable with synthetic boxes, and ships with
  Apache-2.0 attribution.
- **Hand-roll a fresh grid heuristic (rejected).** It reinvents well-tested
  span and tiling logic for no benefit.

---

## 6. Decision

### 6.1 Data-model changes

Add to `BlockCategory` (`block.py:43`):

```python
class BlockCategory(Enum):
    BLOCK = "BLOCK"
    PARAGRAPH = "PARAGRAPH"
    LINE = "LINE"
    TABLE = "TABLE"   # child_type=BLOCKS, children are CELL blocks
    CELL = "CELL"     # child_type=BLOCKS, children are LINE blocks
```

Add four optional `Block` fields, each defaulting to `None` and meaningful
only on `CELL`-category blocks:

| field | type | meaning |
|---|---|---|
| `row` | `int \| None` | zero-based origin row index of the cell |
| `col` | `int \| None` | zero-based origin column index of the cell |
| `rowspan` | `int \| None` | rows the cell covers (default 1 on a CELL) |
| `colspan` | `int \| None` | columns the cell covers (default 1 on a CELL) |

Add these to `__init__`, `scale`, `to_dict`, `from_dict`, and the pydantic
`typed_dict_schema`. These are the five sites in §4. On non-`CELL` blocks the
fields stay `None` and round-trip as absent or null.

### 6.2 Row-major cell sort

`_sort_items` (`block.py:317`) today sorts by bbox top-left for
`child_type=WORDS` and by bbox order for child blocks. For a `TABLE` this is
**wrong**: a spanning cell or a slightly misaligned cell box can reorder the
grid. Add a category-aware branch. When `block_category == TABLE`, sort the
`CELL` children **row-major by `(row, col)`**, and fall back to bbox top-left
only when grid coordinates are absent. The existing WORDS and generic branches
do not change.

### 6.3 Plain-text grid rendering

`Block.text` (`block.py:508`) is already type-dispatched: WORDS joins on
spaces, PARAGRAPH joins on `\n`, and other shapes join on `\n\n`. Add a
`TABLE` / `CELL` branch that renders the grid as plain text. Rows are separated
by newlines, and cells within a row are separated by a simple delimiter such
as a tab. This is **plain-text only**, with no PGDP or HTML markup; see the §3
Non-Goals. A spanning cell renders once, in its origin slot.

### 6.4 Merged / spanning cells

A spanning cell, meaning one with `rowspan` or `colspan` greater than 1, is
stored **once**. It is the origin `CELL` at its top-left `(row, col)` with the
span set. The grid slots it covers are **absent** from the parent `TABLE`'s
items list. Consumers reconstruct the full grid from
`(row, col, rowspan, colspan)`, **not** from the child count. This mirrors
deepdoctection's rule that a spanning cell deactivates the simple cells it
covers. So a `4×3` table with one cell spanning two columns has 11 `CELL`
children, not 12.

This shapes traversal: any code that wants a dense grid must expand spans
itself. The stored tree is the sparse, origin-only form.

### 6.5 Post-OCR structure pipeline

The step runs **after OCR**, so words already exist on the page. The stages
are:

1. **Table-region detection (exists).** The `"table"` role label is already
   stamped at `page.py:3213` via `bubble_block_roles_from_layout` and the
   existing `LayoutDetector`
   (`pdomain_book_tools/layout/detector.py:43`). No new work is needed; this
   stage just identifies the regions to process.
2. **Table-structure detection (new).** A new detector adapter, TATR via HF
   transformers, crops each `"table"` region, runs structure recognition, and
   emits row / column / spanning-cell boxes in page coordinates. The adapter
   is registered through `register_detector`
   (`pdomain_book_tools/layout/registry.py:257`) exactly like
   `pp_doclayout.py:119`, behind the same Protocol shape.
3. **Cell-to-word assignment (new, pure numpy).** Port the deepdoctection
   geometry concepts (Apache-2.0; see §9.4) as plain numpy functions:
   - `match_anns_by_intersection` matches boxes by an IoU or IoA threshold. A
     "span" is the count of intersecting items above threshold.
   - `stretch_item_per_table` extends row boxes to the full table width and
     column boxes to the full table height.
   - `tile_tables_with_items_per_table` fills gaps so every grid slot maps to a
     region, leaving no uncovered area.
   - `choose_items_by_iou` prunes duplicate row and column detections.
   - `create_intersection_cells` builds cells from the row × column product.
     Spanning cells deactivate the simple cells they cover; see §6.4.

   Then assign the **existing** OCR `Word`s to cells by box overlap. No new
   words are created, and none are discarded.
4. **Tree build and reading-order placement (new).** Build the
   `CELL → LINE → Word` subtree per cell, grouping the assigned words into LINE
   blocks. Assemble the `TABLE` block, then place it in the page's normal
   reading-order stream. Use the column-clustering concept from deepdoctection
   `order.py` for the page-level sort, consistent with
   `Spec: 03-reorganize-pipeline`.

### 6.6 No-silent-drop invariant

This is the authoritative statement of the invariant. Every OCR `Word` in a
table region must end up assigned to a cell **or** placed somewhere on the
page. Words are never dropped during table assembly, including under
spanning-cell logic.

A word that falls outside every detected cell, from a detector gap or
mis-detection, must be routed to a fallback. The fallback may be a nearest-cell
assignment or a non-table block in reading order; see the open question in
§9.2. A word is never deleted. Slice A and Slice B both ship explicit tests
that assert word-count conservation:
`sum of words across cells + fallback == input word count`.

---

## 7. Implementation Plan

Each slice is independently shippable.

### Slice A — data model only

- Add `TABLE` / `CELL` to `BlockCategory`. Add the `row`, `col`, `rowspan`,
  and `colspan` fields.
- Thread all four through the five sites in §4: `__init__`, `scale`,
  `to_dict`, `from_dict`, and the pydantic `typed_dict_schema`.
- Add the row-major `TABLE` sort branch to `_sort_items`; see §6.2.
- Add the `TABLE` / `CELL` plain-text branch to `Block.text`; see §6.3.
- **No detector.** Construct tables by hand in tests.
- Tests: round-trip through `to_dict` / `from_dict` / pydantic; `scale`
  preserves the grid fields; row-major sort, including a spanning cell; span
  reconstruction; text rendering; word-count conservation on a hand-built
  table.

### Slice B — pure-geometry cell assignment

- Implement the numpy geometry functions from §6.5 stage 3 in a new module.
- Input: row / column / cell boxes plus word boxes. Output: a `CELL` tree, or
  the assignment map that Slice D turns into one.
- Unit-test with **synthetic boxes only, no ML**: a simple grid, a spanning
  cell, duplicate row detections, words straddling a boundary, words in no cell
  (the fallback path), and word-count conservation.

### Slice C — TATR detector adapter

- Add a new adapter wrapping
  `microsoft/table-transformer-structure-recognition` via HF transformers,
  behind the `LayoutDetector` Protocol shape and registered through
  `register_detector`. This mirrors `pp_doclayout.py:119`.
- Crop, infer, then map boxes back to page coordinates while preserving
  `is_normalized`.
- Gate tests as slow / model-download, mirroring the existing slow-test
  convention. Exercise both CPU and GPU paths where feasible.

### Slice D — pipeline wiring

- Wire stages 1 through 4 from §6.5 into the page pipeline: detect table
  regions, then structure-detect, then assign words, then build the `TABLE`
  tree, then place it in reading order.
- Keep reading-order placement consistent with `Spec: 03-reorganize-pipeline`.
- Add an end-to-end test on a fixture table page, and assert the no-silent-drop
  invariant on real OCR output.

---

## 8. Test Plan

- **Round-trip (Slice A).** A hand-built `TABLE → CELL → LINE → Word` tree
  survives `to_dict` → `from_dict` and pydantic `validate_python` with all grid
  fields intact, and `scale` preserves them. This guards against the five-site
  drop hazard.
- **Spanning cells (Slices A, B).** The sparse origin-only storage from §6.4
  reconstructs the dense grid correctly, and the row-major sort places a
  spanning cell at its origin.
- **Geometry (Slice B).** Synthetic-box unit tests for each ported function:
  match, stretch, tile, dedup, and intersection-cells.
- **No-silent-drop (Slices B, D).** Word-count conservation is asserted:
  `cells + fallback == input`.
- **Detector (Slice C).** A slow, model-download smoke test confirms TATR
  returns plausible row and column boxes for a fixture table crop, and that the
  box-to-page coordinate mapping is correct.
- **End-to-end (Slice D).** A fixture table page produces a placed `TABLE`
  block in reading order with all words assigned.

---

## 9. Open Questions

### 9.1 LINE grouping inside a cell

How should assigned words inside a cell be grouped into `LINE` blocks? The
options are to reuse the existing line-grouping heuristic from the reorganize
pipeline, or to use a cell-local vertical clustering. Cells are small, so the
page-level heuristic may be overkill.

### 9.2 Fallback placement for unassigned words

When a word falls outside every detected cell (§6.6), what is the fallback? The
options are a nearest-cell snap, a synthetic edge cell, or a non-table block
adjacent to the table in reading order. Any choice must satisfy
no-silent-drop.

### 9.3 Defensive guard for CELL / TABLE shapes

The LINE guard (`block.py:194-201`) is deliberately LINE-only. Do we add an
optional defensive guard that a `CELL` or `TABLE` uses `child_type=BLOCKS`, or
do we leave the shapes unvalidated to match PARAGRAPH and BLOCK? The current
lean is toward **no new guard**, to match the existing leniency.

### 9.4 deepdoctection attribution (Apache-2.0)

The cell-assignment geometry (§6.5 stage 3) and the page-level
column-clustering (§6.5 stage 4) reimplement concepts from deepdoctection's
`pipe/segment.py` and `pipe/order.py` (Apache-2.0). The implementation must
carry an attribution note in the module docstring. If the workspace keeps a
`THIRD_PARTY` or licenses ledger, it must also carry an entry there. We borrow
**concepts and algorithm shape**, not source. Confirm the attribution wording
against the license-ledger convention before Slice B merges.

### 9.5 Future: training (out of scope here, flagged only)

These three points are captured for a future cross-repo training plan. They
are **not designed in this spec**:

- (a) The new grid fields plus the existing `Word` ground-truth fields mean
  recovered cells carry ground truth **for free**. A human-corrected grid is
  just corrected `(row, col, rowspan, colspan)` on `CELL` blocks plus corrected
  word text.
- (b) Fine-tuning a table-**structure** detector is **new ground** for
  `pdomain-ocr-training`, which today owns only DocTR detection and recognition
  training. A TATR fine-tune is a different model family and would need its own
  training surface there.
- (c) The labeler (`pdomain-ocr-labeler-spa`) is where corrected grids would be
  captured, via a table-grid editing surface that feeds ground truth back.

These are pointers for the future plan, not commitments in this spec.

## Adversarial Review

- **Stage:** Migration/design review performed 2026-07-13; no implementation was found.
- **Source:** Full spec and current `Block`, page pipeline, layout detector/registry, serialization, and test code.
- **Accepted findings (and how folded in):** Resolve unassigned-word placement and cell-local line grouping before treating Slices B/D as implementable; define an exact text-rendering contract; specify TATR label/threshold and resize-to-page coordinate mapping; define how existing table-role blocks are replaced without duplication; and add structural validation plus compatibility tests for sparse spans.
- **Disposition:** Accepted corrections and unresolved ideas are preserved in `docs/context/intent-map.md` as deferred work or owner decisions; the source body remains unchanged pending its next evidence-backed revision.
- **Residual risks:** Model availability, historical-scan accuracy, licensing attribution, CPU/GPU resource cost, and real-fixture word conservation remain unproven. The recursive Block change affects every serializer and downstream traversal.
