---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I2
---

# drop-cap Iteration C missing heading cross-check for ambiguous lexicon

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I2
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** Medium — chapter openings stay unrecovered
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** editing dropcap recovery or footnotes-stacked-with-anchor fixture
- **Search terms:** Iteration C, drop cap unrecovered, BELIEF, footnotes-stacked-with-anchor
- **Relates to:** [plan F1 / S10](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** F1 / S10

## Summary

Drop-cap A/B shipped. Iteration C (roadmap): when lexicon is ambiguous, use chapter title above to resolve cap (e.g. "A BELIEF IN OMENS…"). Fixture `footnotes-stacked-with-anchor` and tests pin unrecovered "BELIEF" for missing "A".

## Impact

- Specific chapter openings need human review forever.
- Baseline text missing leading drop-cap letter.

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

- [plan F1 / S10](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)
- [roadmap](../plans/roadmap.md)

### 1. Decisive observation

```bash
rg -n 'unrecovered|BELIEF|footnotes-stacked' tests/ocr/test_dropcap.py | head -30
rg -n 'BELIEF' tests/fixtures/layout_regression/expected_text/baseline/footnotes-stacked-with-anchor.reorganize.txt \
  tests/fixtures/layout_regression/inputs/footnotes-stacked-with-anchor.pgdp.txt
```

Roadmap “Drop-cap Iteration C” section. Tests pin unrecovered for cap “A” +
body “BELIEF”. Baseline text lacks leading “A” vs PGDP `A BELIEF…`.

## Root-cause hypotheses

1. **(Most likely) Queued after A/B; no code yet for title cross-check** — Roadmap says queued.

## Defects to fix

1. **Heading cross-check** in dropcap when single-letter prepend is ambiguous.
2. **Flip fixture/test** from unrecovered to recovered for the BELIEF case.

## Next steps

1. Implement after A/B stability; no Theme E required.
2. Avoid depending on pixel-domain fix (C2) if using normalized fixtures only.

## What is NOT broken

- A/B block-cap and cursive paths work on preface-style fixtures.
- Unrecovered tagging for human review is intentional failure mode for residual cases.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
