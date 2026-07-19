---
Status: built
Owner: CT
Created: 2026-07-19
Last verified: 2026-07-19
Kind: architecture
---

# Tesseract Integration Dependency Boundary

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Read when:** changing the OpenCV Tesseract adapter, its optional dependency handling, or real-image integration tests.
- **Search terms:** tesseract, pytesseract, cv2 OCR, optional dependency, integration-test skip.

The Tesseract adapter separates runtime failure behavior from test-environment
skips. Production OCR calls fail clearly when the Python dependency is absent.
Real-image integration tests skip when either required dependency is absent.

## Runtime calls require the Python package

`tesseract_ocr_cv2_image` checks whether `pytesseract` imported successfully.
If it did not, the function raises `ImportError` with guidance to install the
`tesseract` extra. The adapter does not turn a missing runtime dependency into
a silent skip.

The `pytesseract` package invokes the separate `tesseract` executable. When the
Python package is present, executable failures remain runtime failures from
that integration rather than being converted into library-level skips.

## Real-image tests require both dependencies

`TestRealImageIntegration` runs only when `importlib.util.find_spec` locates the
`pytesseract` package and `shutil.which("tesseract")` finds the executable.
Otherwise, pytest skips the class with a reason that names both requirements.
When both checks pass, the tests exercise real grayscale and color images end
to end.

Package discovery does not guarantee that a broken installation can import
successfully. Such an installation still fails the test instead of being
skipped.

Unit tests remain runnable without the executable because they mock the
external OCR calls. A separate unit test forces the unavailable-package state
and verifies the clear `ImportError` message.

## Evidence for the dependency boundary

- Code: `pdomain_book_tools/ocr/cv2_tesseract.py`
- Tests: `tests/ocr/test_cv2_tesseract.py`
- Shipped by: merge commit `1d5859a`
- Verified: 2026-07-19 by code inspection and a focused test run; 145 selected
  tests passed and five expected layout-regression cases xfailed.

The focused command did not satisfy the repository-wide 87% coverage gate
because it ran only the selected files.
