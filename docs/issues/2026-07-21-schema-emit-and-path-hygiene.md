---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I2
---

# schema emit incomplete for glyphs; public-api path drift; Block GT tuples

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I2
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** Medium — wire-form gaps and stale doc pointers
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** changing schemas/emit, Word glyph wire form, or public-api paths
- **Search terms:** PUBLIC_MODELS GlyphAnnotations, docs/public-api.md, unmatched_ground_truth_words
- **Relates to:** [plan D2 / S9](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** D2 / S9

## Summary

Stale `docs/public-api.md` pointers in package/tests; real path is `docs/usage/public-api.md`. `GlyphAnnotations` not in PUBLIC_MODELS (any_schema on Word). `Block.unmatched_ground_truth_words` does not restore list→tuple after JSON. Provenance models emitted but not on Page after intentional Task 4 removal.

## Impact

- Broken links for agents following package docstrings.
- Codegen consumers lack glyph structure.
- Type assumptions after JSON round-trip fail for Block unmatched pairs.

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

- [plan D2 / S9](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)

### 1. Decisive observation

```bash
rg -n 'docs/public-api.md' pdomain_book_tools tests | head -20
rg -n 'PUBLIC_MODELS|GlyphAnnotations|any_schema' pdomain_book_tools/schemas/emit.py pdomain_book_tools/ocr/word.py | head -30
```

Stale path refs; glyphs not in PUBLIC_MODELS; Block unmatched GT pairs not
tuple-restored after JSON (contrast Page gt_orphans).

### Progress (2026-07-21 S0)

**Defect 1 (path refs) fixed** in `pdomain_book_tools/__init__.py` and
`tests/test_public_api.py` → `docs/usage/public-api.md`. Remaining open:
glyph PUBLIC_MODELS, Block unmatched GT list→tuple, provenance ownership
sentence (still S9 with D1).

## Root-cause hypotheses

1. **(Most likely) Docs moved to usage/ without pointer update** — Confirmed path drift.

## Defects to fix

1. **Path refs** → docs/usage/public-api.md.
2. **Glyph schema** — structured PUBLIC_MODELS or document opacity.
3. **Block from_dict** — list→tuple for unmatched GT words.
4. **Provenance ownership** — one sentence in architecture/public-api.

## Next steps

1. Fix path strings (S0-cheap with A5/D3).
2. Glyph + Block tuple in same schema PR as D1 if expanding.

## What is NOT broken

- Page gt_orphans.lines already restore tuples.
- Emit still covers core Point/BBox/Word/Block/Page models.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
