---
Status: built
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-19
Kind: architecture
---

# Type Checking

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Read when:** changing basedpyright configuration, its CI gate, or the
  generated warning baseline.
- **Search terms:** basedpyright, type checking, strict mode, warning
  baseline, CI, typings stubs.

The repository runs basedpyright at `typeCheckingMode = "strict"`, requiring
zero diagnostics across the full include (`pdomain_book_tools`, `tests`,
`scripts`). The repo raised this from recommended mode on 2026-07-15.

Two settings escalate checking beyond plain strict mode.
`reportUnnecessaryTypeIgnoreComment` requires every suppression to still be
needed. `reportImplicitOverride` requires overrides to say `@override`.

`failOnWarnings = true`. The Makefile `typecheck` gate runs
`uv run basedpyright` over the whole include, so any new diagnostic of any
severity fails CI. `.basedpyright/baseline.json` contains no grandfathered
files.

Local stubs under `typings/` cover untyped third-party libraries: cupy,
cupyx.scipy.ndimage, and pytesseract. The stubs are scoped to the API
surface this repo uses. The repo also depends on the `pandas-stubs` dev
dependency.

Two scoped deviations exist. `reportPrivateUsage` is off for the `tests`
execution environment because unit tests exercise private helpers.
`reportMissingModuleSource` is off only in the three source trees that support
the optional CuPy runtime and in tests, which exercise those optional paths.
Local stubs still provide the checked CuPy API on CPU-only installs. Missing
imports, unknown types, and other diagnostics remain enabled. See
`docs/process/lint-deviations.md` for these and the other catalogued
suppressions.

The baseline is a generated integration artifact. Regenerate it only when
the repository deliberately changes the accepted diagnostic set; do not
edit it on parallel file-level branches.

## Evidence

- Code: `pyproject.toml` (`[tool.basedpyright]`), `Makefile` (`typecheck`),
  `typings/`, `.basedpyright/baseline.json`
- Tests: `make ci AI=1`; `uv run basedpyright` reports 0 errors, 0 warnings,
  0 notes on GPU-capable and CPU-only dependency sets (2026-07-19)
- Artifacts: empty basedpyright file baseline
- Verified: 2026-07-19 after reproducing the CPU-only CI dependency set; the
  original 2026-07-15 migration drove 7,697 strict errors to zero

## Residual intent

- The strict-config target's ruff deltas (`FA`, `PIE`, `PLE`, `PTH`
  families) are not yet adopted; adding them is a separate decision.
- `typings/` stubs cover only the used API surface; extend them when new
  cupy/pytesseract calls appear rather than suppressing.
