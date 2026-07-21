---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: research
---

# Deep code review findings (2026-07-21)

## Agent Index

- **Kind:** research
- **Status:** active
- **Read when:** starting hardening work, choosing the next engineering theme, or checking whether a product gap is real vs documented residual intent.
- **Search terms:** deep review, adversarial review, reorganize gaps, coordinate system, test quality, unimplemented specs, continued work.

## Main point

**Core OCR and geometry is real**, and architecture docs are largely honest about it. Nine specialist audits plus three adversarial challenge passes still found that production confidence is inflated by three patterns.

The three patterns are coordinate-domain bugs in reorganize heuristics; CI that does not lock the default reorganize path or layout-fed behavior; and a large design backlog. That backlog (specs 06b/09/10, page-order, scannos, hyphen) is **not implemented and not fully on the live roadmap**.

Adversarial challengers re-read the cited source and **confirmed** every high-severity claim in this report against the tree. They retained no separate challenge artifact files.

## How this review was run

| Phase | What ran |
|---|---|
| Map | Package tree, roadmap, public API, specs index, coverage status (~90.3% headline) |
| Specialists (7) | OCR, layout, image processing, geometry correction, test quality, specs vs code, API/schemas/packaging |
| Focused (2) | Unfinished modules inventory; reorganize_page branch risk |
| Adversarial (3) | Coordinate/reorg findings; IP/API findings; test/spec claims |

## Severity legend

- **P0** — Correctness trap or false green CI on a product path.
- **P1** — Material gap or incomplete dual-path/API contract; ship soon.
- **P2** — Hygiene, deferred features, or doc drift without immediate product break.

---

## P0 — confirmed product risks

### 1. Reorganize classifies bands with the wrong scale

`_classify_row_block` compares each row **block** `bounding_box` to
`0.12 * page_height` / `0.88 * page_height` (raw page pixel dims). It skips
the `coord_w` / `coord_h` adaptation used in other steps.

Under DocTR-normalized geometry (box values in `[0, 1]`), “near top of
image” is almost always true. “Near bottom” almost never is. Footer and
sidenote geometry classification can collapse.

A related bug has the opposite polarity. `split_mixed_content_lines` uses a
bare Y gap of `0.08` (~2192). That constant is fraction-scale, so it works under
normalized coords and almost never clears on **pixel** boxes.

**Where:** `pdomain_book_tools/ocr/reorganize_page_utils.py` (~4129–4161;
mixed-line Y gap ~2192).

### 2. Layout regression corpus does not feed layout into reorganize

The text baseline harness loads `*.layout.json` for debug overlays only.
It calls `page.reorganize_page(drop_layout_words=True)` **without** `layout=`.

Heuristic figure-noise drop still runs when `drop_layout_words=True`. The
corpus does **not** lock layout-gated work on the flagship 31-case set: word
tagging, layout-aware figure-internal drops, geometric sidenotes, role
bubble-up, and caption association.

**Where:** `tests/ocr/test_reorganize_page_utils_grouping.py` (~319–339);
`tests/fixtures/layout_regression/dump_reorganize_output.py` (~58).

### 3. Empty row-block early return skips word preservation

When grouping yields no row blocks, `Page.reorganize_page` emits header/footer
bands and returns **without** `reconcile_dropped_words`. Body words that never
formed rows can vanish with no strict raise and no soft recovery.

**Where:** `pdomain_book_tools/ocr/page.py` (~3124–3140 vs reconcile ~3186).

### 4. Soft recover path is not covered in CI

Reconcile tests force `PD_OCR_REORGANIZE_STRICT=1`. Production default is
non-strict: warn, append a `recovered` block, continue. That path has no CI
assertion.

**Where:** `reorganize_page_utils.py` (~973–989);
`tests/ocr/test_reconcile_dropped_words.py`.

### 5. Default reorganize mode is not what baselines lock

Corpus baselines use `drop_layout_words=True` (legacy figure-noise path).
Production default is `drop_layout_words=False` (word-preserving).

CI can stay green while the default path regresses.

**Where:** harness/dump force True —
`tests/ocr/test_reorganize_page_utils_grouping.py` (~339);
`dump_reorganize_output.py` (~58). Default False on
`Page.reorganize_page` (`page.py` ~2783).

### 6. Five strict xfails mask figure-noise product gaps

`KNOWN_FAILING_BASELINES` lists five plates/frontispieces with
`pytest.mark.xfail(..., strict=True)`. Desired baselines require noise drops
the product does not yet achieve. CI stays green by design.

**Where:** `tests/ocr/test_reorganize_page_utils_grouping.py` (~227–272).

### 7. GPU textline foreground polarity ≠ CPU

CPU `_ensure_foreground` requires mean &lt; 128 for `{0,255}` binaries before
pass-through. GPU accepts any `{0,255}` binary unchanged.

Library-standard text=0 / background=255 binaries invert polarity on GPU
morphology.

**Where:** `cupy_processing/textline_dewarp.py` (~63–70) vs
`cv2_processing/textline_dewarp.py` (~43–57).

---

## P1 — material gaps

### Doc and measurement confidence (demoted from P0)

These do not break a product code path by themselves. They still mislead
consumers and hide risk.

