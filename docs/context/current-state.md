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

- The conformance and lifecycle migration is on docs/docgraph-conformance.
- Implemented specs still need durable architecture replacements before formal
  retirement.

## Risks

- Required-section conformance is enforced as an error after the 2026-07-13
  conformance migration closed all 37 findings and adversarially reviewed 15
  specs.
- The orphan queue is clear after promoting type-checking and layout-debug
  behavior to architecture and retiring their implementation documents.
