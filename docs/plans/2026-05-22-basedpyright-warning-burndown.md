---
status: active
synced: ~
milestone: ~
repo: pd-book-tools
created: 2026-05-22
---

# basedpyright Warning Burndown Plan

## Background

`pd-book-tools` adopted a `basedpyright` baseline file (`.basedpyright/baseline.json`)
that grandfathers 3365 warnings so CI stays green while `failOnWarnings = true` gates
_new_ code. This plan tracks burning down the own-code warnings in waves — cheapest
mechanical wins first, heavy annotation-design work later.

## Authoritative Warning Counts (2026-05-22 snapshot)

Derived from `.basedpyright/baseline.json` at commit `ddefc8d`.

| Category | Count |
|---|---|
| Own-code warnings (target of this plan) | **2,416** |
| Third-party cascade (cupy_processing/ + cv2_processing/) | 949 |
| **Grand total in baseline** | **3,365** |

Third-party cascade files are **out of scope** — their warnings come from
missing upstream stubs (cupy, cv2), not from own code. Do not touch them.

### Per-Rule Breakdown — Own-Code Only

| Rule | Count | Category |
|---|---|---|
| reportUnknownArgumentType | 560 | Annotation gap |
| reportUnknownMemberType | 498 | Annotation gap |
| reportAny | 374 | Annotation gap |
| reportUnknownVariableType | 346 | Annotation gap |
| reportUnknownParameterType | 136 | Annotation gap |
| reportMissingParameterType | 128 | Definite fix |
| reportExplicitAny | 99 | Definite fix |
| reportImplicitStringConcatenation | 54 | Definite fix |
| reportUnusedCallResult | 51 | Definite fix |
| reportUnnecessaryComparison | 34 | Definite fix |
| reportUnannotatedClassAttribute | 20 | Definite fix |
| reportUnnecessaryIsInstance | 18 | Definite fix |
| reportPrivateUsage | 15 | Definite fix |
| reportUnknownLambdaType | 13 | Annotation gap |
| reportUnreachable | 12 | Definite fix |
| reportMissingTypeStubs | 11 | Third-party stubs |
| reportUnusedImport | 10 | Definite fix |
| reportUnusedParameter | 10 | Definite fix |
| reportImplicitOverride | 8 | Definite fix |
| reportUnnecessaryTypeIgnoreComment | 7 | Definite fix |
| reportUntypedNamedTuple | 5 | Definite fix |
| reportPropertyTypeMismatch | 4 | Definite fix |
| reportUnusedFunction | 2 | Definite fix |
| reportUnusedClass | 1 | Definite fix |

**Annotation gap rules** (reportUnknown*, reportAny, reportExplicitAny, reportUnknownLambdaType)
total ~2,026 and are the main effort. They require adding type annotations — either real
types or `cast()` / `Any` suppressions where upstream types are genuinely opaque.

**Definite fix rules** total ~390. These are mechanical: remove dead imports,
annotate missing params, replace stale `# type: ignore`, etc.

### Per-File Breakdown — Own-Code Files Only

