---
Status: active
Owner: CT
Created: 2026-07-13
Last verified: 2026-11-13
Kind: context
---

# Current State

## Agent Index

- **Kind:** context
- **Status:** active
- **Last verified:** 2026-11-13
- **Read when:** starting work that depends on current priorities, risks, or in-flight documentation changes.
- **Search terms:** current state, priorities, risks, in flight.

## What matters now

Open work is the [roadmap](../plans/roadmap.md). The [issue index](../issues/README.md) points at that list. Shipped behavior is the [architecture index](../architecture/README.md), including the [PGDP-aware matcher](../architecture/pgdp-aware-matcher.md).

The [continued-work plan](../plans/2026-07-21-continued-work-from-deep-review.md) is still active. Its opening note names the slices already proven in code. Theme G waits on the roadmap's question of which repo should hold page-order, scannos, and hyphen n-grams. The [migration ledger](github-issues-migration-ledger.md) remains the record of the 214 GitHub source issues.

The architecture migration adds current contracts for [legacy baseline estimation](../architecture/baseline-estimation.md), [image I/O](../architecture/image-io.md), and [geometry coordinate domains](../architecture/geometry-coordinate-domains.md). The geometry center/containment issue is resolved by consumed contracts 0.3.1. The broader scale/four-point helper audit remains open.

All 91 in-scope current documents were reviewed. Only that geometry issue qualified for retirement; all eight specs and both plans remain active. Owner decisions and the five strict-xfail layout baselines remain open.

## In-flight work

- Published book-tools remains v0.31.0. A v0.31.1 release is planned; this documentation migration has not released it.
- GitHub Issues is disabled. Local files under `docs/issues/` are the tracker.
- Greenfield modules stay blocked on the owner decisions in the [intent map](intent-map.md).
- Items this pass could not prove are listed under "Needs owner decision" in that map. Their files stay.
- `fix/caption-reading-order` (`ed54ecd`, 2026-09-19) is an unverified reading-order attempt. It stays off master.

## Risks

- Do not treat deletion of a GitHub source as resolution of its governed file.
- Do not delete an issue file because it looks old. Retire it only when code and tests prove the outcome.
- The broader C3 scale/four-point helper audit remains unverified. The resolved center/containment contract is in [geometry coordinate domains](../architecture/geometry-coordinate-domains.md).
