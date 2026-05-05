# Layout-regression fixture corpus

Real public-domain pages drawn from `source-pgdp-data/` to exercise the
layout detector + layout-aware reorganize pipeline against the kinds of
pages that actually break the geometric reorg path.

## Per-case files

Each fixture case is a slug; for slug `<case>`:

| File | Purpose | Generation |
|---|---|---|
| `inputs/<case>.png` | source page image | hand-picked from `source-pgdp-data/output/<projectID>/` |
| `inputs/<case>.pgdp.txt` | PGDP-proofread target text | extracted from that project's `pages.json` |
| `inputs/<case>.json` | OCR `Page` model | run DocTR via `scripts/ocr_fixtures.py` (TODO) |
| `inputs/<case>.layout.json` | `PageLayout` from PP-DocLayout | `make layout-fixtures-regenerate` |
| `expected_text/baseline/<case>.reorganize.txt` | reorganize_page output | `dump_reorganize_output.py <case>` |

The `.pgdp.txt` files are **not** what `reorganize_page` is expected to
output verbatim — they're the gold-standard target the pipeline is
*approaching*. OCR will mis-recognize words, recognition models drift,
and the labeler/trainer flow exists precisely to close that gap.

What this corpus tests is **layout**: are the right regions found, in
the right reading order, with captions associated to figures, headers
and footers stripped, marginalia routed to the right place. Word- and
character-level fidelity belongs to `pd-ocr-labeler` / `pd-ocr-trainer`.

## Cases

Categories sort by what the page exercises in the pipeline.

### Frontispieces / standalone illustrations

| Slug | Source | Tests |
|---|---|---|
| `frontispiece-madison-portrait` | `projectID629292e7559a8/004.png` | full-page portrait engraving with single centered caption — simplest figure+caption case |
| `frontispiece-on-deck-dual-caption` | `projectID63ac684a641d4/a0020.png` | dual caption: centered title + right-aligned `[Frontispiece.` |
| `plate-service-on-board` | `projectID63ac684a641d4/p0081.png` | full-page wood engraving with caption + right-aligned `[To face page N.` |
| `plate-rio-harbour-photo` | `projectID63ac684a641d4/p0101.png` | photographic plate; different visual texture, same dual-caption layout |
| `plate-iquique-landscape` | `projectID63ac684a641d4/p1381.png` | wide landscape engraving; signature embedded in plate |
| `plate-coronel-text-in-image` | `projectID63ac684a641d4/p0322.png` | town panorama with OCR-trap text inside the picture (signage) |
| `plate-chairs-beauvais-tapestry` | `projectID66c62fca99a93/215.png` | full-page tapestry/chair plate with 2-line caption (titlecase title + italic parenthetical subtitle); regression-guards the `Page.recompute_bounding_box` empty-list crash that previously bit this layout |

### Plates with extended multi-line captions

| Slug | Source | Tests |
|---|---|---|
| `plate-i-fall-of-angels-color` | `projectID6737b15d33ff3/f000.png` | header label `PLATE I` above image + 2-line caption below — three-region layout |
| `plate-ii-celestial-influences` | `projectID6737b15d33ff3/p058b.png` | `PLATE II` circular figure with 3-line caption (italic title + cross-reference) |
| `plate-v-anglosaxon-herbal` | `projectID6737b15d33ff3/p150a.png` | figure CONTAINS Anglo-Saxon manuscript text — must NOT lift into body stream |

### Inline figures

| Slug | Source | Tests |
|---|---|---|
| `inline-figure-parthenon-steed` | `projectID6737b15d33ff3/p008b.png` | `FIG. N.—` style caption with cross-reference; typical inline figure block |
| `figures-side-by-side-with-captions` | `projectID6737b15d33ff3/p177` | two inline figures (FIG. 72 and FIG. 73) arranged side-by-side, each with its own multi-line caption underneath — exercises figure→caption pairing in narrow columns |
| `text-wraps-around-figure` | `projectID6737b15d33ff3/p178` | body text wraps around an inset left-side figure (FIG. 74), then continues full-width below — asymmetric column reading order |
| `inline-figure-with-greek-labels` | `projectID6737b15d33ff3/p179` | large figure (FIG. 75) with Greek alphabet labels embedded INSIDE the image + multi-line italic caption — labels must NOT lift into body stream |
| `rotated-peutinger-map` | `projectID6737b15d33ff3/p042.png` | **90° rotated full-page map** with sideways page number — see plan §7 (page rotation detection) |
| `diagram-dante-universe` | `projectID6737b15d33ff3/p087.png` | many inline labels embedded in the diagram — must classify labels as part of figure |

