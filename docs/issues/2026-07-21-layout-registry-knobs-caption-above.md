---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I2
---

# PP-DocLayout registry rejects security kwargs; captions ignore above side

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I2
- **Last verified:** 2026-07-21
- **Resolution:** Open
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

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
