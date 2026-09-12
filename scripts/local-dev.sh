#!/usr/bin/env bash
# scripts/local-dev.sh — toggle pdomain-book-tools into local-dev mode.
#
# pdomain-book-tools is the foundation lib (no siblings); local-dev here means
# "GPU extras active + marker present" per spec §5.3.
#
# Two markers are written for compatibility with both the shell scripts
# (.pdomain-local-mode, read by local-upgrade-deps.sh / local-check.sh) and the
# Python check_dev_local.py probe (.pdomain-dev-local, read by upgrade-deps guard).
set -euo pipefail

# uv installs into UV_PROJECT_ENVIRONMENT when that is set and into .venv
# otherwise, so mirror the same rule instead of hardcoding either name. The
# pd-suite devcontainer sets ".venv-container" because the workspace is a bind
# mount shared with the host; a plain checkout outside a container gets .venv.
venv_under() {
  case "${UV_PROJECT_ENVIRONMENT:-}" in
    "") printf '%s/.venv' "$1" ;;
    /*) printf '%s' "$UV_PROJECT_ENVIRONMENT" ;;
    *) printf '%s/%s' "$1" "$UV_PROJECT_ENVIRONMENT" ;;
  esac
}

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_VENV="$(venv_under "$REPO_ROOT")"
MARKER="$PROJECT_VENV/.pdomain-local-mode"

echo "[local-dev] → uv sync --extra gpu"
uv sync --extra gpu

mkdir -p "$(dirname "$MARKER")"
touch "$MARKER"
echo "[local-dev] ✓ GPU extras active; marker written: $MARKER"

# Also write the Python-compatible marker used by check_dev_local.py
# so the two-tier upgrade-deps guard (make upgrade-deps) detects local-dev.
uv run python "$REPO_ROOT/scripts/write_dev_local_marker.py" --venv "$PROJECT_VENV"
