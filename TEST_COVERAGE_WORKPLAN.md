# Test Coverage Analysis & Work Plan (Historical Snapshot)

> Note: This document is a point-in-time snapshot and may not reflect current
> coverage. To regenerate current coverage data, run `make coverage`.

**Generated:** September 13, 2025
**Initial Snapshot Coverage:** 70.7%
**Updated:** April 28, 2026
**Updated Snapshot Coverage:** 78.9% (system-tool-dependent tests excluded:
~78.5%)

## Executive Summary

The pd-book-tools project has excellent coverage for core data models and now
has solid baseline coverage for most image-processing and adapter modules.
Remaining gaps are concentrated in the largest OCR modules (`page.py`,
`word.py`, `document.py`) and in functionality that requires external tools at
import or runtime (Tesseract, doctr / PyTorch, CUDA / CuPy).

## Coverage Status by Module

### 🟢 Excellent Coverage (95%+)

- **`geometry/point.py`**: 100.0% ✅
- **`ocr/word.py`** *(per-class)*: high coverage on core ✅
- **`ocr/block.py`**: 91.1% ✅
- **`pgdp/pgdp_results.py`**: 100.0% ✅
- **`geometry/bounding_box.py`**: 93.2% ✅
- **`image_processing/cv2_processing/canvas.py`**: 100% ✅
- **`image_processing/cv2_processing/colors.py`**: 100% ✅
- **`image_processing/cv2_processing/crop.py`**: 100% ✅
- **`image_processing/cv2_processing/edge_finding.py`**: 100% ✅
- **`image_processing/cv2_processing/encoding.py`**: 100% ✅
- **`image_processing/cv2_processing/invert.py`**: 100% ✅
- **`image_processing/cv2_processing/io.py`**: 100% ✅
- **`image_processing/cv2_processing/morph.py`**: 100% ✅
- **`image_processing/cv2_processing/perspective_adjustment.py`**: 96.6% ✅
- **`image_processing/cv2_processing/rescale.py`**: 100% ✅
- **`image_processing/cv2_processing/rotate.py`**: 100% ✅
- **`image_processing/cv2_processing/split.py`**: 100% ✅
- **`image_processing/cv2_processing/threshold.py`**: 100% ✅
- **`image_processing/cv2_processing/thumbnails.py`**: 100% ✅
- **`image_processing/cv2_processing/whitespace.py`**: 100% ✅
- **`image_processing/external_tools.py`**: 100% ✅
- **`ocr/cv2_tesseract.py`**: 92.3% (when tesseract is mocked) ✅
- **`ocr/image_utilities.py`**: 100% ✅
- **`ocr/label_normalization.py`**: 91.5% ✅
- **`utility/timing.py`**: 100% ✅
- **`utility/ipynb_widgets.py`**: 100% ✅
- **`ocr/provenance.py`**: 87.3%
- **`ocr/ground_truth_matching.py`**: 84.6%

### 🟡 Moderate Coverage (50-90%)

- **`ocr/page.py`**: 69.5% - Largest module; remaining gaps are in advanced
  rendering / debugging helpers.
- **`ocr/word.py`**: 74.3% - Moderate coverage; remaining gaps include
  serialization edge cases and ipynb-widget rendering.
- **`ocr/document.py`**: 71.4% - Document construction paths still need more
  edge-case tests.
- **`image_processing/cv2_processing/contours.py`**: 73.7% - Most paths
  covered; remaining branches handle edge cases in `remove_small_contours`.
- **`ocr/doctr_support.py`**: 50.0% - Import-error and default-predictor paths
  covered with mocks; the fine-tuning helper needs PyTorch in the environment
  to fully exercise its happy path.

### 🔴 Poor/No Coverage (0-50%)

- **All `cupy_processing/` modules**: 0% (require CUDA + CuPy at runtime).
  Comprehensive test suites have been added under
  `tests/image_processing/cupy_processing/` that automatically skip when
  CuPy / CUDA are unavailable.

### ⚪ Test Infrastructure