| File | Warnings | Rule Mix (top rules) | Effort | Primary type |
|---|---|---|---|---|
| `ocr/reorganize_page_utils.py` | **631** | UnknownArgumentType=197, UnknownMemberType=147, UnknownVariableType=110, Any=63, UnknownParameterType=34, MissingParameterType=33 | XL | Annotation gap |
| `ocr/ground_truth_matching.py` | **433** | UnknownArgumentType=131, UnknownMemberType=128, UnknownVariableType=101, UnknownParameterType=23, MissingParameterType=23 | XL | Annotation gap |
| `ocr/page.py` | **286** | UnknownMemberType=81, Any=55, UnknownArgumentType=30, UnknownVariableType=22, UnusedCallResult=17, MissingParameterType=16, ExplicitAny=13, ImplicitStringConcat=13 | L | Mixed |
| `ocr/document.py` | **144** | Any=47, ExplicitAny=25, UnknownMemberType=25, UnknownVariableType=14, UnknownArgumentType=12 | L | Annotation gap |
| `ocr/layout_aware_reorg.py` | **129** | UnknownMemberType=45, UnknownArgumentType=33, UnknownVariableType=18, UnnecessaryComparison=6 | M | Annotation gap |
| `pgdp/pgdp_results.py` | **121** | UnknownArgumentType=77, UnknownMemberType=12, UnknownParameterType=9 | M | Annotation gap |
| `ocr/block.py` | **103** | UnknownMemberType=23, UnknownArgumentType=22, Any=12, ExplicitAny=6, PrivateUsage=7 | M | Mixed |
| `ocr/word.py` | **85** | Any=44, ExplicitAny=6, UnknownArgumentType=6, UnusedCallResult=5 | M | Mixed |
| `ocr/doctr_support.py` | **70** | UnknownVariableType=17, UnknownArgumentType=14, UnknownMemberType=13, UnknownParameterType=11, MissingParameterType=9 | M | Annotation gap |
| `geometry/bounding_box.py` | **55** | Any=22, UnusedImport=7, UnknownParameterType=7, MissingParameterType=5, ExplicitAny=4 | S | Mixed |
| `ocr/dropcap.py` | **48** | UnknownVariableType=22, UnknownArgumentType=13, UnnecessaryComparison=5 | S | Annotation gap |
| `layout/registry.py` | **41** | UnknownArgumentType=11, Any=8, ImplicitStringConcat=6, ExplicitAny=4, UnusedCallResult=3 | S | Mixed |
| `layout/adapters/pp_doclayout.py` | **38** | Any=17, UnannotatedClassAttribute=7, UnknownMemberType=5, StaleTypeIgnore=2 | S | Mixed |
| `utility/timing.py` | **35** | UnknownParameterType=9, UnknownVariableType=9, MissingParameterType=6, UnknownArgumentType=6 | S | Annotation gap |
| `ocr/provenance.py` | **25** | ExplicitAny=7, Any=7, UnknownMemberType=4, UnnecessaryIsInstance=2 | S | Mixed |
| `layout/types.py` | **22** | Any=12, ImplicitStringConcat=4, ExplicitAny=4 | S | Mixed |
| `ocr/glyph_annotations.py` | **18** | Any=9, ImplicitStringConcat=5, ExplicitAny=4 | XS | Mixed |
| `geometry/image_ops.py` | **17** | Any=15, UnnecessaryComparison=2 | XS | Annotation gap |
| `geometry/point.py` | **16** | Any=5, UnannotatedClassAttribute=3, ImplicitOverride=3, ExplicitAny=3 | XS | Mixed |
| `layout/detector.py` | **16** | Any=9, UnannotatedClassAttribute=7 | XS | Mixed |
| `ocr/image_utilities.py` | **16** | Any=6, UnnecessaryComparison=4, UnknownMemberType=2 | XS | Mixed |
| `utility/ipynb_widgets.py` | **15** | Any=10, MissingTypeStubs=1, UnknownParameterType=1 | XS | Mixed |
| `ocr/character.py` | **9** | Any=6, ExplicitAny=3 | XS | Mixed |
| `layout/visualize.py` | **8** | Any=3, UnusedCallResult=3, UnknownArgumentType=1 | XS | Mixed |
| `ocr/cv2_tesseract.py` | **7** | UnknownVariableType=3, MissingTypeStubs=2, ImplicitStringConcat=2 | XS | Mixed |
| `image_processing/formats.py` | **6** | MissingTypeStubs=2, ImplicitStringConcat=2, UnknownMemberType=1, UnusedImport=1 | XS | Mixed |
| `hf/download.py` | **4** | ImplicitOverride=1, StaleTypeIgnore=1, UnusedCallResult=1 | XS | Definite fix |
| `licenses.py` | **4** | Any=2, UnnecessaryIsInstance=1, Unreachable=1 | XS | Definite fix |
| `ocr/review.py` | **4** | ExplicitAny=2, Any=2 | XS | Mixed |
| `schemas/emit.py` | **4** | ExplicitAny=2, UnusedParameter=1, UnusedCallResult=1 | XS | Definite fix |
| `image_processing/external_tools.py` | **2** | UnusedCallResult=2 | XS | Definite fix |
| `hf/models.py` | **1** | UnusedCallResult=1 | XS | Definite fix |
| `layout/__init__.py` | **1** | UnknownVariableType=1 | XS | Annotation gap |
| `ocr/label_normalization.py` | **1** | ImplicitStringConcat=1 | XS | Definite fix |
| `schemas/__main__.py` | **1** | UnusedCallResult=1 | XS | Definite fix |

