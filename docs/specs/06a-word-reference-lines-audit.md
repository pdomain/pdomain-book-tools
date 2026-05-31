# Spec: Word / Line Reference Lines — Audit and Gap Analysis

> **Status**: Active
> **Last updated**: 2026-05-21
> **Split from**: [06-word-reference-lines.md](../archive/specs/06-word-reference-lines.md)

Audit of existing baseline-estimation code in `pdomain-book-tools` and gap
analysis of the four reference lines (top, x-height, baseline, bottom).
This is part 1 of a three-part split of the original
`06-word-reference-lines.md` spec (914 lines, exceeded the 800-line cap).

- Part 1 (this file): Audit + gap analysis
- Part 2: [06b-word-reference-lines-api.md](06b-word-reference-lines-api.md) — API surface, heuristics, parameters, confidence
- Part 3: [06c-word-reference-lines-testing.md](06c-word-reference-lines-testing.md) — Bottom-crop interaction, open questions, decisions, testing, CI, out of scope

---

## TL;DR

The `pdomain-book-tools` package has partial baseline support (one of four
reference lines) via `Word.estimate_baseline_from_image` and
`Block.estimate_baseline_from_image`. Top-line, x-height, and descender
bottom are entirely missing. The descender character set is duplicated in
three places. This part documents exactly what exists and what gaps remain.

## Context

Author intent: extend the existing baseline-estimation surface in
`pdomain-book-tools` from a single per-word/per-line **baseline** estimate
to a richer set of four reference lines per word and per line:

