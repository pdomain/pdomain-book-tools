---
Status: active
Owner: CT
Created: 2026-05-21
Last verified: 2026-07-13
Kind: spec
---

# Spec: Word / Line Reference Lines — API Surface and Heuristics

> **Status**: Active
> **Last updated**: 2026-05-21
> **Split from**: the original spec, preserved in Git history

Recommended API surface, per-line heuristics, tunable parameters,
confidence model, and worked examples for the four reference lines
(top, x-height, baseline, bottom).
This is part 2 of a three-part split of the original
`06-word-reference-lines.md` spec (914 lines, exceeded the 800-line cap).

- Part 1: [06a-word-reference-lines-audit.md](06a-word-reference-lines-audit.md) — Audit + gap analysis
- Part 2 (this file): API surface, heuristics, parameters, confidence
- Part 3: [06c-word-reference-lines-testing.md](06c-word-reference-lines-testing.md) — Bottom-crop interaction, open questions, decisions, testing, CI, out of scope

---

## TL;DR

New `reference_lines.py` module exposes `WordReferenceLines` (frozen
dataclass), `Word.estimate_reference_lines`, and
`Block.estimate_word_reference_lines`. Block-level is primary
(line-aggregate corrects short-word ambiguity and tilt). A shared
`DEFAULT_DESCENDER_CHARS` constant replaces three inline copies.

## Context

See [06a-word-reference-lines-audit.md](06a-word-reference-lines-audit.md)
for the full motivation. In short: only the baseline is partially
implemented; top-line, x-height, and descender bottom are missing.
This part specifies how to add them.

## Constraints

- `WordReferenceLines` must be a frozen dataclass (not a dict).
- All y-values returned in page-image pixel space (consistent with the
  existing `coordinate_space: "pixel"` convention).
- `DEFAULT_DESCENDER_CHARS` lives in the new module; `word.py` and
  `block.py` import it from there.
- Backward compatibility: existing `word.baseline` dict attribute kept
  and populated from the new API result.

## Decision

Two-tier API. Block (line) level is the primary, robust surface;
Word level is the best-effort fallback. See section 3 below.

## 3. Recommended primary surface

Two-tier API. **Block (line) level is the primary, robust surface;
Word level is the best-effort fallback.** Reasoning is in 3.3 below.

### 3.1 Block-level: WordReferenceLines per word, computed line-aware

```python
# pdomain_book_tools/ocr/reference_lines.py  (new module)

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

    confidence: float         # [0, 1] — see section 6
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
themselves. We do not expose two variants — one truth, plus a
documented convention.

### 3.2 Block / Page entry points

```python
# pdomain_book_tools/ocr/block.py

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

# pdomain_book_tools/ocr/page.py

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
# pdomain_book_tools/ocr/word.py

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
  recoverable for the _line_, then back-propagates the line's
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
  on the block estimator it is "do all line characters agree to the
  fitted line". The latter is meaningfully more useful.

The word-level entry point still exists so that callers can:

- Estimate when only a word plus image is available (no line context).
- Test the word-only path in isolation.
- Be called _by_ the block-level entry point as the per-word kernel.

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
`reference_lines` attribute is a runtime-only cache (it is image-derived
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
`mean(word.bbox.height)`) so descenders and ascenders are not clipped
at the edges.

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
- `line_descender_floor_y` = the maximum word-level bottom _among
  words whose text contains a descender character_, projected onto
  the baseline slope. This is the "where descenders actually go" line.

The per-word `bottom` is the word-local lowest ink row. Easy.

### 4.2 baseline

Use the existing `Block.estimate_baseline_from_image` directly when
the line has `>= min_words_for_line_aggregate` words. The slope plus
intercept already give us the baseline at any x — for word `w`,
`baseline_y = slope * w.bbox.center_x + intercept`.

When the line has fewer words (small headings, single-word lines),
fall back to the per-word `Word.estimate_baseline_from_image`.

The descender character set used for weighting is upgraded to the
broadened set the bottom-crop spec proposes:

