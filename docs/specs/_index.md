---
Status: active
Owner: CT
Created: 2026-05-10
Last verified: 2026-11-12
Kind: process
---

# Specs

This index lists the architecture decisions and planning specs for
`pdomain-book-tools`. These durable, citable references explain the rationale
behind a behaviour or knob. Issues, code comments, and downstream pdomain-*
repos point to them.

New specs follow the workspace 9-section template. Existing specs were
imported from `docs/architecture/` and `docs/planning/`. The lint script
that used to live at `/workspaces/ocr-container/scripts/lint-spec.py` is not
in this repo.

The [roadmap](../plans/roadmap.md) asks where page-order, scannos, hyphen
n-grams, and the table detector should be built. Read that question before
starting those specs. Reference lines and character boxes stay in this library.

## Index

| # | Spec | Subsystem | When to read |
|---|---|---|---|
| 01 | [page serialization](../architecture/page-serialization.md) | `Page.to_dict()` / `Page.from_dict()` and the recursive OCR tree | Consuming or changing Page JSON |
| 02 | [page orientation](../architecture/ocr-page-orientation.md) | DocTR quarter-turn orientation probing | Changing rotation detection or its image frame |
| 03 | [page reorganization](../architecture/reorganize-page-pipeline.md) | `Page.reorganize_page` and reading-order assembly | Changing pipeline stages or preservation policy |
| 04 | [layout fixtures](../architecture/layout-regression-fixture-corpus.md) | Layout-regression corpus and baselines | Adding fixtures or changing baseline policy |
| 05 | [glyph annotations](../architecture/glyph-annotations.md) | Printed-form metadata beside canonical text | Changing glyph vocabulary, serialization, or validation |
| 06 | ~~word-reference-lines~~ _(superseded; split into 06a/06b/06c)_ | Per-word baseline / x-height / cap-height / ascender / descender reference geometry (planning) | Superseded 2026-05-23 by the three child specs below; Git history preserves the forwarding stub |
| 06a | [word-reference-lines-audit](06a-word-reference-lines-audit.md) | Audit of existing baseline code + gap analysis of all four reference lines | Starting point for implementing the reference-lines API; understanding what currently exists |
| 06b | [word-reference-lines-api](06b-word-reference-lines-api.md) | `WordReferenceLines` dataclass, `Word.estimate_reference_lines`, `Block.estimate_word_reference_lines`, heuristics, parameters, confidence | Implementing the new reference-lines API; understanding parameter defaults and confidence model |
| 06c | [word-reference-lines-testing](06c-word-reference-lines-testing.md) | Testing approach, bottom-crop interaction, open questions (Q-RL-1 to Q-RL-10), decisions required | Writing tests, answering open questions before implementation, bottom-crop sequencing decisions |
| 07 | ~~dev-local-upgrade-flow~~ _(implemented; retired)_ | dev-local mode detection + `make upgrade-deps` guard | Retired 2026-07-15; shipped contract promoted to [architecture/local-dev-mode.md](../architecture/local-dev-mode.md); Git history preserves the spec |
| 08 | ~~geometry-repr~~ _(shipped)_ | `BoundingBox.__repr__` / `Point.__repr__` contract | Shipped 2026-05-22; spec issue #36 closed; implementation landed in PR #50; tests preserve the contract |
| 09 | [char-bbox-extraction](09-char-bbox-extraction.md) | Per-character bounding-box extraction from word image crops | Implementing `extract_char_bboxes`; CharFixer feature in pdomain-ocr-labeler-spa; handling disconnected strokes (i/j tittles, diacritics), ligatures, and long-s |
| 10 | [table-structure](10-table-structure.md) | `BlockCategory` TABLE/CELL + grid fields; post-OCR TATR structure detection; deepdoctection-derived numpy cell-assignment geometry | Adding table row/col/cell structure to the page model; threading new `Block` grid fields through the five serialization sites; wiring the post-OCR table-structure step; understanding spanning-cell storage and the no-silent-drop invariant |
| — | [page-order-detection](2026-05-24-page-order-detection.md) | `detect_out_of_order_pages` + `SwapProposal`. No `page_order` package exists here | Reading the three-signal design. The roadmap recommends building it in pdomain-prep-for-pgdp, which already has a `page_order` stage |
| — | [scannos-module](2026-05-24-scannos-module.md) | `ScannoRule`, `ScannoCandidate`, `RuleLibrary`, `CandidateStore`, `scan_page`, `promote`. No `scannos` package exists here | Reading the SQLite rules vs JSON sidecar split. The roadmap recommends leaving this with prep-for-pgdp `wordcheck` until a second consumer exists |
| — | [hyphen-ngrams-sqlite](2026-05-24-hyphen-ngrams-sqlite.md) | `HyphenNgramsClient` Protocol, `SqliteClient`, `JsonApiClient`, corpus extraction. No `hyphen_ngrams` package exists here | Reading the download-on-first-use SQLite schema for Google Books n-gram hyphen pairs. The roadmap recommends building the client in prep-for-pgdp beside `hyphen_join` |
| — | ~~writing-docs plugin routing~~ _(implemented; retired)_ | Repository writing guidance and plugin ownership | Retired 2026-07-19; canonical routing lives in `AGENTS.md` and `CONVENTIONS.md`, and Git history preserves the process-only design |
| — | ~~PGDP-aware matcher~~ _(implemented; retired)_ | Immutable match graph, PGDP continuations, legacy projection, book manifest | Retired 2026-11-06; shipped contract is [architecture/pgdp-aware-matcher.md](../architecture/pgdp-aware-matcher.md) |

## Historical numbering

Spec numbers remain useful historical identifiers. Implemented specs move to
`docs/architecture/`, and their old paths may be deleted. New references must
use the current architecture or active-spec path from this index. They must not
rely on a `Spec: NN-name` symbolic citation.

Headings in active specs remain stable while the specs are live. After
promotion, retirement tombstones and Git history preserve older anchors.
