---
Status: implemented
Owner: CT
Created: 2026-05-30
Last verified: 2026-07-13
Kind: plan
---

# Layout Regression Debug Auto-Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Auto-prune `tests/fixtures/layout_regression/debug/` subdirs older than 24 hours at the start of every pytest session.

**Architecture:** A `pytest_sessionstart` hook in `tests/conftest.py` calls a private `_prune_old_debug_runs` helper that scans the debug directory and removes stale timestamped subdirs. No env-var gate — runs unconditionally on every session.

**Tech Stack:** Python stdlib only (`pathlib`, `shutil`, `time`, `logging`). pytest hook API.

**Spec:** `docs/specs/2026-05-30-layout-debug-auto-cleanup.md`

---

## File Map

| Action | Path |
|--------|------|
| Modify | `tests/conftest.py` |
| New test | `tests/test_debug_cleanup.py` |

---

### Task 1: Write the failing test

**Files:**

- Create: `tests/test_debug_cleanup.py`

- [ ] **Step 1: Create the test file**

```python
# tests/test_debug_cleanup.py
import time
from pathlib import Path

import pytest

from tests.conftest import _prune_old_debug_runs  # will fail until implemented


def _make_debug_dir(tmp_path: Path, name: str, age_seconds: float) -> Path:
    """Create a fake debug subdir with a backdated mtime."""
    d = tmp_path / name
    d.mkdir()
    (d / "report.txt").write_text("x")
    mtime = time.time() - age_seconds
    import os
    os.utime(d, (mtime, mtime))
    return d


def test_old_dirs_are_removed(tmp_path: Path) -> None:
    old = _make_debug_dir(tmp_path, "test-20260101_120000", age_seconds=90_000)
    _prune_old_debug_runs(debug_dir=tmp_path, max_age_seconds=86_400)
    assert not old.exists(), "dir older than 24 h should be removed"


def test_recent_dirs_are_kept(tmp_path: Path) -> None:
    recent = _make_debug_dir(tmp_path, "test-20260530_120000", age_seconds=3_600)
    _prune_old_debug_runs(debug_dir=tmp_path, max_age_seconds=86_400)
    assert recent.exists(), "dir younger than 24 h should be kept"


def test_non_matching_dirs_are_kept(tmp_path: Path) -> None:
    other = _make_debug_dir(tmp_path, "something-else", age_seconds=90_000)
    _prune_old_debug_runs(debug_dir=tmp_path, max_age_seconds=86_400)
    assert other.exists(), "dirs not matching test-*/regen-* should not be touched"


def test_missing_debug_dir_is_silent(tmp_path: Path) -> None:
    absent = tmp_path / "debug"
    # must not raise
    _prune_old_debug_runs(debug_dir=absent, max_age_seconds=86_400)


def test_regen_dirs_are_also_pruned(tmp_path: Path) -> None:
    old = _make_debug_dir(tmp_path, "regen-20260101_120000", age_seconds=90_000)
    _prune_old_debug_runs(debug_dir=tmp_path, max_age_seconds=86_400)
    assert not old.exists(), "regen-* dirs older than 24 h should be removed"
```

- [ ] **Step 2: Run to confirm import fails**

```bash
cd /workspaces/ocr-container/pdomain-book-tools
uv run pytest tests/test_debug_cleanup.py -v 2>&1 | head -20
```

Expected: `ImportError: cannot import name '_prune_old_debug_runs'`

---

### Task 2: Implement `_prune_old_debug_runs` in conftest.py

**Files:**

- Modify: `tests/conftest.py`

- [ ] **Step 1: Add imports at the top of `tests/conftest.py`**

Current first two lines:

```python
import os

import pytest
```

Replace with:

```python
import logging
import os
import shutil
import time
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)
```

- [ ] **Step 2: Add the helper and hook after the existing imports block (before `_is_cuda_available`)**

Insert after the logger line, before line `# GPU/CUDA Testing Configuration`:

```python
# Debug output cleanup ========================================================

_LAYOUT_DEBUG_DIR = (
    Path(__file__).parent / "fixtures" / "layout_regression" / "debug"
)


def _prune_old_debug_runs(
    debug_dir: Path = _LAYOUT_DEBUG_DIR,
    max_age_seconds: int = 86_400,
) -> None:
    if not debug_dir.is_dir():
        return
    cutoff = time.time() - max_age_seconds
    for child in debug_dir.iterdir():
        if child.is_dir() and child.name.startswith(("test-", "regen-")):
            if child.stat().st_mtime < cutoff:
                logger.debug("pruning old debug run: %s", child.name)
                shutil.rmtree(child, ignore_errors=True)


def pytest_sessionstart(session: pytest.Session) -> None:  # noqa: ARG001
    _prune_old_debug_runs()
```

- [ ] **Step 3: Run the tests to confirm they pass**

```bash
cd /workspaces/ocr-container/pdomain-book-tools
uv run pytest tests/test_debug_cleanup.py -v
```

Expected: 5 tests PASSED

- [ ] **Step 4: Run full suite to confirm nothing regressed**

```bash
cd /workspaces/ocr-container/pdomain-book-tools
make test AI=1
```

Expected: all tests pass, no new failures.

- [ ] **Step 5: Commit**

```bash
cd /workspaces/ocr-container/pdomain-book-tools
git add tests/conftest.py tests/test_debug_cleanup.py
git commit -m "feat(tests): auto-prune layout debug runs older than 24 h

Adds _prune_old_debug_runs() helper and pytest_sessionstart hook to
tests/conftest.py. Old test-* / regen-* subdirs under
tests/fixtures/layout_regression/debug/ are removed at the start of
every pytest session, unconditionally.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 3: Verify make ci is green

**Files:** (none changed)

- [ ] **Step 1: Run full CI check**

```bash
cd /workspaces/ocr-container/pdomain-book-tools
make ci AI=1
```

Expected: exits 0. Check `.ci-ai.log` if any step fails.

- [ ] **Step 2: Confirm Makefile has no accidental debug flag**

```bash
grep -n "PD_OCR_LAYOUT_DEBUG" /workspaces/ocr-container/pdomain-book-tools/Makefile
```

Expected: no output (the flag must not appear in any Makefile target).

---

## Self-Review

**Spec coverage:**

| Spec requirement | Task |
|-----------------|------|
| Prune dirs older than 24 h on every session | Task 2, `pytest_sessionstart` hook |
| Skip silently when debug/ absent | Task 1 `test_missing_debug_dir_is_silent`, Task 2 `if not debug_dir.is_dir()` |
| Path relative to conftest, not cwd | Task 2, `Path(__file__).parent / ...` |
| `ignore_errors=True` on rmtree | Task 2 |
| Log at DEBUG only | Task 2, `logger.debug(...)` |
| Runs before collection | pytest hook `pytest_sessionstart` fires before collection by spec |
| No env-var gate | hook has no conditional |
| make clean-debug unchanged | not touched |
| No new deps | stdlib only |
| `PD_OCR_LAYOUT_DEBUG` absent from Makefile targets | Task 3 step 2 |

All acceptance criteria covered. No placeholders. No FastAPI+SPA milestone needed (this is a pure Python library).

## Goal

Remove timestamped layout-regression debug directories older than 24 hours at
the start of every pytest session.

## Architecture

A `pytest_sessionstart` hook in `tests/conftest.py` calls
`_prune_old_debug_runs`, which scans the debug directory relative to
`conftest.py`. The helper removes stale `test-*` and `regen-*`
subdirectories and leaves recent, non-matching, or absent directories alone.

## Tech Stack

The implementation uses the pytest hook API and Python standard-library
`pathlib`, `shutil`, `time`, and `logging` modules. Tests use
pytest's `tmp_path` fixture.

## Global Constraints

Run cleanup unconditionally before collection, with no environment-variable
gate and no new dependency. Resolve the debug path independently of the current
working directory, log only at DEBUG, use `ignore_errors=True`, and leave the
existing `make clean-debug` behavior unchanged.
