"""Developer layout recipes reject invalid environment inputs before mutation."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_JUST = shutil.which("just") or "just"


def _run_just(
    recipe: str, variables: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    # Args are test-controlled literals; injection is exactly what we assert
    # the recipe guards reject, so passing them through is intentional.
    return subprocess.run(  # noqa: S603
        [_JUST, "--quiet", recipe],
        cwd=REPO_ROOT,
        env={**os.environ, **variables},
        capture_output=True,
        text=True,
        check=False,
        # Keep developer commands hermetic — no network, no real venv work.
        timeout=60,
    )


def test_layout_fork_pin_rejects_injected_sha(tmp_path: Path):
    sentinel = tmp_path / "pwned"
    malicious = f"deadbeef; touch {sentinel}"
    proc = _run_just("layout-fork-pin", {"SHA": malicious})
    assert proc.returncode != 0
    assert not sentinel.exists(), "injected command executed"
    assert "Invalid SHA" in (proc.stdout + proc.stderr)


def test_layout_fork_pin_rejects_non_hex_sha(tmp_path: Path):
    proc = _run_just("layout-fork-pin", {"SHA": "not-a-sha"})
    assert proc.returncode != 0
    assert "Invalid SHA" in (proc.stdout + proc.stderr)


def test_layout_fork_update_rejects_injected_repo_id(tmp_path: Path):
    sentinel = tmp_path / "pwned-update"
    malicious = f"owner/name; touch {sentinel}"
    proc = _run_just("layout-fork-update", {"HF_LAYOUT_FORK": malicious})
    assert proc.returncode != 0
    assert not sentinel.exists(), "injected command executed"
    assert "Invalid HF_LAYOUT_FORK" in (proc.stdout + proc.stderr)
