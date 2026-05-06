# Medium-Severity Bugs

Bugs that produce incorrect behavior in realistic inputs, cause crashes on non-trivial
edge cases, or create subtle silent failures. Should be fixed before the next release.

---

## [FIXED in 533c23e] ~~M-01 — `perspective_adjustment.py` — top-strip scan starts at row 0 instead of `minY`~~

**File:** `pd_book_tools/image_processing/cv2_processing/perspective_adjustment.py`, lines 36–42
**Affects:** deskew accuracy on pages with content above the text block

The column-sum used to detect skew starts at `Y1 = 0` (hardcoded top of image) instead
of `minY` (the detected content top edge). Stray noise pixels above the text block
corrupt the detected skew angle. The cupy counterpart correctly uses
`img_cp[minY : minY + h_percent, ...]`.

**Fix:** set `Y1 = minY` at line 36.

---

## [FIXED in 143fdf0] ~~M-02 — Edge detection threshold multiplier `* 256` should be `* 255`~~

**Files:**

- `pd_book_tools/image_processing/cv2_processing/edge_finding.py`, lines 27–28
- `pd_book_tools/image_processing/cupy_processing/edge_finding.py`, lines 27–28

A column of `N` fully-bright pixels sums to `N * 255`, which is strictly less than
`N * 256`. The effective detection threshold requires one extra pixel beyond the stated
`pixel_count_columns` parameter. With `pixel_count_columns=1` (used in auto-deskew),
the threshold requires 2 pixels, missing single-pixel content edges. Both backends
share this bug consistently.

**Fix:** change `* 256` to `* 255` in both files.

---

## [FIXED in 9a2fc8e] ~~M-03 — Edge detection fuzzy-window override of `0` is silently ignored~~

**File:** `pd_book_tools/image_processing/cv2_processing/edge_finding.py`, lines 37–38

```python
fuzzy_px_w = fuzzy_px_w_override if fuzzy_px_w_override else int(w * fuzzy_pct)
```

Passing `fuzzy_px_w_override=0` (meaning "no fuzzy window") evaluates to `False` and
the default `int(w * fuzzy_pct)` is used instead, ignoring the caller's explicit zero.
The cupy version correctly uses `if fuzzy_px_w_override is not None`.

**Fix:** change both checks to `if fuzzy_px_w_override is not None`.

---

## [FIXED in e74740c] ~~M-04 — `auto_deskew` has an inconsistent return type~~

**File:** `pd_book_tools/image_processing/cv2_processing/perspective_adjustment.py`, lines 29–32, 107–121

Early-exit path (line 31, when `h_percent == 0`) returns a plain `np.ndarray`.
All other paths return `tuple[np.ndarray, np.ndarray, np.ndarray]`.
The cupy counterpart `auto_deskew_gpu` always returns a 3-tuple.
Callers must do runtime type dispatch with `isinstance(result, tuple)`.

**Fix:** always return a 3-tuple; use `np.empty((0, 0))` placeholders for the early-exit case.

---

## [FIXED in f0cd07b] ~~M-05 — `read_image` returns `None` silently; `create_file_thumbnail` crashes on missing file~~

**Files:**

- `pd_book_tools/image_processing/cv2_processing/io.py`, lines 11–12
- `pd_book_tools/image_processing/cv2_processing/thumbnails.py`, lines 17–19

`cv2.imread` returns `None` when a file does not exist or cannot be opened. `read_image`
passes this `None` directly back to the caller. `create_file_thumbnail` then passes
`None` to `rescale_image`, which crashes at `img.shape[:2]` with
`AttributeError: 'NoneType' object has no attribute 'shape'`.

**Fix:** in `read_image`, raise `FileNotFoundError` when `cv2.imread` returns `None`.

---

## [FIXED in 3824628] ~~M-06 — `run_gegl_c2g` passes c2gOptions as a single string argument instead of splitting it~~

**File:** `pd_book_tools/image_processing/external_tools.py`, lines 29–36

```python
args=["gegl", src, "-o", tgt, "--", "c2g", c2gOptions]
```

When `c2gOptions = "--samples 4 --iterations 10"`, it is passed as one token to the
subprocess. GEGL rejects this. When `c2gOptions = ""`, an empty-string argument is
passed, which GEGL may also reject.

**Fix:** `args.extend(shlex.split(c2gOptions))` after `"c2g"`, or change the
parameter to `list[str]`.

---

## [FIXED in b67786c] ~~M-07 — `Document.source_path` serializes `None` as the string `"None"`~~

**File:** `pd_book_tools/ocr/document.py`, lines 108–110

`to_dict()` calls `str(self.source_path)` which produces `"None"` for `None`. In
`from_dict()`, `data.get("source_path")` is truthy for this non-empty string, so
`Path("None")` is returned — a valid `Path` object pointing to a file literally named
`None` in the current directory. The serialization round-trip is broken.

