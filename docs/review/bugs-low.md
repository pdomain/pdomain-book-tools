# Low-Severity Bugs

Minor correctness issues, edge-case failures, unhelpful error messages, and behavioral
inconsistencies. Worth fixing but not blocking.

---

## [FIXED in b921c74] ~~L-01 — `has_usable_coordinates` check is effectively always `True`~~

**File:** `pd_book_tools/geometry/bounding_box.py`, lines 124–131

`has_usable_coordinates` checks `all(c is not None ...)`. For a validly constructed
`BoundingBox`, `minX/minY/maxX/maxY` are backed by Shapely `Point` coordinates and
can never be `None`. The check also never validates for `float('nan')` or
`float('inf')`, despite the docstring claiming it checks for "finite numbers suitable
for rendering". The bare `except Exception: return False` silently suppresses any
genuine errors.

**Fix:** check `math.isfinite(c)` alongside the `is not None` check, and remove the
try/except so real errors surface.

---

## [FIXED in 36939fa] ~~L-02 — `clamp_to_image` can produce a zero-width or zero-height box without warning~~

**File:** `pd_book_tools/geometry/bounding_box.py`, lines 658–677

When a box is entirely outside the image, clamping produces a zero-area
`BoundingBox` (`left == right` or `top == bottom`). Since `from_ltrb` allows
`left == right`, this is silently returned. Callers may later get divide-by-zero or
empty crops.

**Fix:** return `None` (or raise `ValueError`) when the clamped result is zero-area,
and document the behavior.

---

## [FIXED in 72b51ce] ~~L-03 — `expand` produces a confusing error when Shapely buffer collapses to empty geometry~~

**File:** `pd_book_tools/geometry/bounding_box.py`, lines 780–793

When a shrink amount exceeds the box's half-size, `shapely.buffer()` returns empty
geometry with `bounds == (nan, nan, nan, nan)`. The subsequent
`BoundingBox.from_ltrb(nan, ...)` raises a confusing
`"Cannot mark as normalized: coordinates must lie within [0,1]"` instead of a clear
"expansion delta collapses box to zero" message.

**Fix:** check `g.is_empty` before extracting `.bounds` and raise
`ValueError("Expansion deltas collapse box to zero area")`.

---

## L-04 — `from_points` rejects zero-width/height boxes; other constructors accept them

**File:** `pd_book_tools/geometry/bounding_box.py`, lines 233–239

`from_points()` raises `ValueError` for `point1.x == point2.x` (zero-width). All
other constructors (`from_ltrb`, `from_float`, `from_ltwh`, `_build`) accept
`left == right`. The inconsistency is undocumented.

**Fix:** either all constructors reject degenerate zero-area boxes, or `from_points`
uses `>=` like the others. Pick one policy and document it.

---

## L-05 — `iou()` returns `0.0` for two identical zero-area boxes

**File:** `pd_book_tools/layout/geometry.py`, lines 14–28

Two identical degenerate (zero-size) boxes have IoU = 1.0 by convention, but the
`if inter <= 0: return 0.0` early exit returns `0.0`. Code using IoU for deduplication
would incorrectly treat two identical point-regions as non-overlapping.

**Fix:** document the 0/0 convention explicitly (degenerate boxes → IoU = 0.0) so the
behavior is intentional rather than accidental.

---

## L-06 — `caption_for_figure` searches only below a figure, never above

**File:** `pd_book_tools/layout/geometry.py`, lines 80–81

`gap = r.T - figure.B; if gap < 0: continue` rejects all regions whose top edge is
above the figure's bottom. Captions appearing above a figure (common in some Victorian
book styles) are never found.

**Fix:** add an `above=True` parameter that also searches regions directly above
(`gap = figure.T - r.B`), or at minimum document the limitation clearly.

---

## L-07 — `region_reading_order` sorts by `(T, L)` — wrong for two-column layouts

**File:** `pd_book_tools/layout/geometry.py`, lines 99–107

A right-column region with `T=190` sorts before a left-column region with `T=200`,
producing wrong reading order for two-column pages. The function docstring notes this
is "a starting point for the column-aware sort to come," but there is no corresponding
ticket or TODO, and callers using this for two-column content get silently wrong output.

