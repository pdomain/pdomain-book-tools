---
Status: active
Owner: CT
Created: 2026-07-19
Last verified: 2026-07-19
Kind: process
---

# Repository quality gates

## Agent Index

- **Kind:** process
- **Status:** active
- **Read when:** changing lint rules, pre-commit hooks, commit-message checks, tests, coverage, or the full CI gate.
- **Search terms:** quality gates, Ruff, pre-commit, gitlint, gitleaks, uv lock, warnings error, branch coverage.

`make ci AI=1` is the repository's full pre-commit verification gate. The
target performs setup, runs pre-commit across the repository, checks Ruff
formatting and lint without mutation, runs strict basedpyright, executes tests,
builds the package, and reports layout-detector fork drift.

## Pre-commit and commit-message checks

The pre-commit stage trims whitespace, fixes final newlines, validates YAML,
JSON, and TOML, rejects large additions, detects debug statements and merge
markers, and scans secrets with gitleaks. It runs Ruff import fixes, safe lint
fixes, formatting, Markdown lint, and `uv lock --check`. The repository's
`pre-commit-check` target skips the duplicate basedpyright hook; `make ci` runs
the separate `typecheck` target afterward. The commit-msg stage runs gitlint.

`pre-commit-update` checks hook revisions and may modify
`.pre-commit-config.yaml`. A feature commit may skip that self-updater when its
only result is an unrelated dependency bump, but the remaining hooks still run.

## Ruff, tests, and coverage

Ruff owns import sorting, linting, and formatting; standalone isort and pylint
are not development dependencies. The selected families include the baseline
E, W, F, I, N, B, SIM, UP, RUF, ERA, and T20 rules plus the repository's
annotation, security, comprehension, performance, type-checking, import,
pytest, return, pylint-subset, docstring, exception, logging, and logging-format
families. `pyproject.toml` is the exact current rule authority.

Pytest treats warnings as errors and measures branch coverage. The configured
coverage threshold and soft target may strengthen independently of the original
May 2026 rollout; current values in `pyproject.toml` and the Makefile are
authoritative.

Coverage uses two source sets with one threshold. A GPU-capable local run uses
`pyproject.toml` and includes `cupy_processing` modules in the 87% branch
coverage gate. A CPU-only or CI run uses `.coveragerc.cpu`, which omits
`cupy_processing` and `cv2cuda_processing` because those paths cannot execute
without the GPU extra. `cv2cuda_processing` is also omitted from the full
configuration because it is a thin wrapper around the exercised CuPy backend.

The Makefile selects the full configuration when it detects a usable NVIDIA
GPU and `CI` is absent. This split keeps CPU-only results honest without
removing GPU modules from full coverage. It does not establish a separate
GPU-only threshold or a required remote GPU CI job.

## Type checking

[`type-checking.md`](../architecture/type-checking.md) owns the basedpyright
contract. The repository initially migrated through standard and recommended
modes, then strengthened the gate to strict mode with zero diagnostics across
the package, tests, and scripts.

## Evidence

- **Configuration:** `.pre-commit-config.yaml`, `pyproject.toml`,
  `.coveragerc.cpu`, `.gitlint`, and `.editorconfig`
- **Commands:** `Makefile` targets `pre-commit-check`, `lint-check`, `typecheck`, `test`, `build`, and `ci`
- **Initial rollout:** commits `cbaa74a`, `4ab7a93`, `bd0de40`, `4a59ff2`, `b742231`, `c500d91`, `2e11974`, and `f809701`
- **Current type-checking contract:** [`type-checking.md`](../architecture/type-checking.md)
