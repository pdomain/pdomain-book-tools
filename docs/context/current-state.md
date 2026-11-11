---
Status: active
Owner: CT
Created: 2026-07-13
Last verified: 2026-11-10
Kind: context
---

# Current State

## Agent Index

- **Kind:** context
- **Status:** active
- **Last verified:** 2026-11-10
- **Read when:** starting work that depends on current priorities, risks, or in-flight documentation changes.
- **Search terms:** current state, priorities, risks, in flight.

## What matters now

Open work is the short list in the [roadmap](../plans/roadmap.md) and the [issue index](../issues/README.md). Shipped behavior is the architecture set those pages link, including the [PGDP-aware matcher](../architecture/pgdp-aware-matcher.md).

The [continued-work plan](../plans/2026-07-21-continued-work-from-deep-review.md) is still active. Its opening note names the slices already proven in code. The [migration ledger](github-issues-migration-ledger.md) remains the record of the 214 GitHub source issues.

## In-flight work

- GitHub Issues is disabled. Local files under `docs/issues/` are the tracker.
- Greenfield modules stay blocked on the owner decisions in the [intent map](intent-map.md).
- Items this pass could not prove are listed under "Needs owner decision" in that map. Their files stay.
- Branch `fix/roadmap-no-owner-items` is committed locally and not merged. It holds plan items C1, C4, D1, D2, and B4. Master does not have this work yet.
- Branch `fix/caption-reading-order` is unverified work in progress. Leave it alone until its owner picks it up.

## Risks

- Do not treat deletion of a GitHub source as resolution of its governed file.
- Do not delete an issue file because it looks old. Retire it only when code and tests prove the outcome.
- [Plan item C3](../issues/2026-07-21-geometry-primitive-flag-hygiene.md) can only be fixed in `pdomain-book-contracts`.
- [The floated-caption split](../issues/2026-11-10-floated-caption-thresholds-ignore-normalized-coords.md) does nothing on normalized pages, which includes DocTR output.