**Fix:** add a column-aware sort, or at minimum add a `# TODO` with a ticket reference
and a `UserWarning` for multi-column input.

---

## L-08 — `visualize.py` — `cv2.imwrite` return value is not checked

**File:** `pd_book_tools/layout/visualize.py`, lines 84–85

`draw_layout_overlay` always returns `dest_path` even when `cv2.imwrite` returns
`False` (disk full, bad permissions, unsupported extension). Callers checking
`if draw_layout_overlay(...) is not None` believe the file was written.

**Fix:** check the return value; return `None` (or raise `OSError`) on failure.

---

## L-09 — `visualize.py` — label text can overflow the right image boundary

**File:** `pd_book_tools/layout/visualize.py`, lines 66–69

When `r.L + tw + 6 > image_width`, the label rectangle and text extend past the right
edge and become partially or fully invisible. Common for page-number and sidenote
regions near the right margin.

**Fix:** clamp the label x-start: `lx = min(r.L, overlay.shape[1] - tw - 6)`.

---

## L-10 — `visualize.py` — color comment for `"text"` is wrong

**File:** `pd_book_tools/layout/visualize.py`, line 23

```python
"text": (200, 200, 60),  # cyan-ish
```

In BGR, `(200, 200, 60)` is B=200, G=200, R=60 — a yellow-green color, not cyan.
Cyan in BGR is `(255, 255, 0)`.

**Fix:** correct the comment to `# yellow-green` (or change the color to actual cyan).

---

## L-11 — `_mappings.py` — comment "Page chrome — dropped before reorg" is false

**File:** `pd_book_tools/layout/_mappings.py`, line 27

The comment says header/footer/footnote are "dropped before reorg," but they are
mapped to `RegionType.header`, `RegionType.footer`, and `RegionType.footnote` —
they are preserved as typed regions. Whether they are dropped later depends on the
call site, not on this mapping.

**Fix:** remove or rewrite the comment to accurately describe what the mapping does.

---

## L-12 — `_mappings.py` — `"reference"` mapped to `"list"` is semantically wrong

**File:** `pd_book_tools/layout/_mappings.py`, line 34

In PP-DocLayout, `reference` is a bibliography citation item. In PGDP, `list` means
a formatted bullet/numbered list. Mapping bibliography citations to `list` causes
PGDP-aware tools to apply list formatting to bibliography entries.

**Fix:** map `"reference"` to `"text"` (or a new `RegionType.reference` if needed).

---

## L-13 — `remove_small_contours` mutates the input image in-place without documentation

**File:** `pd_book_tools/image_processing/cv2_processing/contours.py`, lines 61–69

`img[y:y+h, x:x+w] = 0` modifies the underlying NumPy array data. Callers who did
not copy their image before calling will find their original modified.

**Fix:** either operate on a copy (`result = img.copy()` at the start) to match the
cupy version's approach, or document the in-place mutation explicitly with a note in
the docstring.

---

## L-14 — `Page.is_content_normalized` checks only the first word's coordinate flag

**File:** `pd_book_tools/ocr/page.py`, lines 582–588

Returns the `is_normalized` flag of the first word that has a bounding box. A
mixed-coordinate page (possible after certain editing operations) returns the flag
of whatever word comes first, misleading callers.

**Fix:** check whether all words agree; raise `ValueError` if they disagree (mixed
coordinate state indicates a logic error upstream).

---

## L-15 — `OCRProvenance.models` is a mutable `list` inside a `frozen=True` dataclass

**File:** `pd_book_tools/ocr/provenance.py`, lines 38–39

`frozen=True` prevents attribute reassignment but not mutation of mutable field
values. `provenance.models.append(...)` succeeds silently, violating the intent of
immutability.

**Fix:** change to `tuple[OCRModelProvenance, ...]` and update `__post_init__` to
convert any incoming list to a tuple.

---

## L-16 — `OCRProvenance.coerce` performs an unnecessary dict round-trip

**File:** `pd_book_tools/ocr/provenance.py`, lines 96–105

When the input is already an `OCRProvenance`, `coerce` calls
`OCRProvenance.from_dict(value.to_dict())` — serializes and immediately deserializes,
producing an equal but wasteful copy. Since the class is frozen, returning `value`
directly is safe.

