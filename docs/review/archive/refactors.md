# Archive — Refactor Opportunities (closed)

Closed entries originally tracked in `docs/review/refactors.md`. Moved
here on 2026-05-07. Resolution markers (`[FIXED in <sha>]`,
`[FIXED — ...]`, `[DECLINED — ...]`) and the original entry bodies
are preserved verbatim. Order matches the original review numbering.

Open / deferred items remain in the active `refactors.md` and are NOT
duplicated here:

- R-01, R-02, R-03, R-08 — DEFERRED (cross-repo coordination required)
- R-15 — partial; the closed sub-parts (det/reco helpers extracted)
  appear here. The remaining work (arch-detection helper, full
  `build_predictor` extraction) stays in the active doc.
- R-16 — open

---

## [FIXED in 31d09a9] ~~R-04 — `refine_bounding_box` and `refine_bbox` on `Word` should be consolidated~~

**File:** `pd_book_tools/ocr/word.py`, lines 681–689 (`refine_bounding_box`), lines 768+ (`refine_bbox`)

Two overlapping in-place methods with different fallback behavior:

- `refine_bounding_box(image, padding_px=0)` — no crop fallback, returns `None`
- `refine_bbox(page_image)` — falls back to `crop_bottom`, returns `bool`

`Block.refine_bounding_boxes` calls both on different code paths, producing
inconsistent behavior. The docstring on `refine_bounding_box` is also placed after a
`logger.debug` call, making it an orphaned expression rather than a real docstring.

**Direction:** consolidate to a single `refine_bbox(image, padding_px=0) -> bool` with
`crop_bottom` fallback. Update all callers.

---

## [FIXED in 2fab29c] ~~R-05 — `_purge_word_from_blocks` is duplicated between two modules~~

**Files:**

- `pd_book_tools/ocr/layout_aware_reorg.py`, lines 226–245
- `pd_book_tools/ocr/reorganize_page_utils.py`, lines 175–198

Near-identical logic. The comment in `reorganize_page_utils.py` explains the
duplication exists to avoid pulling the layout-types import into the geometry pipeline.
This is valid reasoning, but the correct fix is to extract the shared logic into
`pd_book_tools/ocr/block.py` (which has no layout dependency), allowing both modules
to import from there.

---

## [FIXED in 59495ff] ~~R-06 — `cupy_processing/canvas.py` has a hard dependency on `cv2_processing` for an enum~~

**File:** `pd_book_tools/image_processing/cupy_processing/canvas.py`, line 7

```python
from pd_book_tools.image_processing.cv2_processing.canvas import Alignment
```

Any import of the cupy backend pulls in cv2, breaking GPU-only deployments.

**Direction:** move `Alignment` (and any other shared constants) to
`pd_book_tools/image_processing/common.py`. Both backends import from there.

---

## [FIXED in 5862af4] ~~R-07 — `Point.__getattr__` delegates to Shapely, leaking all Shapely internals as public API~~

**File:** `pd_book_tools/geometry/point.py`, lines 96–97

```python
def __getattr__(self, item):
    return getattr(self._geom, item)
```

Every Shapely attribute and method (including internal and deprecated ones) becomes
part of `Point`'s undocumented public API. Shapely version changes silently propagate
to `Point`.

**Direction:** remove `__getattr__`. Provide `as_shapely() -> shapely.geometry.Point`
for the rare cases where the underlying geometry is needed. Add explicit properties or
methods for any Shapely features actually used by callers.

---

## [FIXED in f1448eb] ~~R-09 — `colorToGray.py` is the only camelCase module in the package~~

**File:** `pd_book_tools/image_processing/cupy_processing/colorToGray.py`

PEP8 requires module names to be `lowercase_with_underscores`. The function names
inside (`cupy_colorToGray`, `np_uint8_float_colorToGray`) also violate PEP8 and are
inconsistent with every other function in the cupy backend (`bgr_to_gray_gpu`,
`gaussian_filter_gpu`, etc.).

**Direction (breaking change, coordinate with downstream):**
Rename `colorToGray.py` → `color_to_gray.py`.
Rename `cupy_colorToGray` → `cupy_color_to_gray`.
Rename `np_uint8_float_colorToGray` → `np_uint8_color_to_gray`.
Update `__init__.py`, test file, and all downstream imports in `pd-ocr-cli` and
`pd-ocr-labeler`.

