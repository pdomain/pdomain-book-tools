# Spec: Word / Line Reference Lines (top, x-height, baseline, bottom)

Status: spec only — no implementation yet. Decision-oriented; intended
to be green-lit, pushed back on, or revised before code is written.

Author intent: extend the existing baseline-estimation surface in
`pd-book-tools` from a single per-word/per-line **baseline** estimate
to a richer set of four reference lines per word and per line:

1. **top-line** (cap-line / ascender top — the highest ink row, with
   ascender-presence detection so callers can distinguish "ascender
   top" from "x-height top")
2. **centerline / x-height line** (top of lowercase letters with no
   ascender — the top of the densest body band)
3. **baseline** (where most letters sit; already partially solved)
4. **bottom** (descender bottom — the lowest ink row, including
   descenders)

This spec exists because of work happening in pd-ocr-labeler on the
**Bottom-Crop Bbox Tool** (see
[`/workspaces/ocr-container/pd-ocr-labeler/docs/planning/bottom-crop-tool-spec.md`](../../../pd-ocr-labeler/docs/planning/bottom-crop-tool-spec.md)).
That tool needs `baseline_y + descender_allowance` per word; it
currently reaches for `Word.estimate_baseline_from_image` and computes
its own `descender_allowance` from `median_height`. Promoting the
existing baseline helper into a full reference-lines API would let
that tool — and any future top-/centerline-aware tool — depend on a
single, well-tested abstraction. See section 8 for the cross-spec
interaction (specifically: should the bottom-crop spec be revised to
depend on this new API or proceed independently?).

## 1. Audit: what already exists

### 1.1 Word.estimate_baseline_from_image

Location: `pd_book_tools/ocr/word.py:961`.

Signature:

```python
def estimate_baseline_from_image(
    self, image: ndarray | None
) -> dict[str, float | str] | None
```

What it actually does:

- Calls `self.split_into_characters_from_whitespace(image)`
  (`pd_book_tools/ocr/word.py:768`) to get a list of `Character`
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
  clamped to `[0, 1]`. It's the only confidence signal currently
  exposed.

Robustness story:

- Strong: weighting descenders down means a single `g` doesn't drag
  the baseline below the line.
- Weak: the estimator only looks at character-bbox `maxY`. There's
  no horizontal projection profile. If
  `split_into_characters_from_whitespace` segments incorrectly (which
  it can — see the morphology fallback at `word.py:831`), the baseline
  inherits that error.
- Weak: a two-letter word with both letters at the same height
  produces `weighted_std == 0` and therefore confidence `1.0` —
  see `tests/ocr/test_word.py:1332-1348`. So "high confidence" does
  not mean "this is a real baseline", just "the per-character bottoms
  agree". A single-character word also produces a meaningless
  confidence (zero variance).
- The `dict` return type is loose — there's no dataclass, no
  named field, the `coordinate_space: "pixel"` is encoded as a
  string-typed value inside a `dict[str, float | str]`. Awkward but
  consistent with the older serialization-friendly shape used
  elsewhere in the repo.

Per-word, not per-line.

### 1.2 Block.estimate_baseline_from_image

Location: `pd_book_tools/ocr/block.py:1000`.

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

So the line-level baseline is **not horizontal** — it's a slanted line
`y = slope*x + intercept`, which is correct for tilted scans.

It also calls `item.estimate_baseline_from_image(image)` as a
side-effect on every word in the block (`block.py:1028`), populating
each word's `self.baseline`. So calling block-level once gives you
a per-line baseline + one horizontal per-word baseline per word.

### 1.3 The descender heuristic in split_into_characters_from_whitespace

Location: `pd_book_tools/ocr/word.py:927-958`.

When a word is split into 2+ characters, the function does *not*
compute a baseline as such, but it does:

- Take the weighted average of `tops`, `bottoms`, and `heights`
  (with the same descender down-weighting).
- Use `top_delta = 0.2 * median_height` and
  `bottom_delta = 0.1 * median_height` to label per-character
  `superscript` / `subscript` text-style components.

The variable `median_height` here is *the average character height*
(misleadingly named; it's a weighted mean, not a median). It is **not
x-height** — for a word like "Page" containing both an ascender and
descenders, this average height is closer to full type height than to
x-height. So while x-height is *implicit* in this calculation, it is
not directly exposed.

### 1.4 The descender character set

Defined inline in three places:

- `pd_book_tools/ocr/word.py:937` — used in
  `split_into_characters_from_whitespace`.
- `pd_book_tools/ocr/word.py:974` — used in
  `estimate_baseline_from_image`.
- `pd_book_tools/ocr/block.py:1017` — used in
  `Block.estimate_baseline_from_image`.

All three copies are the literal `{"p", "g", "j", "q", "Q"}`. The
bottom-crop spec proposes broadening this set; this spec proposes the
same broadening (see section 4.2) and, importantly, **dedup'ing the
literal into a module-level constant** so all four reference-line
helpers and the bottom-crop tool use the same source of truth.

### 1.5 No top-line, no x-height, no cap-height code anywhere

Greps across the package
(`grep -rnE "x_height|cap_height|ascender|topline|centerline|mean_line"`
on `pd_book_tools/`) returned only the descender-related references
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
`pd_book_tools/ocr/page.py:3055`, but **there is no
`Page.estimate_baseline_from_image` or any page-level
reference-line aggregation.** A caller wanting per-line baselines for
every line on a page must iterate blocks themselves.

## 2. Gap analysis — per reference line

| Reference line | Status | Notes |
|---|---|---|
| **Bottom (descender bottom / lowest ink)** | **Missing** | No helper returns "lowest ink row in the word ROI". The bottom-crop spec's plan is to add `BoundingBox.crop_bottom_to_y` for this; that primitive *would* compute the lowest ink row internally but does not expose it. The closest existing thing is the implicit lowest-row detection in `BoundingBox._vertical_crop` (`bounding_box.py:611-650`), which is internal. |
| **Baseline** | **Partial — usable but limited** | `Word.estimate_baseline_from_image` and `Block.estimate_baseline_from_image` exist. They are the good news. Limitations: dict-return (no dataclass), pixel-space only, confidence signal is "do per-character bottoms agree" rather than "is this likely the true baseline", no fallback when characters can't be split. The block-level estimator returns a *slanted* linear baseline; the word-level one returns a horizontal scalar. The two return shapes do not unify. |
| **Centerline / x-height** | **Missing** | Implicit in `split_into_characters_from_whitespace`'s `median_top`, but not exposed and not the right value (it's an average of *all* character tops, ascenders included, not the top of the densest body band). |
| **Top-line (cap / ascender top)** | **Missing** | No helper returns "highest ink row" or "top of tallest character". `median_top` again gives an average, not a max. There is also no helper that says "this word contains an ascender" so a caller cannot decide whether top-line and x-height-line collide. |

Summary: 1 of 4 partial, 3 of 4 missing. The baseline machinery is the
seed; everything else is greenfield.

## 3. Recommended primary surface

Two-tier API. **Block (line) level is the primary, robust surface;
Word level is the best-effort fallback.** Reasoning is in 3.3 below.

### 3.1 Block-level: WordReferenceLines per word, computed line-aware

```python
# pd_book_tools/ocr/reference_lines.py  (new module)

@dataclass(frozen=True)
class WordReferenceLines:
    """Four reference y-coordinates for a single word, in pixel space.

    All four are absolute y-coordinates in the page-image coordinate
    system (i.e. the same space as the word's pixel bounding box, not
    ROI-local). When the word's bbox is normalized, the caller is
    responsible for converting via the page's image dimensions.
    """

    top: float                # highest ink row
    x_height: float           # top of the densest body band
    baseline: float           # baseline y
    bottom: float             # lowest ink row (descender included)

    has_ascender: bool        # True if `top` and `x_height` differ
                              # by more than `ascender_min_gap_px`
    has_descender: bool       # True if `bottom` and `baseline` differ
                              # by more than `descender_min_gap_px`

    confidence: float         # [0, 1] — see section 5.4
```

Page-image space (not ROI-local) is the recommendation. Justification:

- Every existing baseline return value is page-image pixel-space
  (`coordinate_space: "pixel"` in both `Word.estimate_baseline_from_image`
  and `Block.estimate_baseline_from_image`). Matching that avoids
  surprising callers.
- Callers usually want to compare across words on the same line, which
  only makes sense in a shared coordinate space. ROI-local would force
  every caller to add `bbox.minY` themselves.
- For the bottom-crop tool specifically, `target_y` is page-image
  pixels (see the bottom-crop spec section 9 for
  `BoundingBox.crop_bottom_to_y`). Same space.

If a caller really wants ROI-local, they subtract `bbox.minY`
themselves. We don't expose two variants — one truth, plus a
documented convention.

### 3.2 Block / Page entry points

```python
# pd_book_tools/ocr/block.py

def estimate_word_reference_lines(
    self,
    image: ndarray | None,
    *,
    descender_chars: frozenset[str] = DEFAULT_DESCENDER_CHARS,
    min_words_for_line_aggregate: int = 3,
) -> dict[Word, WordReferenceLines | None]:
    """For a LINE block, return four-line refs for every contained word.

    Per-word values are corrected against a single line-level baseline
    when the line has at least `min_words_for_line_aggregate` words
    (and that aggregate is more reliable than any individual word's
    estimate). Below that threshold, falls back to per-word estimation
    only.

    Returns None for any word whose ROI is empty / unparseable.
    Side effects: also stores the result on each `Word` (see 3.4).
    """

# pd_book_tools/ocr/page.py

def estimate_word_reference_lines(
    self,
    image: ndarray | None = None,
    **kwargs,
) -> dict[Word, WordReferenceLines | None]:
    """Iterate LINE blocks; merge per-line results into a single dict."""
```

Block returns a dict keyed on `Word` rather than a list, so that
callers can ask `result.get(word)` without index-tracking. Same shape
on the page entry point so call sites compose.

### 3.3 Word-level: best-effort, used by the line-level estimator and as fallback

```python
# pd_book_tools/ocr/word.py

def estimate_reference_lines(
    self,
    image: ndarray | None,
    *,
    descender_chars: frozenset[str] = DEFAULT_DESCENDER_CHARS,
    line_baseline_y: float | None = None,
    line_x_height_px: float | None = None,
) -> WordReferenceLines | None:
    """Per-word four-line ref, with optional line-level corrections.

    When `line_baseline_y` and/or `line_x_height_px` are provided
    (typically by the Block-level helper), they override the
    word-local estimate for the corresponding lines. This is how a
    word like "no" — which on its own has no ascender or descender
    cue — inherits the line's reference frame.
    """
```

Why line-level is primary:

- **Short-word problem.** A word like "no", "is", or "to" gives the
  word-only estimator no descender ink and no ascender ink. Its own
  ROI tells the function "x-height = top of the highest ink, baseline
  = bottom of the lowest ink, no ascender, no descender". For that
  word the cap-line and x-height collide, and the descender-bottom
  collides with the baseline. The line-level helper averages over
  enough words that ascender / descender presence is statistically
  recoverable for the *line*, then back-propagates the line's
  reference frame onto every word.
- **Tilt.** `Block.estimate_baseline_from_image` already returns a
  slanted linear baseline. The word-level estimator, called on a
  tilted line, would get a different `baseline_y` for each word —
  visually correct (each word's baseline is at a different absolute y),
  but only the line-level slope-fit recovers that correctly. The new
  block-level helper should reuse that slope-fit for the baseline,
  and apply analogous slope-fits for the top, x-height, and bottom
  reference lines.
- **Robustness via aggregation.** The current `confidence` on
  `Word.estimate_baseline_from_image` is "do my own characters agree";
  on the block estimator it's "do all line characters agree to the
  fitted line". The latter is meaningfully more useful.

The word-level entry point still exists so that callers can:

- Estimate when only a word + image is available (no line context).
- Test the word-only path in isolation.
- Be called *by* the block-level entry point as the per-word kernel.

### 3.4 Persistence on the Word

`Word` already has a `baseline: dict[str, float | str] | None`
attribute (`word.py:71`) populated as a side-effect of
`estimate_baseline_from_image`. Keep that for backward compatibility,
and add a new attribute:

```python
class Word:
    ...
    reference_lines: WordReferenceLines | None = None
```

Both the word-level and block-level estimator populate
`self.reference_lines` (in addition to returning it), mirroring the
existing baseline-side-effect convention. The old `self.baseline`
dict is also kept up to date for backward compatibility — populated
from `WordReferenceLines.baseline` when the new helper runs. Existing
callers that read `word.baseline["y"]` keep working.

A small migration note: `to_dict` / `from_dict` in `Word` currently
serialize the `baseline` dict (`word.py:648`, `word.py:671`). The new
`reference_lines` attribute is a runtime-only cache (it's image-derived
and cheap to recompute); we do **not** add it to the JSON schema in
v1. Same posture as character splits.

## 4. Heuristics per reference line

All four lines are computed in the **block-level** helper, where the
best ink-density evidence and the most words are available. The
word-level helper inherits `baseline` and `x_height` from line context
when given, and computes its own `top` / `bottom` from the word ROI.

Common preprocessing: use `BoundingBox._threshold_inverted`
(`bounding_box.py:835`) to get the binarized ROI of the **whole line
block** — same Otsu pipeline as refine and crop. Pad the ROI vertically
by `~ 0.5 * estimated_x_height` (estimated coarsely from
`mean(word.bbox.height)`) so descenders and ascenders don't get
clipped at the edges.

### 4.1 bottom (descender bottom — lowest ink)

For each word: lowest non-zero row in its column slice of the
binarized line ROI. To despeckle, require a horizontal run of at
least `ink_run_min_length_px` (default 2; same default as the
bottom-crop spec section 7) connected ink pixels in that row before
accepting it.

For the line aggregate: not a single bottom — descender words and
non-descender words have genuinely different bottoms. Instead the
line-level helper does **two** computations:

- `line_baseline_y` (slanted, from existing
  `Block.estimate_baseline_from_image`).
- `line_descender_floor_y` = the maximum word-level bottom *among
  words whose text contains a descender character*, projected onto
  the baseline slope. This is the "where descenders actually go" line.

The per-word `bottom` is the word-local lowest ink row. Easy.

### 4.2 baseline

Use the existing `Block.estimate_baseline_from_image` directly when
the line has `>= min_words_for_line_aggregate` words. The slope +
intercept already give us the baseline at any x — for word `w`,
`baseline_y = slope * w.bbox.center_x + intercept`.

When the line has fewer words (small headings, single-word lines),
fall back to the per-word `Word.estimate_baseline_from_image`.

The descender character set used for weighting is upgraded to the
broadened set the bottom-crop spec proposes:

```python
# pd_book_tools/ocr/reference_lines.py
DEFAULT_DESCENDER_CHARS: frozenset[str] = frozenset({
    "g", "j", "p", "q", "y",
    "J", "Q",
    ",", ";",
    "(", ")", "[", "]", "{", "}",
})
```

The single literal lives in this new module and is imported by both
`word.py` and `block.py`, replacing the three current inline copies.
This is the dedup the bottom-crop spec also calls for.

### 4.3 x-height (centerline)

The hardest of the four. The current code does not compute this
correctly — `median_top` in
`split_into_characters_from_whitespace` averages over *all* character
tops including ascenders.

Approach: horizontal projection profile of the binarized line ROI.

1. Compute `ink_per_row = thresh.sum(axis=1)` — a 1D array, length
   `roi_h`, of how many ink pixels are in each row.
2. Smooth with a small (3-row) running mean to suppress single-row
   spikes.
3. Find the **densest band**: the contiguous range of rows whose
   ink-per-row exceeds `band_threshold * max(ink_per_row)`, with
   `band_threshold = 0.5` as a default. The top of that band is the
   x-height line.
4. The bottom of the densest band should land at or near the baseline
   (sanity check; if it disagrees with the regression baseline by more
   than `0.3 * x_height`, downgrade confidence).

Justification: the densest horizontal band of ink in any line of
typeset text is the body of x-height-tall lowercase letters
(`a c e m n o r s u v w x z`). Even on heading lines that are
all-uppercase the densest band collapses to "from baseline to cap-line"
which is what we want for the centerline = x-height = cap-line case.

Per word: the line-level x-height (the y-distance from the line's
baseline up to the line's x-height row) is back-propagated. This is
exactly the case that motivates "line is primary, word is fallback"
— a single word's projection profile is too short to find a robust
densest band.

When line-level confidence is low (e.g. `< 0.4`), fall back to
`x_height = baseline - 0.6 * mean_word_height` as a typographic
default. Mark the result with a low confidence so callers can
choose to ignore.

### 4.4 top-line (cap / ascender top)

Two distinct values:

- `top` (the unconditional highest ink row in the word's ROI, with the
  same `ink_run_min_length_px` despeckle as `bottom`).
- `has_ascender` is `True` when `(x_height - top) >= ascender_min_gap_px`,
  default `ascender_min_gap_px = max(2, 0.2 * (baseline - x_height))`.

For a word like "noun" (no ascender), `top == x_height` (within
tolerance) and `has_ascender == False`. The cap-line and x-height
line collide. Callers who want the cap-line for a word with no
ascender should fall back to the line's cap-line (computed across all
words on the line — the maximum word-level `top` from any word with
`has_ascender == True`).

The line-level cap-line projection works the same way as
`line_descender_floor_y` in 4.1: take the maximum (i.e. highest, lowest
y-value in image space) word-level `top` *among words with
`has_ascender == True`*, projected onto the baseline slope at the
target x. Words on lines with no ascenders at all (rare — most lines
have at least one capital letter) get a `cap_line == x_height` from
the line, with a low-confidence flag.

This **separation** — `top` is per-word ink, `has_ascender` is a flag,
the cap-line is a separate line-level value — is the cleanest way to
handle the "cap-line and x-height collide for some words" problem
without lying to callers about what the geometry is.

If we end up wanting a per-word `cap_line` field on `WordReferenceLines`
(as opposed to "ask the block for it"), an open question is whether
that should be the per-word `top` *when has_ascender* and the
line-aggregate cap-line *when not*. See section 9 question Q-RL-3.

## 5. Tunable parameters and defaults

| Parameter | Default | Notes |
|---|---|---|
| `descender_chars` | `DEFAULT_DESCENDER_CHARS` (4.2) | Module-level constant; per-corpus override possible. |
| `min_words_for_line_aggregate` | `3` | Below this, word-level fallback. Same default as bottom-crop spec section 7. |
| `ink_run_min_length_px` | `2` | Despeckle. Same as bottom-crop spec. |
| `band_threshold` | `0.5` | Fraction of `max(ink_per_row)` used to define the densest band for x-height detection (4.3). |
| `ascender_min_gap_px` | `max(2, 0.2 * (baseline - x_height))` | When `top` is closer to `x_height` than this, the word has no ascender. |
| `descender_min_gap_px` | `max(1, 0.1 * (baseline - x_height))` | Same idea for descenders. |
| `confidence_low_cutoff` | `0.4` | Below this on line-level x-height, fall back to typographic default. |
| `oldstyle_figures_descend` | `False` | Mirror the bottom-crop spec: when True, `3 4 5 7 9` are added to the descender set. Off by default. |

Defaults are decision-oriented; the implementation should expose them
as kwargs on the public functions.

## 6. Confidence and "I don't know"

Match the existing convention: a `confidence` float in `[0, 1]` on
the returned `WordReferenceLines`, computed as the minimum of:

- baseline confidence (from existing baseline estimator, or
  word-level fallback).
- x-height-band confidence: how peaky is the projection profile?
  Quantify as `max_density / mean_density`; low values (flat profile)
  → low confidence.
- aspect-sanity: is `(baseline - x_height) / x_height` in a plausible
  range (typographically usually `0.4` to `0.7`)? If wildly off,
  cap confidence.

When the helper genuinely cannot estimate (no characters split,
ROI empty, image None), it returns `None`, not a low-confidence
`WordReferenceLines`. This matches the existing
`Word.estimate_baseline_from_image` convention of returning `None`
rather than an "I don't know" sentinel dict.

The block-level helper returns `dict[Word, WordReferenceLines | None]`,
mapping `None` for any word it could not estimate. Callers iterate and
check.

No exceptions are raised for inability to estimate. Exceptions are
reserved for programmer errors (e.g. `image is None` while called
through a code path that documents image-required, mirroring
existing crop_bottom error semantics at `word.py:1083-1088`).

## 7. Per-word vs per-line robustness — worked examples

Each example assumes the line has been processed by the block-level
helper.

- **"noun" on a body line.** Has no ascender, no descender. Word-only
  estimator reports `top == x_height` (collide), `bottom == baseline`
  (collide), `has_ascender = False`, `has_descender = False`. Line
  aggregate provides the line's *true* x-height. Caller asking for
  the cap-line for this word should fall back to the line's cap-line.
- **"page" on a body line.** Has descenders (`p`, `g`) and an
  ascender (none — `p` and `g` go down, no letter in "page" goes
  significantly above x-height). Word-only estimator: `top ==
  x_height`, `bottom < baseline`. `has_ascender = False`,
  `has_descender = True`. The bottom-crop tool can use this directly:
  bottom = lowest ink row, no need to consult the line.
- **"The" on a body line.** Has ascender (`T`, `h`), no descender.
  Word-only: `top < x_height`, `bottom == baseline`. `has_ascender
  = True`, `has_descender = False`. Word's `top` is also the
  cap-line for any line that contains "The".
- **"," standalone (single-character word).** All-descender token.
  This is exactly the case that the bottom-crop spec safety rule
  5.4 exists for. Reference-lines API returns `None` — single character
  has no internal layout to derive lines from.
- **"THE END" all-uppercase line.** No descenders, no lowercase. The
  densest-band heuristic produces a band from baseline to cap-line;
  x-height degenerates to cap-line. `has_ascender = True` for every
  word's tallest ink, but the line as a whole has no x-height-only
  letters. Confidence on x-height is reduced.

## 8. Interaction with the bottom-crop spec

The bottom-crop spec's proposed pd-book-tools surface (section 9 of
that spec) currently is:

- `BoundingBox.crop_bottom_to_y(image, target_y, ...)` — pure geometry.
- `Word.crop_bottom_to_baseline(image, baseline_y, has_descender,
  x_height, ...)` — combines flag + baseline + x-height into a
  target_y.
- `Block.crop_word_bottoms_to_baseline(image, descender_chars,
  use_gt_text_first, ...)` — line-level entry; estimates baseline and
  x-height, classifies each word's text against descender_chars,
  calls per-word.
- `Page.crop_word_bottoms_to_baseline(...)` — page-level convenience.

If this reference-lines spec lands first, the bottom-crop spec
collapses cleanly into a thin wrapper:

```python
# Sketch of revised bottom-crop, post reference-lines API:
class Word:
    def crop_bottom_to_baseline(
        self,
        image,
        line_refs: WordReferenceLines | None = None,
        descender_allowance_frac: float = 0.35,
        safety_pad_px: int = 1,
        min_crop_px: int = 2,
    ) -> bool:
        refs = line_refs or self.estimate_reference_lines(image)
        if refs is None:
            return False
        if self._gt_or_ocr_has_descender():
            x_height_px = refs.baseline - refs.x_height
            target_y = refs.baseline + descender_allowance_frac * x_height_px
        else:
            target_y = refs.baseline + safety_pad_px
        # ...snap to nearest ink row above target_y, etc...
```

Specifically:

- `has_descender` (text-conditional flag) stays in the bottom-crop
  spec — the reference-lines API does not classify text, only
  geometry.
- `baseline` and `x_height` no longer need to be computed inside
  `Block.crop_word_bottoms_to_baseline`. They come from
  `Block.estimate_word_reference_lines`.
- The shared `DEFAULT_DESCENDER_CHARS` constant from this spec
  replaces the three current inline copies *and* the bottom-crop
  spec's proposed broadened set (section 2.1 of that spec). Single
  source of truth.
- The new bottom-crop tests for descender / no-descender words
  (bottom-crop spec section 11.1) get cheaper because the
  reference-lines API is independently tested and provides ground
  truth for `baseline` / `x_height` in synthetic-glyph test fixtures.

**Recommendation: the bottom-crop spec should declare an explicit
dependency on this reference-lines API** rather than re-deriving
baseline + x-height locally. Land this API first, then the bottom-crop
tool. Concretely:

- Land `WordReferenceLines`, `Word.estimate_reference_lines`,
  `Block.estimate_word_reference_lines`,
  `Page.estimate_word_reference_lines`, and
  `DEFAULT_DESCENDER_CHARS` in pd-book-tools (one PR).
- Cut a tag (e.g. `v0.10.0`).
- Revise the bottom-crop spec section 9 to consume the new API
  instead of re-deriving baseline / x_height. The surface becomes
  ~30% smaller.
- Implement the bottom-crop tool against the new API. Cut a tag
  (e.g. `v0.11.0`).
- Bump `pd-ocr-labeler`'s `tool.uv.sources` pin to `v0.11.0` and add
  the labeler-side UI plumbing.

Alternative: implement the bottom-crop tool now against the existing
narrow baseline API. Refactor it later when the reference-lines API
lands. This is cheaper in the short term but creates a known refactor
debt and means the bottom-crop tool ships with its own copy of the
descender-set broadening.

The user can decide. Recommendation is the first path (do this
spec's work first) because the bottom-crop spec already calls for
the descender-set dedup as a side-effect, and doing it here once
versus there once means it lands in pd-book-tools either way; the
question is just ordering.

This new spec **does not edit the bottom-crop spec.** It only
cross-references it. The user decides whether to revise that spec.

## 9. Open questions

- **Q-RL-1.** Dataclass vs dict return. Spec recommends a frozen
  dataclass `WordReferenceLines`. The existing
  `estimate_baseline_from_image` returns a `dict[str, float | str]`
  for serialization-friendliness. Are we OK with the new helper
  returning a different shape, or does symmetry matter? Spec
  recommends dataclass — it's a Python-internal value, not a JSON
  shape, and we already have a precedent for dataclasses in the
  package (`Character`).
- **Q-RL-2.** Block-level as primary, word-level as fallback —
  agree, or should we make the word-level the primary public API
  with the block-level positioned as a "convenience aggregator"?
  Spec recommends block-as-primary because the line-aware result is
  meaningfully better and most callers (bottom-crop tool, future
  top-crop tool) operate at line scope.
- **Q-RL-3.** Should `WordReferenceLines` carry a separate `cap_line`
  field, or is `top + has_ascender` sufficient? Spec leans toward
  `top + has_ascender` for simplicity; callers wanting the line's
  cap-line ask the block. Per-word `cap_line` (filled from line
  aggregate when `has_ascender == False`) is fancier but introduces
  a "this field can be either a real measurement or a fallback"
  ambiguity that I'd rather avoid in v1.
- **Q-RL-4.** Coordinate space. Spec recommends page-image pixel-space
  always. An alternative is "match the word's bbox space" (normalized
  if the bbox is normalized). The existing baseline already
  unconditionally returns pixel; matching that is simplest. Confirm.
- **Q-RL-5.** Should `Word.reference_lines` be persisted in
  `to_dict` / `from_dict`? Spec recommends no (runtime cache only).
  Makes JSON schema unchanged. Confirm — alternative is "yes,
  persist, so labelers can pick up cached values without reprocessing
  images on load".
- **Q-RL-6.** When line-aggregation runs and a word's word-level
  estimate disagrees with the line aggregate by more than some
  tolerance, should we report the disagreement (e.g. low confidence
  on that word's `WordReferenceLines`), or silently override? Spec
  recommends "lower the word's confidence", not silently override
  with no signal.
- **Q-RL-7.** Block-level helper signature returns a dict keyed on
  `Word`. Some callers will prefer index-based or
  `(word_index, refs)` tuples. Confirm shape, or make it iterator-y
  (`Iterator[tuple[Word, WordReferenceLines | None]]`).
- **Q-RL-8.** Whether old-style figures descend is corpus-specific;
  the bottom-crop spec also has this question (Q1 of that spec).
  Should they share a single configuration object, or independently
  re-default? Spec recommends share — when a project flips
  `oldstyle_figures_descend = True`, the broader descender set
  applies across both reference-line estimation and bottom-crop.
- **Q-RL-9.** Does the line-level helper need to handle
  non-Latin-script lines? The bottom-crop spec refuses to act on
  non-Latin (its safety rule 5.7). Reference-lines is more general
  (all four lines exist for any horizontally-written script with a
  shared baseline) but the densest-band heuristic for x-height does
  *not* generalize to e.g. Devanagari or Arabic. Spec recommends:
  Latin / Latin-Extended only in v1, log-and-return-None otherwise.
- **Q-RL-10.** Naming. `top` and `bottom` are short but ambiguous
  (top of what? top of the bbox? top of the ink?). Alternatives:
  `ink_top`, `cap_top`, `ascender_top`. Spec uses `top` for
  terseness + a docstring; confirm or rename.

## 10. Decisions requested

The minimum set of decisions needed to start coding:

1. (Section 8) **Do the bottom-crop spec and this spec ship in
   sequence, with the bottom-crop spec depending on this API?**
   Recommendation: yes, this lands first, then bottom-crop is
   implemented against it. Confirm or push back.
2. (Section 3, Q-RL-1) **Dataclass `WordReferenceLines` vs dict
   return.** Recommendation: dataclass. Confirm.
3. (Section 3.2 / 3.3, Q-RL-2) **Block as primary, Word as
   fallback.** Recommendation: yes. Confirm.
4. (Section 3.1, Q-RL-3) **Per-word `cap_line` field, or only
   `top + has_ascender`?** Recommendation: only `top + has_ascender`.
   Confirm.
5. (Section 4.2, Q-RL-8) **Broadened descender set, dedup'd into
   `pd_book_tools/ocr/reference_lines.DEFAULT_DESCENDER_CHARS`.**
   Same set as bottom-crop spec section 2.1. Confirm.
6. (Section 5) **Default tunable values** — happy with the table?
   Particular ones to flag:
   - `band_threshold = 0.5` for x-height detection (4.3).
   - `confidence_low_cutoff = 0.4` for typographic-default fallback.
7. (Section 6, Q-RL-6) **Disagreement handling**: when a word's own
   estimate disagrees with the line aggregate, lower the word's
   confidence vs override silently. Recommendation: lower confidence.

Everything else in section 9 can be answered during implementation
review.

## 11. Testing approach

Same shape as the bottom-crop spec section 11. Synthetic PIL-drawn
glyph fixtures with **known** reference-line positions so tests can
assert exact pixel coordinates for the geometry-only cases, and use
relative-tolerance assertions for the rendering-dependent ones.

Live next to existing baseline tests
(`tests/ocr/test_word.py:1332-1348` and
`tests/ocr/test_block_coverage2.py`).

### 11.1 Unit tests for `Word.estimate_reference_lines`

Helper in the test module: `_render_word(text, x_height_px,
ascender_extra_px, descender_extra_px, baseline_y, font=None) -> ndarray`
that draws the given text on a fixed-size grayscale canvas with
known geometry. Use `PIL.ImageDraw` with the bundled default font
(no font-file dependency, matching the bottom-crop spec section 11
constraint) and use deterministic pixel positions for assertions
where exact comparison matters; use tolerances (±1–2 px) for
rendering-dependent assertions.

Specific cases:

- **"noun" (no ascender, no descender).** Assert `has_ascender ==
  False`, `has_descender == False`, `top == x_height` (within
  tolerance), `bottom == baseline` (within tolerance).
- **"page" (descenders only).** Assert `has_ascender == False`,
  `has_descender == True`, `bottom < baseline`, `top == x_height`.
- **"the" (ascender only).** Assert `has_ascender == True`,
  `has_descender == False`, `top < x_height`, `bottom == baseline`.
- **"Page" (capital + descenders).** Assert both ascender and
  descender flags True. `top` matches the cap-height of the rendered
  `P`.
- **"jury" (multiple descenders).** Assert `has_descender == True`,
  uses the broadened descender set (`y` is in there).
- **"Quito" (capital `Q` descender).** Asserts the broadened set
  includes uppercase `Q`.
- **"," single character.** Returns `None` (cannot estimate from a
  single descender-only character).
- **Empty / whitespace-only word.** Returns `None`.
- **Word with all chars at the same y (synthetic underscore-only).**
  Confidence drops; assert `< confidence_low_cutoff`.
- **Idempotence.** Calling twice with the same image returns
  equal-by-value result.

### 11.2 Unit tests for `Block.estimate_word_reference_lines`

Lives in `tests/ocr/test_block.py` (alongside the existing
`Block.estimate_baseline_from_image` tests).

- **Mixed line: "The page jury yields no result"** — covers
  ascender-only, descender-only, both-flag, and no-flag words on a
  single line. Assert all words receive a baseline that is
  consistent (within ±1 px tilt-tolerance) with the regression
  baseline. Assert the words with no ascender (e.g. "no") inherit a
  cap-line from the line that comes from the words that do have
  ascenders.
- **All-uppercase line ("THE END").** x-height collapses to cap-line,
  confidence is reduced. Assert `confidence < 1.0` and that
  `WordReferenceLines.x_height == top` for every word.
- **All-lowercase line with no ascenders, no descenders ("noun
  rumour")** — synthetic edge case but tests the densest-band
  heuristic on a homogeneous line.
- **Line with `< min_words_for_line_aggregate` words** — falls back
  to per-word path. Assert no slope-fit happens (mock or check
  metadata).
- **Tilted line (rotate fixture ~2°)** — assert per-word baselines
  follow the slope (each word's baseline is at a different absolute
  y) and that word-level `top` / `bottom` are in the correct slope
  relationship.

### 11.3 Property tests

- **Monotonicity per word.** `top <= x_height <= baseline <= bottom`
  always (i.e. top of ink is above the x-height row, which is above
  the baseline, which is above the descender bottom — in image-y
  terms, where higher y = lower visual position).
- **Idempotence at line level.** Running twice produces equal-by-value
  per-word entries.
- **Coordinate-space sanity.** All returned y values are in
  `[bbox.minY, bbox.maxY]` plus a small buffer for ascender /
  descender that extends slightly above / below the bbox. For words
  whose detection bbox is tight, `top >= bbox.minY` and
  `bottom <= bbox.maxY`.

### 11.4 Test data

- Reuse `tests/ocr-test-image.png` for happy-path validation alongside
  synthetic.
- No new font-file dependency. Default PIL font is sufficient for
  geometry assertions; same posture as the bottom-crop spec section
  11.3.
- No new fixtures under `tests/fixtures/layout_regression/` — those
  are heavyweight whole-page fixtures and not needed for unit tests
  here.

### 11.5 What we are NOT testing in v1

- Per-character cap-height precision (sub-pixel font metrics — not
  needed for the use cases driving this spec).
- Non-Latin scripts (Q-RL-9 deferred).
- Cross-Pillow-version pixel parity (same posture as bottom-crop
  spec section 12.5 — assert relative movement, tolerate ±1 px).

## 12. CI integration

No CI changes required. New tests slot into the existing pytest run
via `make test`; no new dependencies. The synthetic PIL glyph helper
introduces no font-file dependency. Coverage targets: match existing
posture (`fail_under = 0`), no new gate.

## 13. Out of scope (v1)

- Sub-pixel font metrics extraction.
- Non-Latin scripts.
- Persisting `WordReferenceLines` in `to_dict` / `from_dict` (Q-RL-5).
- Page-level reference-lines visualization (could be a separate
  `pd_book_tools.layout.visualize` enhancement; not needed for the
  immediate use cases).
- Using DocTR's internal text-line geometry (we deliberately stay
  on raw pixels so this works for any OCR engine, not just DocTR).
