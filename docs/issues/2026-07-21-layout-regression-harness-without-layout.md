---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# layout regression text harness never passes layout= into reorganize_page

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** High — layout-aware pipeline untested on real fixtures
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** changing layout_aware_reorg, layout fixtures, or reorganize baselines
- **Search terms:** layout=, layout_regression, drop_layout_words, tag_words_with_layout
- **Relates to:** [plan B1 / S4](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** B1 / S4

## Summary

The 31-case layout regression text harness loads `*.layout.json` only for debug overlays. It calls `page.reorganize_page(drop_layout_words=True)` without `layout=`. Layout tagging, layout-aware figure-internal drops, geometric sidenotes, role bubble-up, and captions never run against the flagship corpus. Heuristic figure-noise drop still runs when drop is True.

## Impact

- Layout consumption can regress silently outside synthetic unit tests.
- Roadmap layout-consumption work has no production-fixture lock.
- Corpus claims overstate layout coverage.

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

- [plan B1 / S4](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)
- [layout fixture architecture](../architecture/layout-regression-fixture-corpus.md)

### 1. Decisive observation — harness omits layout=

```bash
rg -n 'reorganize_page\(|layout=' tests/ocr/test_reorganize_page_utils_grouping.py \
  tests/fixtures/layout_regression/dump_reorganize_output.py
```

Harness ~339: `page.reorganize_page(drop_layout_words=True)` — no `layout=`.
Dump tool ~58 same pattern. Pipeline layout steps require `layout is not None`.

## Root-cause hypotheses

1. **(Most likely) Baselines predate layout wiring and were never dual-tracked** — Comments about drop_layout_words legacy intent support this.

## Defects to fix

1. **Wire layout=** — load `inputs/<case>.layout.json` and pass into reorganize_page.
2. **Re-baseline per case** — review diffs; no bulk accept.
3. **Sync dump script** — same call signature as the harness.

## Next steps

1. Land A1 dual-domain matrix first (plan prerequisite before baseline rewrite).
2. Wire layout=; regenerate and review baselines case-by-case.

## What is NOT broken

- Synthetic `tests/layout/test_layout_aware_reorg.py` unit coverage exists.
- Fixture `*.layout.json` round-trip / bounds tests still run.
- Geometric reorg without layout is still exercised by the corpus.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