| Gap | Evidence |
|---|---|
| README documents a removed OCR API | `README.md` (~215–223): assigns DocTR return to `doc` and reads `page.rotation_applied`. Real API returns `tuple[Document, int]`; Page rejects that field (`ocr-page-orientation.md`). |
| Headline coverage hides reorganize risk | htmlcov from 2026-07-17 (`htmlcov/status.json` / `index.html`): overall ~**90.3%**; `reorganize_page_utils.py` ~**80.1%** line, **298** missing statements, **220** missing branches, ~1817 statements. |

### Coordinate and geometry contracts

| Gap | Evidence |
|---|---|
| OCR ingress omits explicit `is_normalized` | DocTR `from_nested_float` / Tesseract `from_ltwh` in `document.py` rely on inference |
| Drop-cap forces normalized boxes | `dropcap.py` CC path and stitch write `is_normalized=True` |
| `BoundingBox.center` drops flag | rebuilds `Point(x,y)` without box flag |
| Geometry correction: grid cannot `map_points` | `transforms.py` raises; usage docs still advertise keypoint map after dewarp |
| Dual dewarp gate | Regime only names backend; curvature `recommended == "dewarp"` enables it — docs imply regime alone |

### Layout consumption

| Gap | Evidence |
|---|---|
| No `postclassify_decoration` | Roadmap open; corpus “decoration” case is still model `figure`/`image` |
| PP-DocLayout registry rejects security/revision kwargs | `trust_remote_checkpoint`, `local_files_only`, `revision` not through `get_detector` |
| Caption association is below-only | `above=True` helper exists; `associate_captions` does not use it |
| Sidenote height default still `None` | Roadmap: flip only after fixture pass |

### Image processing and packaging

| Gap | Evidence |
|---|---|
| HEIF/AVIF identify then fail on `cv2.imread` | `formats.py` accepts; `io.read_image` is OpenCV-only |
| Write paths ignore `imwrite` return | Silent no-op on disk full / bad path |
| `[gpu]` lists unused `opencv-cuda` | Real GPU path is CuPy only |
| GPU suite never runs in default CI | `CUDA_VISIBLE_DEVICES=""`, cupy tests skip |
| `@slow` excluded from `make ci` | Model smokes only on `make test-slow` |

### API / schema

| Gap | Evidence |
|---|---|
| Public API thinner than taught surface | README deep-imports `Document`, `hf`, image processing; not in `public-api.md` |
| `GlyphAnnotations` not in `PUBLIC_MODELS` | Word schema uses `any_schema` for glyphs |
| Provenance built then deleted at ingest | Intentional for Page; no handoff API for ops |
| Soft target 88% vs hard 87% | Almost no distinct signal at 90%+ |

### Drop-cap and GT residual

| Gap | Evidence |
|---|---|
| Drop-cap Iteration C unshipped | Roadmap + fixture pins `BELIEF` unrecovered for cap “A” |
| GT match TODOs | Punctuation-aware types; quote attach; untyped `GtOrphans` |

---

## P2 — unfinished design backlog (not code)

These active specs have **no package implementation** of the specified APIs.
The intent-map still lists owner decisions. Adversarial confirmation: they are
design-only.

| Spec / theme | Status |
|---|---|
| 06a–c word reference lines | Baseline-only helpers exist; no `WordReferenceLines` API |
| 09 char-bbox extraction | Whitespace splitter only; no `extract_char_bboxes` |
| 10 table structure | Layout `table` role only; no TABLE/CELL grid fields |
| page-order detection | No `page_order` module |
| scannos | No `scannos` module |
| hyphen-ngrams SQLite | No module or DB artifact |

**Process gap:** issue clusters **#208–#225** (page-order / scannos / hyphen)
are in the 2026-07-17 handoff but **not** absorbed into
`docs/plans/roadmap.md`.

Roadmap language “table detection is complete” means layout region detection,
**not** structure (spec 10).

**Doc drift:** the intent-map still claims spec 07 is pending architecture
promotion. Spec 07 was retired into `architecture/local-dev-mode.md` on
2026-07-15.

Package and tests still cite `docs/public-api.md`; the real path is
`docs/usage/public-api.md`.

---

## What is in good shape

Do not rewrite these for “completeness theater”:

- Geometry merge/split/union fail-closed on coordinate mismatch (tested).
- Layout registry caching, soft build errors, trust-boundary unit tests.
- Glyph annotations, page orientation helper, page serialization contracts
  (architecture residuals are explicit).
- Layout-aware reorg **unit** suite (synthetic); layout types validation.
- Image-processing CPU modules: high volume of unit tests; several parity
  fixes already landed (Otsu, morph borders, read_image fail-hard).
- Meta-tests that pin coverage gates against silent config drift.

Architecture docs for shipped systems are generally honest about residual
intent. The failure mode is **false confidence from aggregate coverage and
xfail/strict-mode CI**, not silent overclaim inside residual sections.

---

## Method notes

Specialists were gap-focused explore agents on isolated packages.

Adversarial challengers re-read source and returned CONFIRM/WEAKEN/REJECT only.
All P0 items above were **CONFIRMED**.

One nuance: `BoundingBox.center` has few call sites but is still a real
flag-loss bug.

Continued execution sequencing lives in
[`docs/plans/2026-07-21-continued-work-from-deep-review.md`](../plans/2026-07-21-continued-work-from-deep-review.md).