**Fix:** add `if isinstance(value, OCRProvenance): return value` before the round-trip.

---

## L-17 — `OCRProvenance` serialization asymmetry: empty string omitted on write, accepted on read

**File:** `pd_book_tools/ocr/provenance.py`, lines 41–49 vs 80–93

`to_dict` uses truthiness (`if self.engine_version`) to decide whether to include
`engine_version` and `config_fingerprint`. An empty string `""` is falsy and omitted.
`from_dict` uses `is not None`, which cannot distinguish a missing key from a key
explicitly set to `None`. An `engine_version=""` round-trips back as `None`.

**Fix:** in `to_dict`, include the field as `None` when empty rather than omitting the
key entirely.

---

## L-18 — Tesseract provenance does not record the OCR language/model name

**File:** `pd_book_tools/ocr/document.py`, lines 469–481

When building Tesseract provenance, `tesseract_metadata["models"] = []`. The Tesseract
language model (`eng`, `deu`, etc.) is not recorded. Two different Tesseract runs with
different language packs produce identical provenance records.

**Fix:** expose `lang` and `config` parameters to the provenance builder and populate
`models` accordingly.

---

## L-19 — `DocTR` word confidence defaults to `0.0` instead of `None` when absent

**File:** `pd_book_tools/ocr/document.py`, line 306

`word_data.get("confidence", 0.0)` stores `0.0` when no confidence value is present.
`0.0` means "0% confidence (near certainty of error)" while `None` means "confidence
unknown." The `Word` type explicitly allows `ocr_confidence: float | None`.

**Fix:** use `word_data.get("confidence")` (defaults to `None`) and let downstream
code handle the `None` case.

---

## L-20 — `update_line_match_difflib_lines_equal` contains dead unreachable guard code

**File:** `pd_book_tools/ocr/ground_truth_matching.py`, lines 238–241

Line 223 checks `if len(line.words) != len(ground_truth_line)` and raises before the
loop. Inside the loop, `if word_idx >= len(ground_truth_line): raise ValueError` can
never be reached — if the lengths were equal, `word_idx` never exceeds the last index.

**Fix:** remove the dead guard at lines 238–241.

---

## L-21 — `match_type.py` — `WORD_NEARLY_EQUAL_DUE_TO_PUNCTUATION` defined but never assigned

**File:** `pd_book_tools/ocr/ground_truth_matching_helpers/match_type.py`, line 8

A placeholder enum member in the public API that is never set on real data. Downstream
tools checking for this type will never find it. The `"TODO: ..."` string following it
is an orphaned expression (not a docstring), so the intent is not even captured.

**Fix:** either implement it (with corresponding logic in `ground_truth_matching.py`)
or remove it.

---

## L-22 — `LINE_REPLACE_WORD_EQUAL` defined in `match_type.py` but never assigned in matching code

**File:** `pd_book_tools/ocr/ground_truth_matching_helpers/match_type.py`, line 18 vs `ground_truth_matching.py`

Within a line-replace context, equal words are stamped `WORD_EXACTLY_EQUAL` instead
of `LINE_REPLACE_WORD_EQUAL`. The distinction — whether the word was matched during a
global equal pass or within a replace pass — is lost, which matters for training data
quality analysis.

**Fix:** in the `op.word_tag == "equal"` branch of `update_line_with_ground_truth`,
assign `MatchType.LINE_REPLACE_WORD_EQUAL` when inside a replace operation.

---

## L-23 — `Block.items` and `Page.items` re-sort on every read

**Files:**

- `pd_book_tools/ocr/block.py`, lines 309–312
- `pd_book_tools/ocr/page.py`, lines 231–235

Every access to `.items` calls `_sort_items()` — O(n log n). Internal methods that
loop over `self.items` multiple times in one operation (e.g., `merge_paragraphs`
accesses `self.items` on lines 748, 765–771, and more) re-sort repeatedly.

**Fix:** add a `_dirty` flag; only resort when items have been added, removed, or
reordered.

---

## L-24 — `copy_ocr_to_ground_truth` uses `any([list comp])` — misleadingly eager evaluation