---

## Chunk Design

Each chunk is a **disjoint file-set** — no file appears in two chunks.
This is the hard constraint for safe parallel subagent execution. Chunks
that share type definitions need ordering (noted below).

### Wave 1 — Mechanical Wins (pure definite-fix rules, no annotation design)

These chunks contain only clear-cut issues: dead imports, stale type-ignore
comments, dead code, unused functions/parameters, implicit string concatenation.
Risk is low; no cross-file type dependency. All chunks in Wave 1 can run in
**parallel with each other**.

#### Chunk W1-A: Tiny files — definite-fix only

Files: `hf/download.py`, `hf/models.py`, `image_processing/external_tools.py`,
`licenses.py`, `schemas/emit.py`, `schemas/__main__.py`, `ocr/label_normalization.py`

| File | Count | Top rules |
|---|---|---|
| `hf/download.py` | 4 | ImplicitOverride, StaleTypeIgnore, UnusedCallResult |
| `hf/models.py` | 1 | UnusedCallResult |
| `image_processing/external_tools.py` | 2 | UnusedCallResult |
| `licenses.py` | 4 | Any(×2), UnnecessaryIsInstance, Unreachable |
| `schemas/emit.py` | 4 | ExplicitAny(×2), UnusedParameter, UnusedCallResult |
| `schemas/__main__.py` | 1 | UnusedCallResult |
| `ocr/label_normalization.py` | 1 | ImplicitStringConcat |

**Total:** 17 warnings | **Effort:** XS | **Risk:** low | **Depends on:** nothing

#### Chunk W1-B: geometry/bounding_box.py

File: `geometry/bounding_box.py`

55 warnings: UnusedImport=7, MissingParameterType=5, ExplicitAny=4,
UnnecessaryComparison=1, ImplicitOverride=1, UnnecessaryIsInstance=1,
PrivateUsage=1, UnknownParameterType=7, UnknownMemberType=2,
UnknownVariableType=2, Any=22.

The Any/Unknown cluster (33 warnings) will need annotation work — `bounding_box.py`
is a geometry primitive and its types should be easy to infer. The mechanical
subset (UnusedImport, ExplicitAny, ImplicitOverride) is ~13 warnings.

**Total:** 55 warnings | **Effort:** S | **Risk:** low-medium |
**Depends on:** nothing (but `page.py`, `block.py`, `word.py` all import it —
fixing its signatures will remove downstream Unknown cascades; ship this before
Wave 3 chunks that touch those files).

#### Chunk W1-C: layout/types.py + layout/\_\_init\_\_.py

Files: `layout/types.py`, `layout/__init__.py`

| File | Count | Top rules |
|---|---|---|
| `layout/types.py` | 22 | Any=12, ImplicitStringConcat=4, ExplicitAny=4, UnnecessaryIsInstance=1, StaleTypeIgnore=1 |
| `layout/__init__.py` | 1 | UnknownVariableType=1 |

`layout/types.py` defines shared layout types used by `layout/detector.py`,
`layout/registry.py`, `layout/adapters/pp_doclayout.py`. Fixing types here
first reduces cascades in those files (Wave 2).

**Total:** 23 warnings | **Effort:** S | **Risk:** low-medium |
**Depends on:** nothing; **Blocks:** W2-C (layout cluster).

#### Chunk W1-D: ocr/glyph_annotations.py + ocr/character.py + ocr/review.py

Files: `ocr/glyph_annotations.py`, `ocr/character.py`, `ocr/review.py`

| File | Count | Top rules |
|---|---|---|
| `ocr/glyph_annotations.py` | 18 | Any=9, ImplicitStringConcat=5, ExplicitAny=4 |
| `ocr/character.py` | 9 | Any=6, ExplicitAny=3 |
| `ocr/review.py` | 4 | ExplicitAny=2, Any=2 |

