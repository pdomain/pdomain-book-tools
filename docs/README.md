---
Status: active
Owner: CT
Created: 2026-05-04
Last verified: 2026-07-13
Kind: process
---

# docs/

How documentation is organized in this repo.

| Folder | Purpose | Use when |
| --- | --- | --- |
| `architecture/` | Durable reference — how the system works today. | Capturing current shape (modules, data flow, contracts, current-state diagrams). |
| `decisions/` | ADRs — dated, append-only "we chose X because Y." | Recording a specific design choice with context, alternatives, consequences. |
| `plans/` | Active execution — what order to make a spec real. | Sequencing work for an approved spec. |
| `process/` | Cross-cutting workflow conventions (verification rules, merge strategy, release process). | Capturing how the team works, not what the system does. |
| `research/` | Investigation in progress. Messy by design. | Exploring before committing to a design. |
| `runbooks/` | Operational reference — something is broken or being operated. | An on-call or ops task needs a recipe. |
| `specs/` | Aspirational, pre-implementation design. | Describing what to build, before code. |
| `templates/` | Issue, spec, plan, ADR boilerplate. | Adding a starter template for a new doc type. |
| `usage/` | Downstream reference — how to consume this app/tool/library. | A user or integrator needs to know how to use it. |

Git history preserves retired documentation. Do not create a parallel archive
tree; promote durable truth into architecture, decisions, or context before
deleting a retired document.

Active docs map to GitHub issues — see this repo's issue tracker for status.
This layout is workspace-standard; see
`/workspaces/ocr-container/docs/README.md` for the master.

## Current documentation

- [Type-checking architecture](architecture/type-checking.md)
- [Layout-debug cleanup architecture](architecture/layout-debug-cleanup.md)
- [Page serialization architecture](architecture/page-serialization.md)
- [OCR page-orientation architecture](architecture/ocr-page-orientation.md)
- [Page reorganization architecture](architecture/reorganize-page-pipeline.md)
- [Layout-regression fixture architecture](architecture/layout-regression-fixture-corpus.md)
- [Glyph-annotation architecture](architecture/glyph-annotations.md)
- [Roadmap](plans/roadmap.md)
- [Specifications](specs/_index.md)
- [Geometry correction usage](usage/geometry-correction.md)
