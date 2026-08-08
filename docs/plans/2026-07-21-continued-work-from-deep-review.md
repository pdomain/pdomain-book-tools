---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: plan
---

# Continued work plan — deep review follow-through

## Agent Index

- **Kind:** plan
- **Status:** active
- **Read when:** picking the next implementation theme after the 2026-07-21 deep review; sequencing P0 fixes vs greenfield modules.
- **Search terms:** continued work, P0 reorganize, coordinate domain, layout harness, drop-cap C, decision pack, prep-for-pgdp modules.

## Goal

Turn the 2026-07-21 deep review into ordered engineering work that:

1. Closes confirmed correctness and CI-blindness risks first.
2. Hardens reorganize and dual CPU/GPU paths so green CI means more.
3. Unblocks prep-for-pgdp and labeler modules only after owner decisions.
4. Cleans process debt so the live roadmap matches the real backlog.

Source findings:
[`docs/research/2026-07-21-deep-code-review-findings.md`](../research/2026-07-21-deep-code-review-findings.md).

Per-item governed trackers (evidence, defects, severity):
[`docs/issues/README.md`](../issues/README.md).

This plan **extends** [`docs/plans/roadmap.md`](roadmap.md). It does not
replace residual layout, image, or dev items already there: sidenote default
flip, drop-cap C, decoration postclassify, and doctr-from-git signal.

## Architecture

The work touches four layers of this library, in the order the themes hit them.

**OCR page model and reorganize.** `pdomain_book_tools/ocr/` holds the `Page`
and `Block` tree plus `reorganize_page_utils.py`, the heuristic pipeline that
groups words into rows, classifies bands, and assigns roles. Themes A and B
land almost entirely here. This is also where the coordinate-domain bugs live,
because the pipeline mixes normalized `[0,1]` geometry from DocTR with pixel
geometry from Tesseract.

**Geometry primitives and correction.** `Point`, `BoundingBox`, and the
`geometry_correction` backends carry the `is_normalized` contract that the
reorganize layer depends on. Theme C hardens it at both ends: explicit flags at
OCR ingress, and fail-closed behavior in the primitives.

**Image processing, CPU and GPU.** `cv2_processing/` and `cupy_processing/`
implement the same algorithms twice. Every change to one is a parity question
for the other. Theme A4 and Theme C6 both sit on this seam.

**Layout adapters and serialization.** The PP-DocLayout registry, caption
association, and the `schemas.emit` surface. Themes C7 and D cover them.

Above all four sits the layout regression corpus in
`tests/fixtures/layout_regression/`: 31 cases with expected-text baselines.
Theme B makes it exercise the paths production actually runs.

## Tech Stack

- **Python 3.13**, packaged with Hatchling, managed with `uv`.
- **OCR engines:** DocTR (normalized coordinates) and Tesseract (pixel
  coordinates). The domain mismatch between them is the root of Theme A1.
- **Layout:** PP-DocLayout via `transformers`, a mandatory dependency since the
  `[layout]` extra was dropped.
- **Image processing:** OpenCV and NumPy on CPU; CuPy under the optional
  `[gpu]` extra.
- **Validation and serialization:** Pydantic models behind `schemas.emit`.
- **Tests:** pytest with `-n auto`; slow model-download tests excluded by
  default.
- **Gates:** ruff, basedpyright in strict mode with zero diagnostics,
  markdownlint, and docgraph.

## Global Constraints

These bind every theme. They are repo rules, not preferences.

1. **Never silently coerce coordinate systems.** Merge, split, and union fail
   explicitly on an `is_normalized` mismatch. A fix that makes a domain error
   pass quietly is worse than the bug.
2. **Preserve `is_normalized` semantics** across `Point`, `BoundingBox`, and the
   OCR model types.
3. **No unreviewed baseline rewrites.** After B1 and B2, review expected-text
   diffs case by case. A bulk accept destroys the signal the corpus exists for.
4. **Both paths, every time.** A change to a CPU algorithm is incomplete until
   the GPU twin agrees. CPU tests always run; GPU tests skip without CUDA.
5. **Public API changes ripple downstream.** Every other `pdomain-*` project
   depends on this library, so a surface change is a cross-repo change.
