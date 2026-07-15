"""Detect whether the current venv is in **dev-local mode**.

A venv is dev-local when it has overrides — sibling pdomain-* editable
installs, the ``[gpu]`` extra, an explicit
``PDOMAIN_DEV_LOCAL=1`` env var, or a ``.venv/.pdomain-dev-local`` marker file —
that ``uv sync --group dev`` (the canonical sync) would silently
revert. ``make upgrade-deps`` and any future recipe that rebuilds the
venv invokes this script to refuse-rather-than-clobber.

Architecture: ``docs/architecture/local-dev-mode.md``.

Exit code:
- 0 if canonical (Makefile recipe proceeds normally).
- 1 if dev-local (Makefile recipe refuses with a message pointing the
  user at ``local-upgrade-deps``).

The detection logic is split into pure helpers so unit tests can drive
it without spinning up real venvs.
"""
# CLI script — print is the output mechanism

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, cast

if TYPE_CHECKING:
    from collections.abc import Iterable


class PipListEntry(TypedDict, total=False):
    """One element of ``uv pip list --format=json`` output.

    All fields are optional at the type level: real ``uv`` output always
    includes ``name``, but the parser is defensive about malformed or
    unexpected entries rather than assuming the schema.
    """

    name: str
    version: str
    editable_project_location: str


# Packages whose presence in the venv signals an active extra/override
# that ``uv sync --group dev`` (no extras) would remove. Names are
# normalized to lowercase for matching.
_GPU_EXTRA_PACKAGES = frozenset({"cupy-cuda12x", "opencv-cuda"})

# This package is the project itself; its editable install is normal in
# every dev venv and MUST NOT be flagged as dev-local on its own.
_THIS_PROJECT_NAME = "pdomain-book-tools"


@dataclass(frozen=True)
class DetectionResult:
    """Outcome of a dev-local probe.

    ``is_dev_local`` is the boolean the Makefile branches on; ``reasons``
    is the human-readable list shown to the user so they know exactly
    what would have been clobbered.
    """

    is_dev_local: bool
    reasons: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pure detection (driven by tests).
# ---------------------------------------------------------------------------


def _is_truthy(value: str | None) -> bool:
    """Standard truthy-string parse: 1/true/yes/on (case-insensitive)."""
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def detect_mode(
    pip_list: Iterable[PipListEntry],
    *,
    project_root: Path,
    marker_path: Path | None,
    env: dict[str, str] | None = None,
) -> DetectionResult:
    """Inspect ``pip_list`` (the parsed ``uv pip list --format=json``
    output) plus optional marker file and env var, return a
    :class:`DetectionResult`.

    Signals collected (spec §2.2):

    1. **Editable install for any package other than the project root.**
       Sibling pdomain-* checkouts surface as ``editable_project_location``
       in ``uv pip list --format=json``.
    2. **A package from the ``[gpu]`` extra is installed**
       (``cupy-cuda12x``, ``opencv-cuda``). Canonical sync drops
       these, so their presence means a ``--extra gpu`` was
       explicitly applied.
    3. **Marker file present** at ``marker_path`` (if supplied) — the
       fallback signal written by ``make dev-local``.
    4. **PDOMAIN_DEV_LOCAL env var set to a truthy value** — last-resort
       opt-in.

    Reasons for every fired signal accumulate in ``DetectionResult.reasons``
    so the Makefile can show all of them at once rather than the user
    discovering them one at a time.
    """
    if env is None:
        env = dict(os.environ)
    project_root_resolved = project_root.resolve()

    reasons: list[str] = []

    for pkg in pip_list:
        name = (pkg.get("name") or "").lower()
        editable = pkg.get("editable_project_location")
        if editable:
            try:
                editable_resolved = Path(editable).resolve()
            except OSError:
                editable_resolved = Path(editable)
            if name != _THIS_PROJECT_NAME or editable_resolved != project_root_resolved:
                reasons.append(f"editable install: {name} at {editable}")
        if name in _GPU_EXTRA_PACKAGES:
            reasons.append(f"[gpu] extra active: {name}=={pkg.get('version', '?')}")

    if marker_path is not None and marker_path.exists():
        reasons.append(f"marker file present: {marker_path}")

    if _is_truthy(env.get("PDOMAIN_DEV_LOCAL")):
        reasons.append("PDOMAIN_DEV_LOCAL env var is set to a truthy value")

    return DetectionResult(is_dev_local=bool(reasons), reasons=reasons)


# ---------------------------------------------------------------------------
# CLI plumbing — thin wrappers, monkey-patched in tests.
# ---------------------------------------------------------------------------


def _coerce_pip_list_entry(item: object) -> PipListEntry | None:
    """Narrow one ``uv pip list --format=json`` array element.

    Non-mapping entries are dropped; string-typed known fields are kept,
    anything else (wrong type, unknown key) is dropped from that field.
    """
    if not isinstance(item, dict):
        return None
    # isinstance narrows to dict[Unknown, Unknown] -- it cannot express key/value
    # types (Python generics aren't reified). Each field pulled from `raw` below
    # is still validated with an explicit isinstance check before being trusted.
    raw = cast("dict[str, object]", item)
    entry: PipListEntry = {}
    name = raw.get("name")
    if isinstance(name, str):
        entry["name"] = name
    version = raw.get("version")
    if isinstance(version, str):
        entry["version"] = version
    editable = raw.get("editable_project_location")
    if isinstance(editable, str):
        entry["editable_project_location"] = editable
    return entry


def _load_pip_list() -> list[PipListEntry]:
    """Run ``uv pip list --format=json`` and return parsed entries.

    Tests monkey-patch this so we never spawn a real subprocess in
    pytest. In production this is the only system-touching call.
    """
    out = subprocess.check_output(["uv", "pip", "list", "--format=json"], text=True)
    data: object = json.loads(out)
    if not isinstance(data, list):
        return []
    # isinstance narrows to list[Unknown] -- it cannot express the element type
    # (Python generics aren't reified). Each element is validated by
    # `_coerce_pip_list_entry` before being trusted.
    items = cast("list[object]", data)
    entries: list[PipListEntry] = []
    for item in items:
        entry = _coerce_pip_list_entry(item)
        if entry is not None:
            entries.append(entry)
    return entries


def _project_root() -> Path:
    """Repo root — the directory containing ``pyproject.toml``."""
    return Path(__file__).resolve().parents[1]


def _marker_path() -> Path:
    """Conventional marker location: ``<project>/.venv/.pdomain-dev-local``."""
    return _project_root() / ".venv" / ".pdomain-dev-local"


def _format_summary(result: DetectionResult) -> str:
    if not result.is_dev_local:
        return "venv is in canonical mode."
    lines = [
        "venv is in dev-local mode. Reasons:",
        *[f"  - {r}" for r in result.reasons],
        "",
    ]
    lines.append(
        "Run `make local-upgrade-deps` instead of `make upgrade-deps` "
        "to upgrade without clobbering these overrides."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Detect dev-local mode in the current venv. Exits 1 if "
            "dev-local, 0 if canonical."
        )
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress all output; rely on the exit code only.",
    )
    args = parser.parse_args(argv)

    pip_list = _load_pip_list()
    result = detect_mode(
        pip_list,
        project_root=_project_root(),
        marker_path=_marker_path(),
    )

    if not args.quiet:
        # Print to stderr so a Makefile recipe that runs this in a
        # subshell can capture exit code without polluting stdout
        # (e.g. for use in `if ! python scripts/...; then`).
        print(_format_summary(result), file=sys.stderr)

    return 1 if result.is_dev_local else 0


if __name__ == "__main__":
    sys.exit(main())
