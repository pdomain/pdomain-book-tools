---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# reorganize_page early-return skips word reconciliation on empty row blocks

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** High — silent body word loss without strict or soft recover
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** editing Page.reorganize_page control flow or word-preservation safety net
- **Search terms:** reorganize_page early return, reconcile_dropped_words, emit_band_only_blocks, word preservation
- **Relates to:** [plan A2 / S2](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** A2 / S2

## Summary

When grouping yields no row blocks, `Page.reorganize_page` emits header/footer bands and returns without `reconcile_dropped_words`. Body words that never formed rows can vanish with no raise and no recovered block. Confirmed against `page.py` ~3124–3140 vs reconcile ~3186.

## Impact

- Possible silent deletion of body words on degenerate grouping paths.
- Strict mode (`PD_OCR_REORGANIZE_STRICT`) never sees the drop.
- Soft recover never runs either.

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

- [plan A2 / S2](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)

### 1. Decisive observation — early return without reconcile

```bash
rg -n 'emit_band_only_blocks|reconcile_dropped_words|row_blocks' pdomain_book_tools/ocr/page.py | head -40
```

Empty-row path (~3124–3140): `emit_band_only_blocks` then `return`.
`reconcile_dropped_words` appears only later on the main path (~3186).

### 2. Band-only assembly

`emit_band_only_blocks` keeps header/footer bands. Content not in those
bands is not reattached before return.

## Root-cause hypotheses

1. **(Most likely) Early-return added for empty pages and never got the later safety net** — Empty-page smoke tests pass; adversarial empty-body case missing.
2. **Assumes row_blocks empty only when page has no body words** — False if peel/group empties items incorrectly.

## Defects to fix

1. **Always reconcile on early return** — run `reconcile_dropped_words` (or assemble leftovers) before every return from `reorganize_page`, including the empty-row path.
2. **(Follow-on, main path) Snapshot signatures** — after early-return is wired, freeze pre-reorg words via `to_dict`/immutable snapshot on the main reconcile path (drop-cap does not run on empty-row early return; live-ref mutation is a general A2 concern).
3. **(Follow-on) Multiset signatures** — set semantics miss duplicate text+bbox drops on any reconcile path.

## Next steps

1. Write failing test: body words present, empty row items after grouping, assert words survive or strict raises.
2. Wire reconcile on early return; fix signature snapshot.
3. Cover strict and soft modes.

## What is NOT broken

- Main path with non-empty row blocks still calls reconcile.
- Strict-mode unit tests for forced drops on the main path still exist.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
