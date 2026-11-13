---
Status: built
Owner: CT
Created: 2026-07-13
Last verified: 2026-11-07
Kind: architecture
---

# Geometry correction

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Last verified:** 2026-11-07
- **Read when:** changing deskew, dewarp, page-side detection, curvature
  routing, transforms, or CPU/GPU parity.
- **Search terms:** geometry correction, deskew, dewarp, textline disparity,
  UVDoc, projection, Sbrunner, regime.

## Shipped pipeline

The shipped geometry-correction pipeline separates page-side detection,
curvature measurement, deskew, and dewarp behind protocols and named
registries. `GeometryPipeline` returns a `PipelineResult`. It carries the corrected image, page-side and curvature results, optional dewarp and deskew results, and an optional regime. Individual transforms
represent identity, affine, homography, grid, or rectified output. The default pipeline
uses owned in-process backends instead of shelling out to image or PDF tools.

Projection and Sbrunner are the shipped fine-deskew backends. Coarse
orientation remains an OCR concern, not a deskew backend. The scanned pipeline
routes flat, flat-curl, and oblique pages separately. The regime picks which
dewarp backend to use, or none. Dewarp runs only when the curvature
measurement recommends it and the regime has picked a backend.

Textline-disparity is the classical scanned-page dewarper. Its NumPy baseline
and CuPy mirror preserve even/odd gutter handling, flat-scan fallback, and
output parity. CPU and GPU `_ensure_foreground` use the same gate: a binary
image whose mean is below 128 already has text at 255, and a library-polarity
image whose mean is at least 128 is inverted. UVDoc is an optional neural backend for photo-like distortion.
It requires the `dewarp-dl` extra and model weights.

## Dewarp outcomes and point mapping

`PipelineResult.dewarp_outcome` distinguishes `not_recommended`, `no_backend`, `identity_no_op`, and `applied`. A backend returning an identity transform is different from having no selected backend.

Grid transforms store backward maps for image sampling. Their `map_points` operation inverts those maps to carry source points into output coordinates. Unreachable points and non-finite input points return NaN coordinates. Rectified transforms have no point mapping and raise `NotImplementedError`.

## Boundaries and non-goals

No Leptonica or Rust binding ships. OCRmyPDF, ImageMagick, unpaper, and the
surveyed research-only neural models are not registered backends. Alternative
engines remain benchmark candidates. They are not part of the current
architecture.

The task-oriented API remains in
[`geometry-correction.md`](../usage/geometry-correction.md).

## Evidence

- **Code:** `pdomain_book_tools/geometry_correction/`,
  `pdomain_book_tools/image_processing/cv2_processing/textline_dewarp.py`,
  `pdomain_book_tools/image_processing/cupy_processing/textline_dewarp.py`
- **Tests:** `tests/geometry_correction/`,
  `tests/image_processing/cv2_processing/test_textline_dewarp.py`,
  `tests/image_processing/cupy_processing/test_textline_dewarp.py`
- **Commits:** `a094ed7` adds grid point mapping and dewarp outcomes; `39cdd9a` handles non-finite points. `tests/geometry_correction/test_transforms.py` covers mapping direction, image agreement, unreachable/non-finite points, edges, large grids, and CuPy conversion. These additions were inspected on 2026-11-13; no new GPU execution is claimed.
- **Salvaged sources:**
  `_tbd/ocr-container-docs/specs/2026-06-02-geometry-correction-design.md`,
  `_tbd/ocr-container-docs/specs/2026-06-02-textline-disparity-dewarp-design.md`,
  `_tbd/ocr-container-docs/research/2026-06-02-deskew-dewarp-backend-options.md`
- **Verified:** 2026-11-06 against `cv2_processing/textline_dewarp.py`, `cupy_processing/textline_dewarp.py`, `tests/image_processing/cv2_processing/test_textline_dewarp.py` (`test_ensure_foreground_passes_through_text255_majority_dark`, `test_ensure_foreground_reinverts_library_text0_binary`), and `tests/image_processing/cupy_processing/test_textline_dewarp.py` (`test_ensure_foreground_parity_text255_and_text0`). Earlier pipeline facts were verified 2026-07-13.
