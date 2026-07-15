"""Unit tests for ``scripts/check_dev_local.py``.

The script detects whether the current venv is in **dev-local mode** —
i.e. has overrides (the ``[gpu]`` extra, sibling-pdomain-*
editable, or any non-project editable install) that ``uv sync --group
dev`` would silently revert. A DocTR-from-Git probe is deferred, not
implemented — see the architecture doc's Residual intent. These tests exercise its pure-function
core via importable helpers so we don't need to spin up a real venv.

Architecture: ``docs/architecture/local-dev-mode.md``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterable

    from scripts.check_dev_local import DetectionResult, PipListEntry

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_dev_local.py"


if TYPE_CHECKING:

    class _CheckDevLocalModule(Protocol):
        """Typed surface of ``scripts/check_dev_local.py`` exercised by these
        tests. The module itself is loaded dynamically (see
        ``_load_script_module``), so this Protocol is the honest boundary
        between that untyped ``ModuleType`` and the rest of the test file."""

        def detect_mode(
            self,
            pip_list: Iterable[PipListEntry],
            *,
            project_root: Path,
            marker_path: Path | None,
            env: dict[str, str] | None = None,
        ) -> DetectionResult: ...

        def main(self, argv: list[str] | None = None) -> int: ...

        def _load_pip_list(self) -> list[PipListEntry]: ...

        def _project_root(self) -> Path: ...

        def _marker_path(self) -> Path: ...


def _load_script_module() -> _CheckDevLocalModule:
    """Load the script as a module. Register in ``sys.modules`` BEFORE
    executing so ``@dataclass`` (which inspects ``cls.__module__``) can
    resolve forward references."""
    spec = importlib.util.spec_from_file_location("check_dev_local", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_dev_local"] = module
    spec.loader.exec_module(module)
    # `module` is a dynamically loaded `ModuleType`; there is no static way
    # to prove it matches `_CheckDevLocalModule` short of loading it, which
    # is exactly what this function does. Narrowest honest boundary cast.
    return cast("_CheckDevLocalModule", module)


@pytest.fixture(scope="module")
def cdl() -> _CheckDevLocalModule:
    return _load_script_module()


def _pkg(
    name: str, version: str = "1.0.0", editable_location: str | None = None
) -> PipListEntry:
    """Build a fake `uv pip list --format=json` entry."""
    entry: PipListEntry = {"name": name, "version": version}
    if editable_location is not None:
        entry["editable_project_location"] = editable_location
    return entry


# ---------------------------------------------------------------------------
# detect_mode contract
# ---------------------------------------------------------------------------


def test_canonical_mode_returns_canonical(
    cdl: _CheckDevLocalModule, tmp_path: Path
) -> None:
    """A venv with only the project itself editable + no [gpu] extras
    is canonical (a registry-pinned python-doctr install included). Every
    downstream `uv sync --group dev` of this lockfile should produce
    this shape."""
    project_root = tmp_path
    pkgs = [
        _pkg("pdomain-book-tools", editable_location=str(project_root)),
        _pkg("torch"),
        _pkg("python-doctr", "1.0.2"),
    ]
    result = cdl.detect_mode(pkgs, project_root=project_root, marker_path=None)
    assert result.is_dev_local is False
    assert result.reasons == []


def test_gpu_extra_flags_dev_local(cdl: _CheckDevLocalModule, tmp_path: Path) -> None:
    """Presence of ``cupy-cuda12x`` (the [gpu] extra) flags dev-local
    because canonical ``uv sync --group dev`` (no ``--extra gpu``)
    would uninstall it."""
    project_root = tmp_path
    pkgs = [
        _pkg("pdomain-book-tools", editable_location=str(project_root)),
        _pkg("cupy-cuda12x", "14.0.1"),
    ]
    result = cdl.detect_mode(pkgs, project_root=project_root, marker_path=None)
    assert result.is_dev_local is True
    assert any("gpu" in r.lower() for r in result.reasons)


def test_sibling_editable_flags_dev_local(
    cdl: _CheckDevLocalModule, tmp_path: Path
) -> None:
    """A sibling pdomain-* editable install (NOT the project root) flags
    dev-local. This is the canonical downstream signal — the spec
    §3 contract."""
    project_root = tmp_path
    sibling_root = tmp_path.parent / "pdomain-ocr-cli"
    pkgs = [
        _pkg("pdomain-book-tools", editable_location=str(project_root)),
        _pkg("pdomain-ocr-cli", editable_location=str(sibling_root)),
    ]
    result = cdl.detect_mode(pkgs, project_root=project_root, marker_path=None)
    assert result.is_dev_local is True
    assert any("editable" in r.lower() for r in result.reasons)


def test_project_root_editable_does_not_flag(
    cdl: _CheckDevLocalModule, tmp_path: Path
) -> None:
    """The project's own editable install is normal (every dev venv has
    it) — it MUST NOT count as a dev-local override."""
    project_root = tmp_path
    pkgs = [_pkg("pdomain-book-tools", editable_location=str(project_root))]
    result = cdl.detect_mode(pkgs, project_root=project_root, marker_path=None)
    assert result.is_dev_local is False


def test_marker_file_flags_dev_local(cdl: _CheckDevLocalModule, tmp_path: Path) -> None:
    """Spec §2.2.2: a marker file written by ``make dev-local`` is the
    fallback signal when the package probe doesn't fire."""
    project_root = tmp_path
    marker = tmp_path / ".pdomain-dev-local"
    marker.write_text("dev-local since 2026-05-07\n")
    pkgs = [_pkg("pdomain-book-tools", editable_location=str(project_root))]
    result = cdl.detect_mode(pkgs, project_root=project_root, marker_path=marker)
    assert result.is_dev_local is True
    assert any("marker" in r.lower() for r in result.reasons)


