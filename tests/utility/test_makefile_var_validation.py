"""Tests that developer-only Makefile targets reject malicious variables.

``layout-fork-pin`` and ``layout-fork-update`` interpolate command-line
Make variables (``SHA``, ``HF_LAYOUT_*``) into shell recipes. Without
validation, a value like ``SHA='x; touch pwned'`` would be a
command-injection surface. These tests confirm the strict regex guards
reject such input before any recipe body runs.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_MAKE = shutil.which("make") or "make"


def _run_make(args: list[str], tmp_path: Path) -> subprocess.CompletedProcess[str]:
    # Args are test-controlled literals; injection is exactly what we assert
    # the Makefile guards reject, so passing them through is intentional.
    return subprocess.run(  # noqa: S603
        [_MAKE, "--no-print-directory", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        # Keep developer commands hermetic — no network, no real venv work.
        timeout=60,
    )


def test_layout_fork_pin_rejects_injected_sha(tmp_path: Path):
    sentinel = tmp_path / "pwned"
    malicious = f"deadbeef; touch {sentinel}"
    proc = _run_make(["layout-fork-pin", f"SHA={malicious}"], tmp_path)
    assert proc.returncode != 0
    assert not sentinel.exists(), "injected command executed"
    assert "Invalid SHA" in (proc.stdout + proc.stderr)


def test_layout_fork_pin_rejects_non_hex_sha(tmp_path: Path):
    proc = _run_make(["layout-fork-pin", "SHA=not-a-sha"], tmp_path)
    assert proc.returncode != 0
    assert "Invalid SHA" in (proc.stdout + proc.stderr)


def test_layout_fork_update_rejects_injected_repo_id(tmp_path: Path):
    sentinel = tmp_path / "pwned-update"
    malicious = f"owner/name; touch {sentinel}"
    proc = _run_make(["layout-fork-update", f"HF_LAYOUT_FORK={malicious}"], tmp_path)
    assert proc.returncode != 0
    assert not sentinel.exists(), "injected command executed"
    assert "Invalid HF_LAYOUT_FORK" in (proc.stdout + proc.stderr)
