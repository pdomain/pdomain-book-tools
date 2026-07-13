---
Status: built
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-13
Kind: architecture
---

# Geometry correction

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Read when:** changing deskew, dewarp, page-side detection, curvature
  routing, transforms, or CPU/GPU parity.
- **Search terms:** geometry correction, deskew, dewarp, textline disparity,
  UVDoc, projection, Sbrunner, regime.

## Shipped pipeline

Geometry correction separates page-side detection, curvature measurement,
deskew, and dewarp behind protocols and named registries. `GeometryPipeline`
returns a `GeometryTransform` that represents identity, affine, grid, or
rectified output. The default pipeline uses owned in-process backends rather
than shelling out to image or PDF tools.

Projection and Sbrunner are the shipped fine-deskew backends. Coarse
orientation remains an OCR concern and is not a deskew backend. The scanned
pipeline routes flat, flat-curl, and oblique pages separately so expensive
dewarp runs only when the measured regime needs it.

Textline-disparity is the classical scanned-page dewarper. Its NumPy baseline
and CuPy mirror preserve even/odd gutter handling, flat-scan fallback, and
output parity. UVDoc is an optional neural backend for photo-like distortion;
it requires the `dewarp-dl` extra and model weights.

## Boundaries and non-goals

No Leptonica or Rust binding ships. OCRmyPDF, ImageMagick, unpaper, and the
surveyed research-only neural models are not registered backends. Alternative
engines remain benchmark candidates, not current architecture.

The task-oriented API remains in
[`geometry-correction.md`](../usage/geometry-correction.md).

## Evidence

- **Code:** `pdomain_book_tools/geometry_correction/`,
  `pdomain_book_tools/image_processing/cv2_processing/textline_dewarp.py`,
  `pdomain_book_tools/image_processing/cupy_processing/textline_dewarp.py`
- **Tests:** `tests/geometry_correction/`,
  `tests/image_processing/cv2_processing/test_textline_dewarp.py`,
  `tests/image_processing/cupy_processing/test_textline_dewarp.py`
- **Salvaged sources:**
  `_tbd/ocr-container-docs/specs/2026-06-02-geometry-correction-design.md`,
  `_tbd/ocr-container-docs/specs/2026-06-02-textline-disparity-dewarp-design.md`,
  `_tbd/ocr-container-docs/research/2026-06-02-deskew-dewarp-backend-options.md`
- **Verified:** 2026-07-13 against the current code and focused tests.