def test_env_var_flags_dev_local(
    cdl: _CheckDevLocalModule, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Spec §2.2.3: ``PDOMAIN_DEV_LOCAL=1`` is the last-resort opt-in flag."""
    project_root = tmp_path
    pkgs = [_pkg("pdomain-book-tools", editable_location=str(project_root))]
    monkeypatch.setenv("PDOMAIN_DEV_LOCAL", "1")
    result = cdl.detect_mode(pkgs, project_root=project_root, marker_path=None)
    assert result.is_dev_local is True
    assert any("PDOMAIN_DEV_LOCAL" in r for r in result.reasons)


def test_env_var_zero_does_not_flag(
    cdl: _CheckDevLocalModule, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``PDOMAIN_DEV_LOCAL=0`` (or any falsey value) MUST NOT flag — only
    truthy values opt in."""
    project_root = tmp_path
    pkgs = [_pkg("pdomain-book-tools", editable_location=str(project_root))]
    monkeypatch.setenv("PDOMAIN_DEV_LOCAL", "0")
    result = cdl.detect_mode(pkgs, project_root=project_root, marker_path=None)
    assert result.is_dev_local is False


def test_multiple_signals_collect_all_reasons(
    cdl: _CheckDevLocalModule, tmp_path: Path
) -> None:
    """When several signals fire (gpu extra + sibling editable), all
    reasons appear in the report so the user understands what would
    be clobbered."""
    project_root = tmp_path
    sibling_root = tmp_path.parent / "pdomain-ocr-cli"
    pkgs = [
        _pkg("pdomain-book-tools", editable_location=str(project_root)),
        _pkg("pdomain-ocr-cli", editable_location=str(sibling_root)),
        _pkg("cupy-cuda12x", "14.0.1"),
    ]
    result = cdl.detect_mode(pkgs, project_root=project_root, marker_path=None)
    assert result.is_dev_local is True
    assert len(result.reasons) >= 2


# ---------------------------------------------------------------------------
# CLI exit-code contract
# ---------------------------------------------------------------------------


def test_cli_exit_zero_when_canonical(
    cdl: _CheckDevLocalModule,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``check_dev_local`` exits 0 when canonical so the Makefile can
    use ``if scripts/check_dev_local.py; then ... ; fi``-style logic.
    Spec §2.4 — canonical-mode behavior unchanged."""
    project_root = tmp_path
    pkgs = [_pkg("pdomain-book-tools", editable_location=str(project_root))]
    monkeypatch.setattr(cdl, "_load_pip_list", lambda: pkgs)
    monkeypatch.setattr(cdl, "_project_root", lambda: project_root)
    monkeypatch.setattr(
        cdl, "_marker_path", lambda: tmp_path / ".pdomain-dev-local-missing"
    )
    monkeypatch.delenv("PDOMAIN_DEV_LOCAL", raising=False)
    rc = cdl.main([])
    assert rc == 0


def test_cli_exit_one_when_dev_local(
    cdl: _CheckDevLocalModule, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``check_dev_local`` exits 1 when dev-local so the Makefile can
    branch and refuse to run a clobbering ``uv sync``."""
    project_root = tmp_path
    sibling_root = tmp_path.parent / "pdomain-ocr-cli"
    pkgs = [
        _pkg("pdomain-book-tools", editable_location=str(project_root)),
        _pkg("pdomain-ocr-cli", editable_location=str(sibling_root)),
    ]
    monkeypatch.setattr(cdl, "_load_pip_list", lambda: pkgs)
    monkeypatch.setattr(cdl, "_project_root", lambda: project_root)
    monkeypatch.setattr(
        cdl, "_marker_path", lambda: tmp_path / ".pdomain-dev-local-missing"
    )
    monkeypatch.delenv("PDOMAIN_DEV_LOCAL", raising=False)
    rc = cdl.main([])
    assert rc == 1


def test_cli_quiet_flag_suppresses_output(
    cdl: _CheckDevLocalModule,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--quiet`` suppresses the human-readable summary so the script
    can be used purely for its exit code."""
    project_root = tmp_path
    pkgs = [
        _pkg("pdomain-book-tools", editable_location=str(project_root)),
        _pkg("cupy-cuda12x", "14.0.1"),
    ]
    monkeypatch.setattr(cdl, "_load_pip_list", lambda: pkgs)
    monkeypatch.setattr(cdl, "_project_root", lambda: project_root)
    monkeypatch.setattr(
        cdl, "_marker_path", lambda: tmp_path / ".pdomain-dev-local-missing"
    )
    monkeypatch.delenv("PDOMAIN_DEV_LOCAL", raising=False)
    rc = cdl.main(["--quiet"])
    assert rc == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


# ---------------------------------------------------------------------------
# #200: dev-local-aware upgrade-deps guard — marker filename consistency
# ---------------------------------------------------------------------------


class TestMarkerFilenameConsistency:
    """Regression tests for #200 — upgrade-deps guard uses check_dev_local.py.

    ``local-dev.sh`` writes ``.venv/.pdomain-local-mode``.
    ``check_dev_local.py`` must detect the mode regardless of which marker
    filename is present, so the two-tier Makefile guard works end-to-end.
    """

    def test_pdomain_local_mode_marker_detected(
        self, cdl: _CheckDevLocalModule, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The .pdomain-local-mode marker written by local-dev.sh must be detected
        as dev-local mode (so upgrade-deps refuses when local-dev is active)."""
        project_root = tmp_path
        # Write the marker that local-dev.sh creates
        marker = tmp_path / ".pdomain-local-mode"
        marker.touch()

        pkgs = [
            _pkg("pdomain-book-tools", editable_location=str(project_root)),
            _pkg("torch"),
        ]
        monkeypatch.setattr(cdl, "_load_pip_list", lambda: pkgs)
        monkeypatch.setattr(cdl, "_project_root", lambda: project_root)
        monkeypatch.setattr(cdl, "_marker_path", lambda: marker)
        monkeypatch.delenv("PDOMAIN_DEV_LOCAL", raising=False)

        rc = cdl.main(["--quiet"])
        assert rc == 1, (
            "check_dev_local must exit 1 (dev-local) when .pdomain-local-mode exists, "
            "so that upgrade-deps refuses rather than clobbering the local-dev venv"
        )

    def test_gpu_extra_detected_without_marker(
        self, cdl: _CheckDevLocalModule, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GPU extra alone (no marker) must still trigger dev-local detection.
        This covers the two-tier case: editable/GPU probe fires even when the
        marker file was never written (e.g. if local-dev.sh ran before #200 fix)."""
        project_root = tmp_path
        pkgs = [
            _pkg("pdomain-book-tools", editable_location=str(project_root)),
            _pkg("cupy-cuda12x", "14.0.1"),
        ]
        monkeypatch.setattr(cdl, "_load_pip_list", lambda: pkgs)
        monkeypatch.setattr(cdl, "_project_root", lambda: project_root)
        monkeypatch.setattr(
            cdl, "_marker_path", lambda: tmp_path / ".pdomain-dev-local-absent"
        )
        monkeypatch.delenv("PDOMAIN_DEV_LOCAL", raising=False)

        rc = cdl.main(["--quiet"])
        assert rc == 1, (
            "GPU extra alone must trigger dev-local detection (two-tier probe)"
        )

    def test_canonical_venv_exits_zero(
        self, cdl: _CheckDevLocalModule, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A clean venv with no GPU extras, no siblings, no marker must allow
        upgrade-deps to proceed (exit 0)."""
        project_root = tmp_path
        pkgs = [
            _pkg("pdomain-book-tools", editable_location=str(project_root)),
            _pkg("torch"),
            _pkg("numpy"),
        ]
        monkeypatch.setattr(cdl, "_load_pip_list", lambda: pkgs)
        monkeypatch.setattr(cdl, "_project_root", lambda: project_root)
        monkeypatch.setattr(
            cdl, "_marker_path", lambda: tmp_path / ".pdomain-dev-local-absent"
        )
        monkeypatch.delenv("PDOMAIN_DEV_LOCAL", raising=False)

        rc = cdl.main(["--quiet"])
        assert rc == 0, "Canonical venv must allow upgrade-deps to proceed (exit 0)"