**Fix:** serialize `None` as JSON `null` (omit the key from the dict) rather than stringifying.

---

## [FIXED in a9741d4] ~~M-08 — Cupy `morph.py` — zero-padding on erosion silently removes edge-touching content~~

**File:** `pd_book_tools/image_processing/cupy_processing/morph.py`, lines 17–25, 31–41

Both `dilate` and `erode` pad with `constant_values=0`. During the erosion step of
`morph_fill`, foreground pixels that touch the image border are erroneously eroded to 0.
`cv2.morphologyEx` uses `BORDER_REFLECT_101` by default, preserving border content.
For book scans where text runs close to the gutter, this silently deletes valid content.

**Fix:** use `mode='reflect'` padding in both `dilate` and `erode`.

---

## [FIXED in 423cea2] ~~M-09 — Cupy `morph.py` — 432 MB+ redundant intermediate allocation per morphological op~~

**File:** `pd_book_tools/image_processing/cupy_processing/morph.py`, lines 24, 41

`cp.max(windows * kernel, axis=(-2,-1))` where `kernel = cp.ones(...)` allocates an
`(H, W, kh, kw)` intermediate array before the reduction. For a 3000×4000 page with a
6×6 kernel this is ~432 MB per operation. `morph_fill` runs four ops — ~1.7 GB peak
GPU memory for a single page. Since `kernel` is always all-ones, the multiplication is
a no-op.

**Fix:** use `cp.max(windows, axis=(-2,-1))` directly. For non-trivial kernels, use
`cupyx.scipy.ndimage.grey_dilation` / `grey_erosion`.

---

## [FIXED in 1012acd] ~~M-10 — `find_and_draw_contours` returns inconsistent array types (2D vs 3D ndarray)~~

**File:** `pd_book_tools/image_processing/cv2_processing/contours.py`, lines 14–19

No contours found: returns `(original_grayscale_img, [])` — the image is a 2D array.
Contours found: returns `(new_bgr_img_with_drawings, contours)` — the image is 3-channel.
Callers who use the returned image must handle both cases. No return type annotation or
documentation warns of this.

**Fix:** always convert to 3-channel before returning, even when no contours are found.
Add a return type annotation.

---

## [FIXED in 1012acd] ~~M-11 — `find_and_draw_contours` uses `COLOR_RGB2BGR` on a single-channel image~~

**File:** `pd_book_tools/image_processing/cv2_processing/contours.py`, line 14

The function receives a grayscale (2D) image that was passed to `cv2.findContours`.
The conversion to 3-channel uses `cv2.COLOR_RGB2BGR` instead of `cv2.COLOR_GRAY2BGR`.
While cv2 happens to accept `COLOR_RGB2BGR` on a 1-channel input, the code is
semantically wrong and misleading.

**Fix:** use `cv2.COLOR_GRAY2BGR`.

---

## [FIXED in 37213f1] ~~M-12 — `map_content_onto_scaled_canvas` always creates a grayscale (2D) canvas~~

**Files:**

- `pd_book_tools/image_processing/cv2_processing/canvas.py`, lines 55, 77
- `pd_book_tools/image_processing/cupy_processing/canvas.py` (same issue)

The canvas is always created as `np.full((new_height, new_width), 255, dtype=np.uint8)`.
Assigning a 3-channel image raises
`ValueError: could not broadcast input array from shape (H,W,3) into shape (H,W)`.
There is no validation, assertion, or documentation of the grayscale-only constraint.

**Fix:** inspect `image.ndim` and create a 3-channel canvas when `image.ndim == 3`.

---

## [FIXED in c548b2b] ~~M-13 — `reconcile_dropped_words` hardcodes a 3-level block traversal~~

**File:** `pd_book_tools/ocr/reorganize_page_utils.py`, lines 877–883

```python
for outer in final_blocks:
    for paragraph in outer.items:
        for line in paragraph.items:
            for w in (line.words if hasattr(line, "words") else []):
```

This only reaches words 3 levels deep. Multi-column or floated-flow paths can produce
deeper nesting; words nested deeper than `BLOCK→PARAGRAPH→LINE` are invisible to
`post_words` and trigger false-positive "dropped word" errors (or false errors in
strict mode).

**Fix:** use `page.words` (which does a recursive walk) instead of the hardcoded comprehension.

---

## [FIXED in 78af86d] ~~M-14 — DocTR and Tesseract adapters produce different nesting depths~~

**File:** `pd_book_tools/ocr/document.py`, lines 310–325 vs 594–616

