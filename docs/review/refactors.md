# Refactor Opportunities

Structural, design, and API improvements that are not bugs but would reduce
maintenance burden, improve correctness guarantees, and make the library easier
to use correctly. Organized roughly by impact.

---

**Status (2026-05-07):** 27 of 30 review-numbered items closed. Closed
items (FIXED / DECLINED / FIXED-with-deprecation) live in
[`archive/refactors.md`](archive/refactors.md). Only the items that
still need work remain below: three DEFERRED structural-coupling items
(R-01, R-02, R-03). New refactor ideas should be added here under the
next available `R-NN` number; when closed, **move** the entry into
`archive/refactors.md` rather than annotating it FIXED in place — see
[`README.md`](README.md) for the workflow.

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
