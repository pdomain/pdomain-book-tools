---
Status: active
Owner: CT
Created: 2026-07-21
Last verified: 2026-09-19
Kind: issue
Level: I1
---

# HEIF/AVIF identify then fail on cv2 load; writes ignore imwrite success

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-09-19
- **Resolution:** Open — 2 of 3 defects resolved; opencv-cuda dependency
  honesty (defect 3) still open
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

1. ~~**Unified load** — Pillow→BGR for formats OpenCV cannot open.~~ Resolved
   2026-09-19.
2. ~~**Raise on imwrite/imencode false**.~~ Resolved 2026-09-19 for
   `write_jpg`/`write_png` (`cv2.imwrite`). `encoding.encode_bgr_image_as_png`
   (`cv2.imencode`) was out of scope for this pass and still discards its
   success flag — unaddressed.
3. **opencv-cuda** — use or remove; clean coverage omit. Still open; not
   touched by this pass.

## Next steps

1. ~~Add failing HEIF load test through production entrypoint if fixture
   available.~~ Done — see Resolution.
2. ~~Fix write checks~~; resolve opencv-cuda dependency honesty (still open).
3. Decide whether `encoding.encode_bgr_image_as_png`'s discarded
   `cv2.imencode` success flag belongs in this report or a new one.

## What is NOT broken

- read_image already fails hard on None from imread (not silent).
- formats magic/plugin registration is carefully designed.

## Resolution

**Partially resolved (2026-09-19).** Fixed on `fix/image-io-write-failures`,
commit message `fix(image-io): raise on failed writes and load HEIF/AVIF via
Pillow fallback`:

1. `write_jpg`/`write_png` in
   `pdomain_book_tools/image_processing/cv2_processing/io.py` now check
   `cv2.imwrite`'s boolean return and raise `ValueError` naming the target
   path on failure, instead of returning normally after writing nothing.
2. `read_image` in the same module now falls back to Pillow (via the
   `pillow-heif` / `pillow-avif-plugin` openers already registered as
   required dependencies by `formats.py`) when `cv2.imread` returns `None`,
   converting the Pillow RGB result to BGR to match cv2's channel
   convention. HEIF/AVIF now load through the same production entrypoint
   that identifies them as supported, instead of raising after being
   accepted. Pillow, pillow-heif, and pillow-avif-plugin were already
   required (non-optional) dependencies, so no new dependency was added.
   Tests: `tests/image_processing/cv2_processing/test_io.py`
   (`TestWriteFailures`, `TestReadImageHeif` — the latter asserts channel
   order explicitly against a known red/blue HEIC fixture generated at test
   time).

**Not resolved:** defect 3 (`opencv-cuda` listed in `[gpu]` but unused;
`cv2cuda_processing` coverage-omit reference to a module that does not
exist) — out of scope for this pass. `encoding.encode_bgr_image_as_png`'s
discarded `cv2.imencode` success flag was noticed during this pass but was
also out of scope (only `write_jpg`/`write_png` were named). Set
`Status: retired` only once both remaining items are resolved or explicitly
descoped, then follow the standard retirement convention (link the final
resolving commit, move the README pointer to "Where resolved work is
recorded", route through `doc-retirer`).
