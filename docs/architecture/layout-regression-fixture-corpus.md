---
Status: built
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-13
Kind: architecture
---

# Layout Regression Fixture Corpus

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Read when:** adding a layout fixture, regenerating cached layout data, reviewing reorganize text changes, or changing baseline policy.
- **Search terms:** layout regression, fixture corpus, PageLayout JSON, reorganize baseline, strict xfail, baseline promotion.

The layout-regression corpus stores real scanned pages and cached OCR/layout outputs under `tests/fixtures/layout_regression/`. It exercises layout detection consumers and reading-order assembly without model downloads during the normal test suite. The corpus contains 31 page images, 31 cached `PageLayout` files, and 31 reorganize text baselines.

## Artifact contract

Each case uses one slug across these committed files:

- `inputs/<case>.png`: source page image.
- `inputs/<case>.pgdp.txt`: proofread reference text; it is an aspirational recognition reference, not the reorganize baseline.
- `inputs/<case>.json`: cached OCR document/page data.
- `inputs/<case>.layout.json`: cached PP-DocLayout `PageLayout`.
- `expected_text/baseline/<case>.reorganize.txt`: committed reading-order and block-rendering expectation.

Generated inspection files live under `expected_text/current/`, `expected_text/diff/`, and `debug/`; Git ignores those directories. `tests/fixtures/layout_regression/README.md` is the per-case source and coverage manifest.

## Test contract

`tests/layout/test_fixture_layouts.py` auto-discovers every `*.layout.json`. It checks `PageLayout` round trips, positive image dimensions, the registered detector name, known region types, region bounds, representative figure-caption association, required corpus region coverage, and mapping compatibility.

`tests/ocr/test_reorganize_page_utils_grouping.py` auto-discovers every baseline that has matching PNG and OCR JSON inputs. It runs reorganize in strict preservation mode, writes current output and unified diffs, and compares rendered text byte-for-byte with the committed baseline. It enables step debug output unless `PD_OCR_TEST_NO_DEBUG` disables image generation. Per-worker output paths isolate xdist runs.

The text harness passes `drop_layout_words=True`; its baselines therefore describe the legacy figure-noise-removal mode rather than the default word-preserving `Page.reorganize_page` mode. Five cases carry strict xfails because their committed baselines describe desired figure-noise removal that current output does not satisfy.

## Baseline policy

A baseline change is an explicit semantic review, not test-output regeneration. Reviewers inspect the unified diff and relevant debug overlays, decide whether the output improves, and promote individual cases with a stated reason. Bulk replacement hides regressions and is outside the corpus policy.

Layout JSON regeneration uses `make layout-fixtures-regenerate`. OCR fixture generation and reorganize dumping use the scripts under `tests/fixtures/layout_regression/` through the repository's `uv run` environment. Model or OCR changes receive the same case-by-case baseline review because recognition drift can alter the rendered text even when reading order remains stable.

## Scope

The corpus covers body text, headers and page numbers, figures, captions, decorations, chapter openings, drop caps, lists, footnotes, sidenotes, dense catalog layouts, and rotated input. It does not contain representative tables, mathematical formulae, or cross-page foldouts. It does not measure word- or character-recognition accuracy.

## Evidence

- Corpus manifest: `tests/fixtures/layout_regression/README.md`
- Inputs and cached outputs: `tests/fixtures/layout_regression/inputs/`
- Text baselines: `tests/fixtures/layout_regression/expected_text/baseline/`
- Layout corpus tests: `tests/layout/test_fixture_layouts.py`
- Reorganize text tests: `tests/ocr/test_reorganize_page_utils_grouping.py`
- Fixture tooling: `tests/fixtures/layout_regression/ocr_fixtures.py`, `tests/fixtures/layout_regression/regenerate_layouts.py`, `tests/fixtures/layout_regression/dump_reorganize_output.py`
- Supported layout regeneration entrypoint: `Makefile` target `layout-fixtures-regenerate`

## Residual intent

The five strict xfails and the choice between current-output and desired-output canonical baselines remain in `docs/context/intent-map.md`. Corpus gaps for tables, formulae, and foldouts remain explicit scope limits rather than evidence of support. Human review remains the semantic oracle for baseline promotion.
