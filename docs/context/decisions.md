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

### 2026-07-13 — Separate geometry regimes and own the classical baseline

- **Context:** Deskew, textline curvature, perspective distortion, and general
  restoration need different algorithms and dependency profiles.
- **Decision:** Keep page-side, curvature, deskew, and dewarp seams separate.
  Ship owned projection/Sbrunner deskew and NumPy/CuPy textline-disparity as
  the classical baseline. Keep UVDoc optional and regime-gated.
- **Rationale:** This preserves CPU availability and GPU parity without making
  weights or external CLI tools mandatory. No Leptonica/Rust binding is needed
  for the shipped behavior.
- **Evidence:** `pdomain_book_tools/geometry_correction/`,
  `tests/geometry_correction/`, and
  `_tbd/ocr-container-docs/specs/2026-06-02-geometry-correction-design.md`.
- **Remaining work:** Alternative backends remain evidence-gated intent.

### 2026-07-13 — Keep OCR values separate from lifecycle and matching state

- **Context:** OCR content, operational persistence, review decisions, and
  ground-truth matching evolve independently.
- **Decision:** Keep Page as the portable OCR value boundary with protocol-based
  blob access. Keep operational lifecycle in pdomain-ops. Keep ReviewMetadata
  separate from matching fields, and use public Pydantic schemas as the
  language-neutral consumer boundary.
- **Rationale:** The split avoids package cycles and prevents application
  persistence or review workflow from becoming foundation-model requirements.
- **Evidence:** `pdomain_book_tools/ocr/page.py`, `ocr/review.py`,
  `schemas/emit.py`, their tests, and
  `_tbd/ocr-container-docs/archive/plans/2026-05-31-page-split-book-tools.md`.
- **Remaining work:** Matching-field clustering and compatibility removal need
  owner-approved consumer evidence.
