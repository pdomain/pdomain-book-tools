"""Layout-detector fork drift check.

Compares the pinned revision (read from pp_doclayout.py) against the fork's
current HEAD and upstream's current HEAD. Drift between fork and upstream is
determined by file-hash comparison rather than commit SHA, so a metadata-only
upstream commit (e.g. README touch) that doesn't change any file we ship will
not be flagged.

Always exits 0; warnings go to stderr so CI logs stay readable.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from huggingface_hub import HfApi
from huggingface_hub.utils import HfHubHTTPError

UPSTREAM = "PaddlePaddle/PP-DocLayout_plus-L_safetensors"
FORK = "CT2534/PP-DocLayout_plus-L"
ADAPTER = (
    Path(__file__).resolve().parents[1]
    / "pd_book_tools/layout/adapters/pp_doclayout.py"
)


def read_pinned_revision() -> str:
    src = ADAPTER.read_text()
    m = re.search(r'^_DEFAULT_REVISION\s*=\s*"([^"]+)"', src, re.MULTILINE)
    if not m:
        raise SystemExit(f"could not find _DEFAULT_REVISION in {ADAPTER}")
    return m.group(1)


def file_hashes(api: HfApi, repo: str, revision: str) -> dict[str, str]:
    info = api.model_info(repo, revision=revision, files_metadata=True)
    out: dict[str, str] = {}
    for s in info.siblings or []:
        h = (s.lfs.sha256 if s.lfs else None) or s.blob_id or ""
        out[s.rfilename] = h
    return out


def changed_files(a: dict[str, str], b: dict[str, str]) -> list[str]:
    return [name for name in sorted(set(a) | set(b)) if a.get(name) != b.get(name)]


def main() -> int:
    pinned = read_pinned_revision()
    api = HfApi()

    try:
        fork_head = api.repo_info(FORK).sha
        up_head = api.repo_info(UPSTREAM).sha
    except (HfHubHTTPError, OSError) as e:
        print(f"pinned (in {ADAPTER}): {pinned}")
        print(
            f"ℹ️  Skipping divergence check — could not reach Hugging Face: {e}",
            file=sys.stderr,
        )
        return 0

    print(f"pinned (in {ADAPTER.relative_to(ADAPTER.parents[3])}): {pinned}")
    print(f"fork  ({FORK}): {fork_head}")
    print(f"upstream ({UPSTREAM}): {up_head}")

    if pinned != fork_head:
        print(
            f"⚠️  WARNING: pinned SHA ({pinned}) does not match fork HEAD "
            f"({fork_head}) — run 'make layout-fork-pin SHA={fork_head}'",
            file=sys.stderr,
        )
        return 0

    if fork_head == up_head:
        print("✅ pinned == fork == upstream")
        return 0

    fork_files = file_hashes(api, FORK, fork_head)
    up_files = file_hashes(api, UPSTREAM, up_head)
    changed = changed_files(fork_files, up_files)

    if not changed:
        print(
            f"✅ pinned == fork; upstream is at {up_head[:12]} but every "
            f"file matches the fork (metadata-only upstream commit)"
        )
        return 0

    print(
        "⚠️  WARNING: upstream files differ from fork — run "
        "'make layout-fork-update' to refresh, then 'make layout-fork-pin'",
        file=sys.stderr,
    )
    print(f"   changed files: {', '.join(changed)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
