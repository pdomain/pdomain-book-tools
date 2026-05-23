# Specs

Architecture decisions and planning specs for `pd-book-tools`. These are
the durable, citable references that issues, code comments, and
downstream pd-* repos point at when they need the rationale behind a
behaviour or knob.

New specs follow the workspace 9-section template enforced by
`/workspaces/ocr-container/scripts/lint-spec.py`. Existing specs were
imported from `docs/architecture/` and `docs/planning/` and are
allowlisted as `legacy:` in `.specrc` until migrated (Procedure 1 in
the workspace's fixing-specs guide).

## Index

| # | Spec | Subsystem | When to read |
|---|---|---|---|
| 01 | [page-model](01-page-model.md) | `Page.to_dict()` / `Page.from_dict` and the `Block` / `Word` / `BoundingBox` JSON form | Authoring a new downstream consumer, debugging a `from_dict` round-trip, looking up the `block_role_labels` / `line_role_labels` vocabulary, disambiguating `PageLayout` from the page tree |
| 02 | [rotation](02-rotation.md) | `Document.from_image_ocr_via_doctr` auto-rotate path and `pd_book_tools/ocr/rotation.py` | Tuning the upright-confidence threshold, debugging unexpected rotation, reasoning about `Page.rotation_applied` and the rotated-frame coordinate convention |
| 03 | [reorganize-pipeline](03-reorganize-pipeline.md) | `Page.reorganize_page` and `pd_book_tools/ocr/reorganize_page_utils.py` | Adding fixtures, tuning header/footer/column/float detection, adding a new pipeline step, debugging unexpected reading-order output |
| 04 | [layout-regression-fixtures](04-layout-regression-fixtures.md) | `tests/fixtures/layout_regression/` | Adding a new fixture page, regenerating OCR / layout / reorganize artifacts, understanding what each existing fixture stresses |
| 05 | [glyph-annotations](05-glyph-annotations.md) | Glyph-level annotation data model (planning) | Designing annotation surfaces above the Word level — drop caps, small caps, italics, ligatures, accents |
| 06 | ~~word-reference-lines~~ _(archived — superseded; split into 06a/06b/06c; see `docs/archive/specs/06-word-reference-lines.md`)_ | Per-word baseline / x-height / cap-height / ascender / descender reference geometry (planning) | Archived 2026-05-23; superseded by the three child specs below |
| 06a | [word-reference-lines-audit](06a-word-reference-lines-audit.md) | Audit of existing baseline code + gap analysis of all four reference lines | Starting point for implementing the reference-lines API; understanding what currently exists |
| 06b | [word-reference-lines-api](06b-word-reference-lines-api.md) | `WordReferenceLines` dataclass, `Word.estimate_reference_lines`, `Block.estimate_word_reference_lines`, heuristics, parameters, confidence | Implementing the new reference-lines API; understanding parameter defaults and confidence model |
| 06c | [word-reference-lines-testing](06c-word-reference-lines-testing.md) | Testing approach, bottom-crop interaction, open questions (Q-RL-1 to Q-RL-10), decisions required | Writing tests, answering open questions before implementation, bottom-crop sequencing decisions |
| 07 | [dev-local-upgrade-flow](07-dev-local-upgrade-flow.md) | dev-local mode detection + `make upgrade-deps` guard | Touching the dev-local detection logic, the `[gpu]` extra reapply path, or the `.venv/.pd-dev-local` marker lifecycle |
| 08 | ~~geometry-repr~~ _(archived — shipped; see `docs/archive/specs/08-geometry-repr.md`)_ | `BoundingBox.__repr__` / `Point.__repr__` contract | Archived 2026-05-22; spec issue #36 closed; implementation landed in PR #50 |
| 09 | [char-bbox-extraction](09-char-bbox-extraction.md) | Per-character bounding-box extraction from word image crops | Implementing `extract_char_bboxes`; CharFixer feature in pd-ocr-labeler-spa; handling disconnected strokes (i/j tittles, diacritics), ligatures, and long-s |

## Anchor stability

Numbered prefixes (`01-`, `02-`, …) are stable. The numbers do not
re-flow when a spec is added in the middle — new specs take the next
unused number. Issues and code comments can reference
`Spec: 03-reorganize-pipeline` and trust the path will not move.

`## H2` headings inside each spec are also pinned (lint-spec Rule 6):
once committed, they cannot be renamed or removed without splitting
the spec via Procedure 4. Add new sections; do not rename old ones.
