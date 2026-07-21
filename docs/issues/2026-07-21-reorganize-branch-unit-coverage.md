---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# reorganize_page_utils branch coverage thin on high-risk heuristics

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** Medium — core module ~80% line / 220 missing branches under 90% headline
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** adding reorg unit tests or refactoring reorganize_page_utils
- **Search terms:** reorganize_page_utils coverage, plate-noise, column split, branch miss
- **Relates to:** [plan B4](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** B4

## Summary

`reorganize_page_utils.py` (~1817 stmts) has ~298 missing statements and ~220 missing branches while package headline coverage is ~90.3% (htmlcov 2026-07-17). High-risk heuristics (plate noise, column strategies, floated flow) lack focused unit tables.

## Impact

- False confidence from aggregate coverage.
- Heuristic changes regress without targeted fails.

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

- [plan B4](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)

### 1. Decisive observation (coverage artifact)

```bash
python3 -c "import json;d=json.load(open('htmlcov/status.json'));
files=d.get('files',d);
k=[(k,v) for k,v in files.items() if 'reorganize_page_utils' in str(v.get('index',{}).get('file',''))];
print(k[0][1]['index']['nums'] if k else 'missing')"
```

htmlcov (artifact under `htmlcov/`, ~2026-07-15 stamp): ~80.1% line,
n_missing=298, n_missing_branches=220 on `reorganize_page_utils.py` (~1817 stmts)
while package headline ~90.3%.

## Root-cause hypotheses

1. **(Most likely) End-to-end text snapshots dominate; unit tables never written** — Few focused tests vs 70+ defs in the module.

## Defects to fix

1. **Unit tables** — soft recover, early return, plate-noise edges, column strategy 1 vs 2, floated+caption, multiset preservation.
2. **Optional split** — metrics/noise/bands/rows/columns/paragraphs/preserve/debug modules later.

## Next steps

1. Land A2/A3 tests first (highest risk).
2. Add plate and column matrices next; defer file split until tables exist.

## What is NOT broken

- Layout regression corpus still provides end-to-end text signal.
- Coverage gate 87% still enforces a floor.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
