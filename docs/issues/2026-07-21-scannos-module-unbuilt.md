---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# scannos module specified but not implemented

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** Medium — Stage 13 prep-for-pgdp blocked on missing module
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** starting work on G2 (after E) or reading ../specs/2026-05-24-scannos-module.md
- **Search terms:** scannos, ScannoRule, scan_page, #209
- **Relates to:** [plan G2 (after E)](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** G2 (after E)

## Summary

Spec and issues #216–#220 / #209 describe ScannoRule, stores, scan_page, promote. No package module. Blocked on ID/evidence/dual-write decisions. Needs platformdirs or chosen path helper when built. Tracked for plan Theme G–I after decision pack.

## Impact

- **prep-for-pgdp Stage 13** has no shared ScannoRule / scan_page / promote library.
- Schema invented in the app will be hard to migrate later.
- Not a runtime regression in OCR reorganize today.

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

- [plan G2 (after E)](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)
- [spec](../specs/2026-05-24-scannos-module.md)

### 1. Decisive absence check

```bash
ls pdomain_book_tools/scannos 2>&1 || true
rg -n 'ScannoRule|scan_page|CandidateStore' pdomain_book_tools || true
```

Expected: no package; symbols only in specs. Blocked on Theme E ID/evidence decisions.

## Root-cause hypotheses

1. **(Most likely) Design complete, implementation intentionally not started** — Matches adversarial "no implementation" and roadmap omission.

## Defects to fix

1. **Implement per revised spec** after Theme E — see G2 (after E).
2. **Do not code from unrevised post-adversarial drafts** without folding review corrections.

## Next steps

1. Keep blocked until Theme E answers land.
2. Revise spec if adversarial redesign is accepted, then implement.

## What is NOT broken

- OCR Word/Page models exist for a future scanner to consume.
- This issue is design-backlog absence, not a production crash.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
