# Code Review: pd-book-tools

Full library review conducted May 2026 using 7 parallel agents, one per module group.
~130 issues documented across 4 files.

## Files

| File | Contents |
|------|----------|
| [bugs-high.md](bugs-high.md) | 21 critical bugs — data corruption, definite crashes, wrong output |
| [bugs-medium.md](bugs-medium.md) | 30 medium-severity bugs — incorrect behavior on realistic inputs |
| [bugs-low.md](bugs-low.md) | 40 low-severity bugs — edge-case failures, misleading errors, minor correctness |
| [refactors.md](refactors.md) | 30 refactor opportunities — structural, design, and API improvements |

## Highest-priority fixes

Start here before anything else:

1. **H-01** `encoding.py` — PNG channel swap (all image previews have wrong colors)
2. **H-02** `pgdp_results.py` — unescaped `.` in 13 diacritic regexes (silent data corruption)
3. **H-03** `ipynb_widgets.py` — malformed HTML output (missing tags)
4. **H-04** `page.py` — `recompute_bounding_box` undefined → `AttributeError` on all editing ops
5. **H-05** `bounding_box.py` — `_vertical_crop` coordinate-system flip for pixel-space boxes
6. **H-06** `word.py` — `crop_bottom`/`crop_top` can store `None` as `bounding_box`
7. **H-07** `block.py` — `mean_ocr_confidence` crashes after any `Word.split()`
8. **H-08** `block.py` — `Block.from_dict` calls `BoundingBox.from_dict(None)`
9. **H-12** `document.py` — DocTR `original_text` indexes by character, not page
10. **H-14/15/16** `threshold.py` — Cupy Otsu off-by-one, crash on uniform images, wrong return type

## Loop progress

Durable state for the `/loop` bug-fix run, so a fresh session can resume without
remembering prior turns. Update this when an iteration completes (after the
`docs(review): mark H-XX fixed` commit).

**Fixed so far:**

- H-01 `encoding.py` BGR/RGB swap — fix `702d402`, doc mark `b4f1140`
- H-02 `pgdp_results.py` unescaped diacritic `.` regexes — fix `6b1ff5b`, doc mark `466d1df`
- H-03 `ipynb_widgets.py` malformed HTML (operator-precedence) — fix `1f26286`, doc mark `e0da955`
- H-04 `page.py` `Page.recompute_bounding_box` was reported missing but was
  actually implemented in commit `2248366` (April 2025); review was stale —
  regression-locked via test in fix `bd4ece9`, doc mark `24b97f0`
- H-05 `bounding_box.py` `_vertical_crop` discarded `original_is_normalized`
  and always normalized output — fix `2327d2f`, doc mark `<pending>`
- H-06 `word.py` `crop_bottom` / `crop_top` overwrote `self.bounding_box`
  with `None` on the blank-ROI warning path — fix `645c825`, doc mark `<pending>`
- H-07 `block.py` `Block.mean_ocr_confidence` raised `TypeError` because
  `ocr_confidence_scores()` can contain `None` after any `Word.split()` —
  fix `42da1ac`, doc mark `<pending>`
- H-08 `block.py` `Block.from_dict` called `BoundingBox.from_dict(None)`
  when deserializing a block whose `bounding_box` was serialized as JSON
  `null` — fix `3163feb`, doc mark `<pending>`. Note: `Page.from_dict`
  already had the equivalent guard, so the review's parenthetical claim
  about `Page.from_dict` was partly stale.
- H-12 `document.py` `from_doctr_result` passed `doctr_result.render()`
  (a single `str`) as `original_text`, which `from_doctr_output` then
  indexed by `page_idx` — yielding one character per page since `str` is
  a `Sequence[str]`. Existing test mocked `render.return_value` as a
  list, masking the bug. Fixed to pass
  `[page.render() for page in doctr_result.pages]`. — fix `06f22c3`,
  doc mark `<pending>`
