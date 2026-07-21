---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I2
---

# README documents removed rotation_applied and wrong DocTR return type

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I2
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** Medium — consumer-facing API docs are false
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** editing README OCR examples or orientation API
- **Search terms:** rotation_applied, from_image_ocr_via_doctr, README orientation
- **Relates to:** [plan A5 / S0](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** A5 / S0

## Summary

README shows `Document.from_image_ocr_via_doctr(...)` assigned to `doc` and prints `page.rotation_applied`. The real API returns `tuple[Document, int]`; `Page` rejects `rotation_applied`. Architecture `ocr-page-orientation.md` is correct; README is not.

## Impact

- New consumers copy broken examples.
- AttributeError / wrong unpacking on first use.
- Undermines trust in other README samples.

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

- [plan A5 / S0](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)
- [orientation architecture](../architecture/ocr-page-orientation.md)

### 1. Decisive observation

```bash
rg -n 'rotation_applied|from_image_ocr_via_doctr' README.md pdomain_book_tools/ocr/document.py | head -30
```

README still shows assignment to `doc` and `page.rotation_applied` (~215–223).
`document.py` returns `(Document, int)`. Tests reject `rotation_applied` on Page.

## Root-cause hypotheses

1. **(Most likely) Docs not updated when Task removed rotation_applied from Page** — Architecture updated; README lag fits.

## Defects to fix

1. **README examples** — unpack `(document, rotation_degrees)`; remove `page.rotation_applied` usage in samples (architecture link may already exist nearby).

## Next steps

1. Fix unpack + remove `page.rotation_applied` from the broken sample block (~215–223).
2. Optional: smoke that examples match `Document.from_image_ocr_via_doctr` signature.

## What is NOT broken

- Architecture page and unit tests document the correct contract.
- Runtime API itself is consistent; only the README is wrong.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
