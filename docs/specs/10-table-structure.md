# Spec: Table Structure (rows / columns / cells) in the OCR model

> **Status**: Draft
> **Last updated**: 2026-05-28
> **Spec-Issue**: _(none yet)_

Add a table-structure layer to the OCR page model: detect tables already
flagged during layout, recover their row / column / cell grid with a
TATR-style structure detector, and assign existing OCR `Word`s into a
recursive `TABLE → CELL → LINE → Word` tree built from the model's existing
`Block` idiom. This is the **structure** layer only — PGDP table-syntax
emission and any table training pipeline are explicitly downstream / future
(see §3 and §9).

Related specs:

- `Spec: 01-page-model` — the `Page` / `Block` / `Word` JSON form and the
  `block_role_labels` vocabulary (`"table"` already lives there) that this
  spec extends.
- `Spec: 03-reorganize-pipeline` — the reading-order pipeline into which a
  recovered `TABLE` block must be placed.

---

## 1. TL;DR

1. Add `TABLE` and `CELL` members to `BlockCategory`
   (`pdomain_book_tools/ocr/block.py:43`). Shape:
   `TABLE (child_type=BLOCKS) → CELL (child_type=BLOCKS) → LINE (child_type=WORDS) → Word`.
2. Add four optional grid fields — `row`, `col`, `rowspan`, `colspan`
   (default `None`) — to `Block`, meaningful only on `CELL`-category blocks.
   Thread them through **five** serialization / reconstruction sites or they
   are silently dropped.
3. Add a category-aware sort branch so a `TABLE` orders its `CELL` children
   **row-major by `(row, col)`** instead of the current bbox top-left sort
   (`block.py:317`), and a `TABLE`/`CELL` rendering branch to `Block.text`
   (`block.py:508`).
4. A new **post-OCR** structure step runs after words exist: a TATR detector
   adapter (HuggingFace transformers, reusing the existing torch stack)
   emits row / column / spanning-cell boxes per table region; pure-numpy
   geometry (ported from deepdoctection, Apache-2.0) assigns existing words
   to cells; the resulting `TABLE` block is placed in the page's reading
   order.
5. **No-silent-drop invariant**: every OCR `Word` ends up assigned to a cell
   or placed somewhere. Words are never deleted during table assembly,
   including under spanning-cell logic.

---

## 2. Context

### 2.1 What exists today

The OCR page model is already recursive and category-tagged:

- `Block` stores children in `_items: list[Word | Block]`
  (`block.py:162`), switched by the `BlockChildType` enum
  `{WORDS, BLOCKS}` (`block.py:38`).
- The semantic role of a block is the `BlockCategory` enum, today
  `{BLOCK, PARAGRAPH, LINE}` (`block.py:43`).
- A "LINE" is just a `Block` with `block_category=LINE` and
  `child_type=WORDS`. This is enforced by a strict construction guard at
  `block.py:194-201`: a `LINE` whose `child_type` is set and is not `WORDS`
  raises `ValueError`. The guard is **LINE-only** — `PARAGRAPH`/`BLOCK` (and,
  by extension, any new category using `BLOCKS`) are not validated.
- Only `Word` is a separate `@dataclass` (`word.py:55-56`), carrying its
  bbox, `ocr_confidence: float | None` (`word.py:87`), and ground-truth
  fields.
- `Block` is a hand-written class with **identity equality** (not a
  dataclass / pydantic model — see the note at `block.py:158-160`). New
  attributes therefore cannot perturb equality.

Tables are already a first-class layout concept downstream of detection:

- `"table"` is a member of `ALLOWED_BLOCK_ROLE_LABELS` (`block.py:82`).
- It is stamped onto top-level blocks during layout by
  `bubble_block_roles_from_layout` (`page.py:3209`).

So the page model can already say "this region is a table." It cannot yet
say "this table has 4 rows and 3 columns, and this word lives in row 2,
column 1." That is the gap this spec closes.

### 2.2 The ML stack we already have

