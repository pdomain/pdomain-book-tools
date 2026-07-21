---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# roadmap omits #208–#225 clusters; intent-map still claims spec 07 pending

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** Medium — process dual sources of truth before tracker wipe
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** editing roadmap, intent-map, or preparing issue-tracker migration
- **Search terms:** intent-map spec 07, #208, page-order scannos hyphen roadmap, table detection complete
- **Relates to:** [plan D3 / S0](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** D3 / S0

## Summary

Handoff 2026-07-17 required absorbing open issue clusters #208–#225 (page-order, scannos, hyphen) into the live plan before GitHub wipe. `docs/plans/roadmap.md` does not list them. Intent-map still says implemented spec 07 is pending architecture promotion; it was retired to `architecture/local-dev-mode.md` on 2026-07-15. Roadmap "table detection complete" is easy to misread as structure (spec 10) shipped.

## Impact

- Risk of losing backlog provenance if tracker is cleared.
- Agents follow stale intent-map lines.
- Consumers overestimate table structure readiness.

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

- [plan D3 / S0](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)
- [roadmap](../plans/roadmap.md)
- [intent-map](../context/intent-map.md)
- [issue tracker handoff](../handoff/2026-07-17-issue-tracker-migration.md)

### 1. Decisive observation

```bash
rg -n '#208|#211|page-order|scannos|hyphen' docs/plans/roadmap.md docs/handoff/2026-07-17-issue-tracker-migration.md | head -30
rg -n 'spec 07|pending architecture' docs/context/intent-map.md
rg -n 'Table detection is complete' docs/plans/roadmap.md
```

Handoff requires absorb of #208–#225; live roadmap omits clusters; intent-map
still has stale 07 line; table wording over-reads as structure complete.

## Root-cause hypotheses

1. **(Most likely) Deep-review plan created as parallel plan without merging into roadmap yet** — This issues folder is the absorb mechanism.

## Defects to fix

1. **Absorb or date-defer #208–#225** into roadmap or this plan with issue ids.
2. **Fix intent-map** retired-07 line.
3. **Disambiguate** table detection vs structure in roadmap language.

## Next steps

1. Patch intent-map + roadmap language in S0 with README fix.
2. Ensure each greenfield cluster has a docs/issues or plan row.

## What is NOT broken

- Architecture local-dev-mode is the true home for shipped 07.
- Deep-review continued-work plan already lists G/H/I themes.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
