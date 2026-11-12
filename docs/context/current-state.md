---
Status: active
Owner: CT
Created: 2026-07-13
Last verified: 2026-11-12
Kind: context
---

# Current State

## Agent Index

- **Kind:** context
- **Status:** active
- **Last verified:** 2026-11-12
- **Read when:** starting work that depends on current priorities, risks, or in-flight documentation changes.
- **Search terms:** current state, priorities, risks, in flight.

## What matters now

Open work is the [roadmap](../plans/roadmap.md). The [issue index](../issues/README.md) points at that list. Shipped behavior is the [architecture index](../architecture/README.md), including the [PGDP-aware matcher](../architecture/pgdp-aware-matcher.md).

The [continued-work plan](../plans/2026-07-21-continued-work-from-deep-review.md) is still active. Its opening note names the slices already proven in code. Theme G waits on the roadmap's question of which repo should hold page-order, scannos, and hyphen n-grams. The [migration ledger](github-issues-migration-ledger.md) remains the record of the 214 GitHub source issues.

## In-flight work

- GitHub Issues is disabled. Local files under `docs/issues/` are the tracker.
- Greenfield modules stay blocked on the owner decisions in the [intent map](intent-map.md).
- Items this pass could not prove are listed under "Needs owner decision" in that map. Their files stay.

## Risks

- Do not treat deletion of a GitHub source as resolution of its governed file.
- Do not delete an issue file because it looks old. Retire it only when code and tests prove the outcome.