### Chapter openings / drop caps / decorative head-pieces

| Slug | Source | Tests |
|---|---|---|
| `chapter-head-american-people` | `projectID629292e7559a8/021.png` | tall title + CHAPTER I + small-caps subtitle + drop-cap T |
| `chapter-head-credulities` | `projectID63ac6757567bd/p0010.png` | italic display title + CHAPTER I. + subtitle + two-line drop-cap S |
| `chapter-head-with-synopsis` | `projectID63ac684a641d4/p0050.png` | CHAPTER I. + subtitle + multi-line italic synopsis (em-dash topic list) before body |
| `chapter-head-filial-duty` | `projectID67658de495d0c/016.png` | triple-stacked heading + drop-cap O on a narrow-measure book |
| `decorative-headpiece-list-of-illus` | `projectID66c62fca99a93/021.png` | engraved head-piece + LIST OF ILLUSTRATIONS + leader-dot list + right-margin sidenote |
| `preface-with-drop-cap` | *Credulities Past and Present* / preface | PREFACE heading + two-line drop-cap "R" — exercises drop-cap detection on a heading that isn't `CHAPTER N` (foreword/preface variant) |

### Front-matter / list pages

| Slug | Source | Tests |
|---|---|---|
| `notes-on-illustrations-list` | `projectID629292e7559a8/009.png` | leader-dot list with mixed entry lengths and right-aligned PAGE column |
| `contents-page` | `projectID67658de495d0c/005.png` | minimal CONTENTS page with horizontal rule + 3 entries + PAGE header |

### Body pages with header/footer/page-number chrome

| Slug | Source | Tests |
|---|---|---|
| `body-running-header-page-number` | `projectID629292e7559a8/100.png` | running header + centered page number — header/footer drop baseline |
| `body-italic-header-left-pageno` | `projectID63ac6757567bd/p0500.png` | page number on the LEFT, italic running header — different chrome layout |
| `body-header-includes-pageno` | `projectID6737b15d33ff3/p015.png` | page number is part of the running-header line — header/footer geometry collide |

### Footnotes & sidenotes

| Slug | Source | Tests |
|---|---|---|
| `footnotes-stacked-with-anchor` | `projectID63ac6757567bd/p3580.png` | drop-cap A + body + footnote anchor (\*) + 3 stacked footnote paragraphs |
| `sidenote-right-with-footnotes` | `projectID66c62fca99a93/141.png` | right-margin sidenote AND 3 numbered footnotes — sidenote + footnote together |
| `sidenote-left-with-footnotes` | `projectID66c62fca99a93/300.png` | left-margin sidenote + 2 footnotes — mirrors right side on the verso |

### Catalog (high-density multi-region layout)

| Slug | Source | Tests |
|---|---|---|
| `catalog-multi-block-ads` | `projectID63ac6757567bd/w0020.png` | publisher's back-matter catalog: ~8 ad blocks separated by horizontal rules — densest multi-region layout in the corpus |

## Coverage vs `RegionType`

- `text` — every body page
- `title` / `section` — chapter-head-* fixtures
- `figure` — every frontispiece/plate/inline-figure/diagram fixture
- `caption` — every figure fixture (single, dual, multi-line variants)
- `decoration` — `decorative-headpiece-list-of-illus`
- `header` / `footer` / `page_number` — `body-*` fixtures
- `footnote` — `footnotes-*` and `sidenote-*` fixtures
- `abandoned` (marginalia) — `sidenote-*` and `decorative-headpiece-list-of-illus`
- `list` — `notes-on-illustrations-list`, `contents-page`
- rotated input — `rotated-peutinger-map`

`table` and `formula` are not present in this corpus. Source from a
different book if those region types need fixtures.

## Source projects

| projectID | Book |
|---|---|
| `629292e7559a8` | Wilson, *A History of the American People*, Vol. III |
| `63ac6757567bd` | Jones, *Credulities Past and Present* |
| `63ac684a641d4` | Russell, *A Visit to Chile and the Nitrate Fields of Tarapacá* (1890) |
| `66c62fca99a93` | *French Furniture and Decoration in the XVIIIth Century* |
| `6737b15d33ff3` | Singer, *From Magic to Science* |
| `67658de495d0c` | *The Book of Filial Duty* (Hsiao Ching, 1908) |
