---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# layout corpus locks drop_layout_words=True not production default False

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** High — CI green while default reorganize path untested by baselines
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** changing reorganize defaults or layout regression baselines
- **Search terms:** drop_layout_words default, word-preserving, layout_regression baseline
- **Relates to:** [plan B2 / S5](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** B2 / S5

## Summary

Corpus text baselines force `drop_layout_words=True` (legacy figure-noise). Production default is `drop_layout_words=False` (word-preserving). CI can stay green while the default path regresses.

## Impact

- Default production behavior lacks text baseline lock.
- Policy change risk: engineers optimize for True path only.

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

- [plan B2 / S5](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)

### 1. Decisive observation

```bash
rg -n 'drop_layout_words' tests/ocr/test_reorganize_page_utils_grouping.py \
  tests/fixtures/layout_regression/dump_reorganize_output.py \
  pdomain_book_tools/ocr/page.py | head -30
```

Harness forces `True` (~339). Dump tool
`tests/fixtures/layout_regression/dump_reorganize_output.py` (~58) same.
`Page.reorganize_page` default is `False` (~2783). Architecture fixture corpus
doc notes the divergence.

## Root-cause hypotheses

1. **(Most likely) Baselines frozen under old default and never dual-tracked after policy flip** — Matches architecture residual wording.

## Defects to fix

1. **Default-mode track** — second expected-text set or matrix flag for `drop_layout_words=False`.
2. **CI assert** — at least core corpus subset under default flags.

## Next steps

1. After A1 (and preferably B1), add default-mode expected outputs for core cases.
2. Document subset selection if full corpus is too heavy.

## What is NOT broken

- Unit tests may cover default flags in isolation; this issue is corpus baseline lock.
- Legacy True path still needs its own baselines until B3 xfails close.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