**Files:**

- `pd_book_tools/ocr/block.py`, lines 597–607
- `pd_book_tools/ocr/page.py`, lines 553–562

`any([word.copy_ocr_to_ground_truth() for word in self.words])` uses a list
comprehension inside `any()`. This eagerly evaluates all words (the intent — every
word must be processed), but the `any()` wrapper suggests short-circuit evaluation
was intended. Code readers are misled.

**Fix:** `results = [word.copy_ocr_to_ground_truth() for word in self.words]; return any(results)`
to make the eager-evaluation intent explicit.

---

## L-25 — `image_utilities.crop_image_to_bbox` swallows all exceptions silently

**File:** `pd_book_tools/ocr/image_utilities.py`, lines 43–45

A bare `except Exception` logs at `debug` level and returns `None`. Callers cannot
distinguish "no image available" from "coordinates were malformed" or "unexpected
internal error." Genuine bugs are hidden.

**Fix:** only catch the expected exception types (e.g., `ValueError` from invalid
coordinates). Let other exceptions propagate.

---

## L-26 — `PGDPExport.from_json` crashes with `AttributeError` on empty pages dict

**File:** `pd_book_tools/pgdp/pgdp_results.py`, lines 281–289

`path_prefix` is converted from `str` to `pathlib.Path` inside the `for` loop over
`pages`. When `pages` is empty, the loop body never executes, and the subsequent
`path_prefix.stem` call at line 289 tries to call `.stem` on a raw `str`, raising
`AttributeError: 'str' object has no attribute 'stem'`.

**Fix:** move `path_prefix = Path(path_prefix)` above the `for` loop.

---

## L-27 — `contours.py` (cv2) — `remove_small_contours` has an unconditional hard cutoff absent in cupy

**File:** `pd_book_tools/image_processing/cv2_processing/contours.py`, lines 67–69

The cv2 version unconditionally removes any contour smaller than
`(small_contour_w=10, small_contour_h=10)` pixels without checking the neighborhood.
The cupy version has no such fast path — it always checks the neighborhood before
removal. For a nearly-isolated 9×9-pixel dot with ≥ `threshold_sum` neighboring pixels,
cv2 removes it but cupy keeps it. The backends are behaviorally different.

**Fix:** document the behavioral difference. Consider adding the fast path to the cupy
version with the same defaults, or removing it from cv2 for consistency.

---

## L-28 — `timing.py` — first log line uses root logger instead of the injected `logger`

**File:** `pd_book_tools/utility/timing.py`, line 14

