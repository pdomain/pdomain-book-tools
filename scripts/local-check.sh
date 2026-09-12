#!/usr/bin/env bash
# scripts/local-check.sh — print local-dev (GPU-extras) status.
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

if [[ -f "$MARKER" ]]; then
  echo "MODE: local-dev (GPU extras active; marker at $MARKER)"
else
  echo "MODE: registry (no marker; CPU-only base install)"
fi

# Show whether torch is installed and where
TORCH_LOC=$(uv pip show torch 2>/dev/null | awk '/^Location:/ {print $2}' || true)
if [[ -n "$TORCH_LOC" ]]; then
  TORCH_VER=$(uv pip show torch 2>/dev/null | awk '/^Version:/ {print $2}')
  echo "torch:   $TORCH_VER  (at $TORCH_LOC)"
else
  echo "torch:   NOT installed"
fi
