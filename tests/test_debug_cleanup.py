# tests/test_debug_cleanup.py
import os
import time
from pathlib import Path

from tests.conftest import _prune_old_debug_runs  # will fail until implemented


def _make_debug_dir(tmp_path: Path, name: str, age_seconds: float) -> Path:
    """Create a fake debug subdir with a backdated mtime."""
    d = tmp_path / name
    d.mkdir()
    (d / "report.txt").write_text("x")
    mtime = time.time() - age_seconds
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
