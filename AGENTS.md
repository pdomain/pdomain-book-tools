---
Status: active
Owner: CT
Created: 2026-05-04
Last verified: 2026-07-13
Kind: process
---

# CLAUDE — pdomain-book-tools

Foundation Python library for public domain book scans: OCR (Tesseract +
DocTR), layout analysis, image processing. All other `pdomain-*` projects depend
on it, so public API changes ripple downstream.

## Commands

| target | does |
|---|---|
| `make setup AI=1` | install all deps via uv + pre-commit hooks |
| `make test AI=1` | `uv run pytest -n auto` (slow model-download tests excluded by default) |
| `make test-slow AI=1` | run ALL tests including slow model-download smoke tests (needs network) |
| `make test-k K='pattern' AI=1` | targeted test run |
| `make lint AI=1` / `make format AI=1` | ruff check / ruff format |
| `make build AI=1` | `uv build` (hatchling) |
| `make ci AI=1` | full check including layout-fork-info |
| `make coverage AI=1` | HTML report under `htmlcov/` |
| `make local-dev` | switch to local-dev mode (GPU extras active + marker) |
| `make local-check` | print local-dev mode status (marker + torch location) |
| `make local-upgrade-deps` | upgrade deps + re-sync GPU extras (local-mode only) |

The local-dev commands above define this repository's supported workflow.

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
Plans under `docs/plans/` in the workspace root are synced there
via `/decompose-spec --sync`. Milestone naming: `spec: <plan-basename> (#N)`.

When shipping a plan task:

- Before starting: `gh issue view <N> --repo ConcaveTrillion/ocr-container-meta`
- After completing: `gh issue close <N> --repo ConcaveTrillion/ocr-container-meta`
- List open tasks:
  `gh issue list --repo ConcaveTrillion/ocr-container-meta --milestone "spec: <name> (#N)" --state open`

## docs/ folder

This repo follows the workspace docs/ template — see [`docs/README.md`](docs/README.md). Active
folders: `architecture/`, `decisions/`, `plans/`, `process/`, `research/`,
`runbooks/`, `specs/`, `templates/`, and `usage/`.

**Superpowers redirect.** When a superpowers skill (e.g. `brainstorming`,
`writing-plans`) instructs you to save to `docs/superpowers/specs/<file>.md`
or `docs/superpowers/plans/<file>.md`, save to `docs/specs/<file>.md` or
`docs/plans/<file>.md` instead. There is no `docs/superpowers/` subdirectory
in this repo.

<!-- workspace-process:start -->

## Before coding

These steps are workspace defaults for any coding task. **User-level settings
override them** — a user's own `~/.claude/CLAUDE.md`, `settings.json`, or a
direct instruction in the conversation takes precedence and may waive or
change any step below.

### Working principles

- **Use skills.** Invoke the relevant superpowers skill before starting —
  process skills first (`brainstorming`, `systematic-debugging`,
  `writing-plans`, `test-driven-development`), then implementation skills.
  If a skill applies, using it is not optional.
- **Write clearly.** Use the `writing-docs` plugin for direct user updates,
  handoffs, final summaries, docs, reports, issue text, PR text, and
  user-facing copy. Apply its inline standard to short prose. Route new durable
  prose through `writing-docs:write-readably` and existing prose through
  `writing-docs:edit-for-readability`. Stop with a missing-skill error if
  either route is unavailable. Keep agent communication short, clear, and easy
  to scan.
- **Delegate by default.** Dispatch subagents for non-trivial work: per-repo
  agents for repo changes, `Explore` for code searches. This keeps large tool
  output out of the parent context.
- **Parallelize.** Run independent tasks as concurrent subagents — multiple
  agent calls in a single message. Set `model: sonnet` on implementers and
  reviewers.

### Steps

1. **Check the working tree.** `git status --short`. Surface or resolve stray
   uncommitted work before starting — don't build on it.
2. **Read repo guidance.** This repo's `CLAUDE.md` and `CONVENTIONS.md` for
   repo-specific rules.
3. **Consult `docs/` for authoritative context** (whichever folders exist):
   `plans/` (the work plan), `specs/` (design specs — follow any `Spec:`
   pointer from the issue), `research/` (prior investigations), `decisions/`
   (ADRs / constraints), `architecture/` (shipped design).
4. **Check live issue status.** `gh issue view <N> --repo <owner/repo>` —
   confirm it isn't already closed; note its milestone.
5. **Check for in-flight work.** Open PRs and existing branches touching the
   same area, to avoid colliding with work-in-progress.
6. **Consult agent memory.** `.claude/agent-memory/<repo>/feedback_*.md` for
   corrections not yet promoted to `CONVENTIONS.md`.
7. **Locate code with `Explore` first.** Use an `Explore` subagent to find
   relevant files before broad `Read`/grep.
8. **Isolate in a worktree.** Never work directly in the interactive checkout
   at `/workspaces/ocr-container/<repo>/`. Use the `using-git-worktrees` skill
   to set up an isolated worktree. When delegating to a full-power
   implementation agent, pass `isolation: "worktree"` on the `Agent` call
   (skip for `-docs` agents and the `driver` agent). When an agent returns a
   worktree path + branch, use the `finishing-a-development-branch` skill to
   decide how to integrate.
9. **TDD.** Write the failing test first where the plan calls for it.
10. **Verify before committing.** Focused verification plus `make ci`.
11. **Commit locally; do not push** without explicit say-so.

<!-- workspace-process:end -->

<!-- >>> repo-setup:repo-facts sha256:a7c2d483c59c259653fa0e22b7b71bd1fbba3fde2f896fc8a0525eb33ccc170f -->
- Python package: `pdomain_book_tools/`, built with Hatchling and managed with uv.
- Tests: `tests/`; repository automation: `scripts/`; documentation: `docs/`.
- Primary project metadata and tool configuration: `pyproject.toml`.
- Supported workflow entry points: `Makefile`.
<!-- <<< repo-setup:repo-facts -->
<!-- >>> repo-setup:commands-and-gates sha256:69cbe1fd91401260b56ec6cf0e234e564e1fed0e0dbf86aa8672b0643775ced9 -->
- `make test` runs the Python test suite.
- `make lint` runs the repository lint workflow.
- `uv run pytest ...` is the direct allow-listed pytest fallback.
- `uv run ruff check ...` and `uv run ruff format ...` are the direct allow-listed Ruff fallbacks.
- `uv run basedpyright ...` is the direct allow-listed type-check fallback.
- Verified repository scripts include `scripts/local-dev.sh`, `scripts/local-check.sh`, and `scripts/local-upgrade-deps.sh`.
<!-- <<< repo-setup:commands-and-gates -->
<!-- >>> repo-setup:writing-and-review sha256:7790f5372ef07c7909c566468403043c7659bf819a9dd204c7fc63aab866d250 -->
- Route new durable reader-facing documents through the `writing-docs:write-readably` skill.
- Route edits of existing prose through the `writing-docs:edit-for-readability` skill.
- Use `adversarial-review:adversarial-review` when the consuming plugin's policy requires it.
- For Python changes, follow the `writing-python:writing-python` skill and its mandatory gate.
<!-- <<< repo-setup:writing-and-review -->
