# Architecture documentation

Long-form reference material for how the pieces of `pd-book-tools` fit
together. These docs are aimed at maintainers who need to *change* a
subsystem and want to know what each knob does.

## Index

| Doc | Subsystem | When to read |
|---|---|---|
| [reorganize_pipeline.md](reorganize_pipeline.md) | `Page.reorganize_page` and `pd_book_tools/ocr/reorganize_page_utils.py` | Adding fixtures, tuning header/footer/column/float detection, adding a new pipeline step, debugging unexpected reading-order output |
| [rotation.md](rotation.md) | `Document.from_image_ocr_via_doctr` auto-rotate path and `pd_book_tools/ocr/rotation.py` | Tuning the upright-confidence threshold, debugging a page that was rotated unexpectedly (or wasn't rotated when it should have been), reasoning about `Page.rotation_applied` and the rotated-frame coordinate convention |
| [layout_regression_fixtures.md](layout_regression_fixtures.md) | `tests/fixtures/layout_regression/` | Adding a new fixture page, regenerating OCR / layout / reorganize artifacts, understanding what each existing fixture stresses |
| [page-model.md](page-model.md) | `Page.to_dict()` / `Page.from_dict` and the `Block` / `Word` / `BoundingBox` JSON form | Authoring a new downstream consumer, debugging a `from_dict` round-trip, looking up the `block_role_labels` / `line_role_labels` vocabulary, disambiguating `PageLayout` from the page tree |

Add a new file here when you add or significantly change a subsystem with
non-obvious heuristics. Update [`docs/README.md`](../README.md) and this
index when you do.
