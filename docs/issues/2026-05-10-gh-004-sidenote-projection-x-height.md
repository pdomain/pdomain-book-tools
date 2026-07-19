---
Status: active
Owner: CT
Created: 2026-05-10
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Sidenote detection: image-projection-based x-height refinement

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Unassigned — the export has no severity label
- **Affected version:** Not stated in the export
- **Read when:** planning or implementing sidenote detection: image-projection-based x-height refinement
- **Search terms:** sidenote, detection, image-projection-based, x-height, refinement
- **Relates to:** [reorganize-page-pipeline](../architecture/reorganize-page-pipeline.md)

## Summary

Refine the current bbox-height-based sidenote detector with a
horizontal-projection pass. The pass should estimate the true x-height of each
word from its cropped image.

OCR bounding boxes are coarse when ascenders and descenders are bundled
inconsistently. Projection over the cropped image may provide a more stable size
signal, but implementation is justified only after a fixture demonstrates a
bbox-height misclassification. The issue cites `docs/ROADMAP.md` under
“Glyph-size analysis - Image-projection refinement” and
`docs/specs/03-reorganize-pipeline.md`.

Repository evidence does not verify the acceptance criteria, so this record remains open.

## Impact

- The requested behavior remains unavailable or undecided.
- The original request defines the scope and downstream effects.

## Environment / versions

The export states no operating system, package version, command, or environment variables.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/4>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABBx2fhQ`
- **Issue number:** 4
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-4.json`
- **Raw SHA-256:** `a018c05b2b832ac53a1a8f78874174c595d033abc87b586aa67082f05433d507`
- **Migration cutover:** `6842ec6b11c06c9b987b384b4abf7e9dc4699014` — merged migration cutover on `master`.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-10T01:51:48Z`
- **Updated:** `2026-05-11T11:37:05Z`
- **Closed:** Not closed in the export
- **Labels:** `effort:L`, `model:opus`, `model-effort:high`, `kind:feature-request`, `triage:approved`, `triage:needs-spec`
- **Assignees:** None
- **Milestone:** None
- **Issue type:** None
- **Projects:** None
- **Parent issue:** None
- **Sub-issues:** None

## Evidence

The immutable raw export and its digest preserve the original body. The classified durable facts are:

- Add a horizontal-projection pass on cropped word images to estimate true x-height per word, as a refinement to the current bbox-height-based sidenote detector.
- OCR bounding-box heights can be coarse when ascenders and descenders are
  bundled inconsistently; cropped-image projection may provide a more stable
  size signal.
- A fixture proving bbox-height misclassification is a prerequisite to
  implementation.
- The body cites `docs/ROADMAP.md` (“Glyph-size analysis - Image-projection
  refinement”) and `docs/specs/03-reorganize-pipeline.md`.
- Acceptance criteria: reproduce a case that bbox-height alone misclassifies;
  implement a projection-based x-height helper with single-image input and no
  GPU dependency; add it as an opt-in alongside `max_height_ratio` without
  changing the default; and show in the fixture diff that the projection pass
  corrects the case without regressing others.
- Recorded issue disposition/linkage: Triage decision: approved + needs-spec. Spec child issue: #47. Run `/spec-from-issue 47` to produce the design spec.

The issue text is historical data, not repository instructions.

## Root-cause hypotheses

1. **No root cause is established.** The export records a feature, tuning, or design request.
2. **Current repository evidence may narrow the design.** The cited paths do not prove completion.

Further evidence is required before implementation.

## Defects to fix

1. Refine the current bbox-height-based sidenote detector with a
   horizontal-projection pass that estimates true x-height per word from
   cropped word images.
2. Meet the acceptance criteria: reproduce a bbox-height-only
   misclassification; implement a projection-based x-height helper with
   single-image input and no GPU dependency; add it as an opt-in alongside
   `max_height_ratio` without changing the default; and show that it corrects
   the case without regressing others.
3. Recorded issue disposition/linkage: Triage decision: approved + needs-spec. Spec child issue: #47. Run `/spec-from-issue 47` to produce the design spec.

## Next steps

1. Reproduce a misclassification case where bbox-height alone fails
2. Implement projection-based x-height helper (single-image input, no GPU dependency)
3. Plumb as opt-in alongside `max_height_ratio` (do not change default)
4. Fixture diff shows the projection pass corrects the case without regressing others

## What is NOT broken (to scope the fix)

- The request does not change the default or require a GPU dependency.

## Relationships and material comments

- Triage links this request to spec-child issue #47.
- 2026-05-11T11:37:05Z — `ConcaveTrillion`: Triage decision: approved + needs-spec. Spec child issue: #47. Run `/spec-from-issue 47` to produce the design spec. ([comment](https://github.com/pdomain/pdomain-book-tools/issues/4#issuecomment-4420313149))
- Disposable chatter: 1 duplicate child-fork comment adds no durable fact.

## Repository evidence

- `docs/plans/roadmap.md` records the proposed cropped-image horizontal
  projection, its x-height purpose, and the prerequisite fixture evidence.
- `docs/architecture/reorganize-page-pipeline.md` verifies that geometric
  sidenote tagging is part of the present pipeline; it does not claim that
  image-projection refinement exists.

## Remaining work

- Acceptance criteria remain unverified against an implementation; preserve as open work.

## Resolution

_Open._ Retire this record only after evidence verifies the criteria or records an owner disposition.
