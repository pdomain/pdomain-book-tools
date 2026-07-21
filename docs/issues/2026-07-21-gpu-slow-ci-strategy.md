---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# default CI never runs GPU or @slow model paths

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** Medium — optional stacks untested on every PR
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** changing CI, markers, or GPU testing policy
- **Search terms:** make ci-slow, not slow, CUDA_VISIBLE_DEVICES, cupy coverage omit
- **Relates to:** [plan C6 / S8b](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** C6 / S8b

## Summary

pytest default `-m "not slow"`; `make ci` uses `make test` not slow. GPU tests skip without CUDA / under CI; cupy sources omitted from CPU coverage. `make ci-slow` **aliases `ci`** (full CPU gate) and therefore **does not run** slow/GPU suites. Plan default: expand CPU parity + seed GPU fixtures; document residual risk.

## Impact

- Dual-path and model adapter regressions only found locally or late.
- Coverage % overstates GPU quality.

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

- [plan C6 / S8b](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)

### 1. Decisive observation

```bash
rg -n 'not slow|ci-slow|^ci:|^test:' Makefile pyproject.toml | head -30
rg -n 'skipif_ci|cupy_module' tests/conftest.py | head -20
```

addopts exclude slow; `ci-slow` aliases `ci`; cupy omitted under `.coveragerc.cpu`.

## Root-cause hypotheses

1. **(Most likely) Cost/time tradeoff without a written residual-risk strategy** — GPU_TESTING.md exists but `ci-slow` aliases `ci`; does not run slow/GPU.

## Defects to fix

1. **Written strategy** — nightly CUDA and/or CPU parity default.
2. **Seed GPU random fixtures**.
3. **ci-slow** — run slow tests or rename/document alias.

## Next steps

1. Implement plan default unless owner overrides (Theme E).
2. Update GPU_TESTING.md with the residual risk table.

## What is NOT broken

- CPU suite remains the primary gate and is substantial.
- slow tests exist and can be run with make test-slow.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
