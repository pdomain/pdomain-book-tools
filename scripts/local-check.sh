#!/usr/bin/env bash
# scripts/local-check.sh — print local-dev (GPU-extras) status.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MARKER="$REPO_ROOT/.venv/.pdomain-local-mode"

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
