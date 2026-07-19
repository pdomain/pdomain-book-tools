---
Status: active
Owner: CT
Created: 2026-05-04
Last verified: 2026-07-13
Kind: process
---

# docs/

This directory organizes the repo's documentation by purpose.

| Folder | Purpose | Use when |
| --- | --- | --- |
| `architecture/` | Durable reference: how the system works today. | Capturing the current modules, data flow, contracts, or current-state diagrams. |
| `decisions/` | Dated, append-only ADRs: "we chose X because Y." | Recording a specific design choice, including its context, alternatives, and consequences. |
| [`issues/`](issues/README.md) | Governed issue records and migration ledgers. | Tracking active work, evidence, and issue provenance in the repository. |
| `plans/` | Active execution: the order for making a spec real. | Sequencing work for an approved spec. |
| `process/` | Cross-cutting workflow conventions, such as verification rules, merge strategy, and release process. | Capturing how the team works rather than how the system works. |
| `research/` | An investigation in progress. Messy by design. | Exploring before committing to a design. |
| `runbooks/` | Operational reference for something broken or being operated. | Providing a recipe for an on-call or ops task. |
| `specs/` | Aspirational, pre-implementation design. | Describing what to build before writing the code. |
| `templates/` | Boilerplate for issues, specs, plans, and ADRs. | Adding a starter template for a new doc type. |
| `usage/` | Downstream reference for consuming this app, tool, or library. | Explaining how to use it to a user or integrator. |

Git history preserves retired documentation. Do not create a parallel archive
tree; promote durable truth into architecture, decisions, or context before
deleting a retired document.

Active docs map to GitHub issues. See this repo's issue tracker for status.

This layout follows the workspace standard. See
`/workspaces/ocr-container/docs/README.md` for the master.

## Current documentation

- [Type-checking architecture](architecture/type-checking.md)
- [Layout-debug cleanup architecture](architecture/layout-debug-cleanup.md)
- [Page serialization architecture](architecture/page-serialization.md)
- [OCR page-orientation architecture](architecture/ocr-page-orientation.md)
- [Page reorganization architecture](architecture/reorganize-page-pipeline.md)
- [Layout-regression fixture architecture](architecture/layout-regression-fixture-corpus.md)
- [Glyph-annotation architecture](architecture/glyph-annotations.md)
- [Tesseract integration architecture](architecture/tesseract-integration.md)
- [DocTR checkpoint-loading trust boundary](architecture/checkpoint-loading-trust-boundary.md)
- [PP-DocLayout model trust boundary](architecture/pp-doclayout-trust-boundary.md)
- [Completed GitHub issue migration ledger](context/github-issues-migration-ledger.md)
- [Roadmap](plans/roadmap.md)
- [Specifications](specs/_index.md)
- [Geometry correction usage](usage/geometry-correction.md)
