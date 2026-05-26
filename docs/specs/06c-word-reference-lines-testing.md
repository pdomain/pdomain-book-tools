# Spec: Word / Line Reference Lines — Testing, Decisions, and Interactions

> **Status**: Active
> **Last updated**: 2026-05-21
> **Split from**: [06-word-reference-lines.md](../archive/specs/06-word-reference-lines.md)

Bottom-crop spec interaction, open questions (Q-RL-1 through Q-RL-10),
decisions requested, testing approach, CI integration, and out-of-scope
items for the four reference lines feature.
This is part 3 of a three-part split of the original
`06-word-reference-lines.md` spec (914 lines, exceeded the 800-line cap).

- Part 1: [06a-word-reference-lines-audit.md](06a-word-reference-lines-audit.md) — Audit + gap analysis
- Part 2: [06b-word-reference-lines-api.md](06b-word-reference-lines-api.md) — API surface, heuristics, parameters, confidence
- Part 3 (this file): Bottom-crop interaction, open questions, decisions, testing, CI, out of scope

---

## TL;DR

Land the reference-lines API before the bottom-crop tool so the
bottom-crop spec can slim down to a thin wrapper. Synthetic PIL-drawn
fixtures let tests assert exact pixel coordinates without font-file
dependencies. Ten open questions (Q-RL-1 through Q-RL-10) are listed
here; the minimum set needed to start coding is in section 10.

## Context

See [06a-word-reference-lines-audit.md](06a-word-reference-lines-audit.md)
for the motivation and gap analysis.
See [06b-word-reference-lines-api.md](06b-word-reference-lines-api.md)
for the API surface and heuristics.

## Constraints

- Testing must not introduce font-file dependencies (use default PIL font).
- No new fixtures under `tests/fixtures/layout_regression/` — those are
  heavyweight whole-page fixtures and not needed for unit tests here.
- No new CI infrastructure required; new tests slot into existing pytest run.

## Decision

The bottom-crop spec should declare an explicit dependency on this
reference-lines API rather than re-deriving baseline and x-height locally.
Land this API first, then the bottom-crop tool. See section 8.

## 8. Interaction with the bottom-crop spec

The bottom-crop spec's proposed pdomain-book-tools surface (section 9 of
that spec) currently is:

- `BoundingBox.crop_bottom_to_y(image, target_y, ...)` — pure geometry.
- `Word.crop_bottom_to_baseline(image, baseline_y, has_descender,
  x_height, ...)` — combines flag plus baseline plus x-height into a
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
  replaces the three current inline copies _and_ the bottom-crop
  spec's proposed broadened set (section 2.1 of that spec). Single
  source of truth.
- The new bottom-crop tests for descender / no-descender words
  (bottom-crop spec section 11.1) get cheaper because the
  reference-lines API is independently tested and provides ground
  truth for `baseline` / `x_height` in synthetic-glyph test fixtures.

**Recommendation: the bottom-crop spec should declare an explicit
dependency on this reference-lines API** rather than re-deriving
baseline and x-height locally. Land this API first, then the bottom-crop
tool. Concretely:

- Land `WordReferenceLines`, `Word.estimate_reference_lines`,
  `Block.estimate_word_reference_lines`,
  `Page.estimate_word_reference_lines`, and
  `DEFAULT_DESCENDER_CHARS` in pdomain-book-tools (one PR).
- Cut a tag (e.g. `v0.10.0`).
- Revise the bottom-crop spec section 9 to consume the new API
  instead of re-deriving baseline / x_height. The surface becomes
  approximately 30% smaller.
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
versus there once means it lands in pdomain-book-tools either way; the
question is just ordering.

This spec **does not edit the bottom-crop spec.** It only
cross-references it. The user decides whether to revise that spec.

## 9. Open questions

- **Q-RL-1.** Dataclass vs dict return. Spec recommends a frozen
  dataclass `WordReferenceLines`. The existing
  `estimate_baseline_from_image` returns a `dict[str, float | str]`
  for serialization-friendliness. Are we OK with the new helper
  returning a different shape, or does symmetry matter? Spec
  recommends dataclass — it is a Python-internal value, not a JSON
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
  ambiguity that should be avoided in v1.
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
  _not_ generalize to e.g. Devanagari or Arabic. Spec recommends:
  Latin / Latin-Extended only in v1, log-and-return-None otherwise.
