# Refactor Opportunities

Structural, design, and API improvements that are not bugs but would reduce
maintenance burden, improve correctness guarantees, and make the library easier
to use correctly. Organized roughly by impact.

---

## [DEFERRED] R-01 — Image operations belong in `image_utilities.py`, not on `Word`, `Block`, and `Page`

**Deferred:** This is a real coupling — `Word` / `Block` import `cv2` and
`numpy` at module top to support `refine_bounding_box`, `refine_bbox`,
`split_into_characters_from_whitespace`, `estimate_baseline_from_image`,
`crop_bottom`, `crop_top`, etc. — but the proposed fix breaks public API
across multiple downstream repos. The labeler in particular calls
`word.refine_bbox(...)`, `word.crop_bottom(...)`,
`page.refine_bounding_boxes(...)` directly (see
`pd-ocr-labeler/pd_ocr_labeler/operations/ocr/bbox_operations.py:241`,
`pd-ocr-labeler/pd_ocr_labeler/operations/ocr/page_operations.py:738+`)
and has tests that monkey-patch these as instance methods
(`tests/pd_ocr_labeler/operations/ocr/test_bbox_operations.py` —
`word.crop_bottom = lambda img: ...` ~12 sites,
`test_page_operations.py:649,664,679` — `mock_page.refine_bounding_boxes`).
Converting these to free functions also loses the natural `(self, image)`
binding for in-place mutation (`self.bounding_box = ...`), which is how
all six methods currently work. Scope: ~6 methods × 2 classes (Word,
Block) + Page facade + ~15+ downstream call sites + monkey-patch test
idioms. Needs a dedicated cross-repo coordination iteration with the
user; not a unilateral library-only change.

**Files:**

- `pd_book_tools/ocr/word.py`, lines 768–959
- `pd_book_tools/ocr/block.py`, lines 1000–1059

`Word` and `Block` directly import `numpy` and `cv2` to implement
`split_into_characters_from_whitespace`, `estimate_baseline_from_image`, `refine_bbox`,
`crop_bottom`, `crop_top`, and visualization helpers. The image is always passed as a
parameter — it is never owned by `Word` or `Block`. This couples the data model to
OpenCV, so any consumer of `Word` or `Block` (tests, training code, labeler) pays the
full OpenCV import cost even when images are never used.

**Direction:** move all image-dependent methods out of `Word` and `Block` into
`pd_book_tools/ocr/image_utilities.py` as free functions: `refine_word_bbox(word, image)`,
`split_word_into_characters(word, image)`, etc. `Word` and `Block` should only know
about `BoundingBox`.

---

## [DEFERRED] R-02 — `Page` uses `@dataclass` but also defines a custom `__init__` — pick one

**Deferred:** The pattern is real (custom `__init__` shadows the
generated one and silently relies on class-level annotation defaults to
make `_cv2_numpy_page_image_*` accessible — verified 2026-05 that this
works in practice rather than raising `AttributeError` as the review
claimed; review is partly stale on the symptom). However, the cleanest
behavior-preserving fix has hidden complexity:

1. Removing `@dataclass` loses the auto-generated `__eq__` / `__repr__`.
   The current `__eq__` is already broken — it includes 9 `ndarray`
   fields whose `__eq__` raises "ambiguous truth value" — but no test
   compares Pages so the breakage is dormant. Touching this risks
   surfacing latent bugs.
2. The custom `__init__` sets ~10 instance attributes
   (`image_path`, `name`, `source`, `ocr_failed`, `provenance_*`,
   `rotation_applied`, `diagnostic_*`) that are NOT declared as fields —
   any "convert fully to dataclass" path needs to add these as fields
   first, which is itself a behavior change (they'd appear in `__repr__`
   / `dataclasses.fields`).
3. `field(default_factory=list, init=False)` on `_items` interacts with
   the custom `__init__` in a way that does work (verified) but is
   fragile.

This is best done as a single thoughtful PR with a regression test
pinning current observable behavior (constructor args, attribute access
post-init, `to_dict` round-trip) BEFORE any structural change. Scope:
single file but ~150 lines of `__init__` and ~20 instance attributes
needing decisions about field-vs-not. Defer to a focused iteration.

**File:** `pd_book_tools/ocr/page.py`, lines 57–200

