# Layout Regression Debug — Auto-Cleanup on Test Run

**Date:** 2026-05-30
**Status:** approved

## Problem

`tests/fixtures/layout_regression/debug/` accumulates timestamped subdirectories
(`test-*`, `regen-*`) from every debug-enabled test run. The only way to reclaim
disk is a manual `make clean-debug`. Old runs accumulate silently.

## Goal

Automatically prune debug subdirectories older than 24 hours at the start of
every pytest session — regardless of whether `PD_OCR_LAYOUT_DEBUG` is set.

## What changes

### `tests/conftest.py`

Add a `pytest_sessionstart` hook and a private `_prune_old_debug_runs` helper:

```python
def _prune_old_debug_runs(max_age_seconds: int = 86_400) -> None:
    import shutil, time
    debug_dir = Path(__file__).parent / "fixtures" / "layout_regression" / "debug"
    if not debug_dir.is_dir():
        return
    cutoff = time.time() - max_age_seconds
    for child in debug_dir.iterdir():
        if child.is_dir() and child.name.startswith(("test-", "regen-")):
            if child.stat().st_mtime < cutoff:
                logger.debug("pruning old debug run: %s", child.name)
                shutil.rmtree(child, ignore_errors=True)

def pytest_sessionstart(session: pytest.Session) -> None:
    _prune_old_debug_runs()
```

Key properties:
- Path is resolved relative to `conftest.py`, not `cwd` — safe under xdist workers.
- Skips silently when `debug/` does not exist.
- Uses `ignore_errors=True` so a concurrent writer in a separate process can't crash the session.
- Logs at `DEBUG` level only — silent in normal `make test` output.
- Runs before collection, so it cannot race with active writers in the same session.

## What does not change

- `PD_OCR_LAYOUT_DEBUG` instrumentation in `reorganize_page_utils.py` and
  `visualize.py` — kept as permanent diagnostic tooling, env-var gated.
- `make clean-debug` — retained for manual full-wipe.
- All Makefile test targets — no `PD_OCR_LAYOUT_DEBUG` added; debug stays off
  by default.

## No new dependencies

`shutil`, `time`, `pathlib`, and `logging` are all stdlib. A module-level
`logger = logging.getLogger(__name__)` will be added to `conftest.py`.

## Acceptance criteria

1. `make test` with no env vars: `debug/` subdirs older than 24 h are removed;
   newer ones are untouched.
2. `make test` when `debug/` does not exist: session starts without error.
3. `make test` with `PD_OCR_LAYOUT_DEBUG=1`: new debug run is written; previous
   runs older than 24 h are removed before the new one starts.
4. `make clean-debug` still works as before.