- **Q-RL-10.** Naming. `top` and `bottom` are short but ambiguous
  (top of what? top of the bbox? top of the ink?). Alternatives:
  `ink_top`, `cap_top`, `ascender_top`. Spec uses `top` for
  terseness plus a docstring; confirm or rename.

## 10. Decisions requested

The minimum set of decisions needed to start coding:

1. (Section 8) **Do the bottom-crop spec and this spec ship in
   sequence, with the bottom-crop spec depending on this API?**
   Recommendation: yes, this lands first, then bottom-crop is
   implemented against it. Confirm or push back.
2. (Section 3 of [06b](06b-word-reference-lines-api.md), Q-RL-1)
   **Dataclass `WordReferenceLines` vs dict return.**
   Recommendation: dataclass. Confirm.
3. (Section 3.2/3.3 of [06b](06b-word-reference-lines-api.md), Q-RL-2)
   **Block as primary, Word as fallback.** Recommendation: yes. Confirm.
4. (Section 3.1 of [06b](06b-word-reference-lines-api.md), Q-RL-3)
   **Per-word `cap_line` field, or only `top + has_ascender`?**
   Recommendation: only `top + has_ascender`. Confirm.
5. (Section 4.2 of [06b](06b-word-reference-lines-api.md), Q-RL-8)
   **Broadened descender set, dedup'd into
   `pdomain_book_tools/ocr/reference_lines.DEFAULT_DESCENDER_CHARS`.**
   Same set as bottom-crop spec section 2.1. Confirm.
6. (Section 5 of [06b](06b-word-reference-lines-api.md))
   **Default tunable values** — happy with the table?
   Particular ones to flag:
   - `band_threshold = 0.5` for x-height detection (4.3 in [06b](06b-word-reference-lines-api.md)).
   - `confidence_low_cutoff = 0.4` for typographic-default fallback.
7. (Section 6 of [06b](06b-word-reference-lines-api.md), Q-RL-6)
   **Disagreement handling**: when a word's own estimate disagrees
   with the line aggregate, lower the word's confidence vs override
   silently. Recommendation: lower confidence.

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
where exact comparison matters; use tolerances (±1-2 px) for
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
  `pdomain_book_tools.layout.visualize` enhancement; not needed for the
  immediate use cases).
- Using DocTR's internal text-line geometry (deliberately stay
  on raw pixels so this works for any OCR engine, not just DocTR).

## Contract / Acceptance

- Ten open questions (Q-RL-1 through Q-RL-10) are documented.
- Seven minimum decisions for coding start are listed in section 10.
- Bottom-crop interaction analysis in section 8 is complete.
- Testing approach covers: word-level unit tests (11.1), block-level
  unit tests (11.2), property tests (11.3), test-data constraints
  (11.4), and v1 exclusions (11.5).
- `make ci` passes with no new test gates or CI infrastructure.

## Trade-offs considered

- **Land this before bottom-crop vs concurrently.** Landing first
  avoids duplicating descender-set work. See section 8 for the
  full analysis.
- **Property testing vs example-based.** Both used; property tests
  catch monotonicity violations that example-based tests miss on
  novel inputs.

## Consequences

- The bottom-crop spec implementation will be lighter if this spec
  lands first.
- Q-RL-1 through Q-RL-10 must be answered before implementation
  review can close.

## Open questions

All open questions for this feature are listed in section 9 above
(Q-RL-1 through Q-RL-10).

## References

- [06a-word-reference-lines-audit.md](06a-word-reference-lines-audit.md) — Audit + gap analysis
- [06b-word-reference-lines-api.md](06b-word-reference-lines-api.md) — API surface, heuristics, parameters
- [06-word-reference-lines.md](../archive/specs/06-word-reference-lines.md) — Parent forwarding stub (archived)
- `tests/ocr/test_word.py:1332-1348` — existing baseline tests
- `tests/ocr/test_block_coverage2.py` — existing block baseline tests