DocTR: `Page → Block(PARAGRAPH) → Block(LINE) → Word` (2 levels).
Tesseract: `Page → Block(BLOCK) → Block(PARAGRAPH) → Block(LINE) → Word` (3 levels).
Code that iterates `page.items[0]` assuming a `BLOCK`-category item fails with DocTR
output. No documented contract exists for which depth is canonical.

**Fix:** either document the difference with consumer-side guards, or have the DocTR
adapter wrap `PARAGRAPH` blocks in an outer `BLOCK` to match Tesseract depth.

---

## [FIXED in 4819bd0] ~~M-15 — DocTR adapter silently drops all artefacts~~

**File:** `pd_book_tools/ocr/document.py`, line 291

DocTR's block export contains both `"lines"` and `"artefacts"` keys. The adapter
iterates only `block_data.get("lines", [])` — artefacts (stamps, figures, non-text
elements detected by DocTR) are silently discarded with no logging.

**Fix:** iterate `block_data.get("artefacts", [])` and either skip them with a
`logger.debug` or convert them to `RegionType`-tagged placeholder blocks.

---

## [FIXED in f27c766] ~~M-16 — DocTR word geometry is accessed by hard key, raising `KeyError` on partial data~~

**File:** `pd_book_tools/ocr/document.py`, line 304

Block and line geometry use `.get("geometry")` with guards. Word geometry uses
`word_data["geometry"]` — a `KeyError` if the key is absent. Inconsistent with the
guarded pattern used at every other level.

**Fix:** `word_data.get("geometry")` with a guard, consistent with block/line handling.

---

## [FIXED in 27a113f] ~~M-17 — `colorToGray.py` — `np_uint8_float_colorToGray` silently corrupts float input~~

**File:** `pd_book_tools/image_processing/cupy_processing/colorToGray.py`, line 87

```python
img_float = img.astype(np.float32) / 255.0
```

If `img` is already `float32` in `[0, 1]`, the `/ 255.0` step collapses values to
`[0, 0.004]`, producing a near-black output with no warning or error.

**Fix:** check `img.dtype`: if already float, skip the division. Add a docstring
stating the input must be `np.uint8`.

---

## [FIXED in feb2eb8] ~~M-18 — `colorToGray.py` — `_compute_envelopes` crashes on 2D (grayscale) input~~

**File:** `pd_book_tools/image_processing/cupy_processing/colorToGray.py`, line 17

```python
height, width, _ = img.shape
```

Raises `ValueError` if `img.ndim == 2`. No input validation is present. Also silently
accepts 4-channel RGBA images (drops alpha via `img[ny, nx, :3]`).

**Fix:** add `assert img.ndim == 3 and img.shape[2] >= 3` at the entry of `cupy_colorToGray`.

---

## [FIXED in d7f341a] ~~M-19 — `cv2_tesseract.py` — hardcoded `--dpi 300` ignores actual scan resolution~~

**File:** `pd_book_tools/ocr/cv2_tesseract.py`, line 33

All images are processed with `--dpi 300` regardless of their actual resolution. For
150 or 600 DPI scans, Tesseract mis-estimates character sizes, degrading OCR accuracy.

**Fix:** make DPI a parameter with a default of `300`. Consider deriving from image
metadata when available.

---

## M-20 — `cv2_tesseract.py` — `image_grayscale` stays `None` for RGBA / 4-channel images

**File:** `pd_book_tools/ocr/cv2_tesseract.py`, lines 20–27

The guard handles only `ndim == 2` and `ndim == 3 and shape[2] == 3`. For a 4-channel
BGRA image, a `(H, W, 1)` array, or any other shape, `image_grayscale` remains `None`.
Passing `None` to `pytesseract.image_to_data` raises a confusing `TypeError` at the
Tesseract call site.

**Fix:** add explicit handling for 4-channel images (strip alpha with
`cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)`), and raise a clear `ValueError` for other
unsupported shapes.

---

## M-21 — `cv2_tesseract.py` — `textord_noise_debug=1` pollutes caller's stderr

**File:** `pd_book_tools/ocr/cv2_tesseract.py`, line 32

Library code should never write debug output to the caller's stderr. This config
option forces Tesseract to emit noise-detection debug messages to stderr on every call.

**Fix:** remove `-c textord_noise_debug=1` from the Tesseract config string.

---

## M-22 — `doctr_support.py` — silent `None` return when model checkpoint files are absent

**File:** `pd_book_tools/ocr/doctr_support.py`, lines 138, 256

`get_finetuned_torch_doctr_predictor` initializes `full_predictor = None` and only
assigns it when both checkpoint files exist. When either file is missing, the function
returns `None` with no warning or exception. Callers receive `None` and then crash with
a confusing `TypeError` or `AttributeError` at the first use.

**Fix:** raise `FileNotFoundError` (or at minimum `logger.warning`) before returning `None`.

---