These OCR leaf types are imported by `word.py` and `block.py`. Fixing their
annotations reduces upstream Unknown cascades.

**Total:** 31 warnings | **Effort:** S | **Risk:** low |
**Depends on:** nothing; **Blocks:** W3-A (word.py), W3-B (block.py).

#### Chunk W1-E: utility/ cluster

Files: `utility/timing.py`, `utility/ipynb_widgets.py`

| File | Count | Top rules |
|---|---|---|
| `utility/timing.py` | 35 | UnknownParameterType=9, UnknownVariableType=9, MissingParameterType=6, UnknownArgumentType=6, UnknownMemberType=3, ImplicitStringConcat=2 |
| `utility/ipynb_widgets.py` | 15 | Any=10, MissingTypeStubs=1, UnknownParameterType=1, MissingParameterType=1, UnknownArgumentType=1, ImplicitStringConcat=1 |

`timing.py` is a standalone decorator utility; `ipynb_widgets.py` wraps ipywidgets.
Both are low-dependency. `ipynb_widgets.py` has `MissingTypeStubs` for ipywidgets —
use `# pyright: ignore[reportMissingTypeStubs]` there rather than fighting upstream.

**Total:** 50 warnings | **Effort:** S | **Risk:** low |
**Depends on:** nothing.

#### Chunk W1-F: image_processing/formats.py + ocr/cv2_tesseract.py

Files: `image_processing/formats.py`, `ocr/cv2_tesseract.py`

| File | Count | Top rules |
|---|---|---|
| `image_processing/formats.py` | 6 | MissingTypeStubs=2, ImplicitStringConcat=2, UnknownMemberType=1, UnusedImport=1 |
| `ocr/cv2_tesseract.py` | 7 | UnknownVariableType=3, MissingTypeStubs=2, ImplicitStringConcat=2 |

Both have `MissingTypeStubs` warnings for PIL/cv2 stubs — suppress with
`# pyright: ignore[reportMissingTypeStubs]`.

**Total:** 13 warnings | **Effort:** XS | **Risk:** low |
**Depends on:** nothing.

---

### Wave 2 — Medium files with mixed definite + annotation work

Run after Wave 1 chunks that define types they depend on have landed.
Chunks within Wave 2 can run **in parallel with each other** (disjoint files).

#### Chunk W2-A: ocr/provenance.py + ocr/image_utilities.py

Files: `ocr/provenance.py`, `ocr/image_utilities.py`

| File | Count | Top rules |
|---|---|---|
| `ocr/provenance.py` | 25 | ExplicitAny=7, Any=7, UnknownMemberType=4, UnnecessaryIsInstance=2, UnknownVariableType=2, UnknownArgumentType=2, Unreachable=1 |
| `ocr/image_utilities.py` | 16 | Any=6, UnnecessaryComparison=4, UnknownMemberType=2, UnknownParameterType=2, MissingParameterType=1, UnknownVariableType=1 |

**Total:** 41 warnings | **Effort:** S | **Risk:** low |
**Depends on:** nothing from Wave 1 (these are self-contained utility modules).

#### Chunk W2-B: geometry/ cluster

Files: `geometry/image_ops.py`, `geometry/point.py`

| File | Count | Top rules |
|---|---|---|
| `geometry/image_ops.py` | 17 | Any=15, UnnecessaryComparison=2 |
| `geometry/point.py` | 16 | Any=5, UnannotatedClassAttribute=3, ImplicitOverride=3, ExplicitAny=3, UnusedParameter=1, UnnecessaryIsInstance=1 |

`point.py` is a base geometry class — ship before anything that subclasses it.

**Total:** 33 warnings | **Effort:** S | **Risk:** low |
**Depends on:** nothing (but W1-B/bounding_box.py should land first for
complete geometry picture).

#### Chunk W2-C: layout/ cluster (detector, registry, adapters, visualize)

Files: `layout/detector.py`, `layout/registry.py`,
`layout/adapters/pp_doclayout.py`, `layout/visualize.py`

