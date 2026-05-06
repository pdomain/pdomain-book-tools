# High-Severity Bugs

Critical bugs that cause data corruption, definite crashes in reachable code paths, or
silently produce wrong output. Fix these before any new feature work.

---

## [FIXED in 702d402] ~~H-01 — PNG images have swapped red/blue channels~~

**File:** `pd_book_tools/image_processing/cv2_processing/encoding.py`, lines 8–9
**Affects:** all `data:image/png;base64` previews in the labeler UI

`encode_bgr_image_as_png` calls `cv2.cvtColor(bgr_image, COLOR_BGR2RGB)` before
`cv2.imencode`. `imencode` already understands BGR input and writes correct RGB PNGs.
The extra channel flip sends BGR→RGB in memory; `imencode` then writes that as if it
were BGR, so every PNG has blue and red swapped.

**Fix:** delete the `cvtColor` call. `cv2.imencode('.png', bgr_image)` alone is correct.

---

## [FIXED in 6b1ff5b] ~~H-02 — All 13 PGDP diacritic regex patterns use unescaped `.` (wildcard)~~

**File:** `pd_book_tools/pgdp/pgdp_results.py`, lines 206–218
**Affects:** `fix_pgdp_diacritics` — silent data corruption on any input with
bracket-enclosed text

All dot-above patterns are written as `r"\[.A\]"` etc. In regex, `.` outside a
character class matches any character. `r"\[.A\]"` matches `['A]`, `[=A]`, `[1A]`,
`[xA]`, and so on. In text that mixes multiple diacritic types, one pattern silently
consumes bracket sequences meant for another, replacing them with the wrong character.

**Fix:** escape the dot in all 13 patterns: `r"\[\.A\]"`, `r"\[\.E\]"`, etc.

---

## ~~H-03 — `get_html_styled_span` always produces malformed HTML~~ [FIXED in 1f26286]

**File:** `pd_book_tools/utility/ipynb_widgets.py`, line 14
**Affects:** all labeled-word HTML previews in the labeler

```python
return HTML(f"<span {css_style}>" + item if item else "" + "</span>")
```

Python parses this as `(f"..." + item) if item else ("" + "</span>")`.
When `item` is non-empty: result is `"<span ...>hello"` — missing closing tag.
When `item` is empty: result is `"</span>"` — missing opening tag.
The test only checks the return type (`ipywidgets.HTML`), so this is undetected by CI.

**Fix:** `return HTML(f"<span {css_style}>{item}</span>")`

---

## [FIXED in bd4ece9] ~~H-04 — `Page.recompute_bounding_box()` is never defined → `AttributeError` on every editing operation~~

**File:** `pd_book_tools/ocr/page.py`, call sites at lines 752, 953, 967, 998, and others
**Affects:** `merge_paragraphs`, `delete_paragraphs`, `split_paragraphs`,
`_recompute_nested_bounding_boxes`, and any other method that mutates blocks

`Page` repeatedly calls `self.recompute_bounding_box()`, but the method is never
defined on `Page` (only on `Block`). Every editing operation that triggers a recompute
raises `AttributeError: 'Page' object has no attribute 'recompute_bounding_box'`.

**Fix:** define `Page.recompute_bounding_box()` to compute
`BoundingBox.union([b.bounding_box for b in self._items if b.bounding_box is not None])`.

---

## [FIXED in 2327d2f] ~~H-05 — `_vertical_crop` always normalizes output, flipping coordinate system for pixel-space boxes~~

**Files:**

- `pd_book_tools/geometry/bounding_box.py`, line 649
- `pd_book_tools/ocr/word.py`, lines 1080–1108 (`crop_bottom`, `crop_top`)

`_vertical_crop` captures `original_is_normalized` from `_extract_roi` but discards it
(assigned to `_`), then unconditionally calls `.normalize(img_w, img_h)` on the result.
For a pixel-space `BoundingBox` (`is_normalized=False`), the returned box is normalized
(`is_normalized=True`). `crop_bottom` and `crop_top` then store this corrupted box back
as `self.bounding_box`, creating a mixed coordinate state that silently breaks all
subsequent geometry operations.

**Fix:** pass `original_is_normalized` through and use `_finalize_pixel_bbox` (already
used by `refine`) instead of the unconditional `.normalize()` call.

Note: the docstring at approximately line 612 has the `keep='top'`/`keep='bottom'`
mapping backwards — fix that comment at the same time.

---

## [FIXED in 645c825] ~~H-06 — `crop_bottom` / `crop_top` can store `None` as `self.bounding_box`~~

**File:** `pd_book_tools/ocr/word.py`, lines 1080–1108
**Affects:** any word whose image region is blank

