# Test Coverage Analysis & Work Plan (Historical Snapshot)

> Note: This document is a point-in-time snapshot and may not reflect current
> coverage. To regenerate current coverage data, run `make coverage`.

**Generated:** September 13, 2025
**Initial Snapshot Coverage:** 70.7%
**First Update (April 28, 2026):** 78.9%
**Latest Update (April 29, 2026):** 89.8%

## Executive Summary

Targeted test additions across the OCR data model (Word, Block, Document,
Page), the docTR adapter, the image-processing helpers, and small utility
modules pushed overall coverage from 70.7% to 89.8% on a CPU-only test run
(GPU-only `cupy_processing/` modules are now omitted from coverage via
`pyproject.toml`, since their tests require CUDA at runtime).

## Coverage Status by Module (latest snapshot)

### 🟢 Excellent Coverage (95%+)

- `geometry/point.py`: 100.0%
- `geometry/bounding_box.py`: 93.2%
- `pgdp/pgdp_results.py`: 100.0%
- `ocr/character.py`: 100.0%
- `ocr/cv2_tesseract.py`: 92.3% (mocked)
- `ocr/doctr_support.py`: 100.0% (with PyTorch/doctr mocks)
- `ocr/document.py`: 96.1%
- `ocr/image_utilities.py`: 100.0%
- `ocr/label_normalization.py`: 96.2%
- `ocr/provenance.py`: 100.0%
- `ocr/word.py`: 94.6%
- `ocr/ground_truth_matching_helpers/*`: 100.0%
- All `image_processing/cv2_processing/*`: 96-100%
  (only `contours.py` at ~74% remains, see below)
- `image_processing/external_tools.py`: 100.0%
- `utility/timing.py`: 100.0%
- `utility/ipynb_widgets.py`: 100.0%

### 🟡 Moderate Coverage (80-95%)

- `ocr/block.py`: 91.3%
- `ocr/ground_truth_matching.py`: 84.6%
- `ocr/page.py`: 82.7%

### 🟡 Lower Coverage

- `image_processing/cv2_processing/contours.py`: 73.7% — remaining lines are
  in the medium-contour retention branches of `remove_small_contours`.

### ⚪ Excluded from coverage

- `image_processing/cupy_processing/*` — GPU-only; tests exist but skip on
  CPU-only runners. Excluded via `[tool.coverage.run].omit` in
  `pyproject.toml`.

## Work Plan Priorities

### ✅ Completed in this round

- Word.py: targeted tests for `apply_style_scope`, `apply_component`,
  `clear_all_scopes`, `remove_style_label`, `update_style_attributes`,
  `read_style_attribute`, `bbox_signature`, `refine_bbox`, `expand_bbox`,
  `expand_then_refine_bbox`, `crop_top` / `crop_bottom`,
  `refine_bounding_box`, normalization helpers,
  `split_into_characters_from_whitespace`, and
  `estimate_baseline_from_image`. (74.3% → 94.6%)
- Document.py: init validation, page sorting / setter, scale, JSON
  round-trip, `safe_float`, `_safe_package_version`,
  `_detect_tesseract_engine_version`, `_normalize_ocr_models`,
  `_build_ocr_provenance`, `from_image_ocr_via_doctr` paths (ndarray /
  grayscale / PIL / single-channel / file path / failure), tesseract
  `from_tesseract`, and from_dict default paths. (71.4% → 96.1%)