| File | Count | Top rules |
|---|---|---|
| `layout/detector.py` | 16 | Any=9, UnannotatedClassAttribute=7 |
| `layout/registry.py` | 41 | UnknownArgumentType=11, Any=8, ImplicitStringConcat=6, ExplicitAny=4, UnusedCallResult=3, UnknownParameterType=2, MissingParameterType=2 |
| `layout/adapters/pp_doclayout.py` | 38 | Any=17, UnannotatedClassAttribute=7, UnknownMemberType=5, StaleTypeIgnore=2 |
| `layout/visualize.py` | 8 | Any=3, UnusedCallResult=3, UnknownArgumentType=1, ImplicitStringConcat=1 |

These all depend on types from `layout/types.py` (W1-C). `registry.py` uses
`detector.py`; `pp_doclayout.py` uses both. Ship W1-C first.

**Total:** 103 warnings | **Effort:** M | **Risk:** medium |
**Depends on:** W1-C (`layout/types.py`).

#### Chunk W2-D: ocr/dropcap.py

File: `ocr/dropcap.py`

48 warnings: UnknownVariableType=22, UnknownArgumentType=13,
UnnecessaryComparison=5, UnknownMemberType=3, ImplicitStringConcat=2,
UnknownParameterType=1, MissingParameterType=1, Unreachable=1.

Dropcap is relatively self-contained (uses `block.py` types but doesn't define
shared types). Depends on `block.py` annotations being reasonable (W3-B).
Can be started independently; some Unknown cascade will remain until W3-B lands.

**Total:** 48 warnings | **Effort:** S | **Risk:** medium |
**Depends on:** W1-D (character.py for glyph types); W3-B (block.py) preferred
but not strictly required.

#### Chunk W2-E: pgdp/pgdp_results.py

File: `pgdp/pgdp_results.py`

121 warnings: UnknownArgumentType=77, UnknownMemberType=12,
UnknownParameterType=9, UnknownVariableType=8, MissingParameterType=8,
Any=6, UnusedCallResult=1.

Heavily annotation-gap — 77 UnknownArgumentType suggests the file calls many
partially-typed APIs. Most fixes will be adding type annotations or `cast()`.
This file is mostly independent of the deep OCR pipeline; it processes PGDP-format
results. Can be parallelized freely with other Wave 2 chunks.

**Total:** 121 warnings | **Effort:** M | **Risk:** medium |
**Depends on:** nothing in Wave 1 (self-contained PGDP logic).

---

### Wave 3 — Core OCR type model (word, block, document, doctr_support)

These files form the OCR type hierarchy: `doctr_support.py` wraps DocTR types,
`word.py` and `block.py` build on it, `document.py` and `page.py` aggregate them.
The dependency ordering is:

```text
doctr_support.py
    └── word.py, character.py (W1-D already done)
            └── block.py
                    └── document.py, page.py
```

Chunks within Wave 3 **cannot be fully parallelized** because of this chain —
ship in the sub-order below, but keep each chunk on its own branch so baseline
regeneration happens once at integration.

#### Chunk W3-A: ocr/doctr_support.py

File: `ocr/doctr_support.py`

70 warnings: UnknownVariableType=17, UnknownArgumentType=14,
UnknownMemberType=13, UnknownParameterType=11, MissingParameterType=9,
ImplicitStringConcat=2, UnusedImport=2, UnusedCallResult=1, UnusedParameter=1.

DocTR objects (`Document`, `Page`, `Block`, `Word`) have partially-typed stubs.
Many unknowns here flow downstream. Adding proper `TypeVar` or `cast()` patterns
here multiplies the benefit.

**Total:** 70 warnings | **Effort:** M | **Risk:** medium-high |
**Depends on:** W1-D (character.py), W1-B (bounding_box.py). |
**Blocks:** W3-B (word.py), W3-C (block.py).

#### Chunk W3-B: ocr/word.py

File: `ocr/word.py`