6. **Verify before committing.** Focused tests for the changed contract, then
   the full gate.
7. **No permanent strict xfail.** A remaining entry needs a dated owner accept
   with an issue id, not silence.

## Non-goals

- Implementing greenfield specs against unrevised post-adversarial drafts
  before the decision pack (risk of thrash).
- Restoring OCR provenance fields onto `Page` (would undo Task 4).
- Layout fine-tune or PP-DocLayout training (other repos).
- PGDP table **syntax** export (explicitly out of scope in roadmap).
- Shipping decoration postclassify before the fine-tune policy allows it.

## Themes and sequence

Work top to bottom. Start a later theme only after its prerequisites clear.

```text
Theme A  Correctness & CI truth          (P0, no product decision freeze)
Theme B  Reorganize / layout test depth   (P0–P1)
Theme C  Geometry & dual-path hardening  (P0–P1)
Theme D  API / schema / doc contract     (P0–P1, cheap)
Theme E  Owner decision pack             (process, unblocks G–I)
Theme F  Drop-cap C + reorg quality      (after A/B; no E required)
Theme G  Prep-for-pgdp modules           (after E)
Theme H  Labeler geometry stack          (after E; 06 → 09)
Theme I  Table structure                 (after E; slice A first)
Theme J  Coverage & process hygiene      (ongoing)
```

---

## Theme A — Correctness and CI truth (start immediately)

### A1. Fix reorganize coordinate-domain thresholds

**Why:** Band classify and some absolute thresholds use page pixel dims
against box coordinates that may be normalized. This is a confirmed bug.

**Work:**

1. Centralize domain: prefer `BoundingBox.is_normalized`, fall back to
   metrics helpers already used in Step E.
2. Fix `_classify_row_block` top/bottom/side thresholds to use
   `coord_w` / `coord_h`.
3. Fix `split_mixed_content_lines` Y-gap and other absolute thresholds
   identified in the findings.
4. Add a **dual-domain matrix** unit test: same synthetic page as normalized
   `[0,1]` and as pixel `W×H`; assert identical role outcomes.

**Done when:** the dual-domain unit matrix is green. No fixture text change
without a reviewed re-baseline.

### A2. Always reconcile words (including early return)

**Why:** The empty row-blocks path can drop body words with no safety net.

**Work:**

1. Run `reconcile_dropped_words` (or equivalent leftover assembly) before
   every return from `reorganize_page`.
2. Freeze pre-reorg word signatures via deep `to_dict` (or immutable
   snapshot), not live object references mutated by drop-cap trim.
3. Prefer multiset signatures where duplicate text+bbox is possible.

**Done when:** empty-rows / empty-body tests fail without the fix and pass
with it under both strict and soft modes.

### A3. Test the soft recover path

**Why:** Production default is non-strict; CI only exercises strict.

**Work:**

1. Unit tests with `PD_OCR_REORGANIZE_STRICT` unset.
2. Forced drop yields a `recovered` role block, a stderr warning, and words
   still on the page.
3. Document and assert intentional **filter** for bbox-less words (they are
   dropped before soft recover; do not invent a “recover failure” path).

**Done when:** at least one non-strict recover test lands in CI under default
markers, plus a filter/docs assert for bbox-less words if useful.

### A4. Fix GPU textline `_ensure_foreground`

**Why:** Confirmed dual-path polarity bug.

**Work:** Match the CPU mean &lt; 128 gate. Add parity tests for text=0 and
text=255 binaries on both backends.

**Done when:** GPU and CPU agree on both polarities in unit tests. GPU tests
skip without CUDA; the CPU side always runs.

### A5. Fix README orientation examples

**Why:** Documented API is wrong today.

**Work:** Unpack `(document, rotation_degrees)`. Remove
`page.rotation_applied`. Link the architecture page.

**Done when:** README examples match `ocr-page-orientation.md` and would
run against current `Document.from_image_ocr_via_doctr` signatures.

---

## Theme B — Reorganize and layout test debt

**Prerequisite:** Theme **A1** dual-domain matrix is green before any
layout-fed or default-mode **baseline rewrite** (B1/B2). Unit wiring may
start earlier. Do not commit new expected-text files until A1 lands.

