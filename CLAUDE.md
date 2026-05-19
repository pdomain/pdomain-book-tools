# CLAUDE — pd-book-tools

Foundation Python library for public domain book scans: OCR (Tesseract +
DocTR), layout analysis, image processing. All other `pd-*` projects depend
on it, so public API changes ripple downstream.

## Commands

| target | does |
|---|---|
| `make setup AI=1` | install all deps via uv + pre-commit hooks |
| `make test AI=1` | `uv run pytest -n auto` |
| `make test-k K='pattern' AI=1` | targeted test run |
| `make lint AI=1` / `make format AI=1` | ruff check / ruff format |
| `make build AI=1` | `uv build` (hatchling) |
| `make ci AI=1` | full check including layout-fork-info |
| `make coverage AI=1` | HTML report under `htmlcov/` |

`AI=1` captures verbose output to `.ci-ai.log`; stdout shows `✅` on pass or
filtered failure sections on error. Remove `AI=1` only if you need full verbose
output for debugging.

## Rules

- Always run `make ci AI=1` before committing.
- Make targets first; fall back to `uv run …` only when no target exists.
- Never `python -m pytest` / `python3 -m pytest`. Always `uv run pytest -n auto` or `make test`. Bare `python`/`python3`/`.venv/bin/python` miss the venv.
- Preserve `is_normalized` semantics across `Point`, `BoundingBox`, and OCR model types.
- Never silently coerce coordinate systems in merge/split/union; fail explicitly on mismatch.
- Use `to_dict`/`from_dict` for deep-copy-safe transformations of OCR entities.
- Keep image refinement routines consistent with existing ROI/threshold helper patterns.
- GPU paths (`[gpu]` extra) are opt-in; test both CPU and GPU code paths where relevant.

## Decisions

- 2024: `[layout]` install extra never shipped — `transformers` promoted to mandatory dep.
- 0.11.0: `cupy-cuda12x`/`opencv-cuda` moved to `[project.optional-dependencies].gpu`.
- `aspect_ratio` param removed from `rescale_image` family; aspect shaping done downstream via `map_content_onto_scaled_canvas`.

## GH issues

Cross-cut work tasks are tracked as GH issues in
**`ConcaveTrillion/ocr-container-meta`** (not in this repo's own tracker).
Plans under `docs/superpowers/plans/` in the workspace root are synced there
via `/decompose-spec --sync`. Milestone naming: `spec: <plan-basename> (#N)`.

When shipping a plan task:

- Before starting: `gh issue view <N> --repo ConcaveTrillion/ocr-container-meta`
- After completing: `gh issue close <N> --repo ConcaveTrillion/ocr-container-meta`
- List open tasks:
  `gh issue list --repo ConcaveTrillion/ocr-container-meta --milestone "spec: <name> (#N)" --state open`

## docs/ folder

This repo follows the workspace docs/ template — see [`docs/README.md`](docs/README.md). Active
folders: `architecture/`, `decisions/`, `plans/`, `process/`, `research/`,
`runbooks/`, `specs/`, `templates/`, `usage/`, plus parallel `archive/`
subfolders.

**Superpowers redirect.** When a superpowers skill (e.g. `brainstorming`,
`writing-plans`) instructs you to save to `docs/superpowers/specs/<file>.md`
or `docs/superpowers/plans/<file>.md`, save to `docs/specs/<file>.md` or
`docs/plans/<file>.md` instead. There is no `docs/superpowers/` subdirectory
in this repo.