85 warnings: Any=44, ExplicitAny=6, UnknownArgumentType=6,
UnusedCallResult=5, UnknownParameterType=5, MissingParameterType=5,
UnknownMemberType=4, UnnecessaryComparison=4, UnknownVariableType=2,
MissingTypeStubs=1, PropertyTypeMismatch=1, UnnecessaryIsInstance=1,
Unreachable=1.

`word.py` holds the `Word` dataclass — central OCR type. Annotations here flow
into `block.py` and everything above.

**Total:** 85 warnings | **Effort:** M | **Risk:** medium |
**Depends on:** W3-A (doctr_support.py), W1-D (character.py). |
**Blocks:** W3-C (block.py).

#### Chunk W3-C: ocr/block.py

File: `ocr/block.py`

103 warnings: UnknownMemberType=23, UnknownArgumentType=22, Any=12,
PrivateUsage=7, ExplicitAny=6, UnknownParameterType=5,
MissingParameterType=5, UnnecessaryIsInstance=3, UnusedCallResult=3,
ImplicitStringConcat=2, UnnecessaryComparison=2, MissingTypeStubs=1,
ImplicitOverride=1, PropertyTypeMismatch=1, Unreachable=1.

`block.py` holds `Block` — the central layout unit. PrivateUsage (7) likely
accesses internals of DocTR objects; review whether to expose or suppress.

**Total:** 103 warnings | **Effort:** M | **Risk:** medium |
**Depends on:** W3-B (word.py), W3-A (doctr_support.py). |
**Blocks:** W3-D (document.py), W3-E (page.py), W2-D (dropcap.py — partial).

#### Chunk W3-D: ocr/document.py

File: `ocr/document.py`

144 warnings: Any=47, ExplicitAny=25, UnknownMemberType=25,
UnknownVariableType=14, UnknownArgumentType=12, UnknownParameterType=6,
MissingParameterType=6, MissingTypeStubs=3, UnnecessaryIsInstance=2,
StaleTypeIgnore=2, PropertyTypeMismatch=1, Unreachable=1.

**Total:** 144 warnings | **Effort:** L | **Risk:** medium-high |
**Depends on:** W3-C (block.py). |
**Blocks:** (nothing, but W3-E/page.py uses document types).

---

### Wave 4 — Heavy annotation-design files

These are the largest files with the deepest annotation gaps. They cannot
be meaningfully parallelized because:

- `reorganize_page_utils.py` and `layout_aware_reorg.py` share helper types
- `page.py` aggregates types from `document.py` and `block.py`

Each needs a focused subagent with full context of the types it uses.

#### Chunk W4-A: ocr/page.py

File: `ocr/page.py`

286 warnings: UnknownMemberType=81, Any=55, UnknownArgumentType=30,
UnknownVariableType=22, UnusedCallResult=17, MissingParameterType=16,
UnknownParameterType=14, ExplicitAny=13, ImplicitStringConcat=13,
UnknownLambdaType=6, UnnecessaryIsInstance=5, UnnecessaryComparison=5,
Unreachable=3, ImplicitOverride=2, PrivateUsage=2,
PropertyTypeMismatch=1, StaleTypeIgnore=1.

`page.py` is the top-level OCR result container. Many Unknown cascades here
will resolve automatically once W3-B/W3-C/W3-D land. Wait for those to
integrate before starting W4-A to avoid annotating what becomes self-evident.

**Total:** 286 warnings | **Effort:** L | **Risk:** high |
**Depends on:** W3-C (block.py), W3-D (document.py).

#### Chunk W4-B: ocr/layout_aware_reorg.py

File: `ocr/layout_aware_reorg.py`

129 warnings: UnknownMemberType=45, UnknownArgumentType=33,
UnknownVariableType=18, UnknownParameterType=7,
MissingParameterType=7, UnnecessaryComparison=6, Any=5,
PrivateUsage=4, UnusedFunction=2, ImplicitStringConcat=1,
UnusedParameter=1.

This file works with types from `page.py`, `block.py`, and layout types.
UnusedFunction (2) may indicate dead code paths to remove.

**Total:** 129 warnings | **Effort:** M | **Risk:** medium-high |
**Depends on:** W4-A (page.py), W3-C (block.py), W2-C (layout cluster).