- H-14 `image_processing/cupy_processing/threshold.py` `otsu_binary_thresh`
  defined `weight2 = weight1[-1] - weight1` (exclusive suffix sum), which
  combined with `weight2[1:]` / `mean2[1:]` in the variance expression
  excluded bin `k+1` from both classes and biased the threshold high on
  realistic bimodal images. Switched to
  `weight2 = cp.flip(cp.cumsum(cp.flip(hist)))` (inclusive suffix sum,
  matching `skimage.filters.threshold_otsu`). Verified live with cupy and
  skimage: pre-fix threshold ~0.55, fixed and skimage both ~0.42 on
  overlapping Gaussian clusters. — fix `2e1b2be`, doc mark `<pending>`
- H-15 `image_processing/cupy_processing/threshold.py` `otsu_binary_thresh`
  on uniform-valued images. The reviewed crash (`ValueError: max must be
  larger than min` from `cp.histogram(..., range=(min, max))`) no longer
  reproduces on cupy 14.x — the histogram call now silently produces a
  bogus single-bin distribution over an arbitrary [-0.5, 0.5]-style edge
  span, so `cp.argmax` of an all-zero between-class variance returns 0
  and the function emits a meaningless threshold (~`-0.498`) and an
  all-1.0 mask for an all-zero input. Added an early return when
  `min_val == max_val` that emits an all-zero binary mask, matching
  skimage/cv2 semantics (uniform image's Otsu threshold is the uniform
  value itself; strict-`>` binarization is therefore all-zero). Review
  was partly stale on the symptom but the underlying defect (no uniform
  guard) was real. — fix `92d7c32`, doc mark `<pending>`
- H-16 `image_processing/cupy_processing/threshold.py` `otsu_binary_thresh`
  returned `cp.float32` 0.0/1.0 while the cv2 backend's same-named function
  returns `uint8` 0/255. Pipeline code switching backends silently got
  incompatible dtype/range, breaking downstream `invert_image` etc. Aligned
  cupy's contract to `cp.uint8` {0, 255}; updated the H-15 uniform-image
  early-return to emit uint8 too; simplified `np_uint8_float_binary_thresh`
  wrapper since the underlying call now returns 0/255 already. — fix
  `53ed3f5`, doc mark `<pending>`
- H-09 `ocr/word.py` `Word.from_dict` used hard key access
  `dict["ocr_confidence"]`, raising `KeyError` on legacy JSON serialized
  before `ocr_confidence` was added. `Character.from_dict` already used
  `.get()`; aligned `Word.from_dict` to the same tolerant pattern so
  missing key defaults to `None`. — fix `a0170a4`, doc mark `<pending>`
- H-10 `ocr/document.py` `from_tesseract` passed Tesseract's `conf == -1`
  rejected-word sentinel through `safe_float`, which stored it as a real
  `-1.0`. The negative value then passed `rotation.py`'s
  `word.ocr_confidence is not None` guard, dragging `_mean_confidence`
  below the 0.6 rotation threshold and triggering spurious 90/180/270
  probes on clean pages; it also corrupted `Block.mean_ocr_confidence`
  and confidence-based filters. Added `Document._tesseract_confidence`
  that maps `conf <= 0` (and NaN / non-numeric / None) to `None`, leaving
  `safe_float` (used for box geometry where 0.0 is the right default)
  untouched. — fix `4c946b2`, doc mark `<pending>`
- H-11 `ocr/document.py` `from_tesseract` did `Word(text=str(word_row.text))`
  for every word row. When Tesseract emits a rejected/empty row the pandas
  `text` cell is `NaN`, and `str(float('nan'))` is the literal string
  `'nan'`, producing a ghost Word that propagated as real OCR output into
  ground-truth matching and final text. Added `Document._tesseract_text`
  mapping `NaN` / `None` to the empty string and used it at the word
  ingest site. Row geometry is preserved as an empty-text Word — we do
  not silently drop OCR rows. — fix `779bd59`, doc mark `<pending>`