`@dataclass` generates an `__init__` that is immediately superseded by the custom one.
Dataclass `field(default_factory=list, init=False)` declarations like `_items` are
never initialized by the generated `__init__` (which never runs). Image cache fields
(`_cv2_numpy_page_image_*`) are declared as dataclass fields but only set in
`refresh_page_images()` — accessing them before that call raises `AttributeError`.

**Direction:** either:

- Remove `@dataclass` and initialize all fields explicitly in the custom `__init__`, or
- Convert fully to `@dataclass` (using `__post_init__` for computed fields) and
  eliminate the custom `__init__`.

---

## [DEFERRED] R-03 — `BoundingBox` mixes geometry with image-processing (imports cv2 directly)

**Deferred:** The principle is real — `bounding_box.py` imports `cv2`
and contains `_extract_roi`, `_threshold_inverted`,
`_tight_bbox_from_thresh`, `_connected_content_bbox_from_image_thresh`,
`_finalize_pixel_bbox`, `_vertical_crop`, `refine`, `crop_top`,
`crop_bottom` — none of which belong on a geometric value type. But the
refactor has the same blast radius as R-01:

1. **Public API change.** Callers do
   `self.bounding_box.refine(image, padding_px=...)`,
   `self.bounding_box.crop_top(image)`, `self.bounding_box.crop_bottom(image)`
   (Word, Block facades, plus downstream tests in pd-ocr-labeler that mock
   `mock_word.bounding_box.refine = MagicMock(...)` —
   `test_page_operations.py:760, 776`).
2. **Overlaps with R-01.** Both refactors funnel into the same
   "image_utilities" landing module. Doing them as one coordinated
   change is cheaper than two sequential PRs each forcing downstream
   pinning.
3. **Cost/benefit weak.** cv2 is a hard runtime dependency of
   pd-book-tools (not optional); no consumer currently needs cv2-free
   geometry. The "cleaner module boundary" benefit is real but
   speculative until a consumer actually wants it.

Defer with R-01 to a dedicated cross-repo geometry/cv2 separation
iteration. Track them together when planning.

**File:** `pd_book_tools/geometry/bounding_box.py`, lines 475–650

The `refine` / `crop_bottom` / `crop_top` family of methods and their helpers
(`_extract_roi`, `_threshold_inverted`, `_tight_bbox_from_thresh`, etc.) import and
use `cv2` directly. A geometry data type should not depend on a computer vision
framework. This prevents using `BoundingBox` in environments where cv2 is unavailable.

**Direction:** extract the image-dependent helpers into a separate module
(e.g., `pd_book_tools/geometry/image_ops.py` or fold into `ocr/image_utilities.py`)
and have `BoundingBox` expose only coordinate geometry.

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

## [DEFERRED] R-08 — All `__init__.py` files are empty; `utility/` has no `__init__.py` at all

**Files:**

- `pd_book_tools/pd_book_tools/__init__.py` (0 lines)
- `pd_book_tools/pd_book_tools/geometry/__init__.py` (0 lines)
- `pd_book_tools/pd_book_tools/pgdp/__init__.py` (0 lines)
- `pd_book_tools/pd_book_tools/utility/` (no `__init__.py`)

The library has no stable public API surface. Every consumer must know and use full
internal submodule paths. Internal restructuring (moving `bounding_box.py`,
renaming submodules) is a breaking change for all downstream packages.

**Direction:**

- `pd_book_tools/__init__.py`: re-export `BoundingBox`, `Point`
- `pd_book_tools/geometry/__init__.py`: re-export `BoundingBox`, `Point`
- `pd_book_tools/pgdp/__init__.py`: re-export `PGDPResults`, `PGDPExport`
- `pd_book_tools/utility/__init__.py`: create with `timing` and `ipynb_widgets` exports
- `pd_book_tools/layout/__init__.py`: add `draw_layout_overlay`, `clear_detector_cache`,
  and all geometry helpers (`caption_for_figure`, `iou`, `contains`, etc.)

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

## R-13 — `lrtb` and `lrwh` properties are misnamed and redundant duplicates

**File:** `pd_book_tools/geometry/bounding_box.py`, lines 62–63, 81–82