---

## [DECLINED — already addressed in `b9ec50a`; declining further consolidation as a public-API break] R-10 — `normalize_word_component` and `normalize_character_component` are identical

**File:** `pd_book_tools/ocr/label_normalization.py`, lines 99–120

Both delegate to `_normalize_component` with the same `allowed_components=ALLOWED_COMPONENTS`
frozenset. The only distinction is the error message string (`"word component"` vs
`"character component"`). If word and character components genuinely share the same
allowed set, there should be one function with a `component_type: str` parameter for
the error message.

**Declined:** The structural concern the review flagged — a duplicated
normalization implementation across the two functions — was already
addressed by `b9ec50a` ("refactor(ocr): simplify component labels and
remove Character bool fields", March 2026). Both public functions are
now two-line thin wrappers around a single private `_normalize_component`
helper that takes the component-type label as a `label_type: str`
parameter — exactly the pattern the review recommends.

The further step of merging the two public wrappers into one
`normalize_component(component, component_type)` function would be a
public-API break, not a behavior-preserving refactor:

- `normalize_word_component` is imported by `pd_book_tools/ocr/word.py`
  (3 call sites) and by
  `pd-ocr-labeler/pd_ocr_labeler/views/projects/pages/word_operations.py`
  (1 call site). The labeler is a separate repo — collapsing the API
  would force a coordinated cross-repo update.
- The two named entry points carry semantic intent at the call site
  (a word's components vs. a character's components) and produce
  distinct user-visible error messages keyed off that intent.

The remaining duplication is intentional surface API, not implementation
duplication. R-10's actual concern is resolved.

---

## [FIXED in 90caa36] ~~R-11 — `BoundingBox.from_dict(self.to_dict())` is used as a copy idiom~~

**File:** `pd_book_tools/geometry/bounding_box.py`, lines 579, 585, 617, 625, 638

Several places serialize and immediately deserialize through a dict to obtain a copy.
`BoundingBox` is a `@dataclass` and could implement `__copy__` or use
`dataclasses.replace(self)` for a clean, zero-allocation copy.

---

## [FIXED in 39bcf86] ~~R-12 — `contains_point` uses Shapely for a trivial axis-aligned containment check~~

**File:** `pd_book_tools/geometry/bounding_box.py`, line 373

`contains_point` builds a Shapely geometry and calls `.covers()`. For an axis-aligned
bounding box this is equivalent to:

```python
self.minX <= point.x <= self.maxX and self.minY <= point.y <= self.maxY
```

The Shapely path allocates objects unnecessarily.

---

## [FIXED — deprecation warnings emitted; behaviour preserved] ~~R-13 — `lrtb` and `lrwh` properties are misnamed and redundant duplicates~~

**File:** `pd_book_tools/geometry/bounding_box.py`, lines 62–63, 81–82

- `lrtb` returns `(left, top, right, bottom)` — the acronym implies left-right-top-bottom
- `to_ltrb()` returns identical values with a correct name
- `lrwh` returns `(left, top, width, height)` — implies left-right-width-height
- `to_ltwh()` returns identical values with a correct name

**Direction:** deprecate `lrtb` and `lrwh`; keep only `to_ltrb()` and `to_ltwh()`.

Resolved by emitting `DeprecationWarning` from both properties while
preserving their return values (delegates to `to_ltrb()` / `to_ltwh()`).
Workspace-wide grep found no callers outside this repo's own tests, so
removal can land in a future major; deprecation is the safe interim.
Tests assert the warning fires and the return values still match the
canonical methods.

---

## [FIXED — narrowed to LINE+WORDS only; PARAGRAPH allows either child_type] ~~R-14 — `Block` validates `child_type` but not `block_category` / `child_type` consistency~~

**File:** `pd_book_tools/ocr/block.py`, lines 420–446

`Block` is used for lines, paragraphs, and document-level blocks, distinguished only
by `block_category`. There is no validation that `block_category=LINE` requires
`child_type=WORDS`, or that a `PARAGRAPH` must contain `BLOCKS` not `WORDS` directly.

**Direction:** add a `__post_init__` consistency check:

```python
if self.block_category == BlockCategory.LINE:
    assert self.child_type == BlockChildType.WORDS
```

---

## [FIXED in 794377b — closes the partial extraction archived earlier] ~~R-15 — `get_finetuned_torch_doctr_predictor` does too much in one function~~

**File:** `pd_book_tools/ocr/doctr_support.py`

The function: detects architecture from checkpoint filename heuristics,
downloads architecture-specific pretrained weights (wasteful — see M-24,
already addressed), loads two state dicts, assembles an `OCRPredictor`,
and optionally wraps it. Each concern should be a separate function.

Closed in two stages:

- First wave: `_load_det_model(path, arch) -> DetectionModel` and
  `_load_reco_model(path, arch) -> RecognitionModel` extracted alongside
  the existing `_detect_*_arch` and `_read_*_sidecar` helpers; both
  encapsulate the torch_load → arch resolution → build_arch(pretrained=False)
  → load_state_dict-with-M23-context pipeline.
- Final wave (`794377b`): the remaining inlined orchestration was
  extracted into three more module-level helpers — `_select_torch_device()`
  (CUDA > MPS > CPU device pick), `_build_doctr_arch(arch_name, doctr_models, **kwargs)`
  (the doctr factory lookup with the historical fallback policy, formerly
  a closure inside the public function), and `_assemble_doctr_predictor(det_model, reco_model, *, pretrained)`
  (the `ocr_predictor` + `detection_predictor` + `recognition_predictor`
  wrap-up that attaches the latter two onto the full predictor).
  `get_finetuned_torch_doctr_predictor` is now a thin top-level
  orchestrator over six named helpers; the public signature is unchanged.
  `tests/ocr/test_doctr_support.py::TestR15ExtractedHelpers` pins each
  new helper independently.

---

## [FIXED] ~~R-17 — `detect_best_rotation` always runs OCR at 0° even when the caller has the result~~

**File:** `pd_book_tools/ocr/rotation.py`

The function unconditionally calls `ocr_fn(image)` for the upright orientation. A
caller who already has OCR output for the upright page cannot pass it in, causing
a redundant OCR pass.

**Direction:** add an optional `upright_result` parameter:

```python
def detect_best_rotation(image, ocr_fn, ..., upright_result=None):
    result_0 = upright_result if upright_result is not None else ocr_fn(image)
```

Resolved by adding the optional ``upright_result`` keyword parameter.
When provided, the upright OCR call is skipped entirely. Two new tests
pin the behavior: pre-supplied high-confidence upright result triggers
zero ocr_fn calls; pre-supplied low-confidence upright result triggers
exactly 3 fallback calls (90/180/270 only).

---

## [FIXED] ~~R-18 — Mixed old-style and new-style type annotations throughout~~

**Files:** throughout `pd_book_tools/ocr/`, `pd_book_tools/geometry/`

The codebase mixed:

- `Optional[List[str]]` (legacy `typing` forms, Python 3.5–3.8 style)
- `list[str]`, `str | None` (modern Python 3.10+ forms)

Within single files (e.g., `page.py` imported `List`, `Optional` from `typing`
but used `list[str]` elsewhere). This created visual inconsistency and
confused tools that check annotation style.

Resolved by standardizing on modern forms (`list`, `dict`, `tuple`,
`X | None`) across `pd_book_tools/`. Files that previously imported
`Optional`/`List`/`Dict`/`Tuple`/`Union` from `typing` either gained
`from __future__ import annotations` (for runtime-evaluated annotation
contexts such as dataclass fields) or were updated in place. A
workspace-wide grep for `(Optional|Dict|List|Tuple|Union)\[` over files
that import from `typing` returns zero hits.

---

## [FIXED] ~~R-19 — `PGDPResults` uses bare class-level annotations without `@dataclass`~~

**File:** `pd_book_tools/pgdp/pgdp_results.py`, lines 12–18

The class declares `png_file: str`, `png_full_path: pathlib.Path`, etc. as
class-level annotations without `@dataclass`. These look like class variables
with defaults but are instance variables set in `__init__`. Before `__init__` runs,
accessing them on the class raises `AttributeError`.

**Direction:** either apply `@dataclass` and generate `__init__`, or remove the
class-level annotations and rely solely on the custom `__init__`.

Resolved by removing the misleading class-level annotations and declaring
all instance attributes inline in `__init__` (with `processed_*` initialized
to empty defaults before `process()` populates them). `@dataclass` was
declined because the public constructor takes only `(png_file, page_text)`
and computes all other fields in `process()` — a custom `__init__` is the
honest representation of that shape.

---

## [FIXED] ~~R-20 — `PGDPResults` processing methods are `@classmethod` but use neither `cls` nor class state~~

**File:** `pd_book_tools/pgdp/pgdp_results.py`, lines 55, 64, 74, 86, 162, 166, 178, 183

All 8 processing methods (`remove_blank_page`, `remove_proofer_notes`, etc.) are
`@classmethod` that receive only `text: str` and return `str`. None use `cls`.
`@classmethod` suggests these might construct instances or call other class methods;
`@staticmethod` communicates the actual intent.

Resolved by converting all 8 methods to `@staticmethod`. Workspace-wide
grep confirmed all callers use the `PGDPResults.method(text)` form (no
instance method calls, no `cls` usage), so the swap is behavior-preserving.

---

## [FIXED in 90466bb] ~~R-21 — `_require_same_coords` decorator is missing `functools.wraps`~~

**File:** `pd_book_tools/geometry/bounding_box.py`, lines 376–384

Decorated methods lose `__name__`, `__doc__`, and `__qualname__`. `functools.wraps`
is already imported in `timing.py`; it needs to be added to `bounding_box.py` as well.

---

## [FIXED — canonical name added; deprecated alias preserved] ~~R-22 — `timing.py` public API has a typo in the function name~~

**File:** `pd_book_tools/utility/timing.py`, line 7

`func_log_excution_time` — `excution` should be `execution`. This is a public function
imported by tests by name; fixing it requires a deprecation alias.

**Direction:**

```python
def func_log_execution_time(...):  # new canonical name
    ...

func_log_excution_time = func_log_execution_time  # deprecated alias
```

---

## [FIXED — `log_level` keyword canonical; `logLevel` deprecated] ~~R-23 — `timing.py` `logLevel` parameter should be `log_level` (PEP8)~~

**File:** `pd_book_tools/utility/timing.py`, line 7

`logLevel` is camelCase; PEP8 requires `log_level`. Minor but inconsistent with the
rest of the codebase.

---

## [FIXED — deprecation warning emitted on non-default values; behavior preserved] ~~R-24 — `aspect_ratio` parameter in both `rescale` backends is accepted but never used~~

**Files:**

- `pd_book_tools/image_processing/cv2_processing/rescale.py`, lines 20–26
- `pd_book_tools/image_processing/cupy_processing/rescale.py`, lines 11–12

Both functions compute a `target_long_side` variable from `aspect_ratio` (cv2) or
accept the parameter (cupy) but never use it. Both functions always preserve the
original aspect ratio. Callers who pass `aspect_ratio` believing it does something
silently get the wrong behavior.

**Direction:** either implement the clamping (cap long side at `target_short_side * aspect_ratio`),
or remove the parameter from both signatures.

Resolved by deprecating the parameter rather than implementing the
clamping. `pd-prep-for-pgdp/core/pipeline/process_page.py:154` actively
passes `aspect_ratio=cfg.page_h_w_ratio` thinking it does something —
silently changing the math underneath that caller would risk
regressions on production pipelines. Both backends now emit a
`DeprecationWarning` only when a non-default value is passed (the
existing `1.65` default is silent so existing default-using callers
don't get spammed). The warning will be promoted to removal in a
future major; downstream callers should drop the keyword argument.

---

## [FIXED — `register_detector`/`unregister_detector` added; built-in keys reserved] ~~R-25 — Layout registry has no extensibility path for custom adapters~~

**File:** `pd_book_tools/layout/registry.py`; `pd_book_tools/layout/adapters/__init__.py`

The `_build()` function is a hard-coded `if/elif` chain. The comment acknowledges this
is "by design," but `pd-ocr-trainer` produces custom fine-tuned checkpoints that will
eventually need custom adapter keys.

**Direction:** add a `register_detector(key: str, factory_fn: Callable[..., LayoutDetector])`
function that populates a user-extension dict checked before the built-in chain.

---

## [FIXED — now raises ValueError] ~~R-26 — `PageLayout.of_type()` with no arguments silently returns `[]`~~

**File:** `pd_book_tools/layout/types.py`, lines 126–128

`layout.of_type()` tests `r.type in set()` — always `False`. Passing no types returns
an empty list, which looks like "no regions found" rather than "all regions."

**Direction:** either return all regions when called with no arguments, or raise
`ValueError("at least one RegionType required")`.

---

## [FIXED — setter canonicalizes empty/None to None] ~~R-27 — `ground_truth_text` property maps both `None` and `""` to the same external value~~

**File:** `pd_book_tools/ocr/word.py`, lines 140–146

`return self._ground_truth_text or ""` means `None` and `""` are externally
indistinguishable. But `to_dict` serializes both as `None`, while
`copy_ocr_to_ground_truth` and `clear_ground_truth` treat them differently.

**Direction:** pick one canonical null value (`None`) and handle it consistently
through the property getter, setter, `to_dict`, and `from_dict`.

---

## [FIXED — deprecation warning emitted; legacy order still accepted] ~~R-28 — `ipynb_widgets.py` has inconsistent argument order across related functions~~

**File:** `pd_book_tools/utility/ipynb_widgets.py`, lines 65–89

`get_html_string_from_cropped_image(img, bounding_box, ...)` and
`get_html_widget_from_cropped_image(img, bounding_box)` take `(img, bounding_box)`.
`get_hbox_widget_for_cropped_image(bounding_box, img)` reverses the order. Callers
easily pass arguments in the wrong order, getting silent wrong output.

**Direction:** standardize to `(img, bounding_box)` order across all three functions.

Resolved by standardizing `get_hbox_widget_for_cropped_image` to
`(img, bounding_box)`. The legacy `(bounding_box, img)` order is
detected at runtime via `isinstance` type discriminator (BoundingBox
vs ndarray — they never overlap), arguments are swapped internally,
and a `DeprecationWarning` is raised pointing callers at the canonical
order. Workspace-wide grep found no callers outside this repo's own
tests, so removal can land in a future major; deprecation is the safe
interim. The repo's own test was updated to use the canonical order,
plus a new test pins the deprecation-warning behavior.

---

## [FIXED] ~~R-29 — `ipynb_widgets.py` has dead commented-out code and PascalCase local variable names~~

**File:** `pd_book_tools/utility/ipynb_widgets.py`, lines 30, 87–88, 92–95

`text_HBox` and `ImageHBox` use PascalCase (reserved for classes in PEP8). A
commented-out old implementation remains at lines 92–95.

**Direction:** rename to `text_hbox` / `image_hbox`; remove the commented-out code.

---

## [FIXED — canonical name added; deprecated alias preserved] ~~R-30 — `np_uint8_float_*` naming convention is ambiguous~~

**Files:**

- `pd_book_tools/image_processing/cupy_processing/colorToGray.py`
- `pd_book_tools/image_processing/cupy_processing/threshold.py`

The `np_uint8_float_*` prefix is used for "takes uint8 numpy input, processes as float
internally." The rest of the package uses `np_uint8_*` to mean "takes/returns CPU
uint8 numpy arrays." The `_float_` infix misleads callers into thinking float input is
accepted or returned.

**Direction:** rename to `np_uint8_*` (dropping the `_float_` infix), which is
consistent with the rest of the `np_uint8_*` wrapper family.

After the f1448eb rename of `np_uint8_float_colorToGray` →
`np_uint8_color_to_gray`, the only remaining offender was
`np_uint8_float_binary_thresh`. Resolved by adding
`np_uint8_otsu_binary_thresh` as the canonical name (semantically
clearer: this wrapper is specifically for Otsu's method) and keeping
`np_uint8_float_binary_thresh` as a thin deprecated alias that emits
`DeprecationWarning`. Workspace-wide grep found no actual code callers
outside this repo's own tests; only `pd-prep-for-pgdp/specs/` markdown
references the old name (left as-is — historical spec context).