When `BoundingBox.crop_bottom()` returns `None` (blank image slice), the code logs a
warning but still executes `self.bounding_box = cropped_bbox` where `cropped_bbox` is
`None`. All subsequent operations that call `.bounding_box.width` or any attribute
crash with `AttributeError: 'NoneType' object has no attribute ...`.

**Fix:** only assign if `cropped_bbox is not None`.

---

## [FIXED in 42da1ac] ~~H-07 — `Block.mean_ocr_confidence` crashes after any `Word.split()`~~

**File:** `pd_book_tools/ocr/block.py`, lines 896–913
**Affects:** any block that has had words split

`ocr_confidence_scores()` returns `list[float | None]` because `Word.split()` sets
`ocr_confidence=None` on both split words. `mean_ocr_confidence()` then calls
`sum(scores) / len(scores)` — `sum()` on a list containing `None` raises `TypeError`.

**Fix:** filter None values: `scores = [s for s in self.ocr_confidence_scores() if s is not None]`

---

## [FIXED in 3163feb] ~~H-08 — `Block.from_dict` (and `Page.from_dict`) call `BoundingBox.from_dict(None)`~~

**File:** `pd_book_tools/ocr/block.py`, line 982
**Affects:** deserializing any JSON document where a block has a null bounding box

`to_dict` serializes `None` bounding boxes as JSON `null`. But `from_dict` uses
`BoundingBox.from_dict(data["bounding_box"])` unconditionally — raises `TypeError`
when the value is `None`.

**Fix:** `BoundingBox.from_dict(data["bounding_box"]) if data.get("bounding_box") else None`

---

## H-09 — `Word.from_dict` raises `KeyError` on JSON from older code

**File:** `pd_book_tools/ocr/word.py`, line 665
**Affects:** loading any serialized document saved before `ocr_confidence` was added

`dict["ocr_confidence"]` — hard key access. Older JSON files that omit the key raise
`KeyError` at load time. `Character.from_dict` correctly uses `.get("ocr_confidence")`.

**Fix:** `data.get("ocr_confidence")`

---

## H-10 — Tesseract `conf == -1` stored as `-1.0`, corrupting rotation detection and confidence stats

**File:** `pd_book_tools/ocr/document.py`, line 590
**Affects:** rotation detection; `Block.mean_ocr_confidence`; any downstream confidence filtering

Tesseract returns `conf = -1` for rejected/empty words. `safe_float(-1)` returns
`-1.0`, not `None`. This propagates into `rotation.py`'s mean-confidence calculation
(the `word.ocr_confidence is not None` guard passes), pulling means below the `0.6`
threshold and potentially triggering spurious rotation probes on perfectly good pages.

**Fix:** treat `conf <= 0` (specifically `conf == -1`) as "no confidence" and store `None`.

---

## H-11 — Tesseract NaN text cell produces `Word(text='nan', ...)`

**File:** `pd_book_tools/ocr/document.py`, line 588
**Affects:** any page where Tesseract returns a rejected word with no text

When the `text` column is a pandas `NaN`, `str(NaN) == 'nan'`. A ghost word with
literal text `'nan'` is created and propagates as real OCR output into all downstream
processing, including ground-truth matching and final text output.

**Fix:** check `pd.isna(word_row.text)` and skip the word (or use `""`) before converting.

---

## [FIXED in 06f22c3] ~~H-12 — DocTR `original_text` indexes the rendered string by character, not by page~~

**Files:** `pd_book_tools/ocr/document.py` line 245; `pd_book_tools/ocr/doctr_support.py`
**Affects:** `original_ocr_tool_text` on every page of every DocTR document

`from_doctr_result` passes `doctr_result.render()` — a single `str` — as
`original_text` to `from_doctr_output`. Since `str` is a `Sequence[str]` in Python,
`original_text[page_idx]` returns the **character** at that position, not the page's
text. For a document rendering `"Hello World"`, page 0 gets `original_ocr_tool_text = 'H'`.

The test in `test_document_coverage.py` mocks `render.return_value = ["rendered"]`
(a list), masking this in CI.

**Fix:** `original_text = [page.render() for page in doctr_result.pages]`

---

## H-13 — `doctr_support.py` — `Path.exists()` called as unbound class method

**File:** `pd_book_tools/ocr/doctr_support.py`, line 181
**Affects:** loading a fine-tuned DocTR predictor when the path is a `str`

`Path.exists(dectection_pt_file)` works only when the argument is already a
`pathlib.Path` instance. When the caller passes a plain `str`, Python 3.13 raises
`AttributeError: 'str' object has no attribute 'stat'` because `Path.exists` is an
instance method.

**Fix:** `Path(dectection_pt_file).exists()`

---

## [FIXED in 2e1b2be] ~~H-14 — Cupy Otsu thresholding has off-by-one in `mean2`/`weight2`~~

