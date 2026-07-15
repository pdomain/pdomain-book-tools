"""Unit tests for ``scripts/write_dev_local_marker.py``.

The marker-write helper backs the `make dev-local` recipe (spec
§2.2.2 / §4): it writes a self-explanatory marker file at
``.venv/.pdomain-dev-local`` that future ``check_dev_local`` invocations
can pick up. Tests drive the pure helper so we don't have to spin up
a real venv or run ``make``.

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

SCRIPT_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "write_dev_local_marker.py"
)


if TYPE_CHECKING:

    class _WriteDevLocalMarkerModule(Protocol):
        """Typed surface of ``scripts/write_dev_local_marker.py`` exercised
        by these tests."""

        def write_marker(self, venv_dir: Path) -> Path: ...

    class _CheckDevLocalModule(Protocol):
        """Typed surface of ``scripts/check_dev_local.py`` needed by the
        round-trip test below."""

        def detect_mode(
            self,
            pip_list: Iterable[PipListEntry],
            *,
            project_root: Path,
            marker_path: Path | None,
            env: dict[str, str] | None = None,
        ) -> DetectionResult: ...


def _load_script_module() -> _WriteDevLocalMarkerModule:
    """Load the script as a module. Register in ``sys.modules`` BEFORE
    executing so any future ``@dataclass`` forward refs resolve cleanly
    (mirrors the pattern used in ``test_check_dev_local.py``)."""
    spec = importlib.util.spec_from_file_location("write_dev_local_marker", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["write_dev_local_marker"] = module
    spec.loader.exec_module(module)
    # `module` is a dynamically loaded `ModuleType`; there is no static way
    # to prove it matches `_WriteDevLocalMarkerModule` short of loading it,
    # which is exactly what this function does. Narrowest honest boundary
    # cast.
    return cast("_WriteDevLocalMarkerModule", module)


@pytest.fixture(scope="module")
def wm() -> _WriteDevLocalMarkerModule:
    return _load_script_module()


# ---------------------------------------------------------------------------
# write_marker contract
# ---------------------------------------------------------------------------


def test_write_marker_creates_file(
    wm: _WriteDevLocalMarkerModule, tmp_path: Path
) -> None:
    """Writing into a venv where no marker exists yet creates the
    marker at the expected path."""
    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()
    target = venv_dir / ".pdomain-dev-local"
    assert not target.exists()

    written = wm.write_marker(venv_dir)

    assert written == target
    assert target.exists()


def test_write_marker_content_is_self_explanatory(
    wm: _WriteDevLocalMarkerModule, tmp_path: Path
) -> None:
    """Spec §5: the marker should be self-explanatory if a user
    ``cat``s it — include a timestamp and a hint about what it means."""
    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()

    wm.write_marker(venv_dir)
    text = (venv_dir / ".pdomain-dev-local").read_text()

    # Timestamp (year is enough — guard against empty file regression).
    assert "20" in text
    # Some indication that this venv is in dev-local mode.
    assert "dev-local" in text.lower()


def test_write_marker_overwrites_existing(
    wm: _WriteDevLocalMarkerModule, tmp_path: Path
) -> None:
    """Re-running ``make dev-local`` MUST refresh the marker rather
    than fail or no-op silently — the timestamp helps users understand
    when they last entered dev-local mode."""
    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()
    target = venv_dir / ".pdomain-dev-local"
    target.write_text("stale content from a previous run")

    wm.write_marker(venv_dir)

    assert "stale content" not in target.read_text()


def test_write_marker_refuses_when_venv_missing(
    wm: _WriteDevLocalMarkerModule, tmp_path: Path
) -> None:
    """If the venv doesn't exist yet, fail loudly. The recipe should
    have run ``make install`` first; a marker outside a venv is a
    stale-state class of bug."""
    venv_dir = tmp_path / ".venv-missing"
    assert not venv_dir.exists()

    with pytest.raises(FileNotFoundError):
        wm.write_marker(venv_dir)


def test_write_marker_round_trips_with_check_dev_local(
    wm: _WriteDevLocalMarkerModule, tmp_path: Path
) -> None:
    """The whole point of writing this marker: ``check_dev_local``
    must pick it up and flag the venv as dev-local. This is the
    end-to-end contract that ties §2.2.2 (marker fallback) to
    §4 (in-repo dev-local)."""
    cdl_path = Path(__file__).resolve().parents[2] / "scripts" / "check_dev_local.py"
    spec = importlib.util.spec_from_file_location("check_dev_local", cdl_path)
    assert spec is not None
    assert spec.loader is not None
    cdl_module = importlib.util.module_from_spec(spec)
    sys.modules["check_dev_local"] = cdl_module
    spec.loader.exec_module(cdl_module)
    # Same dynamic-loading boundary as `_load_script_module` above.
    cdl = cast("_CheckDevLocalModule", cdl_module)

    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()
    marker = wm.write_marker(venv_dir)

    project_root = tmp_path
    pkgs: list[PipListEntry] = [
        {
            "name": "pdomain-book-tools",
            "version": "0.0.0",
            "editable_project_location": str(project_root),
        }
    ]
    result = cdl.detect_mode(pkgs, project_root=project_root, marker_path=marker)
    assert result.is_dev_local is True
    assert any("marker" in r.lower() for r in result.reasons)
