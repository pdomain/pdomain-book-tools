---
Status: active
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-13
Kind: context
---

# Decisions

## Agent Index

- **Kind:** context
- **Status:** active
- **Read when:** checking durable documentation and cross-repository decisions.
- **Search terms:** decisions, archive removal, reportAny, typing.

### 2026-07-13 — Preserve retired docs in Git instead of an archive tree

- **Context:** The first docgraph migration found 15 archived Markdown files,
  including closed ledgers, forwarding stubs, and already-shipped plans.
- **Decision:** Remove docs/archive/ after promoting its remaining durable
  intent and repairing live inbound links.
- **Rationale:** Git history preserves the original prose without keeping
  retired nodes in the live retrieval graph.
- **Evidence:** Owner instruction on 2026-07-13; docgraph neighbor checks; live
  replacements in docs/specs/, code, and tests.
- **Remaining work:** Fill the removal commit in the retirement tombstone.

### 2026-07-13 — Resolve issue 206 typing warnings downstream

- **Context:** The archived issue 206 investigation tested direct typed access
  and defensive getattr access to page attributes.
- **Decision:** Treat the warnings as a downstream payload-resolution problem,
  not a missing pdomain-book-tools annotation.
- **Rationale:** getattr and an Any-typed PageLoadOutcome.payload erase the
  library's exported types. A downstream resolver returning Page or None
  restores typed attribute access.
- **Evidence:** Git history for
  docs/archive/research/2026-05-23-issue-206-attribute-typing-investigation.md;
  pyproject.toml; pdomain_book_tools/py.typed.
- **Remaining work:** Implement the resolver in the affected downstream
  repository when that work is scheduled.

### 2026-07-13 — Retired archive tree

- **Old paths:** docs/archive/**/*.md (15 files)
- **Outcome:** deleted as retired, superseded, implemented, or closed research
- **Superseded by:** live specs, code/tests, and the context entries above
- **Removal commit:** 91bda25
- **Rationale kept:** this decision log, docs/context/intent-map.md, live specs,
  code, tests, and Git history
- **Remaining work:** none

### 2026-07-13 — Enforce required document sections

- **Context:** The conformance migration updated 20 legacy documents and closed
  all 37 missing-section findings; 15 specs received adversarial review.
- **Decision:** Set required live-section severity to `error`.
- **Rationale:** Specs must retain an adversarial review, while plans and
  research must state their required evidence and constraints before becoming
  retrievable truth.
- **Evidence:** MCP `docgraph_check` reported zero `missing_section`
  findings after the reviewed batches.
- **Remaining work:** Resolve the separate orphan and lifecycle-candidate
  advisories.
