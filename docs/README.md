---
Status: active
Owner: CT
Created: 2026-05-04
Last verified: 2026-11-12
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

Open work is the [roadmap](plans/roadmap.md). Shipped behavior is the [architecture index](architecture/README.md). GitHub Issues is disabled for this repository.

The folder table above is this repo's layout. The old pointer to `/workspaces/ocr-container/docs/README.md` described a workspace that is no longer the master copy.

## Current documentation

- [What this library is](architecture/README.md), the index of shipped architecture
- [Roadmap](plans/roadmap.md)
- [Specifications](specs/_index.md)
- [Issue index](issues/README.md)
- [Public API](usage/public-api.md)
- [Geometry correction usage](usage/geometry-correction.md)
- [GitHub issue migration ledger](context/github-issues-migration-ledger.md)
