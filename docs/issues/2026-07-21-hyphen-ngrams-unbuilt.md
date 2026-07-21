---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# hyphen n-grams client and SQLite asset not implemented

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** Medium — Stage 15 offline hyphen data missing
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** starting work on G3 (after E) or reading ../specs/2026-05-24-hyphen-ngrams-sqlite.md
- **Search terms:** hyphen_ngrams, HyphenNgramsClient, #210
- **Relates to:** [plan G3 (after E)](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** G3 (after E)

## Summary

Spec and issues #221–#225 / #210 describe HyphenNgramsClient, SqliteClient, build pipeline. No code or DB artifact. Plan sequencing *suggests* Protocol + JsonApiClient before a ~50MB SQLite asset, pending Theme E packaging decisions. Tracked for plan Theme G after decision pack.

## Impact

- **prep-for-pgdp Stage 15** lacks an offline hyphen-pair client/asset in this package.
- Online-only hyphen joins stay fragile until a client lands.
- Not required for reorganize correctness today.

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

- [plan G3 (after E)](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)
- [spec](../specs/2026-05-24-hyphen-ngrams-sqlite.md)

### 1. Decisive absence check

```bash
ls pdomain_book_tools/hyphen_ngrams 2>&1 || true
rg -n 'HyphenNgramsClient|SqliteClient' pdomain_book_tools || true
```

Expected: no package or DB artifact. Packaging/download/locking remain Theme E decisions.
Plan sequencing *suggests* Protocol + JsonApiClient before a ~50MB SQLite asset — not a locked design until E answers.

## Root-cause hypotheses

1. **(Most likely) Design complete, implementation intentionally not started** — Matches adversarial "no implementation" and roadmap omission.

## Defects to fix

1. **Implement per revised spec** after Theme E — see G3 (after E).
2. **Do not code from unrevised post-adversarial drafts** without folding review corrections.

## Next steps

1. Keep blocked until Theme E answers land.
2. Revise spec if adversarial redesign is accepted, then implement.

## What is NOT broken

- Stage 15 can still use an external JSON client until this package owns one.
- This is backlog absence, not a silent OCR failure.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