This repo's layout detection is **torch + HuggingFace transformers** based.
The current detector is an RT-DETR layout model (fork
`CT2534/PP-DocLayout_plus-L`) wired through `PPDocLayoutPlusLDetector`
(`layout/adapters/pp_doclayout.py:119`), registered behind the
`LayoutDetector` Protocol (`layout/detector.py:43`) via the registry's
`register_detector` (`layout/registry.py:257`).

Because the stack is already DETR-family + transformers, a TATR-style table
**structure** detector — HuggingFace
`microsoft/table-transformer-structure-recognition`, a DETR model trained on
PubTables-1M — drops into the same adapter + registry pattern with no new
heavyweight dependency. We explicitly **avoid** the classic deepdoctection
Cascade-R-CNN / Detectron2 route, which would add an incompatible detection
framework.

### 2.3 Why deepdoctection, and how we use it

We evaluated the deepdoctection project (Apache-2.0) for table-aware OCR. Its
table reconstruction has two separable halves:

- A **detector** half (Detectron2 Cascade-R-CNN) — rejected; we use TATR
  instead.
- A **pure-geometry** half in `pipe/segment.py` and `pipe/order.py`:
  box-math that turns detected row / column / spanning-cell boxes plus a set
  of word boxes into a filled cell grid. This is plain intersection / span
  reasoning with no ML.

The decision is to **reimplement the pure-geometry half** as plain numpy box
math (with attribution — see §9.4), and depend on TATR for the boxes. We
borrow concepts, not code.

---

## 3. Goals / Non-Goals

### Goals

- Represent table structure (rows, columns, cells, spans) inside the
  existing `Block` model using its own idiom — no parallel data structure.
- Recover that structure from already-flagged `"table"` regions in a
  post-OCR step, assigning existing OCR `Word`s to cells.
- Round-trip the structure losslessly through `to_dict` / `from_dict` /
  pydantic validation and through `scale`.
- Place recovered tables correctly in page reading order.
- Guarantee the no-silent-drop invariant for words during assembly.

### Non-Goals (out of scope)

- **PGDP table-syntax emission.** Turning the recovered grid into PGDP
  `|`-delimited table markup lives **downstream in `pdomain-ocr-cli`**, not
  here. This repo produces the table _structure_; PGDP rendering is a
  separate downstream slice.
- **Rich-text / HTML table rendering.** `Block.text` gains only a
  plain-text grid rendering branch. Any structured (HTML / markdown /
  PGDP) emission is a downstream consumer's job, reading the grid fields.
- **Training on table data.** Fine-tuning the structure detector and
  capturing human-corrected grids is a separate future cross-repo plan,
  flagged in §9 but not designed here.
- **Nested tables** (a table inside a cell) are out of scope for the initial
  slices; the recursive model can represent them later without a schema
  change.

---

## 4. Constraints

