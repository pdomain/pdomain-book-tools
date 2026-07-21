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

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
