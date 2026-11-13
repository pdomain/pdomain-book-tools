---
Status: built
Owner: CT
Created: 2026-11-13
Last verified: 2026-11-13
Kind: architecture
---

# Image-derived word and line baselines

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Last verified:** 2026-11-13
- **Read when:** using or changing legacy image-derived baseline estimates.
- **Search terms:** baseline, horizontal, linear, pixel, WordReferenceLines.

The library estimates one horizontal baseline per Word and one linear baseline per line Block. Both methods return a dictionary or `None`, and store that result on the object's `baseline` attribute.

## Coordinate and mutation contract

`Word.estimate_baseline_from_image(image)` segments the word into character boxes using whitespace. The splitter scales normalized boxes against image dimensions and leaves pixel boxes in pixels. Character coordinates and the resulting baseline address the supplied image's pixel frame.

The word estimate averages character bottoms, with weight 0.35 for `p`, `g`, `j`, `q`, and `Q`, and 1.0 otherwise. Its dictionary contains `type: horizontal`, `y`, `confidence`, and `coordinate_space: pixel`. Confidence comes from weighted bottom spread relative to character height. Missing images, empty text, or no characters clear `baseline` and return `None`.

`Block.estimate_baseline_from_image(image)` applies only to LINE blocks with WORDS children. It fits `y = slope*x + intercept` through character centers and bottoms, with the same descender weights. Its dictionary contains `type: linear`, `slope`, `intercept`, `confidence`, and `coordinate_space: pixel`. Confidence uses residual spread relative to the vertical span. Missing images, ineligible blocks, or fewer than two character samples clear the block baseline and return `None`.

The block method also estimates each sampled word's baseline. Those word attributes can change even when the block has too few samples to fit a line.

## Scope and residual work

These are the legacy dictionary helpers. They do not implement the four reference lines, `WordReferenceLines`, or the proposed reference-line serialization and testing contract. That work remains in [the roadmap](../plans/roadmap.md) and specs [06a](../specs/06a-word-reference-lines-audit.md), [06b](../specs/06b-word-reference-lines-api.md), and [06c](../specs/06c-word-reference-lines-testing.md).

## Evidence

- **Code:** `pdomain_book_tools/ocr/word.py`, `split_into_characters_from_whitespace` and `estimate_baseline_from_image`; `pdomain_book_tools/ocr/block.py`, `estimate_baseline_from_image`.
- **Tests inspected:** `tests/ocr/test_word.py::test_word_estimate_baseline_from_image_sets_attribute`, `tests/ocr/test_block.py::test_line_block_estimate_baseline_from_image_sets_attribute`, baseline round-trip coverage in `test_block.py`, and early-return cases in `test_word_coverage.py` and `test_block_coverage2.py`.
- **History:** `e82fdcd` carries these helpers into the renamed `pdomain_book_tools` package; it is not claimed as their original implementation commit.
- **Source snapshot:** `50fcb0e`; source and tests inspected on 2026-11-13. This document records test coverage, not a new execution result.