`logging.log(logLevel, ...)` on line 14 calls the root `logging` module, while lines
19 and 23–25 use the injected `logger` parameter. The first message ("Function X
called from Y with args") always goes to the root logger, bypassing any module-level
logger configuration the caller set up.

**Fix:** change line 14 to `logger.log(logLevel, ...)`.

---

## L-29 — `timing.py` — decorator logs full raw `args` and `kwargs` on every call

**File:** `pd_book_tools/utility/timing.py`, line 16

Logging full argument values can produce megabytes of output when called with NumPy
arrays or image data, and may inadvertently log sensitive values.

**Fix:** log argument count and types, not raw values:
`f"Function {func.__name__} called with {len(args)} positional args"`.

---

## L-30 — `timing.py` — `inspect.stack()[1]` is called on every decorated function invocation

**File:** `pd_book_tools/utility/timing.py`, line 13

`inspect.stack()` walks the Python call stack — expensive at every call site. Inside
the wrapper, `stack()[1]` is the immediate caller of the wrapper, not the original
function's caller. For any framework-driven call the value is typically unhelpful.

**Fix:** remove or guard behind a debug flag: `if logLevel <= logging.DEBUG: caller = inspect.stack()[1]`.

---

## L-31 — `LayoutRegion` has no coordinate validation

**File:** `pd_book_tools/layout/types.py`, lines 41–57

`LayoutRegion` accepts `L > R` or `T > B` silently. `width` returns negative.
`contains_point` returns wrong results. `area` returns 0 (guarded), suggesting the
author anticipated bad coordinates without adding a constructor guard.

**Fix:** add `__post_init__` validation: raise `ValueError` for `L > R` or `T > B`;
clamp negative coordinates to 0.

---

## L-32 — `LayoutRegion` is unhashable (cannot be used in sets or dict keys)

**File:** `pd_book_tools/layout/types.py`, lines 41–91

`@dataclass(eq=True)` sets `__hash__ = None`. The `caption_for_figure` function
already works around this with identity checks (`r is figure`).

**Fix:** add `unsafe_hash=True` or implement `__hash__` based on `(type, L, R, T, B)`.

---

## L-33 — Layout detector registry has a TOCTOU cache race under concurrent access

**File:** `pd_book_tools/layout/registry.py`, lines 78–83

Two threads can both see a cache miss simultaneously and both call `_build()`. For
`PPDocLayoutPlusLDetector` this triggers a double model download and double VRAM
allocation, potentially causing OOM.

**Fix:** wrap the cache check-then-set with `threading.Lock`, or use
`functools.lru_cache` with a hashable key.

---

## L-34 — `ContourDetector` parameters are ignored by `get_detector`

**File:** `pd_book_tools/layout/registry.py`, lines 42–62

`ContourDetector` accepts `min_area_frac`, `max_area_frac`, `min_aspect`,
`max_aspect`, `close_kernel_px`, but `_build()` always constructs
`ContourDetector()` with defaults. `confidence` and `checkpoint_path` passed to
`get_detector('contour', ...)` are silently ignored. Different confidence values
create separate (but behaviorally identical) cache entries, wasting memory.

**Fix:** pass supported parameters through, or document that they are unused and skip
caching for `'contour'`.

---

## L-35 — `hf_download` sidecar filename construction fails for paths with dots in directory name

**File:** `pd_book_tools/hf/download.py`, line 97

`filename.rsplit(".", 1)[0] + ext` — if `filename` is `"path.to/model"` (a dot in a
directory component), `rsplit(".", 1)` splits on the directory's dot, producing
`"path"` + `.arch` = `"path.arch"` instead of `"path.to/model.arch"`.

**Fix:** use `str(Path(filename).parent / (Path(filename).stem + ext))`.

---

## L-36 — `deskew.py` — unreachable dead code after `bottom_left_column == top_left_column` check

**File:** `pd_book_tools/image_processing/cupy_processing/deskew.py`, lines 68–70

```python
if dist_b == dist_c:
    return ...
```

`dist_b == dist_c` is mathematically impossible after the guard `if bottom_left_column == top_left_column: return` on line 61 has been passed. If the columns differ, `dist_c > dist_b` is always guaranteed. The floating-point `==` comparison is also fragile.

**Fix:** remove lines 68–70 as dead code.

---

## L-37 — `bounding_box.py` — `(y - 0)` is a dead no-op expression

**File:** `pd_book_tools/geometry/bounding_box.py`, line 647

`y2 = y1 + (y - 0)` — `(y - 0)` is always `y`. An earlier version had arithmetic here
that was reduced to a no-op but never cleaned up.

**Fix:** `y2 = y1 + y`

---

## L-38 — `Word.split` passes `text_style_label_scopes` by reference (aliasing risk)

**File:** `pd_book_tools/ocr/word.py`, lines 739–764

`left_word` and `right_word` are constructed with
`text_style_label_scopes=self.text_style_label_scopes`. If `_normalize_text_style_label_scopes`
returns the passed dict directly (rather than a copy), both split words share mutable
state with the parent.

**Fix:** pass `dict(self.text_style_label_scopes)` (a shallow copy) in the `split` method.

---

## L-39 — `pyproject.toml` — `isort` listed as a runtime dependency

**File:** `pd_book_tools/pyproject.toml`, line 22

`isort` is an import-sorting dev tool with no runtime usage anywhere in `pd_book_tools/`.

**Fix:** move to `[dependency-groups].dev`.

---

## L-40 — `pyproject.toml` — `cupy-cuda12x` is a mandatory runtime dependency

**File:** `pd_book_tools/pyproject.toml`, line 18

CUDA-12-specific binary that fails to install on CPU-only machines (CI, Mac, CPU Linux).

**Fix:** move to `[project.optional-dependencies]` under a `gpu` extra and import
conditionally at call sites.
