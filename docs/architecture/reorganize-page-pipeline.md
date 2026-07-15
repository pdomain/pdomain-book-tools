---
Status: built
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-13
Kind: architecture
---

# Reorganize Page Pipeline

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Read when:** changing `Page.reorganize_page`, reading order, layout-aware OCR grouping, word-preservation policy, or layout debug stages.
- **Search terms:** reorganize page, reading order, PageMetrics, row blocks, layout hints, drop caps, word preservation.

`Page.reorganize_page` converts OCR blocks, lines, and words into the ordered block tree consumed by `Page.text`. It is the pipeline's orchestration entry point.

Step logic lives in `pdomain_book_tools/ocr/reorganize_page_utils.py`. Layout-model integration lives in `pdomain_book_tools/ocr/layout_aware_reorg.py`. Drop-cap recovery lives in `pdomain_book_tools/ocr/dropcap.py`.

The pipeline accepts normalized or pixel-space OCR geometry. `compute_page_metrics` derives the coordinate domain and page-relative medians once for the geometry heuristics.

Layout regions act as hints while geometric grouping still runs. They tag words and influence roles, sidenote routing, and illustration/caption placeholders.

## Pipeline order

The current order is:

1. Capture the optional pure-OCR diagnostic snapshot.
2. Apply layout word tags and geometric sidenote tags when a `PageLayout` is present.
3. Apply figure-internal deletion only when `drop_layout_words=True`; heuristic figure-noise deletion also requires `drop_figure_internal_text=True`.
4. Refine bounding boxes when the page image is loaded.
5. Reorganize fragmented lines.
6. Split mixed-content lines and extract header/footer bands.
7. Build row blocks, choose the lower-cost geometric or word-seeded grouping, and reorganize lines inside the selected rows.
8. Expand floated, mixed-column, and multi-column row blocks into reading order.
9. Classify special-role blocks and split ordinary body rows into paragraphs.
10. Detect and stitch recognised or decorative drop caps.
11. Assemble header, body, and footer blocks and reconcile dropped words.
12. Stamp layout-derived block roles, route sidenotes, and associate captions and optional illustration placeholders when layout data is present.

When `PD_OCR_LAYOUT_DEBUG` is enabled, debug emitters expose the mixed-line, header/footer, row-block, expansion, paragraph, classification, drop-cap, and layout-region stages. Diagnostic page snapshots and dropped-noise counters remain runtime-only state. They do not enter serialized page data.

## Word-preservation contract

The default `drop_layout_words=False` path preserves meaningful OCR words. After assembly, `reconcile_dropped_words` compares text-and-bbox signatures.

Strict mode (`PD_OCR_REORGANIZE_STRICT=1`) raises `ReorganizeDroppedWordsError`. Normal mode appends missing words in a final block tagged `recovered` and emits a warning. Empty-text or bbox-less artifacts do not participate in this comparison.

The layout regression text harness intentionally calls `Page.reorganize_page(drop_layout_words=True)` because its committed baselines encode the legacy figure-noise-removal mode. Those baselines do not redefine the default preservation contract.

## Output contract

Top-level blocks carry `override_page_sort_order`. This setting makes `Page.items` retain the assembled reading order instead of reverting to bbox order.

Header and footer bands carry page-role labels. Special blocks carry role labels such as sidenote, poetry, blockquote, caption, illustration, or recovered.

A stitched drop cap remains a separate `Word` tagged `drop cap`. `Block.text` joins it to the following body word without a space.

## Evidence

- Code: `pdomain_book_tools/ocr/page.py`, `pdomain_book_tools/ocr/reorganize_page_utils.py`, `pdomain_book_tools/ocr/layout_aware_reorg.py`, `pdomain_book_tools/ocr/dropcap.py`, `pdomain_book_tools/ocr/block.py`
- Core behavior tests: `tests/ocr/test_reorganize_page_utils_grouping.py`, `tests/ocr/test_reconcile_dropped_words.py`, `tests/ocr/test_reorganize_diagnostic_snapshots.py`, `tests/ocr/test_dropcap.py`
- Layout integration tests: `tests/layout/test_fixture_layouts.py`, `tests/layout/test_geometry.py`, `tests/layout/test_mappings.py`
- Fixture artifacts: `tests/fixtures/layout_regression/inputs/`, `tests/fixtures/layout_regression/expected_text/baseline/`

## Residual intent

Five strict-xfail text baselines encode desired output that the current figure-noise behavior does not satisfy. The policy choice between current-output and desired-output baselines remains in `docs/context/intent-map.md`. That context entry also owns closure or explicit acceptance of the five xfails.

Planned metric additions and heuristic tuning remain demand-driven. They do not form part of this architecture contract.
