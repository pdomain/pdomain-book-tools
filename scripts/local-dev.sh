#!/usr/bin/env bash
# scripts/local-dev.sh — toggle pdomain-book-tools into local-dev mode.
#
# pdomain-book-tools is the foundation lib (no siblings); local-dev here means
# "GPU extras active + marker present" per spec §5.3.
#
# Two markers are written for compatibility with both the shell scripts
# (.pd-local-mode, read by local-upgrade-deps.sh / local-check.sh) and the
# Python check_dev_local.py probe (.pd-dev-local, read by upgrade-deps guard).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MARKER="$REPO_ROOT/.venv/.pd-local-mode"

echo "[local-dev] → uv sync --extra gpu"
uv sync --extra gpu

mkdir -p "$(dirname "$MARKER")"
touch "$MARKER"
echo "[local-dev] ✓ GPU extras active; marker written: $MARKER"

# Also write the Python-compatible marker used by check_dev_local.py
# so the two-tier upgrade-deps guard (make upgrade-deps) detects local-dev.
uv run python "$REPO_ROOT/scripts/write_dev_local_marker.py" --venv "$REPO_ROOT/.venv"
