"""Unit tests for ``scripts/check_dev_local.py``.

The script detects whether the current venv is in **dev-local mode** —
i.e. has overrides (the ``[gpu]`` extra, doctr-from-git, sibling-pd-*
editable, or any non-project editable install) that ``uv sync --group
dev`` would silently revert. These tests exercise its pure-function
core via importable helpers so we don't need to spin up a real venv.

Spec: ``docs/specs/07-dev-local-upgrade-flow.md``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_dev_local.py"


def _load_script_module():
    """Load the script as a module. Register in ``sys.modules`` BEFORE
    executing so ``@dataclass`` (which inspects ``cls.__module__``) can
    resolve forward references."""
    spec = importlib.util.spec_from_file_location("check_dev_local", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_dev_local"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def cdl():
    return _load_script_module()


def _pkg(name, version="1.0.0", editable_location=None):
    """Build a fake `uv pip list --format=json` entry."""
    entry = {"name": name, "version": version}
    if editable_location is not None:
        entry["editable_project_location"] = editable_location
    return entry


# ---------------------------------------------------------------------------
# detect_mode contract
# ---------------------------------------------------------------------------


def test_canonical_mode_returns_canonical(cdl, tmp_path):
    """A venv with only the project itself editable + no [gpu] extras
    + no doctr-from-git is canonical. Every downstream `uv sync --group
    dev` of this lockfile should produce this shape."""
    project_root = tmp_path
    pkgs = [
        _pkg("pd-book-tools", editable_location=str(project_root)),
        _pkg("torch"),
        _pkg("python-doctr", "1.0.2"),
    ]
    result = cdl.detect_mode(pkgs, project_root=project_root, marker_path=None)
    assert result.is_dev_local is False
    assert result.reasons == []


def test_gpu_extra_flags_dev_local(cdl, tmp_path):
    """Presence of ``cupy-cuda12x`` (the [gpu] extra) flags dev-local
    because canonical ``uv sync --group dev`` (no ``--extra gpu``)
    would uninstall it."""
    project_root = tmp_path
    pkgs = [
        _pkg("pd-book-tools", editable_location=str(project_root)),
        _pkg("cupy-cuda12x", "14.0.1"),
    ]
    result = cdl.detect_mode(pkgs, project_root=project_root, marker_path=None)
    assert result.is_dev_local is True
    assert any("gpu" in r.lower() for r in result.reasons)


def test_sibling_editable_flags_dev_local(cdl, tmp_path):
    """A sibling pd-* editable install (NOT the project root) flags
    dev-local. This is the canonical downstream signal — the spec
    §3 contract."""
    project_root = tmp_path
    sibling_root = tmp_path.parent / "pd-ocr-cli"
    pkgs = [
        _pkg("pd-book-tools", editable_location=str(project_root)),
        _pkg("pd-ocr-cli", editable_location=str(sibling_root)),
    ]
    result = cdl.detect_mode(pkgs, project_root=project_root, marker_path=None)
    assert result.is_dev_local is True
    assert any("editable" in r.lower() for r in result.reasons)


def test_project_root_editable_does_not_flag(cdl, tmp_path):
    """The project's own editable install is normal (every dev venv has
    it) — it MUST NOT count as a dev-local override."""
    project_root = tmp_path
    pkgs = [_pkg("pd-book-tools", editable_location=str(project_root))]
    result = cdl.detect_mode(pkgs, project_root=project_root, marker_path=None)
    assert result.is_dev_local is False


def test_marker_file_flags_dev_local(cdl, tmp_path):
    """Spec §2.2.2: a marker file written by ``make dev-local`` is the
    fallback signal when the package probe doesn't fire."""
    project_root = tmp_path
    marker = tmp_path / ".pd-dev-local"
    marker.write_text("dev-local since 2026-05-07\n")
    pkgs = [_pkg("pd-book-tools", editable_location=str(project_root))]
    result = cdl.detect_mode(pkgs, project_root=project_root, marker_path=marker)
    assert result.is_dev_local is True
    assert any("marker" in r.lower() for r in result.reasons)


