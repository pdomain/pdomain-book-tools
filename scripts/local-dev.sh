#!/usr/bin/env bash
# scripts/local-dev.sh — toggle pd-book-tools into local-dev mode.
#
# pd-book-tools is the foundation lib (no siblings); local-dev here means
# "GPU extras active + marker present" per spec §5.3.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MARKER="$REPO_ROOT/.venv/.pd-local-mode"

echo "[local-dev] → uv sync --extra gpu"
uv sync --extra gpu

mkdir -p "$(dirname "$MARKER")"
touch "$MARKER"
echo "[local-dev] ✓ GPU extras active; marker written: $MARKER"