## M-23 — `doctr_support.py` — `load_state_dict` calls are unguarded

**File:** `pd_book_tools/ocr/doctr_support.py`, lines 200, 232

`det_model.load_state_dict(det_params)` and `reco_model.load_state_dict(reco_params)`
raise `RuntimeError` (shape mismatch) or `KeyError` (missing key) if the checkpoint
and architecture don't match. The architecture detection is heuristic, making this a
realistic failure mode that surfaces as an unhelpful stack trace.

**Fix:** wrap both with `try/except RuntimeError as e: raise RuntimeError(f"Checkpoint {path} does not match arch {arch}: {e}") from e`.

---

## M-24 — `doctr_support.py` — pretrained weights are downloaded and then immediately overwritten

**File:** `pd_book_tools/ocr/doctr_support.py`, line 199

`_build_arch(det_arch_name, pretrained=True)` downloads pretrained weights from the
internet. The very next line, `det_model.load_state_dict(det_params)`, overwrites all
of them. The download is pure waste.

**Fix:** `pretrained=False`.

---

## M-25 — `ground_truth_matching.py` — `_build_current_work_gt_line_from_prev` returns `""` on space boundary

**File:** `pd_book_tools/ocr/ground_truth_matching.py`, lines 1026–1036

When the boundary character at `previous_ground_truth_text[-prev_char_count]` is a
space, the function returns `""` instead of the unmodified `ground_truth_text`. This
inserts a zero-score empty variant into the candidates list rather than skipping the
variant. The scoring filters it out (fuzz ratio 0), so no wrong result is produced, but
the intent was to skip — not to insert a dead variant.

**Fix:** return `ground_truth_text` (no prepend from previous line) instead of `""`.

---

## M-26 — `character_groups.py` — `DASHES`, `QUOTES`, `PRIMES` ordering is non-deterministic

**File:** `pd_book_tools/ocr/ground_truth_matching_helpers/character_groups.py`, lines 14–26

All four character groups are constructed with `list(set(...))`. Python `set` has
non-deterministic iteration order. When multiple dash/quote variants tie in score
during `_generate_work_variants`, the first tied variant wins — producing different
results across runs.

**Fix:** `list(dict.fromkeys(...))` preserves insertion order deterministically without
changing the set of characters.

---

## M-27 — `canvas.py` (cupy) has a hard dependency on `cv2_processing.canvas` for the `Alignment` enum

**File:** `pd_book_tools/image_processing/cupy_processing/canvas.py`, line 7

```python
from pd_book_tools.image_processing.cv2_processing.canvas import Alignment
```

Any import of a cupy backend module that uses `canvas` also requires cv2 to be
importable, breaking GPU-only deployments where cv2 is not installed.

**Fix:** move `Alignment` to `pd_book_tools/image_processing/common.py` and have both
backends import from there.

---

## M-28 — `Block.merge` silently drops unmatched ground-truth words from one side

**File:** `pd_book_tools/ocr/block.py`, lines 865–867

```python
if self.unmatched_ground_truth_words and block_to_merge.unmatched_ground_truth_words:
    self.unmatched_ground_truth_words.extend(...)
```

When `self` has no unmatched words but `block_to_merge` does, the condition is `False`
and the incoming unmatched words are silently dropped.

**Fix:** `if block_to_merge.unmatched_ground_truth_words: self.unmatched_ground_truth_words.extend(...)`

---

## M-29 — `normalize_text_style_labels` doesn't strip `'regular'` when other labels are present

**File:** `pd_book_tools/ocr/label_normalization.py`, lines 53–57

`normalize_text_style_labels(['regular', 'italics'])` returns `['regular', 'italics']`.
`Word.update_style_attributes` strips `'regular'` from mixed lists (lines 252–257 in
`word.py`), but that logic is not in the normalization layer. A `Word` constructed
directly with `text_style_labels=['regular', 'italics']` stores the redundant label
silently, and the state survives `to_dict`/`from_dict` round-trips.

**Fix:** add the same stripping logic to `normalize_text_style_labels`: if the
normalized list contains any non-`regular` style, remove `'regular'`.

---

## M-30 — `rescale_image_gpu` uses bilinear interpolation for downscaling; cv2 uses `INTER_AREA`

**File:** `pd_book_tools/image_processing/cupy_processing/rescale.py`, line 41

`cupyx.scipy.ndimage.zoom` with `order=1` is bilinear, which aliases badly when
downscaling. `cv2.resize` uses `INTER_AREA` for downscaling (block-average / pixel-area
resampling). For 4× reduction (600 → 150 DPI), aliasing from bilinear is visible and
can degrade OCR accuracy.

**Fix:** for `scale < 1.0`, consider using `order=0` (nearest) followed by averaging,
or at minimum document the quality difference.
