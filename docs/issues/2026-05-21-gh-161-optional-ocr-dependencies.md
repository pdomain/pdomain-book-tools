---
Status: active
Owner: CT
Created: 2026-05-21
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Make heavy OCR dependencies optional

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** High — every downstream installation receives multi-gigabyte ML dependencies
- **Affected version:** Current `pyproject.toml` and the versions represented by the 2026-05-21 export
- **Read when:** changing package extras, imports, or downstream torch-free installation paths
- **Search terms:** torch, DocTR, torchvision, optional extra, import guard, issue 161
- **Relates to:** [Local development mode](../architecture/local-dev-mode.md)

## Summary

Every consumer of the base installation receives Torch, DocTR, and Torchvision
because they are mandatory project dependencies. The exported report describes
this as a suite-wide dependency cost. The requested change must preserve
lightweight imports while moving model-only dependencies behind a clearly named extra.

## Impact

- Every `pd-*` consumer inherits multi-gigabyte Torch dependencies.
- FastAPI processes that never run a model cannot have a truly torch-free installation closure.
- The change affects a foundational library and therefore needs careful import-surface compatibility.

## Environment / versions

The report arose while scaffolding `pd-ocr-trainer-spa` under
`ocr-container-meta` retirement plan #282. No operating system or exact package
version was stated.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/161>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABC_elAw`
- **Issue number:** 161
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-161.json`
- **Raw SHA-256:** `0a7c4c7c49f77dbc64f72b3022bc6645faaf42b0a575ac5d8ff65c6f771069ad`
- **Migration cutover:** Pending — the governed-content commit does not yet exist.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-21T15:19:01Z`
- **Updated:** `2026-05-21T15:19:01Z`
- **Closed:** Not closed in the export
- **Labels:** `status:backlog`, `kind:feature-request`
- **Assignees:** None
- **Milestone:** None
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The report says `pd-book-tools` is the dependency root for the full suite.
- Design decision D-T1 for `pd-ocr-trainer-spa` wants its long-lived FastAPI
  process to import only torch-free configuration models.
- Runtime imports were torch-free, but the installation closure was not.
  `uv tool install pd-ocr-trainer-spa` still installed Torch through
  `pd-book-tools` → `pd-ocr-ops` → the SPA.
- The proposal moves `python-doctr`, `torch`, `torchvision`, and other heavy
  model-only dependencies into an optional extra. The name remains undecided:
  `ocr`, `doctr`, or `ml` were suggested.
- `import pd_book_tools` plus light data-model, layout, and utility names must
  work without Torch.
- Heavy OCR wrappers should load lazily or use import guards. Missing extras
  should raise a helpful `ImportError` that identifies `pd-book-tools[ocr]`,
  rather than fail package import with a raw `ModuleNotFoundError`.
- A subprocess test should hide Torch and verify the lightweight surface.
- The cited `pd-ocr-training` precedent used a `[train]` extra, kept protocols
  and configuration models importable, and resolved heavy names through module
  `__getattr__`.
- The issue tracked no parent at export time.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **Mandatory dependency declarations are the direct cause.** Heavy packages remain in `[project.dependencies]`.
2. **Eager package imports may also block the change.** A torch-hidden subprocess test would identify those paths.

## Defects to fix

1. Separate lightweight and model-backed package dependencies.
2. Preserve a useful import surface when the model extra is absent.
3. Give users an actionable missing-extra error.

## Next steps

1. Inventory imports that transitively require Torch, DocTR, or Torchvision.
2. Choose and document the optional-extra name and compatibility policy.
3. Add a failing torch-hidden subprocess test before restructuring imports.
4. Verify both base and extra-enabled installations.

## What is NOT broken (to scope the fix)

- The report says runtime-only torch-free imports already worked for the SPA's configuration models.

## Relationships and material comments

- Discovered through `pd-ocr-trainer-spa` and retirement plan #282.
- Cites design decision D-T1 and `pd-ocr-training` as a reference implementation.
- No comments were present in the export.

## Repository evidence

- `pyproject.toml` currently lists `python-doctr`, `torch`, and `torchvision`
  under mandatory project dependencies, supporting the installation-closure claim.
- `pyproject.toml` has an optional-dependencies section, showing the package can
  express extras, but it does not place these three packages there.
- `tests/ocr/test_doctr_support.py` exercises missing-Torch behavior inside the
  predictor, but it does not prove a torch-free base installation.
- `docs/architecture/local-dev-mode.md` documents Torch and DocTR as part of
  local development; it does not resolve the base-installation request.

## Remaining work

- The extra name, supported lightweight API, compatibility plan, and installation tests remain open.

## Resolution

_Open._ Current dependency declarations still support the reported installation-closure problem.
