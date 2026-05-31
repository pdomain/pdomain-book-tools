#!/usr/bin/env bash
# scripts/local-upgrade-deps.sh — upgrade deps then restore GPU extras.
#
# Refuses if not in local-dev mode (use `make upgrade-deps` for registry mode).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MARKER="$REPO_ROOT/.venv/.pdomain-local-mode"

if [[ ! -f "$MARKER" ]]; then
  echo "ERROR: not in local-dev mode (no marker at $MARKER)." >&2
  echo "       Run 'make upgrade-deps' instead." >&2
  exit 1
fi

echo "[local-upgrade-deps] → uv lock --upgrade && uv sync --extra gpu"
uv lock --upgrade
uv sync --extra gpu
echo "[local-upgrade-deps] ✓ done. GPU extras restored."