#### Chunk W4-C: ocr/reorganize_page_utils.py

File: `ocr/reorganize_page_utils.py`

631 warnings: UnknownArgumentType=197, UnknownMemberType=147,
UnknownVariableType=110, Any=63, UnknownParameterType=34,
MissingParameterType=33, ExplicitAny=15, UnusedCallResult=11,
ImplicitStringConcat=8, UnknownLambdaType=4, UnusedParameter=3,
UnnecessaryComparison=2, UnannotatedClassAttribute=2, UnusedClass=1,
PrivateUsage=1.

The largest single file (631 warnings). A significant fraction of its
Unknown warnings will cascade-resolve once `page.py`, `block.py`, and
`word.py` are properly annotated. **Do not start this until W4-A and W3-C
have integrated** — otherwise the subagent spends effort annotating types
that become inferred automatically.

UnusedClass (1) and UnusedParameter (3) suggest dead code to prune before
annotating.

**Total:** 631 warnings | **Effort:** XL | **Risk:** high |
**Depends on:** W4-A (page.py), W4-B (layout_aware_reorg.py),
W3-B/W3-C/W3-D. This is the last chunk to ship.

---

## Parallelization Strategy

```text
Wave 1 (all parallel):
  W1-A  W1-B  W1-C  W1-D  W1-E  W1-F
  tiny   bbox  layout char  util  image
  17     55    23    31    50    13

         ↓              ↓       ↓
Wave 2 (all parallel, some gated on W1 chunks):
  W2-A         W2-B   W2-C    W2-D  W2-E
  provenance  geom   layout  dropcap pgdp
  41           33    103    48     121
        (W2-C gates on W1-C)
        (W2-D prefers W1-D)

Wave 3 (SEQUENTIAL within wave):
  W3-A → W3-B → W3-C → W3-D
  doctr   word   block   document
  70      85     103     144
  (each gates on previous; all gate on W1-B, W1-D)

Wave 4 (SEQUENTIAL within wave):
  W4-A → W4-B → W4-C
  page   layout_aware_reorg  reorganize_page_utils
  286    129                 631
  (each gates on previous + W3 complete)
```

**Truly parallel-safe chunks** (disjoint files, no ordering constraint):
Wave 1 (all 6), Wave 2 (all 5 after their Wave 1 deps land).

**Must be sequential** (type dependency chain):
W3-A → W3-B → W3-C → W3-D → W4-A → W4-B → W4-C.

---

## Baseline Regeneration Strategy

### The conflict problem

Each chunk runs on its own branch. `.basedpyright/baseline.json` is a large
generated file. If two branches both regenerate it, `git merge` will produce a
conflict on every single JSON line that changed. This is unworkable at scale.

### Recommended approach: regenerate once at integration time

**Per-branch rule:** subagent branches **must NOT regenerate baseline.json**.
The agent's job is only to fix the warnings (edit source files), verify that
`uv run basedpyright --project pyproject.toml` produces fewer warnings for the
files it touched (spot-check), and commit the source changes. The baseline file
stays unchanged on the branch.

**Integration step (done by CT or merge script, not a subagent):**

1. Merge or rebase all completed chunk branches into an integration branch.
2. Run `uv run basedpyright --project pyproject.toml --writebaseline .basedpyright/baseline.json`
   once on the integration branch.
3. Commit the updated baseline (`chore: regenerate basedpyright baseline after wave N`).
4. CI then validates that the new baseline is smaller (fewer total warnings).

**Per-wave cadence:** regenerate the baseline once per wave after all that
wave's branches land. This gives a clean checkpoint showing the warning count
reduction.

**Verification command for subagent branches (no baseline change):**

```bash
uv run basedpyright --project pyproject.toml 2>&1 | grep -E "^  .*(error|warning)" | \
  grep -f <(echo "${CHANGED_FILES[@]}") | wc -l
```

Or simply: after editing, run `uv run basedpyright --project pyproject.toml` and
confirm that warnings for the edited files are visibly reduced — the CI baseline
will still pass because it only gates NEW warnings above the baseline count.

---

## Tasks

