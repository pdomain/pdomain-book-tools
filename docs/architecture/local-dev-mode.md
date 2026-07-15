---
Status: built
Owner: CT
Created: 2026-07-15
Last verified: 2026-07-15
Kind: architecture
---

# Local-Dev Mode

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Read when:** touching the local-dev detection logic, the `[gpu]` extra
  reapply path, the marker lifecycle, or any recipe that rebuilds the venv.
- **Search terms:** local-dev, dev-local, upgrade-deps guard, GPU extras,
  editable install probe, marker file, PDOMAIN_DEV_LOCAL.

Local-dev mode marks a venv that carries overrides the canonical sync would
silently revert. In this repo, the usual override is the `[gpu]` extra. Any
foreign editable install here fires the same detection. Downstream repos add
editable sibling checkouts.

`make upgrade-deps` detects the mode and refuses to clobber it. The
`local-*` targets manage the mode. No other Make target is guarded. See the
caveat below.

## The three canonical targets

The supported workflow is three Make targets, shipped under spec #362:

- `make local-dev` — enter local-dev mode. Runs `uv sync --extra gpu`, then
  writes both marker files (see below).
- `make local-check` — print the current mode plus the installed torch
  version and location. Note the script prints `registry` as the name of
  the non-local (canonical) state.
- `make local-upgrade-deps` — upgrade deps while staying in local-dev mode.
  Refuses when the shell marker is absent.

The older names `dev-local`, `check-dev-local`, and `upgrade-deps-local` are
deprecated aliases. Each prints a warning and forwards to its `local-*`
replacement.

## How the upgrade-deps guard works

When the venv is in local-dev mode, `make upgrade-deps` refuses to run
instead of clobbering it, because its `uv sync --group dev` would revert
every override. Detection is two-tier:

1. `scripts/check_dev_local.py` exits 1 (dev-local) when any of these
   signals fire:
   - an editable install other than this project at the repo root
   - a `[gpu]` extra package (`cupy-cuda12x`, `opencv-cuda`)
   - the `.venv/.pdomain-dev-local` marker
   - a truthy `PDOMAIN_DEV_LOCAL` env var

   It exits 0 (canonical) otherwise, and supports `--quiet` for Makefile
   branching.
2. A shell fallback in the Makefile also refuses when
   `.venv/.pdomain-local-mode` exists.

The env var is opt-in only. A falsey value (`PDOMAIN_DEV_LOCAL=0`) adds no
signal of its own, and it does not bypass the other signals. There is no
clobber escape hatch. To upgrade from local-dev mode, run
`make local-upgrade-deps`. To return to canonical mode, rebuild the venv.

**Only `upgrade-deps` is guarded.** These other dependency-syncing targets
run `sync-gpu` instead: `setup`, `test`, `test-slow`, `test-verbose`,
`test-single`, `test-k`, and `coverage`. `sync-gpu` decides the
`--extra gpu` flag purely from an nvidia-smi hardware probe, which is
forced off when `CI` is set. That mechanism never consults the markers,
the env var, or `scripts/check_dev_local.py`, so those targets can
re-sync the venv without a refusal.

On a GPU machine, the auto-detect usually restores the same extras. When
the hardware probe and your actual local-dev state disagree, though, those
targets can still silently revert overrides. This can happen, for example,
when `CI` is set locally or when overrides go beyond the GPU extra.

## The two-marker contract

Entering local-dev mode writes two markers, both inside `.venv/` so a venv
rebuild removes them automatically:

- `.venv/.pdomain-local-mode` — read by the shell scripts
  (`local-check.sh`, `local-upgrade-deps.sh`) and the Makefile fallback.
- `.venv/.pdomain-dev-local` — read by the Python probe; written by
  `scripts/write_dev_local_marker.py`, which `local-dev.sh` invokes.

## What local-upgrade-deps restores

`scripts/local-upgrade-deps.sh` runs `uv lock --upgrade` then
`uv sync --extra gpu`. uv's documented default is to sync the `dev`
dependency group, unless `[tool.uv] default-groups` overrides it. In this
repo, `pyproject.toml` sets no such override. Its `[tool.uv]` block pins
only `required-version >= 0.11.16`. So this single command equals the
canonical dev sync plus the GPU extra. If a `default-groups` override is
ever added to `pyproject.toml`, this equivalence breaks and this section
must be updated. The command restores GPU extras only: manual editable
forks or a DocTR URL override are not re-applied and must be restored by
hand.

## The downstream detection contract

This repo publishes a contract for four downstream `pdomain-*` consumers:
`pdomain-ocr-cli`, `pdomain-ocr-labeler-spa`, `pdomain-ocr-training`, and
`pdomain-prep-for-pgdp`. Under this contract, a downstream venv is
dev-local when `uv pip show pdomain-book-tools` reports an
`Editable project location` line. The shared pattern comes from spec #200.
The `Makefile` guard comment names it the "pdomain-ocr-cli canonical
pattern." This doc records the contract as published here. It is not a
verified audit of each consumer's current code.

Any recipe, here or downstream, that installs `pdomain-book-tools` from a
local checkout MUST install it editably. A non-editable local install still
uses the local code, but it drops the `Editable project location` field.
That silently breaks detection in any consumer that relies on this probe.

Inside this repo, an editable install of `pdomain-book-tools` itself is
exempt from the dev-local signal only when both halves of the check pass:
the package name matches and its editable location resolves to this repo
root. The same package still fires the signal if it is installed editably
from any other path, such as a relocated clone or a symlinked checkout.

## Evidence

- Code: `Makefile` (`upgrade-deps`, `local-dev`, `local-check`,
  `local-upgrade-deps`, deprecated aliases), `scripts/check_dev_local.py`,
  `scripts/write_dev_local_marker.py`, `scripts/local-dev.sh`,
  `scripts/local-check.sh`, `scripts/local-upgrade-deps.sh`
- Config: `pyproject.toml` (`[dependency-groups]` and `[tool.uv]`; the
  restore-equivalence claim above depends on it)
- Tests: `tests/utility/test_check_dev_local.py`,
  `tests/utility/test_write_dev_local_marker.py`
- Verified: 2026-07-15 while retiring
  `docs/specs/07-dev-local-upgrade-flow.md` (last spec revision: commit
  `010d382`; history: [`git log -- docs/specs/07-dev-local-upgrade-flow.md`])

## Residual intent

- Consolidate the two markers into one shared contract. Today the shell and
  Python probes each read their own file.
- Decide whether the project wants an intentional-clobber escape: an env
  var that forces `upgrade-deps` through anyway. The refusal message used
  to advertise `PDOMAIN_DEV_LOCAL=0 make upgrade-deps` as an escape, but no
  code ever implemented that bypass. `check_dev_local.py` treats the env
  var as opt-in only, and the shell marker fallback has no env check at
  all. The misleading message line was removed from the `Makefile` on
  2026-07-15, in the same change that retired the spec and created this
  doc.
- Extend the dev-local guard beyond `upgrade-deps`, or accept that
  `setup`, `test`, and `coverage` rely on the nvidia-smi auto-detect alone.
  See the guard caveat above.
- No test drives the Make recipes end to end. Marker-only restoration
  assumes GPU mode, rather than preserving an arbitrary prior environment.
- The DocTR-from-Git probe would flag non-canonical `python-doctr` install
  URLs as dev-local without a marker. It stays deferred until a concrete
  fork-pin workflow needs it.
