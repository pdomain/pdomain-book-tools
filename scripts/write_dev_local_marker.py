"""Write the ``.pd-dev-local`` marker that flags a venv as dev-local.

Backs the ``make dev-local`` recipe (spec §2.2.2 / §4): once the venv
is in dev-local mode (sibling pd-* editables, ``[gpu]`` extra, doctr
fork, etc.), this helper writes a small self-explanatory marker file
inside the venv so that subsequent ``check_dev_local`` invocations
flag the mode without needing to re-probe every override one by one.

Lifecycle is anchored to the venv directory: a venv rebuild
(``make remove-venv``) deletes the marker automatically — no
stale-marker class of bug.

Spec: ``docs/specs/07-dev-local-upgrade-flow.md``.

CLI usage::

    uv run python scripts/write_dev_local_marker.py [--venv .venv]

Exits 0 on success, non-zero (with a message on stderr) when the venv
directory is missing.
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

MARKER_FILENAME = ".pd-dev-local"


def write_marker(venv_dir: Path) -> Path:
    """Write the dev-local marker into ``venv_dir`` and return the path.

    Content is a short human-readable note: a UTC timestamp plus a
    pointer to the spec, so a user who ``cat``s the file understands
    what it means without reading source. Always overwrites existing
    content — re-running ``make dev-local`` should refresh the marker
    so the timestamp tells the truth.

    Raises ``FileNotFoundError`` if ``venv_dir`` does not exist;
    callers must run ``make install`` first.
    """
    if not venv_dir.is_dir():
        raise FileNotFoundError(
            f"venv directory not found: {venv_dir} "
            "(run `make install` first to create it)"
        )

    target = venv_dir / MARKER_FILENAME
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    body = (
        f"This venv is in dev-local mode (entered {timestamp}).\n"
        "\n"
        "Written by `make dev-local`. Detected by\n"
        "`scripts/check_dev_local.py`, which makes `make upgrade-deps`\n"
        "refuse-rather-than-clobber. Use `make upgrade-deps-local`\n"
        "to upgrade dependencies without losing dev-local overrides.\n"
        "\n"
        "Lifecycle is tied to this venv — `make remove-venv` deletes\n"
        "this file along with everything else.\n"
        "\n"
        "Spec: docs/specs/07-dev-local-upgrade-flow.md\n"
    )
    target.write_text(body)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Write the .pd-dev-local marker into the given venv "
            "directory. Backs `make dev-local`."
        )
    )
    parser.add_argument(
        "--venv",
        default=".venv",
        help="Path to the venv directory (default: .venv).",
    )
    args = parser.parse_args(argv)

    try:
        target = write_marker(Path(args.venv))
    except FileNotFoundError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    print(f"📌 Wrote dev-local marker: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
