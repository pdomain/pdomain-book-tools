---
Status: built
Owner: CT
Created: 2026-07-13
Last verified: 2026-11-12
Kind: architecture
---

# Reorganize Page Pipeline

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Last verified:** 2026-11-12
- **Read when:** changing `Page.reorganize_page`, reading order, layout-aware OCR grouping, word-preservation policy, or layout debug stages.
- **Search terms:** reorganize page, reading order, PageMetrics, row blocks, layout hints, drop caps, word preservation.

`Page.reorganize_page` converts OCR blocks, lines, and words into the ordered block tree consumed by `Page.text`. It is the pipeline's orchestration entry point.

Step logic lives in `pdomain_book_tools/ocr/reorganize_page_utils.py`. Layout-model integration lives in `pdomain_book_tools/ocr/layout_aware_reorg.py`. Drop-cap recovery lives in `pdomain_book_tools/ocr/dropcap.py`.

The pipeline accepts normalized or pixel-space OCR geometry. `compute_page_metrics` derives the coordinate domain and page-relative medians once for the geometry heuristics. Band classification uses `_coord_dims_for_block`, so the same page in unit space and in pixel space gets the same roles. `tests/ocr/test_reorganize_coord_domain.py` locks that matrix, including `test_dual_domain_matrix_identical_role_outcomes`.

Floated-caption split and tail absorption use that same coordinate width. The lines must share one `is_normalized` flag, and a mix raises. Normalized boxes compare with 1. Pixel boxes compare with the page width in pixels. When the flags are unset, the width is 1 only if the largest right edge is at or below 2, so one left-edge pixel mark stays on the pixel width. `tests/ocr/test_reorganize_branch_tables.py` locks both scales, that speck, and the mixed-flag refusal (`test_caption_prefix_splits_at_the_first_clear_gap`, `test_caption_tail_stays_in_the_flow`, `test_pixel_caption_tail_ignores_a_left_edge_speck`, `test_caption_split_rejects_mixed_coordinate_flags`).

Geometric sidenote detection measures its margin gap in the word coordinate system. `Page.is_content_normalized` supplies the domain and rejects a mix. Boxes with the flag unset use unit space when their largest right edge is at or below 2. The 1-pixel floor applies only when the boxes are pixels. A word that already has a layout tag other than `layout:text` is not given `layout:sidenote`, so a figure-only line can still be dropped and a footer line stays in its band. `tests/layout/test_layout_aware_reorg.py` covers the normalized cluster, the unflagged unit cluster, the mixed-flag refusal, and the tag exception (`test_right_margin_cluster_tagged_when_normalized`, `test_unit_boxes_without_the_flag_are_still_a_sidenote`, `test_mixed_coordinate_flags_raise`, `test_specific_layout_tag_is_not_retagged_as_sidenote`).

Drop-cap thresholds scale by `PageMetrics.coord_w` and `coord_h` before they are compared with a box. `dropcap.py` sets `is_normalized` from those metrics. A pixel page is not forced into the unit square.

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

The default `drop_layout_words=False` path preserves meaningful OCR words. After assembly, `reconcile_dropped_words` compares text-and-bbox signatures. The empty row-block path does the same after `emit_band_only_blocks`, so body words that never formed a row are not dropped in silence.

Strict mode (`PD_OCR_REORGANIZE_STRICT=1`) raises `ReorganizeDroppedWordsError`. Normal mode appends missing words in a final block tagged `recovered` and emits a warning. Empty-text or bbox-less artifacts do not participate in this comparison. `tests/ocr/test_reorganize_early_return_and_soft_recover.py` covers the early return, the soft recover path, and the empty-bbox filter.

The layout regression text harness intentionally calls `Page.reorganize_page(drop_layout_words=True)` because its committed baselines encode the legacy figure-noise-removal mode. Those baselines do not redefine the default preservation contract.

## Output contract

Top-level blocks carry `override_page_sort_order`. This setting makes `Page.items` retain the assembled reading order instead of reverting to bbox order.

Header and footer bands carry page-role labels. Special blocks carry role labels such as sidenote, poetry, blockquote, caption, illustration, or recovered.

A stitched drop cap remains a separate `Word` tagged `drop cap`. `Block.text` joins it to the following body word without a space.

Caption association claims a shared caption region at most once. `associate_captions` searches above and below the figure (`above=True`). The pipeline builds figure-to-caption-region candidates, orders them by the true gap on either side, and lets the closest figure claim each region. Later figures that select the same region receive no caption words. This rule deduplicates a shared region. It does not provide global word-identity deduplication across unrelated caption regions. `tests/layout/test_layout_aware_reorg.py` (`test_caption_above_figure_attached`) covers a caption printed above its figure.

## Evidence

- Code: `pdomain_book_tools/ocr/page.py`, `pdomain_book_tools/ocr/reorganize_page_utils.py`, `pdomain_book_tools/ocr/layout_aware_reorg.py`, `pdomain_book_tools/ocr/dropcap.py`, `pdomain_book_tools/ocr/block.py`
- Core behavior tests: `tests/ocr/test_reorganize_page_utils_grouping.py`, `tests/ocr/test_reconcile_dropped_words.py`, `tests/ocr/test_reorganize_early_return_and_soft_recover.py`, `tests/ocr/test_reorganize_coord_domain.py`, `tests/ocr/test_reorganize_diagnostic_snapshots.py`, `tests/ocr/test_dropcap.py`
- **Verified:** 2026-11-12 against `page.py` early-return reconciliation, `dropcap.py` coordinate scaling, `reorganize_page_utils.py` caption coordinate width, and `layout_aware_reorg.py` normalized sidenote gap.
- Layout integration tests: `tests/layout/test_fixture_layouts.py`, `tests/layout/test_geometry.py`, `tests/layout/test_mappings.py`, `tests/layout/test_layout_aware_reorg.py`
- Fixture artifacts: `tests/fixtures/layout_regression/inputs/`, `tests/fixtures/layout_regression/expected_text/baseline/`

## Residual intent

Five strict-xfail text baselines are reading-order failures. `plate-rio-harbour-photo` and `plate-service-on-board` want opposite results from nearly the same geometry. Blocker: conflicting baselines. The policy choice remains in `docs/context/intent-map.md`.

Planned metric additions and heuristic tuning remain demand-driven. They do not form part of this architecture contract.