### B1. Wire layout into the regression harness

1. Load `inputs/<case>.layout.json` and call
   `reorganize_page(layout=layout, drop_layout_words=True)`.
2. Review and re-baseline case-by-case (do not bulk-accept diffs).
3. Keep dump script in sync.

**Done when:** every corpus case runs with `layout=` loaded. Dump tool
matches. Re-baselines are reviewed per case.

### B2. Default-mode baseline track

Add a second expected-text track (or matrix flag) for
`drop_layout_words=False` matching production default.

**Done when:** CI asserts default-mode text (or structured invariants) for
at least the core corpus subset owners select.

### B3. Resolve the five strict xfails

For each case in `KNOWN_FAILING_BASELINES`, either:

- fix behavior to meet the desired baseline, or
- revise the baseline under explicit policy review and drop the xfail
  with a dated owner accept note.

Do not leave permanent strict xfail as the product definition of done.

**Done when:** `KNOWN_FAILING_BASELINES` is empty, or each remaining entry
has a dated accept with owner and issue id.

### B4. Branch-targeted reorg unit tables

Prioritize: soft recover, early return, plate-noise edges, column strategy
1 vs 2, floated flow + caption prefix, multiset preservation.

Optional later: split `reorganize_page_utils.py` into metrics / noise /
bands / rows / columns / paragraphs / preserve / debug modules.

**Done when:** each priority path above has a focused unit test. Soft
recover and early return stay covered even if full split is deferred.

---

## Theme C — Geometry and dual-path hardening

### C1. Explicit `is_normalized` at OCR ingress

DocTR → `True`; Tesseract → `False`. Never rely on `[0,1]` inference for
engine output.

### C2. Drop-cap domain correctness

Use page content flag / metrics. Never force normalized on pixel trees.
Add a pixel-style fixture or unit page.

### C3. Geometry primitive flag hygiene

- `center` preserves box flag.
- `contains_point` fail-closed on mismatch (match union/intersect).
- Scale helpers document or enforce domain.
- Unit tests for unit-square **pixel** boxes.

### C4. Geometry-correction honesty

1. Align docs with dual gate (curvature enables; regime names backend)
   **or** change code to match docs.
2. Stop advertising `map_points` for grid dewarp until implemented, or
   implement box-corner sampling.
3. Surface **missing backend omit** vs **conf=0 identity no-op** explicitly
   (do not lump both as “skip”).
4. Fix usage **hint** paragraph that wrongly names `SuppliedPageSide`; keep
   the backend table’s `gutter_shadow` default.

### C5. Image I/O contracts

1. Unified load path for formats `is_image_file` accepts (Pillow → BGR
   for HEIF/AVIF when OpenCV cannot).
2. Raise on failed `imwrite` / `imencode`.
3. Drop or use `opencv-cuda`. Remove dead coverage omit for missing
   `cv2cuda_processing`.

**Done when:** HEIF/AVIF round-trip load test passes. Write failure raises.
`opencv-cuda` is either used or removed from `[gpu]`, and coverage omit is
cleaned.

### C6. GPU / slow CI strategy

**Default if no owner pick:** Expand CPU-side parity tests for dual
algorithms and seed all GPU random fixtures. Leave full CUDA as optional
nightly. Document the residual risk in `GPU_TESTING.md`.

Pick one and document:

- Nightly or self-hosted CUDA job for cupy + selected slow smokes, **or**
- Expand CPU-side parity tests that lock dual algorithms without CUDA
  (default above).

Also decide whether `make ci-slow` should run slow tests (today it aliases
`ci`).

**Done when:** a written strategy exists. Default path is implemented.
Seeds are fixed. `ci-slow` behavior matches the written decision.

### C7. Layout adapter knobs and caption sides

1. Allow hashable `revision` / `local_files_only` /
   `trust_remote_checkpoint` through `get_detector` for PP-DocLayout,
   or document “construct adapter + `register_detector` only.”
2. Wire caption `above=True` (or dual-side search) into
   `associate_captions` for dual-caption frontispieces.

