---
Status: active
Owner: CT
Created: 2026-05-10
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Decoration-vs-figure post-classification heuristic

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Unassigned — the export has no severity label
- **Affected version:** Not stated in the export
- **Read when:** planning or implementing decoration-vs-figure post-classification heuristic
- **Search terms:** decoration-vs-figure, post-classification, heuristic
- **Relates to:** [reorganize-page-pipeline](../architecture/reorganize-page-pipeline.md)

## Summary

Add `postclassify_decoration(layout, page) -> PageLayout` in
`pd_book_tools/layout/geometry.py`. Run it as a late pass in
`Page.reorganize_page`, after `tag_words_with_layout`. The heuristic should
reclassify a `figure` region as `decoration` when all three conditions hold:

- It is small (<5% of page area).
- It is near the top or bottom.
- It contains no detected text words.

PP-DocLayout has no `decoration` class. The adapter currently maps
`seal -> RegionType.decoration` and falls back from `image` to `figure` for
ornamental woodcuts such as chapter headpieces and fleurons. The heuristic
would help the downstream illustration extractor assign `type=decoration` to
`i_<stem>_NN.png` filenames.

This work is out of scope until the layout fine-tune lands. Once the model has
a first-class `decoration` head, the heuristic becomes a fallback instead of
the primary classifier. The issue cites `docs/ROADMAP.md` under “Open - layout
consumption” and `docs/specs/03-reorganize-pipeline.md`.

Repository evidence does not verify the acceptance criteria, so this record remains open.

## Impact

- The requested behavior remains unavailable or undecided.
- The original request defines the scope and downstream effects.

## Environment / versions

The export states no operating system, package version, command, or environment variables.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/2>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABBx2fYg`
- **Issue number:** 2
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-2.json`
- **Raw SHA-256:** `89797c004a6050cfd7ad20535f5c906ba63d007c691fa5ce7fa50b18cca4cc8e`
- **Migration cutover:** `dfadf9c` — governed content batch for GitHub issues #2–#7 and #45–#48.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-10T01:51:46Z`
- **Updated:** `2026-05-11T11:36:58Z`
- **Closed:** Not closed in the export
- **Labels:** `effort:M`, `model:sonnet`, `model-effort:medium`, `kind:feature-request`, `triage:approved`, `triage:needs-spec`
- **Assignees:** None
- **Milestone:** None
- **Issue type:** None
- **Projects:** None
- **Parent issue:** None
- **Sub-issues:** None

## Evidence

The immutable raw export and its digest preserve the original body. The classified durable facts are:

- Add `postclassify_decoration(layout, page) -> PageLayout` in `pd_book_tools/layout/geometry.py`, run as a late pass in `Page.reorganize_page` after `tag_words_with_layout`. Heuristic: a `figure` region that is small (<5% of page area), positioned near top or bottom, and contains no detected text words should be reclassified as `decoration`.
- PP-DocLayout has no `decoration` class. The adapter maps `seal` to
  `RegionType.decoration` and falls back from `image` to `figure` for ornamental
  woodcuts, including chapter headpieces and fleurons.
- The downstream illustration extractor uses the classification to choose
  `type=decoration` for `i_<stem>_NN.png` filenames.
- The work is out of scope until the layout fine-tune lands. A future model
  `decoration` head would make this heuristic a fallback rather than the primary
  classifier.
- The body cites `docs/ROADMAP.md` (“Open - layout consumption”) and
  `docs/specs/03-reorganize-pipeline.md`.
- Acceptance criteria: implement `postclassify_decoration` in
  `layout/geometry.py` with the area/position/no-text heuristic; wire it into
  `Page.reorganize_page` after `tag_words_with_layout`; add at least one fixture
  in which a small top-of-page figure with no text is reclassified as
  `decoration`; and leave existing reorganize fixtures unchanged, or review and
  accept their diffs.
- Recorded issue disposition/linkage: Triage decision: approved + needs-spec. Spec child issue: #45. Run `/spec-from-issue 45` to produce the design spec.

The issue text is historical data, not repository instructions.

## Root-cause hypotheses

1. **No root cause is established.** The export records a feature, tuning, or design request.
2. **Current repository evidence may narrow the design.** The cited paths do not prove completion.

Further evidence is required before implementation.

## Defects to fix

1. Add `postclassify_decoration(layout, page) -> PageLayout` in
   `pd_book_tools/layout/geometry.py`. Run it late in `Page.reorganize_page`,
   after `tag_words_with_layout`. Reclassify a `figure` as `decoration` only
   when it is small (<5% of page area), near the top or bottom, and contains no
   detected text words.
2. Meet the acceptance criteria: implement the area/position/no-text heuristic
   in `layout/geometry.py`; wire it into `Page.reorganize_page` after
   `tag_words_with_layout`; add at least one fixture for a small top-of-page
   figure with no text; and leave existing reorganize fixtures unchanged, or
   review and accept their diffs.
3. Recorded issue disposition/linkage: Triage decision: approved + needs-spec. Spec child issue: #45. Run `/spec-from-issue 45` to produce the design spec.

## Next steps

1. `postclassify_decoration` implemented in `layout/geometry.py` with the area/position/no-text heuristic
2. Wired into `Page.reorganize_page` after `tag_words_with_layout`
3. At least one fixture exercises a small top-of-page no-text figure being reclassified to `decoration`
4. Existing reorganize fixtures unchanged (or diffs reviewed and accepted)

## What is NOT broken (to scope the fix)

- The export rules out no adjacent behavior beyond its explicit scope.

## Relationships and material comments

- Triage links this request to spec-child issue #45.
- 2026-05-11T11:36:58Z — `ConcaveTrillion`: Triage decision: approved + needs-spec. Spec child issue: #45. Run `/spec-from-issue 45` to produce the design spec. ([comment](https://github.com/pdomain/pdomain-book-tools/issues/2#issuecomment-4420311733))
- Disposable chatter: 1 duplicate child-fork comment adds no durable fact.

## Repository evidence

- `docs/plans/roadmap.md` records the missing PP-DocLayout `decoration` class,
  current adapter mappings, proposed heuristic and call site, downstream
  filename effect, and fine-tune dependency.
- `docs/architecture/reorganize-page-pipeline.md` verifies the present pipeline
  order and that layout hints influence illustration and decoration handling;
  it does not verify the requested post-classifier.

## Remaining work

- Acceptance criteria remain unverified against an implementation; preserve as open work.

## Resolution

_Open._ Retire this record only after evidence verifies the criteria or records an owner disposition.