- **`tests/utility/`**: present; covers `timing.py` and `ipynb_widgets.py`.
- **`tests/image_processing/`**: present; covers `external_tools.py` and the
  full `cv2_processing/` package, plus skip-if-no-cupy tests for the
  `cupy_processing/` package.

## Work Plan Priorities

### ✅ Completed (since last snapshot)

#### 1. OCR Adapter Tests

- [x] `cv2_tesseract.py`: 0% → 92.3% (existing comprehensive tests, plus a
  real-image suite that requires the `tesseract` binary to run end-to-end)
- [x] `doctr_support.py`: 10.5% → 50%
- [x] `image_utilities.py`: 0% → 100%

#### 2. Utility Module Infrastructure

- [x] Created `tests/utility/`
- [x] Added tests for `timing.py` (100%)
- [x] Added tests for `ipynb_widgets.py` (100%)

#### 3. Image Processing (CPU)

- [x] `cv2_processing/crop.py`
- [x] `cv2_processing/threshold.py`
- [x] `cv2_processing/rescale.py`
- [x] `cv2_processing/perspective_adjustment.py`
- [x] `cv2_processing/canvas.py`
- [x] `cv2_processing/colors.py`
- [x] `cv2_processing/contours.py`
- [x] `cv2_processing/edge_finding.py`
- [x] `cv2_processing/encoding.py`
- [x] `cv2_processing/invert.py`
- [x] `cv2_processing/io.py`
- [x] `cv2_processing/morph.py`
- [x] `cv2_processing/rotate.py`
- [x] `cv2_processing/split.py`
- [x] `cv2_processing/thumbnails.py`
- [x] `cv2_processing/whitespace.py`
- [x] `external_tools.py` (subprocess mocked)

#### 4. GPU Processing Modules

- [x] Conditional tests scoped via the `cupy_module` fixture (skip when CuPy
  or CUDA is unavailable). Coverage will register as 0% in CPU-only
  environments.

### 🔥 Remaining High Priority

#### Ground Truth Matching Enhancement

**Target:** `ground_truth_matching.py` (84.6% → 95%+)

- Add coverage for less-common merge / split paths.
- Exercise edge cases (empty inputs, mismatched coordinate systems).

#### Document Processing Enhancement

**Target:** `document.py` (71.4% → 90%+)

- Test multi-page document handling.
- Test serialization edge cases.

#### Page / Word Enhancement

**Target:** `page.py` (69.5% → 85%+), `word.py` (74.3% → 85%+)

- Cover additional rendering / mutation helpers.
- Exercise from-dict / to-dict round-trips for edge cases.

### 🔄 Low Priority

#### GPU Processing Modules — runtime coverage

- The CuPy / CUDA-dependent code paths can only register as covered in an
  environment with a working CUDA toolchain. Coverage will remain 0% in
  CPU-only CI; the test suites do exercise the modules locally on GPU
  machines.

## Detailed Coverage Gaps

### `ocr/page.py` (69.5% - Missing many lines)

Largest module; remaining gaps are concentrated in advanced rendering and
debugging helpers.

### `ocr/word.py` (74.3%)

Missing lines cluster around to-dict / from-dict serialization edge cases and
ipynb widget rendering.

### `image_processing/cv2_processing/contours.py` (73.7% - Missing 11 lines)

Remaining lines are in `remove_small_contours` for the "below threshold but
above min" branch with non-trivial nearby-pixel sums.

## Testing Guidelines

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

## Success Metrics

- **Short term (1-2 weeks):** Achieve 80%+ overall coverage. *(78.9% as of
  this update; the gap is largely in `ocr/page.py`.)*
- **Medium term (1 month):** Achieve 90%+ coverage for core modules.
- **Long term (2 months):** Comprehensive test suite with CI/CD integration.

## Next Actions

1. Continue chipping away at `ocr/page.py` rendering helpers and `ocr/word.py`
   serialization round-trips.
2. Add a CI matrix entry that installs `tesseract` so the
   `tests/ocr/test_cv2_tesseract.py::TestRealImageIntegration` cases run
   end-to-end (currently they require the system binary and fail when it is
   missing).
3. Establish CI coverage reporting thresholds (target: 80%, fail under 75%).
