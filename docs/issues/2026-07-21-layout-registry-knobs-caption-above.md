---
Status: retired
Owner: CT
Created: 2026-07-21
Last verified: 2026-09-19
Kind: issue
Level: I2
---

# PP-DocLayout registry rejects security kwargs; captions ignore above side

## Agent Index

- **Kind:** issue
- **Status:** retired
- **Level:** I2
- **Last verified:** 2026-09-19
- **Resolution:** Resolved (2026-09-19)
- **Severity:** Medium — adapter knobs half-exposed; dual-caption gap
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** changing layout registry, PP-DocLayout adapter, or caption association
- **Search terms:** get_detector trust_remote_checkpoint, associate_captions above, caption_for_figure
- **Relates to:** [plan C7 / S8b](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** C7 / S8b

## Summary

`get_detector("pp-doclayout-plus-l")` rejects extra kwargs; `trust_remote_checkpoint`, `local_files_only`, `revision` cannot pass through registry. `caption_for_figure(..., above=True)` exists but `associate_captions` uses below-only.

## Impact

- Air-gapped / trusted-remote / revision pins need bypass of registry.
- Dual-caption frontispieces miss above captions.

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

- [plan C7 / S8b](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)

### 1. Decisive observation

```bash
rg -n 'trust_remote|local_files_only|extra kwargs|unexpected' pdomain_book_tools/layout/registry.py | head -20
rg -n 'above|associate_captions|caption_for_figure' pdomain_book_tools/ocr/layout_aware_reorg.py pdomain_book_tools/layout/geometry.py | head -30
```

Registry rejects extra kwargs; adapter supports knobs; captions below-only.

## Root-cause hypotheses

1. **(Most likely) Registry built for simple keys before security knobs** — Likely.

## Defects to fix

1. **Registry** — allow hashable security/revision kwargs or document construct+register only.
2. **Captions** — wire above or dual-side search for frontispieces.

## Next steps

1. Decide registry vs document-only (cheap doc path valid).
2. Add dual-side caption unit case.

## What is NOT broken

- Registry caching and on_error soft-build behavior are solid.
- Below-only captions still work for common layouts.

## Resolution

**Resolved (2026-09-19).** Both defects confirmed and fixed on branch
`fix/layout-kwargs-and-captions`:

1. **Registry.** `get_detector`'s cache-key branch and `_build`'s
   `"pp-doclayout-plus-l"` branch each gained handling for the adapter's
   security/provenance kwargs (`revision`, `local_files_only`,
   `trust_remote_checkpoint`), mirroring the existing `"contour"` /
   user-registered-detector pattern: known kwargs are filtered, forwarded to
   `PPDocLayoutPlusLDetector`, and fold into the memoisation cache key
   (distinct revisions/trust settings now memoise distinct instances);
   unrecognised kwargs still raise `TypeError` rather than silently
   passing through.
2. **Captions.** `associate_captions` now calls
   `caption_for_figure(..., above=True)`, so a caption printed above a
   figure is discovered. `caption_for_figure` already searches both
   sides and keeps whichever gap is smaller when both are present; the
   surrounding cross-figure dedup logic in `associate_captions`
   previously assumed below-only placement (its own gap computation
   floored an above-side gap to 0, biasing the "closest figure wins"
   tie-break). A new `_vertical_region_gap` helper computes the true
   signed-correct distance for either side, so when a caption sits
   between two figures, the figure with the smaller true gap wins and
   the other gets no caption — never a duplicate.

Failing-first tests added and confirmed red before the fix, green after:
`tests/layout/test_detector.py::TestRegistry::test_pp_doclayout_security_kwargs_forwarded`,
`test_pp_doclayout_unknown_kwarg_rejected`, and
`tests/layout/test_layout_aware_reorg.py::TestAssociateCaptions::test_caption_above_figure_attached`,
`test_caption_between_two_figures_claimed_by_closer_one`.

Checked the "worth knowing" lead: the `frontispiece-on-deck-dual-caption`
strict xfail in `tests/ocr/test_reorganize_page_utils_grouping.py` did
**not** flip to passing — it remains xfailed for its documented, unrelated
reason (figure-internal char-noise from the engraving, not caption
association). No xfail was removed.

Full gate: `make ci AI=1` passed (pre-commit, lint, format, typecheck,
2954 passed / 5 xfailed, build, layout-fork-info).