**File:** `pd_book_tools/image_processing/cupy_processing/threshold.py`, lines 38–43
**Affects:** all GPU-path Otsu thresholding; produces biased (too-low) thresholds

`between_class_variance` uses `weight2[1:]` and `mean2[1:]` instead of `weight2[:-1]`
and `mean2[:-1]`. The histogram bin at index `i` is included in the numerator of
`mean2[i]` but excluded from the denominator `weight2[i]`. The two off-by-ones
partially cancel but the result is a biased threshold that produces wrong binarization
for most images.

**Fix:** recompute `weight2 = cp.flip(cp.cumsum(cp.flip(hist)))` and use
`weight2[:-1]` / `mean2[:-1]` in `between_class_variance`.

---

## H-15 — Cupy Otsu crashes on uniform images

**File:** `pd_book_tools/image_processing/cupy_processing/threshold.py`, line 33
**Affects:** any blank or near-blank page processed on GPU

`cp.histogram(..., range=(min_val, max_val))` raises
`ValueError: max must be larger than min` when `min_val == max_val` (all pixels the same value).

**Fix:** guard before the histogram call:

```python
if min_val == max_val:
    return cp.zeros_like(img, dtype=cp.uint8)
```

---

## H-16 — Cupy `otsu_binary_thresh` returns `float32` 0.0/1.0; cv2 version returns `uint8` 0/255

**File:** `pd_book_tools/image_processing/cupy_processing/threshold.py`, lines 49–52
**Affects:** any pipeline code that switches between backends

The two backends have incompatible return dtypes and value ranges for the same-named
function. Code that uses either backend interchangeably gets wrong masks without error.

**Fix:** either have the cupy version return `cp.uint8` with 0/255, or explicitly rename
it to surface the float output (e.g., `otsu_binary_thresh_float_gpu`) and document the difference.

---

## H-17 — `pyproject.toml` declares both `opencv-python` and `opencv-contrib-python`

**File:** `pd_book_tools/pyproject.toml`, lines 25–27
**Affects:** package installation

`opencv-contrib-python` already contains everything in `opencv-python`. Declaring both
causes resolver conflicts or silent shadowing depending on pip/uv version.

**Fix:** remove `opencv-python`; keep only `opencv-contrib-python`.

---

## H-18 — Tesseract hierarchy uses `block_idx + 1` instead of the actual `block_num`

**File:** `pd_book_tools/ocr/document.py`, lines 526, 548, 569
**Affects:** any Tesseract result where block numbers are non-contiguous

The code assumes Tesseract's `block_num` values are contiguous starting at 1. If
Tesseract skips a number (merged regions, noise blocks), all children are silently
assigned to the wrong parent block.

**Fix:** use `block_row.block_num` (available from `itertuples`) instead of
`block_idx + 1`. Apply the same fix for `par_num` and `line_num`.

---

## H-19 — `Page.__init__` calls `BoundingBox.union` without filtering `None` bboxes

**File:** `pd_book_tools/ocr/page.py`, lines 115–117
**Affects:** constructing any `Page` that contains a block with `bounding_box=None`

`BoundingBox.union([item.bounding_box for item in self.items])` passes `None` values
into `union`, which then tries to call `.is_normalized` on `None` and raises `AttributeError`.
`Block.recompute_bounding_box` already filters out `None` bboxes; `Page.__init__` does not.

**Fix:** `BoundingBox.union([b.bounding_box for b in self._items if b.bounding_box is not None])`

---

## H-20 — `resolve_layout_source` ignores `layout_model="none"` when `layout_checkpoint` is also set

**File:** `pd_book_tools/hf/models.py`, lines 86–90
**Affects:** callers who pass both `layout_model="none"` and a checkpoint path

The checkpoint branch returns early without ever checking `layout_model`. Passing
`layout_model="none"` to disable layout is silently bypassed if a checkpoint path is
also provided.

**Fix:** evaluate the `"none"` / `"contour"` early-return checks before the checkpoint branch,
or document the precedence explicitly.

---

## H-21 — `ground_truth_matching.py` — `include_starting_quote` / `include_ending_quote` test total combination count, not current span

**File:** `pd_book_tools/ocr/ground_truth_matching.py`, lines 612, 629
**Affects:** quote handling in all combined-word ground-truth matching

At lines 612 and 629, `len(ocr_combination_tuple)` tests the **total number of
word-pair combinations** (always large), not whether the current combination spans
more than one word. Both conditions are therefore always `True` for any non-trivial
input, causing spurious quote inclusion.

**Fix:** use `(ocr_word_end - ocr_word_start) > 1` (from `combination_start_end`)
instead of `len(ocr_combination_tuple)`.
