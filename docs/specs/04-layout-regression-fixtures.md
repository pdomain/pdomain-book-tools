# Layout-Regression Fixture Corpus

> **Status**: Active
> **Last updated**: 2026-05-10
> **Spec-Issue**: pdomain/pdomain-book-tools#28

How the fixture corpus under
[`tests/fixtures/layout_regression/`](../../tests/fixtures/layout_regression/)
is organised, how to add a new fixture, and what role each per-case file
plays.

The corpus is the source-of-truth for **layout** behaviour — header/footer
stripping, figure/caption association, marginalia handling, decoration
detection, drop-cap stitching, and reading-order assembly. It is **not**
the source-of-truth for word- or character-level recognition fidelity;
see ["What this corpus does *not* cover"](#what-this-corpus-does-not-cover)
below.

The corpus is exercised by:

- `tests/layout/test_fixture_layouts.py` — every `<case>.layout.json`
  must round-trip through `PageLayout.from_dict`, every region must lie
  within image bounds, and the corpus as a whole must cover every
  `RegionType` we care about.
- `tests/ocr/test_reorganize_page_utils_grouping.py` — four
  parametrized cases run `Page.reorganize_page` and diff the output
  against `expected_text/baseline/<case>.reorganize.txt`.

## Layout

```text
tests/fixtures/layout_regression/
├── README.md                                  ← per-case manifest
│                                                (see also this doc)
├── inputs/                                    ← committed fixture data
│   ├── <case>.png                             ← page image
│   ├── <case>.pgdp.txt                        ← PGDP-proofread target
│   ├── <case>.json                            ← OCR Page (DocTR result)
│   └── <case>.layout.json                     ← PageLayout (PP-DocLayout)
├── expected_text/
│   ├── baseline/<case>.reorganize.txt         ← committed; the truth
│   ├── current/                               ← gitignored; pytest writes here
│   └── diff/                                  ← gitignored; on regression
├── debug/                                     ← gitignored; per-step PNGs
├── ocr_fixtures.py                            ← runs DocTR → .json
├── regenerate_layouts.py                      ← runs PP-DocLayout → .layout.json
└── dump_reorganize_output.py                  ← runs reorganize → .reorganize.txt
```

## Per-case files

Each fixture case is a single slug (e.g. `chapter-head-credulities`,
`rotated-peutinger-map`, `figures-side-by-side-with-captions`). For
slug `<case>`:

| File | Purpose | How it's generated |
|---|---|---|
| `inputs/<case>.png` | Source page image, hand-picked from `source-pgdp-data/output/<projectID>/`. | Manual selection — picked to expose a layout pattern that the geometric-only reorg path mishandles. |
| `inputs/<case>.pgdp.txt` | PGDP-proofread *target* text. The gold standard the layout-aware pipeline is *approaching*. | Extracted from each project's `pages.json` (PGDP raw rounds output, `/`-separated soft breaks normalised to newlines). |
| `inputs/<case>.json` | Serialised `Document` from a DocTR OCR pass. Tests load this instead of running DocTR. | `python tests/fixtures/layout_regression/ocr_fixtures.py [case]` |
| `inputs/<case>.layout.json` | `PageLayout` from the PP-DocLayout adapter. Tests load this instead of running the layout model. | `python tests/fixtures/layout_regression/regenerate_layouts.py [case]` (or `make layout-fixtures-regenerate`) |
| `expected_text/baseline/<case>.reorganize.txt` | Reorganize-pipeline output. The committed value is the diff target for `test_reorganize_page_expected_text_outputs`. | `python tests/fixtures/layout_regression/dump_reorganize_output.py <case> > expected_text/baseline/<case>.reorganize.txt` |

## Adding a new fixture

When the geometric reorg path fails on a real page in `source-pgdp-data/`
that exercises a layout pattern not in the corpus, do this:

```bash
# 1. Pick a slug. Use kebab-case; lead with what it tests, not the book.
#    e.g. `marginalia-and-footnotes-stacked` not `book42-page-141`.
SLUG=...

# 2. Copy the page image and extract the PGDP target text.
cp source-pgdp-data/output/<projectID>/<page>.png \
   pdomain-book-tools/tests/fixtures/layout_regression/inputs/${SLUG}.png
# (extract `pages.json[page]`, normalise ` / ` to newlines, write
#  inputs/${SLUG}.pgdp.txt — see source-pgdp-data/output/*/pages.json)

# 3. OCR the page (writes inputs/${SLUG}.json).
cd pdomain-book-tools
.venv/bin/python tests/fixtures/layout_regression/ocr_fixtures.py ${SLUG}

# 4. Run the layout model (writes inputs/${SLUG}.layout.json + a
#    debug overlay PNG into debug/${SLUG}/).
.venv/bin/python tests/fixtures/layout_regression/regenerate_layouts.py ${SLUG}

# 5. Bootstrap the reorganize baseline. Eyeball it before committing —
#    this is the value future regressions are diffed against, so what
#    you commit IS the contract.
.venv/bin/python tests/fixtures/layout_regression/dump_reorganize_output.py ${SLUG} \
    > tests/fixtures/layout_regression/expected_text/baseline/${SLUG}.reorganize.txt

# 6. Add an entry under the right category in
#    tests/fixtures/layout_regression/README.md describing what the
#    fixture stresses.

# 7. If the new fixture is the first to exercise a particular feature
#    that test_reorganize_page_expected_text_outputs should diff, add
#    its slug to the parametrize() list in
#    tests/ocr/test_reorganize_page_utils_grouping.py.
```

`make test` should pass after this. If it doesn't, the new baseline
likely contains output you didn't intend to lock in — re-eyeball
`expected_text/baseline/${SLUG}.reorganize.txt` against the source PNG
before committing.

## Regenerating after a pipeline change

The baselines under `expected_text/baseline/` are the **regression
contract**. They exist so a change can be reviewed by reading a diff,
not by inspecting every page by eye. **Never** mass-overwrite them
with a script — doing so converts every regression into noise. The
right loop is always: run → inspect diff → promote intentionally.

### Reorganize behaviour changed (the common case)

`test_reorganize_page_expected_text_outputs` writes the *current* output
to `expected_text/current/<case>.reorganize.txt` and a unified diff
into `expected_text/diff/<case>.reorganize.diff.txt`. Both directories
are gitignored.

```bash
# 1. Run the regression test. It will FAIL on every case where output
#    diverges from the committed baseline.
make test  # or: .venv/bin/python -m pytest tests/ocr/test_reorganize_page_utils_grouping.py

# 2. For each failing case, read the diff. There are exactly four
#    possible verdicts:
#      a) Output got better  → the new text is what we want. Promote
#         this one baseline (see step 3).
#      b) Output got worse   → bug. Fix the code, not the baseline.
#      c) Output is equally  → think hard. Do you actually prefer the
#         valid but different      new shape? If yes, promote. If no,
#                                  pick a side and stick with it.
#      d) Output is just     → Same as (c). The point of the corpus is
#         re-arranged tokens     to lock in shape. Re-arrangements ARE
#         that say the same      regressions until you decide they
#         thing                  aren't.
cat tests/fixtures/layout_regression/expected_text/diff/<case>.reorganize.diff.txt

# 3. Promote ONE case at a time, with intent:
cp tests/fixtures/layout_regression/expected_text/current/<case>.reorganize.txt \
   tests/fixtures/layout_regression/expected_text/baseline/<case>.reorganize.txt

# 4. Re-run pytest. The promoted case should now pass; any remaining
#    failures are still on the table for review.
make test
```

The PR that promotes a baseline must explain in the commit message *why*
the diff is an improvement. "Tests now pass" is not a sufficient reason.

### Layout model output changed

Layout regions feed reorganize as a hint, so a layout change typically
shows up as a reorganize diff first. Regenerate the layout JSONs and
follow the reorganize-change workflow above:

```bash
make layout-fixtures-regenerate   # rewrites inputs/<case>.layout.json
make test                         # observe reorganize diffs in expected_text/diff/
# ... promote each case intentionally as in step 3 above ...
```

`layout-fixtures-regenerate` writes a debug overlay PNG into
`debug/<case>/layout-regions.png` per case — open these alongside the
diff to see *why* the regions changed before deciding to promote.

### OCR predictor / DocTR weights changed

This is the heaviest change because the OCR JSON drives both the layout
regions and the reorganize text. Regenerate everything in order:

```bash
.venv/bin/python tests/fixtures/layout_regression/ocr_fixtures.py --force   # ~3 s/page
make layout-fixtures-regenerate                                              # ~700 ms/page
make test                                                                    # observe reorganize diffs
# ... promote each case intentionally ...
```

Re-OCRing changes word-level recognition (smart quotes, drop-cap glyph
choice, the occasional letter). Resist the urge to bulk-promote; OCR
drift is exactly what these baselines are supposed to *catch*.

### What "promote intentionally" looks like

A good baseline-update PR has:

- One commit per logical change ("reorganize: improve drop-cap stitch
  on preface-style headings; promote `preface-with-drop-cap` baseline").
- The diff visible in the PR description (paste it inline) with a
  one-line verdict next to each before/after pair.
- Either a code change in the same PR that *caused* the diff, or a
  paragraph explaining what *external* change (model weights, fixture
  PNG, etc.) caused it.

If you can't write that paragraph, you're not ready to promote.

## Layout vs OCR: what each layer is responsible for

The corpus is the contract between layers:

| Layer | What this corpus locks in | What it doesn't |
|---|---|---|
| OCR (`<case>.json`) | DocTR's bbox/text output for the fixed input image | Word / character accuracy — those are improved by the labeler/trainer flow |
| Layout (`<case>.layout.json`) | PP-DocLayout regions + types + confidences | Whether every region the human eye sees was found — the model misses some, intentionally exposed by fixtures like `notes-on-illustrations-list` (0 regions returned) |
| Reorganize (`<case>.reorganize.txt`) | Reading-order assembly: which Words ended up in which Block, in what order, with which tags | Word-level OCR fidelity (recognition mistakes pass through unchanged) |

A failing diff in `expected_text/diff/` means *layout/order* changed,
not that *characters* changed. If only character-level diffs remain
after a change to recognition, those are a labeler/trainer concern, not
a regression.

## What this corpus does *not* cover

- **Tables.** None of the six source books contain genuine tables.
  Source from a different book if `RegionType.table` needs a fixture.
- **Mathematical formulae.** Same — `RegionType.formula` has no
  representative fixture.
- **Cross-page foldouts.** Foldout maps spanning two pages stay a
  manual operation; out of scope for layout-aware reorg.
- **Word/character recognition accuracy.** Fixture `.json` files are
  the OCR pass output as-is; mistakes (smart quotes mangled to digits,
  drop caps misread as "+", etc.) flow through into the
  `.reorganize.txt` baselines unchanged. Recognition fidelity belongs
  to `pdomain-ocr-labeler-spa` / `pdomain-ocr-training`.

## Source projects

| projectID | Book |
|---|---|
| `629292e7559a8` | Wilson, *A History of the American People*, Vol. III |
| `63ac6757567bd` | Jones, *Credulities Past and Present* |
| `63ac684a641d4` | Russell, *A Visit to Chile and the Nitrate Fields of Tarapacá* (1890) |
| `66c62fca99a93` | *French Furniture and Decoration in the XVIIIth Century* |
| `6737b15d33ff3` | Singer, *From Magic to Science* |
| `67658de495d0c` | *The Book of Filial Duty* (Hsiao Ching, 1908) |

The per-case manifest with full source paths and a description of what
each fixture stresses lives in
[`tests/fixtures/layout_regression/README.md`](../../tests/fixtures/layout_regression/README.md).

## TL;DR

Not yet captured during the B3 mechanical migration.

## Context

Not yet captured during the B3 mechanical migration.

## Constraints

Not yet captured during the B3 mechanical migration.

## Decision

Not yet captured during the B3 mechanical migration.

## Contract / Acceptance

Not yet captured during the B3 mechanical migration.

## Trade-offs considered

Not yet captured during the B3 mechanical migration.

## Consequences

Not yet captured during the B3 mechanical migration.

## Open questions

Not yet captured during the B3 mechanical migration.

## References

Not yet captured during the B3 mechanical migration.
