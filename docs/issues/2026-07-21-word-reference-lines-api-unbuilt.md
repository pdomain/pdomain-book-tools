---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# word reference lines API (06b/c) not implemented beyond baseline helpers

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** Medium — labeler bottom-crop foundation missing
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** starting work on H1 (after E) or reading ../specs/06b-word-reference-lines-api.md
- **Search terms:** WordReferenceLines, estimate_reference_lines, 06b, Q-RL
- **Relates to:** [plan H1 (after E)](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** H1 (after E)

## Summary

Specs 06a–c active. Only `estimate_baseline_from_image` exists. No WordReferenceLines, estimate_reference_lines, or reference_lines.py. Blocked on Q-RL owner decisions. Tracked for plan Theme G–I after decision pack.

## Impact

- **Labeler bottom-crop** lacks the four-line reference geometry API (06b/c).
- Soft dependency for char-bbox diacritic banding (spec 09).
- Not a prep-for-pgdp Stage 11–15 blocker by itself.

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

- [plan H1 (after E)](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)
- [spec 06b](../specs/06b-word-reference-lines-api.md)
- [spec 06c](../specs/06c-word-reference-lines-testing.md)

### 1. Decisive absence check

```bash
ls pdomain_book_tools/ocr/reference_lines.py 2>&1 || true
rg -n 'WordReferenceLines|estimate_reference_lines' pdomain_book_tools || true
rg -n 'estimate_baseline_from_image' pdomain_book_tools/ocr/word.py | head -5
```

Expected: no WordReferenceLines API; baseline-only helpers exist. Blocked on Q-RL-* decisions.

## Root-cause hypotheses

1. **(Most likely) Design complete, implementation intentionally not started** — Matches adversarial "no implementation" and roadmap omission.

## Defects to fix

1. **Implement per revised spec** after Theme E — see H1 (after E).
2. **Do not code from unrevised post-adversarial drafts** without folding review corrections.

## Next steps

1. Keep blocked until Theme E answers land.
2. Revise spec if adversarial redesign is accepted, then implement.

## What is NOT broken

- `estimate_baseline_from_image` on Word/Block still works as a partial foundation.
- Glyph annotations and serialization contracts are separate shipped work.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
