---
Status: active
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-20
Kind: context
---

# Current State

## Agent Index

- **Kind:** context
- **Status:** active
- **Read when:** starting work that depends on current priorities, risks, or in-flight documentation changes.
- **Search terms:** current state, priorities, risks, in flight.

## What matters now

The GitHub issue migration preserves all 214 source issues as exact raw JSON.
The [completed migration ledger](github-issues-migration-ledger.md) records 181
completed issues. The [governed issue backlog](../issues/README.md) holds 43
active local records: one for each of the 33 source-open issues and 10 retained
closed-source issues (#43, #54, #65, #77, #94 through #98, and #165).

Durable shipped behavior found during the migration has moved into architecture
records. These records cover [geometry correction](../architecture/geometry-correction.md),
[page serialization](../architecture/page-serialization.md),
[OCR model and schema boundaries](../architecture/ocr-model-and-schema-boundaries.md),
[page reorganization](../architecture/reorganize-page-pipeline.md),
[glyph annotations](../architecture/glyph-annotations.md),
[checkpoint loading](../architecture/checkpoint-loading-trust-boundary.md),
[model trust](../architecture/pp-doclayout-trust-boundary.md), and
[local-development mode](../architecture/local-dev-mode.md). The active designs
and remaining delivery order live in the [roadmap](../plans/roadmap.md), the
[specs index](../specs/_index.md), and the governed issue backlog.

## In-flight work

- The migration and Git-only tracking decision are merged on `master`.
- All 214 GitHub source issues were permanently deleted and verified in 23
  journaled batches. The live issue count is zero, and GitHub Issues is
  disabled for this repository.
- GitHub is no longer an issue-tracking authority for this repository. Active
  work and owner decisions remain in `docs/issues/` after source deletion.

## Risks

- Do not treat deletion of a GitHub source as resolution of its governed file.
- Keep every active governed record until its own technical or owner-decision
  resolution passes the normal `doc-retirer` workflow.
