---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# char-bbox extraction (spec 09) not implemented

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** Medium — CharFixer production extractor missing
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** starting work on H2 (after E) or reading ../specs/09-char-bbox-extraction.md
- **Search terms:** extract_char_bboxes, char_extraction, spec 09, CharFixer
- **Relates to:** [plan H2 (after E)](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** H2 (after E)

## Summary

No extract_char_bboxes / CharExtractionConfig. Whitespace character splitter is a weaker adjacent path only. Blocked on polarity/ligature/fallback decisions. Tracked for plan Theme G–I after decision pack.

## Impact

- **Labeler CharFixer** lacks production `extract_char_bboxes` geometry.
- Whitespace character splitter is a weaker adjacent path only.
- Not a Stage 11 page-order blocker.

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

- [plan H2 (after E)](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)
- [spec](../specs/09-char-bbox-extraction.md)

### 1. Decisive absence check

```bash
rg -n 'extract_char_bboxes|CharExtractionConfig' pdomain_book_tools || true
rg -n 'split_into_characters_from_whitespace' pdomain_book_tools/ocr/word.py | head -5
```

Expected: no extract_char_bboxes; whitespace splitter only. Blocked on polarity/ligature decisions.

## Root-cause hypotheses

1. **(Most likely) Design complete, implementation intentionally not started** — Matches adversarial "no implementation" and roadmap omission.

## Defects to fix

1. **Implement per revised spec** after Theme E — see H2 (after E).
2. **Do not code from unrevised post-adversarial drafts** without folding review corrections.

## Next steps

1. Keep blocked until Theme E answers land.
2. Revise spec if adversarial redesign is accepted, then implement.

## What is NOT broken

- `Character` model and whitespace split helpers exist for non-production paths.
- This tracks missing CharFixer-grade extractor, not a reorganize regression.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