1. **top-line** (cap-line / ascender top — the highest ink row, with
   ascender-presence detection so callers can distinguish "ascender
   top" from "x-height top")
2. **centerline / x-height line** (top of lowercase letters with no
   ascender — the top of the densest body band)
3. **baseline** (where most letters sit; already partially solved)
4. **bottom** (descender bottom — the lowest ink row, including
   descenders)

This spec exists because of work happening in pdomain-ocr-labeler-spa on the
**Bottom-Crop Bbox Tool** (see
[`/workspaces/ocr-container/pdomain-ocr-labeler-spa/docs/planning/bottom-crop-tool-spec.md`](../../../pdomain-ocr-labeler-spa/docs/planning/bottom-crop-tool-spec.md)).
That tool needs `baseline_y + descender_allowance` per word; it
currently reaches for `Word.estimate_baseline_from_image` and computes
its own `descender_allowance` from `median_height`. Promoting the
existing baseline helper into a full reference-lines API would let
that tool — and any future top-/centerline-aware tool — depend on a
single, well-tested abstraction.

## Constraints

- Must not break existing callers of `Word.estimate_baseline_from_image`
  or `Block.estimate_baseline_from_image`.
- Descender character set must be deduplicated — it currently appears in
  three places.
- New module (`reference_lines.py`) must live in `pdomain_book_tools/ocr/`.

## Decision

See [06b-word-reference-lines-api.md](06b-word-reference-lines-api.md)
for the API surface decisions and
[06c-word-reference-lines-testing.md](06c-word-reference-lines-testing.md)
for decisions requested.

## 1. Audit: what already exists

### 1.1 Word.estimate_baseline_from_image

Location: `pdomain_book_tools/ocr/word.py:961`.

Signature:

```python
def estimate_baseline_from_image(
    self, image: ndarray | None
) -> dict[str, float | str] | None
```

What it actually does:

- Calls `self.split_into_characters_from_whitespace(image)`
  (`pdomain_book_tools/ocr/word.py:768`) to get a list of `Character`
  objects whose individual `bounding_box` heights came from
  per-character vertical extents inside the binarized ROI.
- Computes a weighted average of the per-character `bounding_box.maxY`
  (the bottom of each character's tight bbox), with descenders
  (`{"p", "g", "j", "q", "Q"}` — `word.py:974`) down-weighted to
  `0.35`.
- Returns a dict
  `{"type": "horizontal", "y": <pixel-y>, "confidence": <float>,
  "coordinate_space": "pixel"}` and stores it as `self.baseline`.

Return type / coordinate space:

- Always pixel-space, regardless of whether the word's own bbox is
  normalized. The caller is expected to convert if they need
  normalized coordinates.
- `confidence` is `1 - (weighted_std_of_bottoms / max(1, mean_height))`,
  clamped to `[0, 1]`. It is the only confidence signal currently
  exposed.

Robustness story:

- Strong: weighting descenders down means a single `g` does not drag
  the baseline below the line.
- Weak: the estimator only looks at character-bbox `maxY`. There is no
  horizontal projection profile. If
  `split_into_characters_from_whitespace` segments incorrectly (which
  it can — see the morphology fallback at `word.py:831`), the baseline
  inherits that error.
- Weak: a two-letter word with both letters at the same height
  produces `weighted_std == 0` and therefore confidence `1.0` —
  see `tests/ocr/test_word.py:1332-1348`. So "high confidence" does
  not mean "this is a real baseline", just "the per-character bottoms
  agree". A single-character word also produces a meaningless
  confidence (zero variance).
- The `dict` return type is loose — there is no dataclass, no named
  field, the `coordinate_space: "pixel"` is encoded as a string-typed
  value inside a `dict[str, float | str]`. Awkward but consistent with
  the older serialization-friendly shape used elsewhere in the repo.

Per-word, not per-line.

### 1.2 Block.estimate_baseline_from_image

Location: `pdomain_book_tools/ocr/block.py:1000`.

Signature:

```python
def estimate_baseline_from_image(
    self, image: ndarray | None
) -> dict[str, float | str] | None
```

What it does:

- Only acts on blocks where `child_type == BlockChildType.WORDS` and
  `block_category == BlockCategory.LINE` (`block.py:1010-1015`).
- For each `Word` in the line, calls
  `split_into_characters_from_whitespace(image)`, then collects
  per-character (mid-x, maxY) points with the same descender weighting
  as the word-level estimator.
- Fits a weighted linear regression (`np.polyfit(..., deg=1)`) to
  produce `slope`, `intercept`, and a confidence score.
- Returns
  `{"type": "linear", "slope": <float>, "intercept": <float>,
  "confidence": <float>, "coordinate_space": "pixel"}`.

So the line-level baseline is **not horizontal** — it is a slanted line
`y = slope*x + intercept`, which is correct for tilted scans.

It also calls `item.estimate_baseline_from_image(image)` as a
side-effect on every word in the block (`block.py:1028`), populating
each word's `self.baseline`. So calling block-level once gives you
a per-line baseline plus one horizontal per-word baseline per word.

### 1.3 The descender heuristic in split_into_characters_from_whitespace

Location: `pdomain_book_tools/ocr/word.py:927-958`.

When a word is split into 2+ characters, the function does _not_
compute a baseline as such, but it does:

- Take the weighted average of `tops`, `bottoms`, and `heights`
  (with the same descender down-weighting).
- Use `top_delta = 0.2 * median_height` and
  `bottom_delta = 0.1 * median_height` to label per-character
  `superscript` / `subscript` text-style components.

The variable `median_height` here is _the average character height_
(misleadingly named; it is a weighted mean, not a median). It is **not
x-height** — for a word like "Page" containing both an ascender and
descenders, this average height is closer to full type height than to
x-height. So while x-height is _implicit_ in this calculation, it is
not directly exposed.

### 1.4 The descender character set

Defined inline in three places:

- `pdomain_book_tools/ocr/word.py:937` — used in
  `split_into_characters_from_whitespace`.
- `pdomain_book_tools/ocr/word.py:974` — used in
  `estimate_baseline_from_image`.
- `pdomain_book_tools/ocr/block.py:1017` — used in
  `Block.estimate_baseline_from_image`.

All three copies are the literal `{"p", "g", "j", "q", "Q"}`. The
bottom-crop spec proposes broadening this set; this spec proposes the
same broadening (see
[06b-word-reference-lines-api.md](06b-word-reference-lines-api.md)
section 4.2) and, importantly, **dedup'ing the literal into a
module-level constant** so all four reference-line helpers and the
bottom-crop tool use the same source of truth.

### 1.5 No top-line, no x-height, no cap-height code anywhere

Greps across the package
(`grep -rnE "x_height|cap_height|ascender|topline|centerline|mean_line"`
on `pdomain_book_tools/`) returned only the descender-related references
above. There is no:

- top-line / cap-line estimator.
- explicit x-height function.
- ascender-presence detector beyond the implicit "if a glyph extends
  far above `median_top` we tag it superscript" inside
  `split_into_characters_from_whitespace`.

There is also no horizontal projection profile primitive. The current
estimators all work on per-character bboxes, not on row-density of
the binarized ROI.

### 1.6 The page level

`Page.refine_bounding_boxes` exists at
`pdomain_book_tools/ocr/page.py:3055`, but **there is no
`Page.estimate_baseline_from_image` or any page-level
reference-line aggregation.** A caller wanting per-line baselines for
every line on a page must iterate blocks themselves.

## 2. Gap analysis — per reference line

| Reference line | Status | Notes |
|---|---|---|
| **Bottom (descender bottom / lowest ink)** | **Missing** | No helper returns "lowest ink row in the word ROI". The bottom-crop spec's plan is to add `BoundingBox.crop_bottom_to_y` for this; that primitive _would_ compute the lowest ink row internally but does not expose it. The closest existing thing is the implicit lowest-row detection in `BoundingBox._vertical_crop` (`bounding_box.py:611-650`), which is internal. |
| **Baseline** | **Partial — usable but limited** | `Word.estimate_baseline_from_image` and `Block.estimate_baseline_from_image` exist. They are the good news. Limitations: dict-return (no dataclass), pixel-space only, confidence signal is "do per-character bottoms agree" rather than "is this likely the true baseline", no fallback when characters cannot be split. The block-level estimator returns a _slanted_ linear baseline; the word-level one returns a horizontal scalar. The two return shapes do not unify. |
| **Centerline / x-height** | **Missing** | Implicit in `split_into_characters_from_whitespace`'s `median_top`, but not exposed and not the right value (it is an average of _all_ character tops, ascenders included, not the top of the densest body band). |
| **Top-line (cap / ascender top)** | **Missing** | No helper returns "highest ink row" or "top of tallest character". `median_top` again gives an average, not a max. There is also no helper that says "this word contains an ascender" so a caller cannot decide whether top-line and x-height-line collide. |

Summary: 1 of 4 partial, 3 of 4 missing. The baseline machinery is the
seed; everything else is greenfield.

## Contract / Acceptance

- All three audit facts (sections 1.1–1.6) are verified against current
  source by grep.
- Gap table (section 2) matches the current state of the codebase.
- No code changes in this spec part; it is observation-only.

## Trade-offs considered

The existing `estimate_baseline_from_image` dict return shape is awkward
but retained for backward compatibility. Replacing it with a dataclass
would break callers; see Q-RL-1 in
[06c-word-reference-lines-testing.md](06c-word-reference-lines-testing.md).

## Consequences

This audit establishes the starting point for the new API specified in
[06b-word-reference-lines-api.md](06b-word-reference-lines-api.md).

## Open questions

See [06c-word-reference-lines-testing.md](06c-word-reference-lines-testing.md)
for the full open-questions list (Q-RL-1 through Q-RL-10).

## References

- [06b-word-reference-lines-api.md](06b-word-reference-lines-api.md) — API design, heuristics, parameters
- [06c-word-reference-lines-testing.md](06c-word-reference-lines-testing.md) — Testing, open questions, decisions
- [06-word-reference-lines.md](../archive/specs/06-word-reference-lines.md) — Parent forwarding stub (archived)
- `pdomain_book_tools/ocr/word.py` — `estimate_baseline_from_image`, `split_into_characters_from_whitespace`
- `pdomain_book_tools/ocr/block.py` — `Block.estimate_baseline_from_image`
