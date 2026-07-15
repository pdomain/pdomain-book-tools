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

Docgraph manages the documentation lifecycle and retrieval for this repository.
Live specs now state whether they are active or implemented. Git history
preserves retired documentation instead of an archive directory.

The shipped geometry behavior is documented in
[`geometry-correction.md`](../architecture/geometry-correction.md). OCR model,
blob, review, and schema ownership are documented in
[`ocr-model-and-schema-boundaries.md`](../architecture/ocr-model-and-schema-boundaries.md).
The local-development mode and `upgrade-deps` guard contract lives in
[`local-dev-mode.md`](../architecture/local-dev-mode.md).

## In-flight work

- The conformance and lifecycle migration is on docs/docgraph-conformance.

## Risks

- Required-section conformance is enforced as an error. This enforcement
  followed the 2026-07-13 conformance migration, which closed all 37 findings
  and completed adversarial review of 15 specs.
- The orphan queue is clear after two changes. Type-checking and layout-debug
  behavior were promoted to architecture, and their implementation documents
  were retired.
