---
Status: built
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-13
Kind: architecture
---

# Type Checking

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Read when:** changing basedpyright configuration, its CI gate, or the
  generated warning baseline.
- **Search terms:** basedpyright, type checking, warning baseline, CI.

The repository runs basedpyright in recommended mode. The Makefile gate checks
error-level diagnostics, while `pyproject.toml` keeps
`failOnWarnings = false`. The historical own-code warning backlog has been
removed and `.basedpyright/baseline.json` contains no grandfathered files.

The baseline is a generated integration artifact. Regenerate it only when the
repository deliberately changes the accepted diagnostic set. Do not edit it on
parallel file-level branches.

## Evidence

- Code: `pyproject.toml`, `Makefile`,
  `.basedpyright/baseline.json`
- Tests: `make ci AI=1`
- Artifacts: empty basedpyright file baseline
- Verified: 2026-07-13 during the docgraph conformance migration

## Residual intent

Warning-level diagnostics are not a CI gate. Any future tightening requires an
explicit policy change. It also requires a freshly measured warning inventory.
