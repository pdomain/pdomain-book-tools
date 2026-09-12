#!/usr/bin/env bash
# scripts/local-upgrade-deps.sh — upgrade deps then restore GPU extras.
#
# Refuses if not in local-dev mode (use `make upgrade-deps` for registry mode).
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

if [[ ! -f "$MARKER" ]]; then
  echo "ERROR: not in local-dev mode (no marker at $MARKER)." >&2
  echo "       Run 'make upgrade-deps' instead." >&2
  exit 1
fi

echo "[local-upgrade-deps] → uv lock --upgrade && uv sync --extra gpu"
uv lock --upgrade
uv sync --extra gpu
echo "[local-upgrade-deps] ✓ done. GPU extras restored."