- **Five-site field threading (hard hazard).** Every new `Block` field must
  be added to all of: `__init__` (`block.py:164`), the `scale` reconstructor
  (`block.py:1009`, which must forward **all** metadata — see the existing
  field list at `block.py:1017-1034`), `to_dict` (`block.py:1047`),
  `from_dict` (`block.py:1073`), and the pydantic core-schema
  `typed_dict_schema` (`block.py:1276`, inside
  `__get_pydantic_core_schema__` at `block.py:1255`). **Omitting a field
  from `to_dict` / `from_dict` / the pydantic schema silently drops it** —
  this is a known repo hazard (see agent-memory
  _"Pydantic schema must list all fields; scale() must forward all
  metadata"_). The grid fields must appear at all five sites with explicit
  round-trip tests.
- **Identity equality is preserved.** Because `Block` uses identity equality
  (`block.py:158-160`), adding optional fields cannot break existing
  equality-based tests.
- **The LINE guard must not be widened.** The strict guard
  (`block.py:194-201`) fires only for `LINE`. `CELL` uses `child_type=BLOCKS`
  and `TABLE` uses `child_type=BLOCKS`, so neither trips the guard and **no
  new guard is required** for the happy path. (An optional defensive guard
  for `CELL`/`TABLE` shapes is an open question — §9.3.)
- **Coordinate-system discipline.** Per repo rules, never silently coerce
  coordinate systems. TATR runs on a **cropped** table image; its box
  outputs must be mapped back into page coordinates before assignment, and
  `is_normalized` semantics must be preserved end-to-end.
- **No-silent-drop invariant.** Words are never deleted during table
  assembly. This is a standing workspace rule for this repo's reorganize /
  OCR code.

---

## 5. Options Considered

### 5.1 Data model: how to represent cells

**Option A — TABLE / CELL as new `BlockCategory` members (chosen).**
Reuse the recursive `Block` tree:
`TABLE (BLOCKS) → CELL (BLOCKS) → LINE (WORDS) → Word`. Grid coordinates ride
on the `CELL` block as optional fields. Fits the model's existing idiom,
serializes through the existing machinery, and inherits reading-order and
text rendering with small targeted branches.

**Option B — a separate `Table` dataclass parallel to `Block`.** Rejected:
duplicates serialization, scaling, reading-order, and text logic; every
downstream consumer would need a second traversal path.

**Option C — store grid metadata only in `additional_block_attributes`**
(the existing free-form dict at `block.py:178`). Rejected for the structural
fields: untyped, invisible to the pydantic schema, and easy to drop. (The
free-form dict remains available for genuinely ad-hoc detector metadata such
as raw confidence scores.)

### 5.2 Structure detector

- **TATR via HF transformers (chosen)** — DETR-family, matches the existing
  torch stack, registers like `pp_doclayout.py`.
- **deepdoctection Cascade-R-CNN / Detectron2 (rejected)** — incompatible
  detection framework, heavy new dependency.

### 5.3 Cell-assignment geometry

- **Port deepdoctection's pure box-math as numpy functions (chosen)** —
  no ML, unit-testable with synthetic boxes, Apache-2.0 attribution.
- **Hand-roll a fresh grid heuristic (rejected)** — reinvents well-tested
  span / tiling logic for no benefit.

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

Add four optional `Block` fields, default `None`, meaningful only on
`CELL`-category blocks:

| field | type | meaning |
|---|---|---|
| `row` | `int \| None` | zero-based origin row index of the cell |
| `col` | `int \| None` | zero-based origin column index of the cell |
| `rowspan` | `int \| None` | rows the cell covers (default 1 when on a CELL) |
| `colspan` | `int \| None` | columns the cell covers (default 1 when on a CELL) |

These are added to `__init__`, `scale`, `to_dict`, `from_dict`, and the
pydantic `typed_dict_schema` (the five sites in §4). On non-`CELL` blocks they
stay `None` and round-trip as absent / null.

### 6.2 Row-major cell sort

`_sort_items` (`block.py:317`) currently sorts purely by bbox top-left for
`child_type=WORDS`, and by bbox order for child blocks. For a `TABLE` this is
**wrong**: a spanning cell or a slightly misaligned cell box can reorder the
grid. Add a category-aware branch: when `block_category == TABLE`, sort the
`CELL` children **row-major by `(row, col)`**, falling back to bbox top-left
only when grid coordinates are absent. The existing WORDS / generic branches
are unchanged.

### 6.3 Plain-text grid rendering

`Block.text` (`block.py:508`) is already type-dispatched (WORDS → joined,
PARAGRAPH → `\n`, else → `\n\n`). Add a `TABLE` / `CELL` branch that renders
the grid as plain text (rows separated by newlines, cells within a row
separated by a simple delimiter such as a tab). **Plain-text only** — no
PGDP / HTML markup (§3 Non-Goals). Spanning cells render once in their origin
slot.

### 6.4 Merged / spanning cells

A spanning cell (`rowspan` or `colspan` > 1) is stored **once**, as the
origin `CELL` at its top-left `(row, col)` with the span set. The grid slots
it covers are **absent** from the parent `TABLE`'s items list — consumers
reconstruct the full grid from `(row, col, rowspan, colspan)`, **not** from
the child count. This mirrors deepdoctection's "spanning cell deactivates the
covered simple cells" rule. A `4×3` table with one cell spanning two columns
therefore has 11 `CELL` children, not 12.

Implication for traversal: any code that wants a dense grid must expand spans
itself; the stored tree is the sparse origin-only form.

### 6.5 Post-OCR structure pipeline

The step runs **after OCR** — words already exist on the page. Stages:

1. **Table-region detection (exists).** The `"table"` role label is already
   stamped (`page.py:3209`) via the existing `LayoutDetector`
   (`layout/detector.py:43`). No new work; this stage just identifies the
   regions to process.
2. **Table-structure detection (new).** A new detector adapter — TATR via HF
   transformers — crops each `"table"` region, runs structure recognition,
   and emits row / column / spanning-cell boxes in page coordinates. The
   adapter is registered through `register_detector`
   (`layout/registry.py:257`) exactly like `pp_doclayout.py:119`, behind the
   same Protocol shape.
3. **Cell → word assignment (new, pure numpy).** Port the deepdoctection
   geometry concepts (Apache-2.0, §9.4) as plain numpy functions:
   - `match_anns_by_intersection` — match boxes by IoU / IoA threshold; a
     "span" is the count of intersecting items above threshold.
   - `stretch_item_per_table` — extend row boxes to full table width and
     column boxes to full table height.
   - `tile_tables_with_items_per_table` — fill gaps so every grid slot maps
     to a region (no uncovered area).
   - `choose_items_by_iou` — prune duplicate row / column detections.
   - `create_intersection_cells` — build cells from row × column products;
     spanning cells deactivate the simple cells they cover (§6.4).

   Then assign **existing** OCR `Word`s to cells by box overlap. No new words
   are created and none are discarded.
4. **Tree build + reading-order placement (new).** Construct the
   `CELL → LINE → Word` subtree per cell (grouping assigned words into LINE
   blocks), assemble the `TABLE` block, and place it in the page's normal
   reading-order stream. Use deepdoctection `order.py`'s column-clustering
   concept for the page-level sort, consistent with
   `Spec: 03-reorganize-pipeline`.

### 6.6 No-silent-drop invariant

Every OCR `Word` in a table region must end up assigned to a cell **or**
placed somewhere on the page; words are never dropped during table assembly,
including under spanning-cell logic. Words that fall outside every detected
cell (detector gaps, mis-detection) must be routed to a fallback — e.g. a
nearest-cell assignment or a non-table block in reading order — never
deleted. Slice A and Slice B both ship explicit tests asserting word-count
conservation: `sum of words across cells + fallback == input word count`.

---

## 7. Implementation Plan

Each slice is independently shippable.

### Slice A — data model only

- Add `TABLE` / `CELL` to `BlockCategory`; add `row` / `col` / `rowspan` /
  `colspan` fields.
- Thread all four through the five sites (§4): `__init__`, `scale`,
  `to_dict`, `from_dict`, pydantic `typed_dict_schema`.
- Add the row-major `TABLE` sort branch to `_sort_items` (§6.2).
- Add the `TABLE` / `CELL` plain-text branch to `Block.text` (§6.3).
- **No detector.** Construct tables by hand in tests.
- Tests: round-trip (`to_dict`/`from_dict`/pydantic), `scale` preserves grid
  fields, row-major sort (including a spanning cell), span reconstruction,
  text rendering, word-count conservation on a hand-built table.

### Slice B — pure-geometry cell assignment

- Implement the numpy geometry functions (§6.5 stage 3) in a new module.
- Input: row / column / cell boxes + word boxes. Output: a `CELL` tree (or
  the assignment map Slice D turns into one).
- Unit-tested with **synthetic boxes only — no ML**: simple grid, spanning
  cell, duplicate row dets, words straddling a boundary, words in no cell
  (fallback path), word-count conservation.

### Slice C — TATR detector adapter

- New adapter wrapping `microsoft/table-transformer-structure-recognition`
  via HF transformers, behind the `LayoutDetector` Protocol shape and
  registered through `register_detector` (mirrors `pp_doclayout.py:119`).
- Crop → infer → map boxes back to page coordinates (preserve
  `is_normalized`).
- Tests gated as slow / model-download (mirror the existing slow-test
  convention); CPU and GPU paths both exercised where feasible.

### Slice D — pipeline wiring

- Wire stages 1–4 (§6.5) into the page pipeline: detect table regions →
  structure-detect → assign words → build `TABLE` tree → place in reading
  order.
- Reading-order placement consistent with `Spec: 03-reorganize-pipeline`.
- End-to-end test on a fixture table page; assert the no-silent-drop
  invariant on real OCR output.

---

## 8. Test Plan

- **Round-trip** (Slice A): a hand-built `TABLE → CELL → LINE → Word` tree
  survives `to_dict` → `from_dict` and pydantic `validate_python` with all
  grid fields intact; `scale` preserves them. Regression guard against the
  five-site drop hazard.
- **Spanning cells** (Slices A, B): the sparse origin-only storage (§6.4)
  reconstructs the dense grid correctly; row-major sort places a spanning
  cell at its origin.
- **Geometry** (Slice B): synthetic-box unit tests for each ported function
  (match / stretch / tile / dedup / intersection-cells).
- **No-silent-drop** (Slices B, D): word-count conservation asserted —
  `cells + fallback == input`.
- **Detector** (Slice C): slow / model-download smoke test that TATR returns
  plausible row / column boxes for a fixture table crop; box-to-page
  coordinate mapping is correct.
- **End-to-end** (Slice D): a fixture table page produces a placed `TABLE`
  block in reading order with all words assigned.

---

## 9. Open Questions

### 9.1 LINE grouping inside a cell

Within a cell, how are assigned words grouped into `LINE` blocks — reuse the
existing line-grouping heuristic from the reorganize pipeline, or a
cell-local vertical clustering? (Cells are small; the page-level heuristic
may be overkill.)

### 9.2 Fallback placement for unassigned words

When a word falls outside every detected cell (§6.6), what is the fallback —
nearest-cell snap, a synthetic edge cell, or a non-table block adjacent to
the table in reading order? Must satisfy no-silent-drop either way.

### 9.3 Defensive guard for CELL / TABLE shapes

The LINE guard (`block.py:194-201`) is deliberately LINE-only. Do we add an
optional defensive guard that a `CELL`/`TABLE` uses `child_type=BLOCKS`, or
leave shapes unvalidated (consistent with PARAGRAPH/BLOCK)? Leaning toward
**no new guard** to match existing leniency.

### 9.4 deepdoctection attribution (Apache-2.0)

The cell-assignment geometry (§6.5 stage 3) and the page-level
column-clustering (§6.5 stage 4) reimplement concepts from deepdoctection's
`pipe/segment.py` and `pipe/order.py` (Apache-2.0). The implementation must
carry an attribution note in the module docstring and, if the workspace keeps
a `THIRD_PARTY` / licenses ledger, an entry there. We borrow **concepts and
algorithm shape**, not source — confirm the attribution wording with the
license ledger convention before Slice B merges.

### 9.5 Future: training (out of scope here, flagged only)

Three points to capture for a future cross-repo training plan — **not
designed in this spec**:

- (a) The new grid fields plus the existing `Word` ground-truth fields mean
  recovered cells carry ground truth **for free**: a human-corrected grid is
  just corrected `(row, col, rowspan, colspan)` on `CELL` blocks plus
  corrected word text.
- (b) Fine-tuning a table-**structure** detector is **new ground** for
  `pdomain-ocr-training`, which today owns only DocTR detection + recognition
  training. A TATR fine-tune is a different model family and would need its
  own training surface there.
- (c) The labeler (`pdomain-ocr-labeler-spa`) is where corrected grids would
  be captured — a table-grid editing surface feeding ground truth back.

These are pointers for the future plan, not commitments in this spec.
