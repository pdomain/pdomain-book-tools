---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# public-api.md is narrower than taught Document/hf/geometry_correction surface

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** Medium — contract hybrid is unsafe for consumers
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** changing public-api.md, package `__all__`, or README imports
- **Search terms:** public-api, `__all__`, Document public, hf public API
- **Relates to:** [plan D1 / S9](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** D1 / S9

## Summary

Documented top-level public API omits surfaces README teaches as usable: at least `Document` / DocTR ingestion and `schemas.emit` (and often deep-imports under `ocr.*`). `geometry_correction` has a separate usage doc; `hf` has package `__all__` / module docstring only (no `docs/usage` page). Neither is listed in `public-api.md`. Do not claim monorepo-wide stability without a consumer cite. Docs also claim submodule paths may move while teaching deep imports. Plan default: expand and pin rather than shrink teaching surface.

## Impact

- Downstream code depends on "internal" paths without pins.
- Refactors break consumers without release notes.

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

- [plan D1 / S9](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)
- [public API usage](../usage/public-api.md)

### 1. Decisive observation

```bash
rg -n 'Document|from_image_ocr|schemas.emit|public-api' README.md docs/usage/public-api.md | head -40
rg -n '`__all__`' pdomain_book_tools/__init__.py
```

public-api.md top list vs package `__all__`; README teaches DocTR/`Document`
paths not fully pinned.

## Root-cause hypotheses

1. **(Most likely) Public API intentionally minimal; docs never reconciled** — Fits.

## Defects to fix

1. **One policy** — expand public-api + `__all__` + tests (default), or mark deep imports internal and stop teaching them.
2. **Pin tests** — full layout/hf `__all__` once expanded.

## Next steps

1. Owner may override default expand (Theme E).
2. Implement chosen policy in one PR with pin tests.

## What is NOT broken

- Listed top-level re-exports are identity-tested.
- Local model round-trips remain strong.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