- H-13 `ocr/doctr_support.py` `get_finetuned_torch_doctr_predictor` did
  `Path.exists(dectection_pt_file)` as if `Path.exists` were a classmethod.
  It worked accidentally for `Path` arguments (descriptor binding) but
  raised `AttributeError: 'str' object has no attribute 'stat'` on
  Python 3.13 when callers passed `str`, despite the function's
  `PathLike` parameter contract. Existing tests passed `tmp_path / "..."`
  so they masked the bug. Fixed to `Path(x).exists()` for both files;
  added a regression test exercising the missing-files branch with `str`
  paths. — fix `ed5937b`, doc mark `<pending>`

- H-17 `pyproject.toml` declared both `opencv-python` and
  `opencv-contrib-python`. They install to the same `cv2` namespace so
  pip resolves them independently and whichever wheel unpacks last wins,
  making runtime behavior nondeterministic (esp. contrib-only modules
  like xfeatures2d / SIFT). Audited every `cv2` import in
  `pd_book_tools/`: all use functions present in base OpenCV, so contrib
  alone covers everything. Dropped `opencv-python` and added
  `tests/test_packaging.py` with regression assertions over
  `pyproject.toml` (also guards against full+headless mixing).
  Lockfile refresh deferred to the user. — fix `364bcd2`,
  doc mark `<pending>`
- H-19 `ocr/page.py` `Page.__init__` called
  `BoundingBox.union([item.bounding_box for item in self.items])`
  without filtering items whose `bounding_box` was `None`. An empty
  child block can legitimately have `bounding_box=None`, and
  `BoundingBox.union` accesses `.is_normalized` on the first element,
  so constructing such a Page raised `AttributeError`. Mirrored
  `Page.recompute_bounding_box`: filter to truthy bboxes, set
  `self.bounding_box=None` when nothing remains. — fix `6ea4828`,
  doc mark `<pending>`
- H-18 `ocr/document.py` `Document.from_tesseract` iterated block /
  paragraph / line rows with ``enumerate`` and filtered child rows
  against ``block_idx + 1`` / ``paragraph_idx + 1`` / ``line_idx + 1``.
  Tesseract's hierarchy fields are NOT guaranteed contiguous — when
  Tesseract skips numbers (empty/dropped intermediate regions), the
  positional filter looks for parents that don't exist, so entire
  branches of the OCR hierarchy silently disappear and survivors get
  mis-grouped. Switched filters to use the actual ``block_row.block_num``
  / ``paragraph_row.par_num`` / ``line_row.line_num`` from each
  DataFrame row. Regression test with non-contiguous numbering
  (blocks 1 and 3, par 5 inside block 3, line 2 inside that paragraph)
  loses the second word pre-fix and recovers it after. — fix `b5bf0b3`,
  doc mark `<pending>`
- H-20 `hf/models.py` `resolve_layout_source` was reported to ignore
  `layout_model="none"` when a checkpoint path was also supplied — the
  review cited the checkpoint branch (lines 86–90) only. Verified stale:
  the `"none"` / `"contour"` short-circuits at lines 81–84 already run
  BEFORE the checkpoint branch, so the disable flag wins regardless of
  `layout_checkpoint`. Regression-locked the precedence with two tests
  so a future refactor can't reorder the branches. — test/lock
  `ca08728`, doc mark `<pending>`
- H-21 `ocr/ground_truth_matching.py` `include_starting_quote` /
  `include_ending_quote` in `try_matching_combined_words` gated on
  `len(ocr_combination_tuple) > 1` — the *total* number of word-pair
  combinations across the whole line, not the current span size. For
  two-word OCR lines that's always exactly 1 combination, so the gate
  never fired and quote-promotion silently dropped trailing/leading
  apostrophes from merged ground-truth words. Fixed to use
  `(combination_end - combination_start) > 1` (the in-scope locals
  unpacked from `combination_start_end`; the review's suggested
  `(ocr_word_end - ocr_word_start)` referenced list-comprehension
  locals not in scope at the use site). Regression test constructs a
  two-word span where combined fuzz ratio (57) beats both individuals
  but fails all three downstream length-band thresholds, so the flag
  is the only path through. — fix `ee3e0a0`, doc mark `<pending>`

