---
Status: active
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-19
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

- The migration and immutable cutover SHA are merged on `master`.
- All 171 deletion-ready completed issues were permanently deleted in 18
  journaled batches. GitHub retains 33 open issues and 10 closed issues whose
  governed records still block deletion.
- GitHub Issues remains enabled because those 43 retained source issues are
  still active or awaiting an owner decision.

## Risks

- Do not delete the 10 held closed issues until their individual evidence gates
  are resolved.
- Do not delete any of the 43 active governed records or their 33 open and 10
  held closed source issues merely to reach a zero tracker count.