- `lrtb` returns `(left, top, right, bottom)` — the acronym implies left-right-top-bottom
- `to_ltrb()` returns identical values with a correct name
- `lrwh` returns `(left, top, width, height)` — implies left-right-width-height
- `to_ltwh()` returns identical values with a correct name

**Direction:** deprecate `lrtb` and `lrwh`; keep only `to_ltrb()` and `to_ltwh()`.

---

## R-14 — `Block` validates `child_type` but not `block_category` / `child_type` consistency

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

## R-15 — `get_finetuned_torch_doctr_predictor` does too much in one function

**File:** `pd_book_tools/ocr/doctr_support.py`

The function: detects architecture from checkpoint filename heuristics, downloads
architecture-specific pretrained weights (wasteful — see H-24), loads two state dicts,
assembles a `OCRPredictor`, and optionally wraps it. Each concern should be a separate
function:

- `_detect_arch_from_checkpoint(path) -> str`
- `_load_det_model(path, arch) -> DetectionModel`
- `_load_reco_model(path, arch) -> RecognitionModel`
- `build_predictor(det_model, reco_model) -> OCRPredictor`

---

## R-16 — `from_doctr_output` and `from_tesseract_output` should break out per-level helpers

**File:** `pd_book_tools/ocr/document.py`

Both adapter functions iterate 3–4 nested levels (document → page → block →
paragraph → line → word) with inline coordinate conversion at each level. Each level
should be a separate function with a clear signature:

```python
def _word_from_doctr(word_data, page_w, page_h) -> Word
def _line_from_doctr(line_data, page_w, page_h) -> Block
def _block_from_doctr(block_data, page_w, page_h) -> Block
def _page_from_doctr(page_data) -> Page
```

---

## R-17 — `detect_best_rotation` always runs OCR at 0° even when the caller has the result

**File:** `pd_book_tools/ocr/rotation.py`

The function unconditionally calls `ocr_fn(image)` for the upright orientation. A
caller who already has OCR output for the upright page cannot pass it in, causing
a redundant OCR pass.

**Direction:** add an optional `upright_result` parameter:

```python
def detect_best_rotation(image, ocr_fn, ..., upright_result=None):
    result_0 = upright_result if upright_result is not None else ocr_fn(image)
```

---

## R-18 — Mixed old-style and new-style type annotations throughout

**Files:** throughout `pd_book_tools/ocr/`, `pd_book_tools/geometry/`

The codebase mixes:

- `Optional[List[str]]` (legacy `typing` forms, Python 3.5–3.8 style)
- `list[str]`, `str | None` (modern Python 3.10+ forms)

Within single files (e.g., `page.py` imports `List`, `Optional` from `typing` on
line 10 but uses `list[str]` on line 68). This creates visual inconsistency and
confuses tools that check annotation style.

**Direction:** standardize on modern forms (`list`, `dict`, `tuple`, `X | None`)
throughout. Remove `from typing import List, Dict, Tuple, Optional, Union` imports
in favor of `from __future__ import annotations` (for Python < 3.10 compat) or
direct modernization.

---

## R-19 — `PGDPResults` uses bare class-level annotations without `@dataclass`

**File:** `pd_book_tools/pgdp/pgdp_results.py`, lines 12–18

The class declares `png_file: str`, `png_full_path: pathlib.Path`, etc. as
class-level annotations without `@dataclass`. These look like class variables
with defaults but are instance variables set in `__init__`. Before `__init__` runs,
accessing them on the class raises `AttributeError`.

**Direction:** either apply `@dataclass` and generate `__init__`, or remove the
class-level annotations and rely solely on the custom `__init__`.

---

## R-20 — `PGDPResults` processing methods are `@classmethod` but use neither `cls` nor class state

**File:** `pd_book_tools/pgdp/pgdp_results.py`, lines 55, 64, 74, 86, 162, 166, 178, 183

All 8 processing methods (`remove_blank_page`, `remove_proofer_notes`, etc.) are
`@classmethod` that receive only `text: str` and return `str`. None use `cls`.
`@classmethod` suggests these might construct instances or call other class methods;
`@staticmethod` communicates the actual intent.

---

## R-21 — `_require_same_coords` decorator is missing `functools.wraps`

**File:** `pd_book_tools/geometry/bounding_box.py`, lines 376–384