**Done when:** knobs are either registry-reachable or documented as
out-of-registry only. Dual-side caption has a unit or fixture case.

---

## Theme D — API, schema, and documentation contract

### D1. One public-API policy

**Default if no owner pick:** Expand `docs/usage/public-api.md`, package
`__all__`, and pin tests to match what README already teaches as usable:
at least `Document` / DocTR ingestion and `schemas.emit` (plus any other
deep imports README demonstrates). `geometry_correction` has a separate
usage doc; `hf` has package `__all__` only — include them only with a
consumer cite or deliberate expand. Alternative: stop teaching deep imports
and mark them internal.

**Done when:** public-api.md, `__all__`, and tests agree on one surface.
README imports only listed names.

### D2. Path and emit hygiene

1. Fix `docs/public-api.md` pointers → `docs/usage/public-api.md`.
2. Add structured schema for `GlyphAnnotations` (or document opacity as
   intentional).
3. Normalize `Block.unmatched_ground_truth_words` list→tuple on
   `from_dict` (mirror Page gt_orphans).
4. Clarify provenance ownership: handoff type vs emit-only models vs ops.

**Done when:** path refs resolve. Glyph schema decision is implemented or
documented. Block JSON round-trip restores tuples. Provenance ownership
sentence lands in architecture or public-api.

### D3. Intent-map and roadmap sync

1. Fix stale “spec 07 pending promotion” line in intent-map.
2. Absorb issue clusters **#208–#225** (or explicit deferrals with issue
   numbers) into this plan or `roadmap.md` before any tracker wipe.
3. Disambiguate “table detection complete” vs structure (spec 10).

**Done when:** intent-map matches retired-07 truth. **#208–#225** appear as
live plan rows or dated deferrals. Roadmap table language cannot be read
as “structure shipped.”

---

## Theme E — Owner decision pack (no code)

Close or explicitly defer these before greenfield builds. Without this,
implementation re-litigates adversarial findings.

| Decision set | Unblocks |
|---|---|
| Q-RL-1…10 (reference lines) | Theme H / 06b–c |
| Char-bbox polarity, ligature, fallback (09) | Theme H |
| Table word fallback, rendering, sort (10) | Theme I |
| Page-order redesign (drop unvalidated visual-sim as swap vote) | Theme G |
| Scannos book/occurrence IDs, dual-write, rule IDs | Theme G |
| Hyphen download, locking, packaging (~50 MB asset) | Theme G |
| Provenance / OcrCompleted home (not on Page) | Task 5/Plan 2 ownership |
| Soft coverage ratchet (e.g. hard 90 / soft 92) | Theme J |
| Public-API expand vs internal-only (override D1 default) | Theme D |
| Geometry-correction dual-gate: docs vs code (override C4) | Theme C |
| GPU/slow CI strategy (override C6 default) | Theme C |

**Done when:** intent-map “Needs owner decision” items each have an answer
or a dated deferral with owner.

---

## Theme F — Roadmap residual quality (library)

This theme can run after A/B start. Drop-cap C does not need Theme E.

### F1. Drop-cap Iteration C

Heading/title cross-check for ambiguous lexicon on fixture
`footnotes-stacked-with-anchor` (cap “A”, body “BELIEF”). Flip the test
that currently pins unrecovered.

### F2. Sidenote height default

Only after a layout-fed fixture pass (Theme B1). Do not flip
`sidenote_max_height_ratio` without evidence.

### F3. Decoration postclassify

Keep deferred until layout fine-tune policy allows. Then implement
`postclassify_decoration` and fix corpus honesty for the decoration case.

---

## Theme G — Prep-for-pgdp modules (after Theme E)

Order by stage pressure and risk:

1. **Page-order skeleton** — filename + OCR signals first; no unvalidated
   visual-sim swap authority (Stage 11).
2. **Scannos V1** — models, SQLite rules, JSON candidates, scan/promote
   (Stage 13).
3. **Hyphen Protocol + JsonApiClient**, then SQLite/data pipeline
   (Stage 15; data work is L effort).

Declare `platformdirs` (or chosen path helper) when scannos/hyphen land.

---

## Theme H — Labeler geometry stack (after Theme E)