- Page.py: index/page_source aliases, `resolved_dimensions`,
  `is_content_normalized`, add/remove items, `remove_line_if_exists`,
  `remove_empty_items`, cv2 image rendering (including all match-score
  color branches), text/ground-truth properties, spatial helpers,
  `move_word_between_lines`, `validated_line_words`, `find_parent_block`,
  `remove_nested_block`, `replace_block_with_split_paragraphs`,
  `first_usable_bbox`, scale/copy/to_dict/from_dict edge cases,
  `recompute_bounding_box`, `refine_bounding_boxes`, plus paragraph/line/
  word operations: `merge_paragraphs`, `delete_paragraphs`,
  `split_paragraphs`, `split_paragraph_after_line`,
  `split_paragraph_with_selected_lines`, `merge_lines`, `delete_lines`,
  `delete_words`, `split_word`, `split_line_after_word`, `rebox_word`,
  `nudge_word_bbox`, `add_word_to_page`, `reorganize_page`,
  `compute_text_row_blocks`, `compute_text_paragraph_blocks`,
  `reorganize_lines`, `add_ground_truth`,
  `split_lines_into_selected_and_unselected_words`,
  `split_line_with_selected_words`, and
  `group_selected_words_into_new_paragraph`. (69.5% → 82.7%)
- doctr_support.py: ImportError branches plus a mocked happy path
  exercising default and fine-tuned predictor builders, custom vocab, and
  CUDA-available branch. (50% → 100%)
- provenance.py: full coverage of `to_dict`/`from_dict`/`coerce` for both
  `OCRModelProvenance` and `OCRProvenance`. (87.3% → 100%)
- contours.py: medium-contour retention and isolation branches.
  (10.5% → 73.7%)
- pyproject.toml: omit GPU-only `cupy_processing/` and
  `cv2cuda_processing/` from coverage so CPU-only runs report a
  meaningful baseline.

### 🔥 Remaining (to push to 90%+ and beyond)

- Page.py rendering / debugging helpers (lines around 2068-2415,
  2810-3234) still uncovered; these involve doctr-format export and
  detection / recognition training-set generators.
- Ground-truth matching: deeper line-pairing / character-group fallback
  branches.
- Real-image integration tests (`tests/ocr/test_cv2_tesseract.py::TestRealImageIntegration`)
  require the `tesseract` system binary and currently fail in
  CPU-only / no-tesseract environments. CI should either install
  `tesseract` or these specific tests should skip gracefully when the
  binary is absent.

## Testing Guidelines (unchanged from last update)

### For OCR Adapters

- Mock external dependencies (Tesseract, DocTR, PyTorch).
- Test data transformation accuracy.
- Test error handling for malformed inputs.
- Test coordinate system conversions.
- Use `monkeypatch.setitem(sys.modules, "<module>", None)` to exercise
  ImportError branches without uninstalling the package.

### For Image Processing

- Use small in-memory test images (avoid large fixtures on disk).
- Test with various image formats.
- Verify output image properties (shape, dtype, content).
- Test edge cases (empty images, single pixels).
- Use `pytest.importorskip("cv2")` at module top so CPU-only environments
  with no OpenCV install gracefully skip.

### For Utility Modules

- Focus on public APIs.
- Test with various input types.
- Verify performance characteristics (for `timing.py`).
- Test Jupyter widget functionality (for `ipynb_widgets.py`).

### For GPU Modules (CuPy)

- Use the shared `cupy_module` fixture so the test is automatically skipped
  when CuPy / CUDA is unavailable.
- Keep test inputs small (CUDA round-trips are expensive).
- These modules are excluded from coverage on CPU-only runs (see
  `pyproject.toml`).

## Success Metrics

- **Short term (1-2 weeks):** Achieve 80%+ overall coverage. *(Done: 89.8%)*
- **Medium term (1 month):** Achieve 90%+ coverage for core modules.
  *(Word, Document, Provenance, doctr_support, image_utilities, all utility
  modules, and most cv2_processing modules already meet this. Page.py is
  the only large module still under 90%.)*
- **Long term (2 months):** Comprehensive test suite with CI/CD integration.

## Next Actions

1. Cover the remaining `ocr/page.py` rendering / training-set generator
   helpers (largest remaining block of uncovered code).
2. Add a CI matrix entry that installs `tesseract` so the
   `tests/ocr/test_cv2_tesseract.py::TestRealImageIntegration` cases run
   end-to-end.
3. Establish CI coverage reporting thresholds (target: 88%, fail under 80%).
