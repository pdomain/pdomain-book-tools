# Agent Instructions (Cross-Tool)

Shared instructions for AI coding agents working in this repository (Copilot, Claude Code, and other assistants).

## Scope and precedence

- This file is the cross-agent baseline.
- Tool-specific files (for example `.github/copilot-instructions.md`) should stay thin and point here.
- If a tool requires extra constraints, those are additive and should not duplicate this file.

## Source of truth (read order)

1. `README.md`
2. `CONTRIBUTING.md`
3. `pyproject.toml`
4. `TEST_COVERAGE_WORKPLAN.md`
5. `GPU_TESTING.md` (when changing GPU code paths)

## Workflow and tooling

- Use Makefile targets as the canonical workflow.
- If running in VS Code, tasks are optional wrappers around Make targets.
- Dependency manager: `uv`.
- Build backend: hatchling (`uv build`).

Common commands:
- Install: `make install`
- Test: `make test`
- Lint: `make lint`
- Format: `make format`
- Build: `make build`
- CI pipeline: `make ci`

## Validation rules

- Prefer `make` targets over direct tool invocation when a target exists.
- All Python tooling must run through `uv` (`uv run pytest`, `uv run ruff format`, etc.).
- After code changes, run formatting first, then targeted tests, then broader checks as needed.
- Keep tests aligned with the existing mirrored structure under `tests/`.

## Domain guardrails (OCR + geometry)

- Preserve normalized vs pixel coordinate semantics (`is_normalized`) across `Point`, `BoundingBox`, and OCR model types.
- Do not silently coerce coordinate systems in merge/split/union operations; fail explicitly on mismatch.
- Use deep-copy-safe object transformations (`to_dict`/`from_dict`) when returning transformed OCR entities.
- Keep image refinement routines consistent with existing ROI/threshold helper patterns.

## Documentation hygiene

- Update docs when implementation changes expected workflows or behavior.
- Keep this file canonical for shared policy; avoid duplicating long guidance in tool-specific instruction files.

## Practical compatibility note

- Many agents discover root-level policy files like `AGENTS.md` and/or `CLAUDE.md`.
- Keep this file as canonical; if needed, create thin tool-specific adapters that reference this file.
