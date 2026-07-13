---
Status: built
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-13
Kind: architecture
---

# Layout Debug Cleanup

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Read when:** changing layout-regression debug retention, pytest session
  startup, or the manual cleanup target.
- **Search terms:** layout debug, cleanup, pytest sessionstart, retention.

Every pytest session invokes `_prune_old_debug_runs` from
`tests/conftest.py`. It scans the layout-regression debug directory and
best-effort removes `test-*` and `regen-*` directories whose directory
mtime is older than 24 hours. Recent, non-matching, and missing directories are
left alone; filesystem removal errors are suppressed.

The automatic cleanup is independent of the current working directory and does
not replace the manual `make clean-debug` target.

## Evidence

- Code: `tests/conftest.py`
- Tests: `tests/test_debug_cleanup.py`
- Artifacts: layout-regression debug run directories
- Verified: 2026-07-13; focused review observed 24 related tests pass, and the
  full repository gate is `make ci AI=1`

## Residual intent

Directory mtime does not prove that a run is inactive. A future change should
add a liveness marker or lock and cover concurrent sessions, deletion failures,
and the exact retention boundary. The tracked intent lives in
`docs/context/intent-map.md`.
