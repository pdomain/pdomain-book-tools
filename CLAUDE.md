# CLAUDE — pd-book-tools

Foundation Python library for public domain book scans: OCR (Tesseract +
DocTR), layout analysis, image processing. All other `pd-*` projects depend
on it, so public API changes ripple downstream.

## Commands

| target | does |
|---|---|
| `make setup` | install all deps via uv + pre-commit hooks |
| `make test` | `uv run pytest -n auto` |
| `make test-k K='pattern'` | targeted test run |
| `make lint` / `make format` | ruff check / ruff format |
| `make build` | `uv build` (hatchling) |
| `make ci` | full check including layout-fork-info |
| `make coverage` | HTML report under `htmlcov/` |

Always pass `AI=1` to make targets: `make ci AI=1`, `make test AI=1`, etc.
This captures verbose output to `.ci-ai.log` and prints only `✅ <target>
passed` on success or filtered failure sections on error. Remove `AI=1` only
if you need full verbose output for debugging.

## Rules

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