- [ ] **W1-A** Tiny files — definite-fix only (17 warnings across 7 files)
- [ ] **W1-B** geometry/bounding_box.py (55 warnings)
- [ ] **W1-C** layout/types.py + layout/\_\_init\_\_.py (23 warnings)
- [ ] **W1-D** ocr/glyph_annotations.py + ocr/character.py + ocr/review.py (31 warnings)
- [ ] **W1-E** utility/timing.py + utility/ipynb_widgets.py (50 warnings)
- [ ] **W1-F** image_processing/formats.py + ocr/cv2_tesseract.py (13 warnings)
- [ ] **Regenerate baseline after Wave 1 integration**
- [ ] **W2-A** ocr/provenance.py + ocr/image_utilities.py (41 warnings)
- [ ] **W2-B** geometry/image_ops.py + geometry/point.py (33 warnings)
- [ ] **W2-C** layout/ cluster — detector, registry, adapters, visualize (103 warnings) [after W1-C]
- [ ] **W2-D** ocr/dropcap.py (48 warnings) [after W1-D; W3-B preferred]
- [ ] **W2-E** pgdp/pgdp_results.py (121 warnings)
- [ ] **Regenerate baseline after Wave 2 integration**
- [ ] **W3-A** ocr/doctr_support.py (70 warnings) [after W1-B, W1-D]
- [ ] **W3-B** ocr/word.py (85 warnings) [after W3-A]
- [ ] **W3-C** ocr/block.py (103 warnings) [after W3-B]
- [ ] **W3-D** ocr/document.py (144 warnings) [after W3-C]
- [ ] **Regenerate baseline after Wave 3 integration**
- [ ] **W4-A** ocr/page.py (286 warnings) [after W3-C, W3-D]
- [ ] **W4-B** ocr/layout_aware_reorg.py (129 warnings) [after W4-A, W3-C, W2-C]
- [ ] **W4-C** ocr/reorganize_page_utils.py (631 warnings) [after W4-A, W4-B, W3-B, W3-C, W3-D]
- [ ] **Regenerate baseline after Wave 4 integration — target: zero own-code warnings**

---

## Warning Count Summary by Wave

| Wave | Warnings addressed | Cumulative fixed | % of own-code total |
|---|---|---|---|
| Wave 1 (6 chunks, parallel) | ~189 | ~189 | ~8% |
| Wave 2 (5 chunks, parallel) | ~346 | ~535 | ~22% |
| Wave 3 (4 chunks, sequential) | ~402 | ~937 | ~39% |
| Wave 4 (3 chunks, sequential) | ~1,046 | ~1,983 | ~82% |
| Remainder (cascade resolves) | ~433 | ~2,416 | ~100% |

Note: Wave 4 warning counts will be materially lower than shown above because
many Unknown cascades in `page.py` and `reorganize_page_utils.py` will
self-resolve once Wave 3 annotations land. The ~433 "remainder" estimate
accounts for this; actual Wave 4 work may be significantly lighter.

---

## Notes for Subagents

- Each chunk gets its own branch: `fix/basedpyright-<chunk-id>` (e.g.
  `fix/basedpyright-w1-a`).
- Do NOT regenerate `.basedpyright/baseline.json` on the branch — leave it
  unchanged. CT regenerates it at wave integration time.
- Verify by running `uv run basedpyright --project pyproject.toml` after
  edits and counting warnings for touched files only.
- `make format && make lint` before committing.
- `make test` (full suite) before marking done — these are type-level changes
  but some involve removing dead code or unused parameters that could break tests.
- For `reportMissingTypeStubs` on third-party libs (ipywidgets, pytesseract,
  PIL sub-modules): use `# pyright: ignore[reportMissingTypeStubs]` — do not
  fight upstream.
- For `reportPrivateUsage`: check if the private attribute is actually
  accessible (common with DocTR internals) — if yes, suppress with
  `# pyright: ignore[reportPrivateUsage]` and add a comment explaining why.
- For `reportImplicitStringConcatenation`: always use explicit `+` or
  f-string or `textwrap.dedent` — implicit continuation is never intentional
  in this codebase.