**bugs-high.md fully cleared.** All 21 high-severity bugs have been
processed (fixes plus stale-but-regression-locked entries). The /loop
now sweeps `bugs-medium.md` top-to-bottom.

- M-01 `image_processing/cv2_processing/perspective_adjustment.py`
  `auto_deskew` top-strip column-sum band started at hardcoded
  `Y1 = 0` instead of `minY`, so stray noise pixels above the text
  block biased the detected skew angle. cupy backend already correct.
  Fixed `Y1 = minY` to mirror cupy. Regression test constructs an
  un-skewed block plus a single sub-threshold noise pixel above it;
  pre-fix the band picks up the noise and rotates ~27°, post-fix the
  band excludes it and the image is returned unchanged. — fix
  `533c23e`, doc mark `<pending>`
- M-02 `image_processing/{cv2,cupy}_processing/edge_finding.py`
  edge-detection threshold multiplier was `pixel_count_columns * 256`
  / `pixel_count_rows * 256` in both backends. A column of N
  fully-bright (uint8 255) pixels sums to `N * 255 < N * 256`, so the
  threshold required one extra pixel beyond the stated parameter; with
  `pixel_count_columns=1` (used by `auto_deskew`) it demanded 2 pixels
  and missed single-pixel content edges. Fixed both backends in one
  commit (same conceptual change). Regression tests added for both
  backends. The M-01 regression test fixture had been sized against the
  buggy `*256` threshold (255-valued noise pixel just below it); updated
  to value 254 so it remains sub-threshold under the corrected
  multiplier and continues to exercise its original code path. — fix
  `143fdf0`, doc mark `<pending>`
- M-03 `image_processing/cv2_processing/edge_finding.py` `find_edges`
  used `if fuzzy_px_w_override:` / `if fuzzy_px_h_override:` so an
  explicit `fuzzy_px_w_override=0` (the documented "no fuzzy window"
  sentinel) was silently treated as falsy and replaced with
  `int(w * fuzzy_pct)`, smearing content across a wide convolution
  kernel — opposite of caller intent. The cupy backend already used
  `is not None`. Aligned cv2 to mirror it. — fix `9a2fc8e`, doc mark
  `<pending>`
