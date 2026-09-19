---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-09-19
Kind: issue
Level: I2
---

# schema emit incomplete for glyphs; public-api path drift; Block GT tuples

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I2
- **Last verified:** 2026-09-19
- **Resolution:** Open — 3 of 4 defects resolved; provenance ownership
  (defect 4) still open
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

1. ~~**Path refs** → docs/usage/public-api.md.~~ Already resolved before this
   pass — confirmed 2026-09-19, zero remaining hits.
2. ~~**Glyph schema** — structured PUBLIC_MODELS or document opacity.~~
   Resolved 2026-09-19.
3. ~~**Block from_dict** — list→tuple for unmatched GT words.~~ Resolved
   2026-09-19.
4. **Provenance ownership** — one sentence in architecture/public-api. Still
   open; out of scope for this pass.

## Next steps

1. ~~Fix path strings (S0-cheap with A5/D3).~~ Done (confirmed already done,
   2026-09-19).
2. ~~Glyph + Block tuple in same schema PR as D1 if expanding.~~ Done
   2026-09-19.
3. Write the provenance-ownership sentence for defect 4 (architecture /
   public-api docs) — still open.

## What is NOT broken

- Page gt_orphans.lines already restore tuples in `Page.from_dict` — though
  the pre-existing regression test for this only called
  `Page.from_dict(p.to_dict())` directly, which does not exercise the hazard
  (`to_dict()` hands back live tuple objects, not JSON-serialized lists); a
  true `json.dumps`/`json.loads` round-trip test was added in this pass
  (`tests/ocr/test_page.py::test_gt_orphans_lines_tuples_survive_json_round_trip`).
- Emit still covers core Point/BBox/Word/Block/Page models.

## Resolution

**Partially resolved (2026-09-19).** Fixed on branch
`fix/block-from-dict-tuples`:

1. **Path refs (defect 1).** Verified already resolved by a prior pass —
   `rg -n 'docs/public-api.md' pdomain_book_tools tests` now returns zero
   hits; all references already point at `docs/usage/public-api.md`. No
   further change needed.
2. **Glyph schema (defect 2).** `GlyphAnnotations`
   (`pdomain_book_tools/ocr/glyph_annotations.py`, re-exporting
   `pdomain_book_contracts.ocr.glyph_annotations.GlyphAnnotations`) is a
   plain stdlib `@dataclass` that Pydantic introspects natively — no
   `__get_pydantic_core_schema__` was needed. Added it to `PUBLIC_MODELS` in
   `pdomain_book_tools/schemas/emit.py` (import + tuple entry, ordered next
   to `Character`/`Word` since it backs `Word.glyph_annotations`). Tests:
   `tests/test_schemas_emit.py`
   (`test_public_models_includes_glyph_annotations`,
   `test_emit_glyph_annotations_schema_has_expected_fields`, and the updated
   closed-set assertion in `test_public_models_includes_full_set`).
3. **Block from_dict list→tuple (defect 3).** `Block.from_dict` in
   `pdomain_book_tools/ocr/block.py` previously `cast()`ed
   `unmatched_ground_truth_words` without converting `[int, str]` lists
   (what JSON produces) back into `(int, str)` tuples, unlike
   `Page.from_dict`'s `gt_orphans.lines` restoration for the identical
   hazard. Copied that restoration's approach (`tuple(entry) if
   isinstance(entry, list) else entry`, cast once at the end for the more
   specific `list[tuple[int, str]]` field type — `Block`'s field is more
   specific than `GtOrphans.lines: list[object]`, so no single helper
   covers both cleanly without either loosening Block's runtime shape or
   adding conditional logic to Page's; kept as two call sites following the
   same pattern rather than forcing one abstraction over genuinely
   different field shapes). Test:
   `tests/ocr/test_block.py::test_block_from_dict_restores_unmatched_ground_truth_words_as_tuples`
   (written first, confirmed failing before the fix, passing after).

**Not resolved:** defect 4 (provenance ownership sentence in
architecture/public-api docs) — out of scope for this pass, not touched.

**Consumer check.** `pdomain-ocr-labeler-spa` round-trips blocks through
JSON (confirmed by grep; not edited). Its one production call site,
`src/pdomain_ocr_labeler_spa/core/page_to_line_matches.py`, only does
`list(...)`, iterates, and unpacks each entry as `insert_idx, gt_word_text
in sorted(unmatched_gt, reverse=True)` — unpacking and `sorted()` behave
identically for a 2-element list and a 2-element tuple in Python, and no
`isinstance(..., tuple)` check or hashing was found anywhere in that repo.
That repository does not actually depend on tuple-ness today, even though
its own test stubs type the field as `list[tuple[int, str]]`; the fix
still closes the type/runtime mismatch at the source.

Set `Status: retired` only once defect 4 is resolved or explicitly
descoped, then follow the standard retirement convention (link the final
resolving commit, move the README pointer to "Where resolved work is
recorded", route through `doc-retirer`).
