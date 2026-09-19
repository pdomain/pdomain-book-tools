---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# five strict-xfail figure-noise baselines leave product gaps green in CI

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** High — false-green until closed or dated accept
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** touching KNOWN_FAILING_BASELINES or figure-noise drop policy
- **Search terms:** KNOWN_FAILING_BASELINES, xfail, figure-noise, layout_regression
- **Relates to:** [plan B3 / S5](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** B3 / S5

## Summary

`KNOWN_FAILING_BASELINES` lists five plates/frontispieces with `pytest.mark.xfail(..., strict=True)`. Desired baselines require figure-noise drops the product does not meet. CI stays green by design while product is wrong vs baseline.

## Impact

- Known wrong reading-order/text cases stay open indefinitely.
- XPASS only if someone accidentally meets baseline; no pressure to fix.

## Environment / versions

```text
pdomain-book-tools 0.21.x-dev @ a7bff12
Repo: pdomain/pdomain-book-tools (master)
Found by: 2026-07-21 deep code review (9 specialists + 3 adversarial challenges)
Plan: docs/plans/2026-07-21-continued-work-from-deep-review.md
Findings: docs/research/2026-07-21-deep-code-review-findings.md
```

## Evidence

Related governed docs:

- [plan B3 / S5](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)

### 1. Decisive observation

```bash
rg -n 'KNOWN_FAILING_BASELINES|xfail' tests/ocr/test_reorganize_page_utils_grouping.py | head -30
```

Five cases, `pytest.mark.xfail(..., strict=True)` (~227–272). Architecture
residual + intent-map already schedule fix or dated accept (not “done forever”).

## What the five xfails are actually hiding (investigated 2026-09-19)

**The xfail reasons misdescribe the failures.** All five say "figure-internal
noise that should be dropped". None of the five diffs shows a noise-dropping
failure. Noise dropping works. Every one is a reading-order and line-structure
bug: the right words, correctly associated with the right region, in the wrong
order.

It is one defect family, not five, and what a reader would see is worse than
the reasons suggest:

- `figures-side-by-side-with-captions`: both figure captions are correctly
  lifted out of the body flow and then reappear at the end of the page as word
  salad, for example `now pallida, Contrastl tury FiG. copy lost, from
  73.—Aristolochia Fig. of by a 79. a sixth-cen- Crateuas. drawing,`. A real
  caption becomes unreadable.
- `frontispiece-on-deck-dual-caption`: two caption lines are glued into one
  with a noise glyph stitched into the middle, `On Deck. iFronlispicce.`
- `plate-rio-harbour-photo`: the corner annotation prints before the caption it
  sits below and to the right of.
- `plate-service-on-board` and `plate-ii-celestial-influences`: short caption,
  credit and heading lines swap position, and blank lines appear.

Two confirmed causes and one shared trigger:

1. **A multi-line caption is packed into one LINE block.** `emit_caption_block`
   in `ocr/layout_aware_reorg.py` and `_build_band_block` in
   `ocr/reorganize_page_utils.py` both collect a caption's words, which may
   span several printed lines, into a single `Block` of category LINE.
   `Block.__init__` sorts a words-child block strictly by x, which interleaves
   the lines. Verified directly: `words_inside()` returns the words in correct
   order, and the corruption appears only after the wrap.
2. **Pixels compared against a normalised coordinate.**
   `route_sidenote_reading_order` computes a midline from `page.width` in
   pixels and compares it against a block centre in normalised space, so every
   sidenote-tagged block reads as left of the midline whatever its real side,
   and is pinned to the top of the page.
3. **The trigger** is `classify_and_paragraphize_blocks`, a geometry-only
   heuristic that misclassifies short isolated caption and credit fragments on
   plate pages, which have no body column to compare against, as sidenote,
   header or footer. That is what routes them into the two bugs above instead
   of ordinary paragraph placement.

One change across those three functions should close all five together. Cases
3 and 5's exact reordering step needs one more trace: the real footer-band
extractor reports no footer lines for them, so the reordering happens later in
the footer-role assembly.

These are the only `strict=True` xfails in the repository. All five still fail
as before, so none is stale.

## Root-cause hypotheses

1. **(Most likely) Desired baselines encode aspirational policy not yet implemented** — xfail reasons describe orphan noise that should be dropped.

## Defects to fix

1. **Per-case close** — fix behavior to match baseline, or revise baseline with dated owner accept and drop xfail.
2. **Empty KNOWN_FAILING_BASELINES** — or only dated accepts with issue ids remain.

## Next steps

1. Inventory the five case names and decide fix vs accept each.
2. Prefer fixing after B1 if layout drop is required for the desired text.

## What is NOT broken

- Non-xfail corpus cases still enforce baselines.
- strict=True is intentional for XPASS detection; the issue is leaving them forever.

### Progress (2026-07-21 B1)

Layout harness now passes `layout=`; the five KNOWN_FAILING_BASELINES cases still xfail under drop=True (residual figure-noise gaps). No dated owner accept yet — still open for fix-or-accept (B3).

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