def test_env_var_flags_dev_local(cdl, tmp_path, monkeypatch):
    """Spec §2.2.3: ``PD_DEV_LOCAL=1`` is the last-resort opt-in flag."""
    project_root = tmp_path
    pkgs = [_pkg("pd-book-tools", editable_location=str(project_root))]
    monkeypatch.setenv("PD_DEV_LOCAL", "1")
    result = cdl.detect_mode(pkgs, project_root=project_root, marker_path=None)
    assert result.is_dev_local is True
    assert any("PD_DEV_LOCAL" in r for r in result.reasons)


def test_env_var_zero_does_not_flag(cdl, tmp_path, monkeypatch):
    """``PD_DEV_LOCAL=0`` (or any falsey value) MUST NOT flag — only
    truthy values opt in."""
    project_root = tmp_path
    pkgs = [_pkg("pd-book-tools", editable_location=str(project_root))]
    monkeypatch.setenv("PD_DEV_LOCAL", "0")
    result = cdl.detect_mode(pkgs, project_root=project_root, marker_path=None)
    assert result.is_dev_local is False


def test_multiple_signals_collect_all_reasons(cdl, tmp_path):
    """When several signals fire (gpu extra + sibling editable), all
    reasons appear in the report so the user understands what would
    be clobbered."""
    project_root = tmp_path
    sibling_root = tmp_path.parent / "pd-ocr-cli"
    pkgs = [
        _pkg("pd-book-tools", editable_location=str(project_root)),
        _pkg("pd-ocr-cli", editable_location=str(sibling_root)),
        _pkg("cupy-cuda12x", "14.0.1"),
    ]
    result = cdl.detect_mode(pkgs, project_root=project_root, marker_path=None)
    assert result.is_dev_local is True
    assert len(result.reasons) >= 2


# ---------------------------------------------------------------------------
# CLI exit-code contract
# ---------------------------------------------------------------------------


def test_cli_exit_zero_when_canonical(cdl, tmp_path, monkeypatch, capsys):
    """``check_dev_local`` exits 0 when canonical so the Makefile can
    use ``if scripts/check_dev_local.py; then ... ; fi``-style logic.
    Spec §2.4 — canonical-mode behavior unchanged."""
    project_root = tmp_path
    pkgs = [_pkg("pd-book-tools", editable_location=str(project_root))]
    monkeypatch.setattr(cdl, "_load_pip_list", lambda: pkgs)
    monkeypatch.setattr(cdl, "_project_root", lambda: project_root)
    monkeypatch.setattr(cdl, "_marker_path", lambda: tmp_path / ".pd-dev-local-missing")
    monkeypatch.delenv("PD_DEV_LOCAL", raising=False)
    rc = cdl.main([])
    assert rc == 0


def test_cli_exit_one_when_dev_local(cdl, tmp_path, monkeypatch):
    """``check_dev_local`` exits 1 when dev-local so the Makefile can
    branch and refuse to run a clobbering ``uv sync``."""
    project_root = tmp_path
    sibling_root = tmp_path.parent / "pd-ocr-cli"
    pkgs = [
        _pkg("pd-book-tools", editable_location=str(project_root)),
        _pkg("pd-ocr-cli", editable_location=str(sibling_root)),
    ]
    monkeypatch.setattr(cdl, "_load_pip_list", lambda: pkgs)
    monkeypatch.setattr(cdl, "_project_root", lambda: project_root)
    monkeypatch.setattr(cdl, "_marker_path", lambda: tmp_path / ".pd-dev-local-missing")
    monkeypatch.delenv("PD_DEV_LOCAL", raising=False)
    rc = cdl.main([])
    assert rc == 1


def test_cli_quiet_flag_suppresses_output(cdl, tmp_path, monkeypatch, capsys):
    """``--quiet`` suppresses the human-readable summary so the script
    can be used purely for its exit code."""
    project_root = tmp_path
    pkgs = [
        _pkg("pd-book-tools", editable_location=str(project_root)),
        _pkg("cupy-cuda12x", "14.0.1"),
    ]
    monkeypatch.setattr(cdl, "_load_pip_list", lambda: pkgs)
    monkeypatch.setattr(cdl, "_project_root", lambda: project_root)
    monkeypatch.setattr(cdl, "_marker_path", lambda: tmp_path / ".pd-dev-local-missing")
    monkeypatch.delenv("PD_DEV_LOCAL", raising=False)
    rc = cdl.main(["--quiet"])
    assert rc == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