1. Land `reference_lines` API (06b) + tests (06c). Dedupe descender sets.
2. Char-bbox v1 sweepline (09) without CTC. Synthetic fixtures first.
3. Soft dependency: 06 improves diacritic banding for 09. Stub if the
   labeler timeline forces partial 09.

---

## Theme I — Table structure (after Theme E)

1. **Slice A:** `TABLE`/`CELL` categories + grid fields through all
   serialization sites + round-trip tests (no ML).
2. Cell assignment / TATR later. Keep the no-silent-drop invariant from
   the start.
3. Keep PGDP table syntax out of this repo.

---

## Theme J — Coverage and process hygiene (ongoing)

1. Ratchet hard/soft coverage only after Theme A/B recover intentional
   misses. Avoid chasing debug PNG branches.
2. Optional: `# pragma: no cover` or single smoke for debug writers so
   they stop dominating the 298 missing count.
3. Expand public-api pin tests to full layout/hf `__all__` once D1 lands.
4. Schema golden snapshot for emit stability across pydantic upgrades.
5. Refresh `current-state.md` priorities: product backlog vs docs-only.

---

## Suggested sprint slices

Concrete batches for separate PRs / sessions:

| Slice | Contents | Effort |
|---|---|---|
| S0 | A5 README + D3 intent-map/roadmap absorb + public-api path fix | S |
| S1 | A1 coord domain + dual-domain tests | M |
| S2 | A2 early-return reconcile + A3 soft recover tests | M |
| S3 | A4 GPU textline polarity + parity tests | S |
| S4 | B1 layout-fed harness + re-baseline (**after A1**) | L |
| S5 | B2 default-mode track + B3 close each xfail (fix or dated accept) | M–L |
| S6 | C1–C2 ingress + dropcap domain | M |
| S7 | C3–C4 geometry primitives + geometry-correction docs/code | M |
| S8 | C5 I/O + packaging cleanup | S–M |
| S8b | C6 GPU/slow CI strategy (implement default or owner pick) + C7 knobs/captions | S–M |
| S9 | D1–D2 public API / schema | M |
| S10 | F1 drop-cap C | S–M |
| S11 | Theme E decision workshop | S (calendar) |
| S12+ | G/H/I greenfield per decisions | M–L each |

## Verification gates

For every code slice:

1. Focused tests for the changed contract.
2. `make ci AI=1` (repo rule) before commit.
3. After B1/B2: review text diffs by case. No silent bulk baseline rewrite.
4. After dual-path changes: CPU tests required; GPU when available.
5. Do not claim “complete” while matching cases remain in
   `KNOWN_FAILING_BASELINES` without an explicit accept decision.

## Relationship to live roadmap

| Existing roadmap item | This plan |
|---|---|
| Drop-cap Iteration C | Theme F1 / S10 |
| Sidenote default flip | Theme F2 after B1 |
| Image-projection x-height | After F2 evidence; still optional |
| Multi-column body detection enhancements | After F2 / glyph-size evidence; still roadmap residual (not a separate theme until fixtures need it) |
| Decoration postclassify | Theme F3 (still deferred) |
| Doctr-from-git dev-local signal | Unchanged; still deferred |
| (missing) page-order/scannos/hyphen | Theme G + D3 absorb |
| (missing) 06/09/10 | Themes H–I after E |

## Success criteria for the plan overall

The plan is “done enough” when:

1. All Theme A items are fixed and tested.
2. Layout regression locks **layout-fed** and **default** modes, or
   documents a deliberate remaining exception with owner sign-off.
3. No permanent strict xfail without a dated owner accept.
4. Theme C is closed, or each remaining C item has a dated owner deferral
   (dual-path polarity, ingress flags, I/O, and CI strategy).
5. Live roadmap or this plan lists every active greenfield cluster with
   issue provenance.
6. Owner decision pack is closed or deferred with dates.
7. README and public-api docs match shipped APIs.

## Out of scope reminders

- Training PP-DocLayout from scratch; custom layout architectures.
- Cross-page foldout stitching; layout-aware OCR model swaps.
- Restoring operational provenance onto the Page JSON tree.
- Implementing visual-similarity swap voting for page-order without a
  validated positional model.
