---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-07-21
Kind: issue
Level: I1
---

# HEIF/AVIF identify then fail on cv2 load; writes ignore imwrite success

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-21
- **Resolution:** Open
- **Severity:** Medium — accept-then-fail load; silent write no-ops
- **Affected version:** pdomain-book-tools 0.21.x-dev @ a7bff12
- **Read when:** editing image_processing io/formats or gpu extras
- **Search terms:** HEIF AVIF read_image, imwrite, opencv-cuda, cv2cuda_processing
- **Relates to:** [plan C5 / S8](../plans/2026-07-21-continued-work-from-deep-review.md)
- **Plan item:** C5 / S8

## Summary

`formats.is_image_file` accepts HEIF/AVIF; `cv2_processing.io.read_image` uses `cv2.imread` only and raises for those formats. `write_jpg`/`write_png` discard `imwrite` bool. `[gpu]` lists unused `opencv-cuda`; coverage omit references missing `cv2cuda_processing`.

## Impact

- Modern phone captures accepted then fail at load.
- Disk-full / permission write failures look like success.
- Installers think CUDA OpenCV is used; only CuPy is.

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

- [plan C5 / S8](../plans/2026-07-21-continued-work-from-deep-review.md)
- [deep review findings](../research/2026-07-21-deep-code-review-findings.md)

### 1. Decisive observation

```bash
rg -n 'HEIF|AVIF|heif|avif' pdomain_book_tools/image_processing/formats.py | head -20
rg -n 'imread|imwrite' pdomain_book_tools/image_processing/cv2_processing/io.py
rg -n 'opencv-cuda|cv2cuda' pyproject.toml pdomain_book_tools || true
```

formats accepts HEIF/AVIF; `read_image` is `cv2.imread` only; writes discard
imwrite bool; `opencv-cuda` listed, unused in package.

## Root-cause hypotheses

1. **(Most likely) Formats module added for identify; load path not unified** — Likely.

## Defects to fix

1. **Unified load** — Pillow→BGR for formats OpenCV cannot open.
2. **Raise on imwrite/imencode false**.
3. **opencv-cuda** — use or remove; clean coverage omit.

## Next steps

1. Add failing HEIF load test through production entrypoint if fixture available.
2. Fix write checks; resolve opencv-cuda dependency honesty.

## What is NOT broken

- read_image already fails hard on None from imread (not silent).
- formats magic/plugin registration is carefully designed.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commit here, move the README pointer to Resolved, and route retirement
through `doc-retirer`.