- M-04 `image_processing/cv2_processing/perspective_adjustment.py`
  `auto_deskew` early-exit path (`w_ten_percent == 0` or `h_percent == 0`)
  returned a bare `np.ndarray` while every other path — and *all* paths
  in the cupy `auto_deskew_gpu` — returned a 3-tuple
  `(image, top_slice, bottom_slice)`. Callers had to do
  `isinstance(out, tuple)` runtime dispatch to switch backends (see
  `pd-prep-for-pgdp/.../process_page.py`). Aligned the cv2 early-exit
  to return `(img, np.empty((0, 0), dtype=img.dtype), np.empty((0, 0),
  dtype=img.dtype))`, mirroring cupy's `cp.empty((0, 0),
  dtype=img_cp.dtype)` placeholders. In-tree callers were tests only;
  updated `test_zero_pct_returns_three_tuple` and simplified
  `test_straight_block_no_skew`. — fix `e74740c`, doc mark `<pending>`
- M-05 `image_processing/cv2_processing/io.py` `read_image` returned
  `cv2.imread`'s `None` sentinel silently when the file was missing,
  unsupported, corrupt, or unreadable. `create_file_thumbnail` then
  passed `None` to `rescale_image`, which crashed at `img.shape[:2]`
  with a confusing `AttributeError: 'NoneType' object has no
  attribute 'shape'` that did not name the offending path. Fixed
  `read_image` to raise `FileNotFoundError` (with the resolved path)
  when the file is absent, and `ValueError` (with the resolved path)
  when `cv2.imread` returns `None` despite the file existing
  (unsupported/corrupt/permission). Happy-path return type unchanged;
  the only in-tree caller is `create_file_thumbnail` and no external
  pd-* repos call `read_image`, so no caller updates were needed. —
  fix `f0cd07b`, doc mark `<pending>`
- M-06 `image_processing/external_tools.py` `run_gegl_c2g` appended
  `c2gOptions` as a single subprocess argv token, so any multi-flag
  string (e.g. `"--samples 4 --iterations 10"`) reached GEGL as one
  giant arg and was rejected; the default empty string also passed
  through as an empty argv entry which GEGL likewise rejects. Switched
  to `shlex.split(c2gOptions)` with a falsy guard so the empty-default
  case appends nothing (last token is `"c2g"`). Existing
  `radius=5` test still passes (single shlex token); added regression
  tests for multi-flag splitting, quoted multi-word values, and
  no-empty-string-in-argv on the default path. — fix `3824628`,
  doc mark `<pending>`
- M-07 `ocr/document.py` `Document.to_dict` did
  `str(self.source_path)`, which produces the literal string `"None"`
  when `source_path` is `None`. `Document.from_dict` then saw a truthy
  non-empty string and produced `Path("None")` (a path literally named
  `None` in the cwd), so a round-trip turned `source_path=None` into
  `Path("None")` and silently corrupted downstream path checks. Fixed
  `to_dict` to emit JSON `null` for `None`; hardened `from_dict` to
  treat the literal string `"None"` as `None` for backward compat with
  files written before this fix. — fix `b67786c`, doc mark `<pending>`
- M-08 `image_processing/cupy_processing/morph.py` `dilate` / `erode`
  padded with `mode='constant', constant_values=0`. The erosion step
  of `morph_fill` therefore zeroed foreground pixels touching the
  image border because the zero-padded min-window saw a 0. cv2's
  `morphologyEx` defaults to `BORDER_REFLECT_101`, so the two backends
  silently disagreed on book scans whose text runs into the gutter.
  Switched both helpers to `mode='reflect'` (numpy/cupy semantics
  `dcb|abcd|cba` matches `BORDER_REFLECT_101`; `'symmetric'` would be
  plain `BORDER_REFLECT` and is wrong here). Regression locked with a
  cross-backend equality test on `erode` and on `morph_fill`. — fix
  `a9741d4`, doc mark `<pending>`
- M-09 `image_processing/cupy_processing/morph.py` `dilate` / `erode`
  did `cp.max(windows * kernel, axis=(-2,-1))` /
  `cp.min(windows * kernel, axis=(-2,-1))`. The only call site
  (`morph_fill`) builds `kernel` as `cp.ones(...)`, so the multiply
  was a no-op that nonetheless materialized a full
  `(H, W, kh, kw)` intermediate before reducing — ~432 MB for a
  3000x4000 page with a 6x6 kernel, ~1.7 GB peak across the four ops
  in `morph_fill`. Path: dropped `* kernel` outright (the simple case;
  the kernel really is always all-ones at the only call site).
  Function signatures unchanged for API stability; comment in each
  function points at `cupyx.scipy.ndimage.grey_dilation` /
  `grey_erosion` for any future non-trivial structuring element.
  Locked with a cv2-parity test on a non-trivial 32x48 random pattern
  with a 5x5 all-ones kernel. — fix `423cea2`, doc mark `<pending>`
- M-10 `image_processing/cv2_processing/contours.py`
  `find_and_draw_contours` returned the 2D grayscale input when no
  contours were found and a 3-channel BGR overlay otherwise, forcing
  callers to runtime-dispatch on shape with no type annotation warning.
  The same function also used `cv2.COLOR_RGB2BGR` on a 2D single-channel
  input — OpenCV silently broadcasts to 3 channels but the conversion
  code is `COLOR_GRAY2BGR`. Fixed by always promoting via
  `cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)` before the optional
  rectangle-drawing step (which incidentally subsumes M-11). Added
  return-type annotation and docstring; updated the existing
  `test_no_contours_returns_original` (which had locked in the buggy
  2D-when-empty shape) and added a regression test asserting both
  branches return matching ndim/dtype. — fix `1012acd`, doc mark
  `<pending>`
- M-11 `image_processing/cv2_processing/contours.py` was reported to
  use `cv2.COLOR_RGB2BGR` on a 2D single-channel input where
  `COLOR_GRAY2BGR` is the semantically correct constant. Already
  incidentally fixed by the M-10 commit `1012acd` (the rewrite uses
  `cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)`); regression-locked in
  test commit `a115fbb` via a monkeypatched no-contours path that
  asserts every output pixel has B == G == R == original gray value
  (a contract only `COLOR_GRAY2BGR` can satisfy). — shared fix sha
  `1012acd`, regression test `a115fbb`, doc mark `98d29d9`
- M-13 `ocr/reorganize_page_utils.py` `reconcile_dropped_words`
  computed `post_words` with a hardcoded 3-level comprehension
  `outer.items -> paragraph.items -> line.words` plus a
  `hasattr(line, "words")` fallback. Any tree shape that wasn't
  exactly `BLOCK -> PARAGRAPH -> LINE -> WORDS` bottomed out at a
  `Word` in the place `line` was expected; `hasattr(Word, "words")`
  is False, so the comprehension yielded an empty list and every
  word was reported as dropped — false-positive in strict mode,
  noisy "recovered" block on the non-strict path. Fixed by
  iterating `final_blocks` and extending `post_words` from each
  block's recursive `Block.words` (terminates at leaf WORDS
  child_type, handles arbitrary nesting). `page.words` itself
  isn't usable here because `final_blocks` hasn't been assigned to
  `page.items` yet at the call site. Safety net preserved with a
  paired test (`test_genuine_drop_still_raises_in_strict_mode`)
  that builds the same shape but deliberately omits a word — locks
  the contract that real drops still raise. — fix `c548b2b`,
  doc mark `<pending>`
- M-12 `image_processing/cv2_processing/canvas.py`
  `map_content_onto_scaled_canvas` always allocated the canvas as
  `np.full((H, W), 255, dtype=np.uint8)` regardless of input ndim, so
  a 3-channel BGR input crashed at the placement step with
  `ValueError: could not broadcast input array from shape (H,W,3)
  into shape (H,W)`. No docstring or assertion advertised the
  grayscale-only contract. Fixed by selecting canvas shape from
  `image.ndim`: 2D input -> 2D canvas; 3D input ->
  `(H, W, channels)` canvas. The `np.full` fill value of 255
  broadcasts to all channels so the white-background contract holds.
  Cupy port `cupy_processing/canvas.py` has the same defect but is
  explicitly documented as 2D-only and is out of scope for this fix.
  — fix `37213f1`, doc mark `<pending>`

- M-14 `ocr/document.py` DocTR adapter produced
  `Page -> Block(PARAGRAPH) -> Block(LINE) -> Word` (3 levels) while
  Tesseract produced `Page -> Block(BLOCK) -> Block(PARAGRAPH) ->
  Block(LINE) -> Word` (4 levels). Consumers iterating `page.items[0]`
  expecting a `BLOCK`-category item silently broke on DocTR output.
  DocTR's underlying data model is `pages -> blocks -> lines -> words`
  (no paragraph layer) so the adapter had been labelling DocTR's
  per-block grouping as PARAGRAPH and skipping the BLOCK level. Fixed
  by wrapping each DocTR block in a synthetic outer BLOCK whose single
  child is a PARAGRAPH carrying the same bbox (one paragraph per
  block); leaf words and word-count are unchanged. Regression test
  asserts both adapters produce the same `(BLOCK, PARAGRAPH, LINE)`
  category path from `page.items[0]`. — fix `78af86d`, doc mark
  `<pending>`
- M-15 `ocr/document.py` DocTR adapter iterated only
  `block_data["lines"]` and silently discarded
  `block_data["artefacts"]` (stamps, barcodes, QR codes, figures,
  unclassified non-text regions). Violated the project invariant that
  OCR-derived content is never silently dropped. Fixed by adding
  `"artefact"` to `Block.ALLOWED_BLOCK_ROLE_LABELS` and emitting each
  artefact as a sibling top-level `Block` on the page
  (`block_category=BLOCK`, `child_type=WORDS`, `items=[]`,
  `block_role_labels=["artefact"]`). DocTR's per-artefact `type` and
  `confidence` are preserved in `additional_block_attributes` so the
  classification is not lost; `page.words` is unchanged because
  artefacts are geometry-only. Consumers filter on the role label to
  keep, render, or strip them, matching how "footnote" /
  "illustration" / "page header" already work. — fix `4819bd0`,
  doc mark `<pending>`
- M-17 `image_processing/cupy_processing/colorToGray.py`
  `np_uint8_float_colorToGray` did `img.astype(np.float32) / 255.0`
  unconditionally. The function name documents a uint8-input contract
  (the /255 normalizes uint8 [0, 255] into [0, 1] before delegating to
  the cupy backend), but float32 [0, 1] callers — a normal intermediate
  format — silently had their values collapsed to [0, 0.004], producing
  near-black grayscale output with no warning. Picked the explicit
  contract: added a dtype guard at function entry that raises
  `TypeError` naming the offending dtype and pointing the caller at
  `cupy_colorToGray` for already-float input. Sibling
  `np_uint8_float_binary_thresh` in `threshold.py` has the same
  unconditional /255 pattern; flagged for a future iteration rather
  than bundled here. — fix `27a113f`, doc mark `<pending>`
- M-16 `ocr/document.py` DocTR adapter accessed `word_data["geometry"]`
  with a hard key while block, line, and (post-M-15) artefact geometry
  already used guarded `.get("geometry")`. A DocTR word with no
  geometry key raised `KeyError` and tore down the whole page
  construction instead of letting the partial word flow through. Fixed
  to mirror the surrounding guarded pattern: emit the word with
  `bounding_box=None` when geometry is absent (project invariant: never
  silently drop OCR-derived content). One frame up, `Block.items`
  setter rejected items whose `bounding_box` was `None`, even though
  the Block itself, `Page.__init__` (post-H-19), and
  `Block.recompute_bounding_box` already treat `None` bboxes as
  legitimate; aligned the setter so partial OCR words and empty child
  blocks are admitted, otherwise the document.py fix alone would raise
  `TypeError` one frame later. — fix `f27c766`, doc mark `<pending>`
- M-18 `image_processing/cupy_processing/colorToGray.py`
  `_compute_envelopes` did `height, width, _ = img.shape` at entry, so
  a 2-D grayscale input raised `ValueError: not enough values to
  unpack` deep inside the helper instead of being rejected at the
  public `cupy_colorToGray` boundary. The function also silently
  accepted 4-channel RGBA via `img[ny, nx, :3]` (alpha dropped without
  notice). Validated input shape at the public entry: `ndim != 3` or
  `channels < 3` raises `ValueError` naming the actual issue;
  `channels == 4` is accepted and explicitly sliced to the first 3
  channels (matches `cv2.cvtColor(..., COLOR_BGRA2GRAY)` policy of
  ignoring rather than alpha-blending) with a one-time `logger.info`
  notice; `channels > 4` raises. Regression test asserts a 4-channel
  input with random alpha produces output bit-equal to running on the
  BGR-only slice — alpha is observably ignored. — fix `feb2eb8`,
  doc mark `<pending>`
- M-20 `ocr/cv2_tesseract.py` `tesseract_ocr_cv2_image` input dispatch
  only handled `ndim == 2` and `ndim == 3 and shape[2] == 3`. Any other
  shape — RGBA / 4-channel BGRA, `(H, W, 1)` single-channel-as-3D,
  accidental 4D batch — fell through with `image_grayscale = None`,
  which then got passed to pytesseract and crashed deep inside with a
  confusing error that did not name the actual problem. Added an
  explicit 4-channel branch using `cvtColor(img, COLOR_BGRA2GRAY)`
  (alpha dropped, matching cv2's documented BGRA2GRAY policy and
  mirroring the M-18 cupy fix for cross-backend parity) plus a one-time
  `logger.info` notice; any remaining unsupported shape now raises a
  clear `ValueError` naming the actual `shape=` and `ndim=`. — fix
  `bd0aef9`, doc mark `<pending>`
- M-19 `ocr/cv2_tesseract.py` `tesseract_ocr_cv2_image` hardcoded
  `--dpi 300` in the Tesseract config regardless of input image
  resolution. Tesseract uses `--dpi` to size character-classifier
  heuristics, so 150 DPI scans were over-estimated and 600 DPI scans
  under-estimated, degrading OCR in both directions. Added a
  `dpi: int = 300` parameter that flows into the config via
  `f"--dpi {int(dpi)}"`; default preserves existing behavior, callers
  with real DPI (PIL `Image.info["dpi"]`, scanner metadata,
  pd-prep-for-pgdp's resolution probe) can now pass it through. Three
  regression tests cover dpi=150, dpi=600, and the dpi=300 default
  back-compat lock. — fix `d7f341a`, doc mark `<pending>`
- M-21 `ocr/cv2_tesseract.py` `tesseract_ocr_cv2_image` hardcoded
  `-c textord_noise_debug=1` into the Tesseract config, forcing
  Tesseract to emit noise-detection debug messages to the caller's
  stderr on every OCR call. Library code must not pollute caller
  stderr by default. Removed the flag entirely (kept the companion
  `-c textord_noise_rej=1`, which is a behavioral switch, not a debug
  toggle). Updated the two pre-existing tests that had locked in the
  buggy default config string / parts list, and added
  `test_tesseract_config_no_textord_noise_debug` as the regression.
  YAGNI on an `extra_config` parameter — add when a real caller needs
  it. — fix `1c961eb`, doc mark `<pending>`

**Next pick:** M-22 — `ocr/doctr_support.py`.
`get_finetuned_torch_doctr_predictor` initializes
`full_predictor = None` and only assigns it when both checkpoint files
exist; when either file is missing, the function returns `None` with
no warning or exception, and callers crash later with a confusing
`TypeError` / `AttributeError` at first use. Fix is to raise
`FileNotFoundError` (or at minimum `logger.warning`) before returning
`None`. (Note: H-13 already touched this same function for the
`Path.exists` mis-call; check current state before writing the test.)

**Workflow per iteration** (one bug per commit, no push):

1. Verify bug still present in the production code.
2. Write a failing test that reproduces the symptom from the review doc.
3. Implement minimal fix; re-run test; run module test suite for regressions.
4. Commit `fix(<module>): <one-line>` referencing the review ID in the body.
5. Edit `docs/review/bugs-*.md`: prepend `[FIXED in <short-sha>]` and wrap the
   heading text in `~~...~~` (matching H-01..H-03 format).
6. Update **Fixed so far** and **Next pick** in this README.
7. Commit `docs(review): mark H-XX fixed`.

## Modules reviewed

- `pd_book_tools/geometry/` — bounding_box.py, point.py
- `pd_book_tools/hf/` — download.py, models.py
- `pd_book_tools/image_processing/cv2_processing/` — all 16 source files
- `pd_book_tools/image_processing/cupy_processing/` — all 15 source files
- `pd_book_tools/layout/` — types, detector, registry, geometry, mappings, visualize, adapters
- `pd_book_tools/ocr/` — all 14 source files including ground_truth_matching helpers
- `pd_book_tools/pgdp/` — pgdp_results.py
- `pd_book_tools/utility/` — ipynb_widgets.py, timing.py
- `pyproject.toml` — dependency declarations