Decorated methods lose `__name__`, `__doc__`, and `__qualname__`. `functools.wraps`
is already imported in `timing.py`; it needs to be added to `bounding_box.py` as well.

---

## R-22 — `timing.py` public API has a typo in the function name

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

## R-23 — `timing.py` `logLevel` parameter should be `log_level` (PEP8)

**File:** `pd_book_tools/utility/timing.py`, line 7

`logLevel` is camelCase; PEP8 requires `log_level`. Minor but inconsistent with the
rest of the codebase.

---

## R-24 — `aspect_ratio` parameter in both `rescale` backends is accepted but never used

**Files:**

- `pd_book_tools/image_processing/cv2_processing/rescale.py`, lines 20–26
- `pd_book_tools/image_processing/cupy_processing/rescale.py`, lines 11–12

Both functions compute a `target_long_side` variable from `aspect_ratio` (cv2) or
accept the parameter (cupy) but never use it. Both functions always preserve the
original aspect ratio. Callers who pass `aspect_ratio` believing it does something
silently get the wrong behavior.

**Direction:** either implement the clamping (cap long side at `target_short_side * aspect_ratio`),
or remove the parameter from both signatures.

---

## R-25 — Layout registry has no extensibility path for custom adapters

**File:** `pd_book_tools/layout/registry.py`; `pd_book_tools/layout/adapters/__init__.py`

The `_build()` function is a hard-coded `if/elif` chain. The comment acknowledges this
is "by design," but `pd-ocr-trainer` produces custom fine-tuned checkpoints that will
eventually need custom adapter keys.

**Direction:** add a `register_detector(key: str, factory_fn: Callable[..., LayoutDetector])`
function that populates a user-extension dict checked before the built-in chain.

---

## R-26 — `PageLayout.of_type()` with no arguments silently returns `[]`

**File:** `pd_book_tools/layout/types.py`, lines 126–128

`layout.of_type()` tests `r.type in set()` — always `False`. Passing no types returns
an empty list, which looks like "no regions found" rather than "all regions."

**Direction:** either return all regions when called with no arguments, or raise
`ValueError("at least one RegionType required")`.

---

## R-27 — `ground_truth_text` property maps both `None` and `""` to the same external value

**File:** `pd_book_tools/ocr/word.py`, lines 140–146

`return self._ground_truth_text or ""` means `None` and `""` are externally
indistinguishable. But `to_dict` serializes both as `None`, while
`copy_ocr_to_ground_truth` and `clear_ground_truth` treat them differently.

**Direction:** pick one canonical null value (`None`) and handle it consistently
through the property getter, setter, `to_dict`, and `from_dict`.

---

## R-28 — `ipynb_widgets.py` has inconsistent argument order across related functions

**File:** `pd_book_tools/utility/ipynb_widgets.py`, lines 65–89

`get_html_string_from_cropped_image(img, bounding_box, ...)` and
`get_html_widget_from_cropped_image(img, bounding_box)` take `(img, bounding_box)`.
`get_hbox_widget_for_cropped_image(bounding_box, img)` reverses the order. Callers
easily pass arguments in the wrong order, getting silent wrong output.

**Direction:** standardize to `(img, bounding_box)` order across all three functions.

---

## R-29 — `ipynb_widgets.py` has dead commented-out code and PascalCase local variable names

**File:** `pd_book_tools/utility/ipynb_widgets.py`, lines 30, 87–88, 92–95

`text_HBox` and `ImageHBox` use PascalCase (reserved for classes in PEP8). A
commented-out old implementation remains at lines 92–95.

**Direction:** rename to `text_hbox` / `image_hbox`; remove the commented-out code.

---

## R-30 — `np_uint8_float_*` naming convention is ambiguous

**Files:**

- `pd_book_tools/image_processing/cupy_processing/colorToGray.py`
- `pd_book_tools/image_processing/cupy_processing/threshold.py`

The `np_uint8_float_*` prefix is used for "takes uint8 numpy input, processes as float
internally." The rest of the package uses `np_uint8_*` to mean "takes/returns CPU
uint8 numpy arrays." The `_float_` infix misleads callers into thinking float input is
accepted or returned.

**Direction:** rename to `np_uint8_*` (dropping the `_float_` infix), which is
consistent with the rest of the `np_uint8_*` wrapper family.
