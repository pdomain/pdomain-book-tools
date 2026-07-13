---
Status: implemented
Owner: CT
Created: 2026-05-07
Last verified: 2026-07-13
Kind: spec
---

# Spec: dev-local-aware `upgrade-deps` flow

> **Status**: Implemented — the optional DocTR-from-Git signal is deferred in the intent map
> **Last updated**: 2026-05-22

Status: **shipped** (2026-05). All required behavior in §2 landed across
commits `ba267f3` (refuse-rather-than-clobber `upgrade-deps` +
`upgrade-deps-local`) and `68c64e2` (`make dev-local` recipe + marker
writer). This document is retained as the canonical contract this repo
exposes to its downstream pdomain-* consumers — the Makefile recipes and
`scripts/check_dev_local.py` are the implementation; deviations from
this spec should update both.

Implementation pointers:

- `Makefile` targets `check-dev-local`, `dev-local`, `upgrade-deps`,
  `upgrade-deps-local`, `sync-gpu`.
- `scripts/check_dev_local.py` — detection logic (exit-code contract,
  `--quiet` mode).
- `scripts/write_dev_local_marker.py` — writes `.venv/.pdomain-dev-local`.

Open follow-up tracked in `docs/ROADMAP.md` ("doctr-from-git probe"):
whether non-canonical `python-doctr` install URLs should auto-flag
dev-local mode without a marker file. Deferred until a concrete
fork-pin workflow needs it.

## 1. Problem

`make upgrade-deps` currently ends with:

```make
upgrade-deps: ## Upgrade dependencies and sync local environment
    uv lock --upgrade
    uv sync --group dev
```

`uv sync --group dev` (no extras, no overrides) silently reverts a venv
that was put into **dev-local mode** — editable sibling pdomain-* checkouts
(`pdomain-book-tools` linked from a local working copy by the consuming
repo), `[gpu]` extras pinned, doctr-from-git, etc. — back to the
canonical published / CPU baseline. The user discovers this only when
their next test run uses the published wheel instead of the working
tree.

The same hazard applies to any other recipe in this repo that
unconditionally runs `uv sync --group dev` on a venv that may have
been customized (today: `upgrade-deps`; in the future: anything else
that rebuilds the environment).

The workspace is standardizing the fix across all `pdomain-*` repos. As
the foundation library, this repo also defines the **detection
contract** that downstream repos consume.

## 2. Required behavior

### 2.1 Detect mode before clobbering

`upgrade-deps` (and any future recipe that rebuilds the venv) MUST
detect whether the current venv is in dev-local vs canonical mode
**before** running `uv sync`. Canonical-mode behavior is unchanged.

### 2.2 Detection mechanism — preferred order

1. **Probe `uv pip show <key-pdomain-package>` for an `Editable project
   location` field.** Robust, no marker file, no env var, survives
   manual editable installs done outside `make dev-local`. This is
   the preferred mechanism.

   In this repo, the key package downstream repos probe is
   **`pdomain-book-tools`** itself (a downstream venv is "in dev-local
   mode" when its `pdomain-book-tools` install points at a local sibling
   checkout). For *this* repo's own venv, the equivalent question is
   "is doctr / opencv-python / cupy / any sibling-style editable
   override in place?" — see §4 for the in-repo check.

2. **Fallback: marker file written by `make dev-local`.** Lifecycle
   anchored to the venv (e.g. `.venv/.pdomain-dev-local`) so a venv
   rebuild kills the marker automatically — no stale-marker class of
   bug.

3. **Last resort: `PDOMAIN_DEV_LOCAL=1` env var.** Opt-in escape hatch
   for users who want to force-flag dev-local mode without touching
   the venv (e.g. CI experiments).

### 2.3 UX on detection — refuse, don't clobber

Default behavior when dev-local mode is detected: **refuse with a
clear message.** Example:

```text
make: *** venv is in dev-local mode (pdomain-book-tools editable from
       /workspaces/ocr-container/pdomain-book-tools, [gpu] extra active).
       Refusing to clobber it with `uv sync --group dev`.

       Run `make upgrade-deps-local` to upgrade and restore dev-local
       mode in one shot, or `make dev` to return to canonical mode
       first.
```

A sibling recipe `upgrade-deps-local` MUST exist that does:

1. `uv lock --upgrade`
2. `uv sync --group dev` (canonical sync, replays lockfile)
3. Restore dev-local overrides (re-run whatever `make dev-local`
   does — editable sibling installs, `[gpu]` extra, doctr-from-git,
   etc.)

…in one shot. Users in dev-local mode should never have to think
about which recipe to run; they run `upgrade-deps-local` and the
venv ends up in the same shape it started, only with upgraded
pinned versions.

### 2.4 Canonical-mode behavior unchanged

If detection finds no dev-local signal, `upgrade-deps` behaves
exactly as today (`uv lock --upgrade && uv sync --group dev`). No
new prompts, no new env-var requirements, no behavior change for
the default path.

### 2.5 Cross-platform

Both Linux (devcontainer, CI) and macOS dev hosts. Detection MUST
NOT rely on GNU-specific `grep`/`sed` flags or Linux-only paths.
`uv pip show` output and shell-portable parsing only.

## 3. Foundation-library contract for downstream repos

This is the load-bearing part of this spec for sibling repos:

**Downstream pdomain-* repos (`pdomain-ocr-cli`, `pdomain-ocr-labeler-spa`,
`pdomain-ocr-labeler-spa`, `pdomain-ocr-training`, `pdomain-prep-for-pgdp`) probe
`uv pip show pdomain-book-tools` and look for an `Editable project
location:` line.** If present, the venv is treated as dev-local.

For that probe to be meaningful, **the `make dev-local` recipe in
*this* repo, and any equivalent in downstream repos that installs
`pdomain-book-tools` from a local checkout, MUST install `pdomain-book-tools`
editably** (`uv pip install -e ../pdomain-book-tools` or equivalent).
A non-editable `uv pip install ../pdomain-book-tools` would still pull
from the local checkout but would not surface the
`Editable project location` field, breaking the detection contract
silently.

This means: any future change to how `make dev-local` (or the
in-repo equivalent) installs sibling pdomain-* packages MUST keep the
editable install. Non-editable shortcuts here are a contract break
for every consumer.

## 4. In-repo dev-local mode

This repo's `make dev-local` recipe runs `sync-gpu` (which applies
the `[gpu]` extra when an NVIDIA GPU is auto-detected) and writes
the `.venv/.pdomain-dev-local` marker via
`scripts/write_dev_local_marker.py`. The signals that put *this*
repo's venv into dev-local mode are narrower than for downstream
repos (it has no pdomain-* siblings to install editably), but still real:

- `[gpu]` extra active (`uv sync --group dev --extra gpu` —
  `make sync-gpu` does this conditionally on GPU autodetect).
- doctr-from-git override (the `python-doctr` fork-aware path; see
  `make layout-fork-info`).
- Any manual `uv pip install -e <some-fork>` the user has layered
  on (e.g. a local opencv build).

For this repo, the in-venv check is "is anything editable, or is
the `[gpu]` extra installed, that the canonical `uv sync --group dev`
would *remove*?" Implementation can lean on the marker file
(§2.2.2) for this since the auto-detect for GPU already exists in
`sync-gpu`.

## 5. Implementation notes (non-binding)

These are sketches for the follow-up pass; they don't constrain the
final implementation.

- A small shell function, e.g. `_check_dev_local`, called at the
  top of `upgrade-deps`. Returns 0 if dev-local detected, 1 if
  canonical. Single source of truth that other recipes can reuse.
- The marker file (§2.2.2) should be written by `make dev-local`
  with enough content to be self-explanatory if a user `cat`s it
  (e.g. timestamp, what extras / overrides were applied).
- The refusal message MUST name the recipe to run instead
  (`make upgrade-deps-local`) — don't make users grep the Makefile.
- Pre-existing `make sync-gpu` already does conditional `--extra gpu`
  syncing based on GPU autodetect. The dev-local detection should
  compose with it cleanly: if a user is on a GPU box and has
  dev-local mode active, `upgrade-deps-local` must end in a venv
  that has both `[gpu]` and the local overrides.

## 6. Out of scope

- Auto-detecting which sibling pdomain-* checkouts to install editably.
  `make dev-local` is explicit; this spec doesn't try to guess.
- Replicating `uv sync` semantics in shell. Detection only; the
  actual sync is still `uv` doing the work.
- Publishing a separate "dev-local lockfile". Same lockfile, just
  layered overrides on top.

## 7. References

- Workspace memory:
  `/workspaces/ocr-container/.claude/agent-memory/pdomain-book-tools/release_strategy_self_hosted_index.md`
- Current `upgrade-deps` recipe: `Makefile:97-102`.
- Conditional GPU sync precedent: `Makefile:87-95` (`sync-gpu`).

## TL;DR

Not yet captured during the B3 mechanical migration.

## Context

Not yet captured during the B3 mechanical migration.

## Constraints

Not yet captured during the B3 mechanical migration.

## Decision

Not yet captured during the B3 mechanical migration.

## Contract / Acceptance

Not yet captured during the B3 mechanical migration.

## Trade-offs considered

Not yet captured during the B3 mechanical migration.

## Consequences

Not yet captured during the B3 mechanical migration.

## Open questions

Not yet captured during the B3 mechanical migration.

## References

Not yet captured during the B3 mechanical migration.

## Adversarial Review

- **Stage:** Migration/post-implementation review performed 2026-07-13.
- **Source:** Current `Makefile`, `scripts/check_dev_local.py`, `scripts/write_dev_local_marker.py`, `scripts/local-dev.sh`, `scripts/local-upgrade-deps.sh`, and focused utility tests. The 24 focused tests passed, although the targeted pytest command failed the repository-wide coverage threshold because it ran only these tests.
- **Accepted findings (and how folded in):** Record the shipped `local-*` targets as canonical and the `dev-local` targets as deprecated aliases; reconcile the restore recipe with the promised `--group dev` flow; remove or implement the advertised `PDOMAIN_DEV_LOCAL=0` clobber escape; consolidate the two-marker contract; and keep the DocTR-from-Git probe explicitly deferred rather than describing it as detected.
- **Disposition:** Accepted corrections and unresolved ideas are preserved in `docs/context/intent-map.md` as deferred work or owner decisions; the source body remains unchanged pending its next evidence-backed revision.
- **Residual risks:** No test executes the Make recipes end to end or proves that every pre-upgrade override is restored. Manual editable forks and DocTR URL overrides can still be missed, and marker-only restoration currently assumes GPU mode rather than preserving an arbitrary prior environment.
