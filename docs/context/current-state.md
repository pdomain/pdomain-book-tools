---
Status: active
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-13
Kind: context
---

# Current State

## Agent Index

- **Kind:** context
- **Status:** active
- **Read when:** starting work that depends on current priorities, risks, or in-flight documentation changes.
- **Search terms:** current state, priorities, risks, in flight.

## What matters now

Docgraph is the documentation lifecycle and retrieval system for this repository.
Live specs now declare whether they are active or implemented. Git history, not
an archive directory, preserves retired documentation.

## In-flight work

- The docgraph bootstrap and first migration are on docs/docgraph-migration.
- Implemented specs still need durable architecture replacements before formal
  retirement.

## Risks

- Required-section conformance remains advisory during bootstrap.
- Required-section and orphan findings remain advisory during bootstrap;
  docgraph check tracks that conformance work.
