# Architecture documentation

Long-form reference material for how the pieces of `pd-book-tools` fit
together. These docs are aimed at maintainers who need to *change* a
subsystem and want to know what each knob does.

## Index

| Doc | Subsystem | When to read |
|---|---|---|
| [reorganize_pipeline.md](reorganize_pipeline.md) | `Page.reorganize_page` and `pd_book_tools/ocr/reorganize_page_utils.py` | Adding fixtures, tuning header/footer/column/float detection, adding a new pipeline step, debugging unexpected reading-order output |

Add a new file here when you add or significantly change a subsystem with
non-obvious heuristics. Update [`docs/README.md`](../README.md) and this
index when you do.