```python
# pdomain_book_tools/ocr/reference_lines.py
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
`split_into_characters_from_whitespace` averages over _all_ character
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
y-value in image space) word-level `top` _among words with
`has_ascender == True`_, projected onto the baseline slope at the
target x. Words on lines with no ascenders at all (rare — most lines
have at least one capital letter) get a `cap_line == x_height` from
the line, with a low-confidence flag.

This **separation** — `top` is per-word ink, `has_ascender` is a flag,
the cap-line is a separate line-level value — is the cleanest way to
handle the "cap-line and x-height collide for some words" problem
without lying to callers about what the geometry is.

If we end up wanting a per-word `cap_line` field on `WordReferenceLines`
(as opposed to "ask the block for it"), an open question is whether
that should be the per-word `top` _when has_ascender_ and the
line-aggregate cap-line _when not_. See Q-RL-3 in
[06c-word-reference-lines-testing.md](06c-word-reference-lines-testing.md).

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
  produce low confidence.
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
  aggregate provides the line's _true_ x-height. Caller asking for
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

## Contract / Acceptance

- `WordReferenceLines` is a frozen dataclass with fields `top`,
  `x_height`, `baseline`, `bottom`, `has_ascender`, `has_descender`,
  `confidence`.
- `Word.estimate_reference_lines` returns `WordReferenceLines | None`.
- `Block.estimate_word_reference_lines` returns
  `dict[Word, WordReferenceLines | None]`.
- `Page.estimate_word_reference_lines` returns same shape, aggregating
  all line blocks.
- `DEFAULT_DESCENDER_CHARS` exported from `reference_lines.py` and
  imported by `word.py` and `block.py` (no more inline copies).
- Existing `word.baseline` dict is still populated for backward compat.
- `reference_lines` attribute NOT serialized in `to_dict` / `from_dict`.

## Trade-offs considered

- **Dataclass vs dict return.** Dataclass chosen for type safety
  and IDE support. Existing dict-return helpers are kept for backward
  compat; the new surface is strictly additive. See Q-RL-1 in
  [06c-word-reference-lines-testing.md](06c-word-reference-lines-testing.md).
- **Block-as-primary vs word-as-primary.** Block wins because
  line-aggregate provides ground truth for short words. See 3.3 above.

## Consequences

- Adds `pdomain_book_tools/ocr/reference_lines.py` (new module).
- `word.py` and `block.py` import `DEFAULT_DESCENDER_CHARS` from there;
  three inline set literals are removed.
- `Word` gains a `reference_lines` attribute (not serialized).
- `Block` and `Page` each gain an `estimate_word_reference_lines` method.

## Open questions

See [06c-word-reference-lines-testing.md](06c-word-reference-lines-testing.md)
for the full list (Q-RL-1 through Q-RL-10).

## References

- [06a-word-reference-lines-audit.md](06a-word-reference-lines-audit.md) — Audit + gap analysis
- [06c-word-reference-lines-testing.md](06c-word-reference-lines-testing.md) — Testing, open questions, decisions
- Original parent spec — superseded by 06a, 06b, and 06c; preserved in Git history
- `pdomain_book_tools/ocr/reference_lines.py` — new module (to be created)
- `pdomain_book_tools/ocr/word.py` — `estimate_reference_lines`, `estimate_baseline_from_image`
- `pdomain_book_tools/ocr/block.py` — `estimate_word_reference_lines`

## Adversarial Review

- **Stage:** Migration/design review dated 2026-07-13; no pre-existing live red-team exercise is claimed.
- **Source:** Full spec compared with current Word, Block, Page, baseline implementations, and the absence of `ocr/reference_lines.py` and reference-line tests.
- **Accepted findings:** The proposal is additive and preserves existing baseline methods, but none of its new API exists yet. Fold in an explicit unimplemented status for every proposed symbol, require executable acceptance tests, and resolve the return-key semantics before implementation. The dataclass shape, pixel coordinate contract, persistence policy, heuristic defaults, and Word-keyed mapping remain `needs_owner_decision`.
- **Disposition:** Accepted corrections and unresolved ideas are preserved in `docs/context/intent-map.md` as deferred work or owner decisions; the source body remains unchanged pending its next evidence-backed revision.
- **Residual risks:** Mutable-object key semantics, heuristic brittleness, non-Latin behavior, cache invalidation, and confidence calibration are not resolved by current evidence.
