---
Status: active
Owner: CT
Created: 2026-07-15
Last verified: 2026-11-12
Kind: process
Level: I1
---

# Issues

## Agent Index

- **Kind:** process
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-11-12
- **Read when:** filing a bug / defect / investigation report, or looking up an
  open issue's status, evidence, or resolution.
- **Search terms:** issues folder, bug report, defect report, issue template,
  issue lifecycle, kind issue.

## Purpose

`docs/issues/` holds **governed, evidence-bearing issue reports** for bugs,
silent failures, regressions, and investigations. These reports provide a
durable, citable record instead of a throwaway chat summary. Each report is a
docgraph node. Readers can retrieve it and link to it from specs, plans, or
context documents. The repository carries the record instead of per-machine
harness memory.

## Convention

- **Location:** `docs/issues/`
- **Filename:** `YYYY-MM-DD-short-slug.md` (creation date + a terse kebab slug).
- **Metadata:** YAML frontmatter **and** a matching `## Agent Index` block. Keep
  frontmatter `Status:` and Agent Index `Status:` identical — a mismatch trips a
  `field_conflict` (→ `status-reconciler`).
  - `Kind: issue`
  - `Level:` informational scope — `I1` repo-wide, `I2` narrow/local.
  - `Status:` governed lifecycle, **not** the issue's open/closed state (see below).
- **Issue state vs governed status:** the docgraph lifecycle is
  `draft → active → implemented → retired`. Express the *issue's* resolution
  state separately. Add a **`Resolution:`** line to the Agent Index (`Open` /
  `Resolved` / `Won't fix` / `Duplicate`) and a final `## Resolution` section.
  Map the governed `Status:`:
  - **Open** → `Status: active`.
  - **Resolved / Won't fix / Duplicate** → route through `doc-retirer`, which
    **deletes** the report. Promote any specific a reader still needs into the
    architecture or process doc that owns it, repoint inbound references at the
    resolving commit, drop the pointer below, and append a tombstone to
    `docs/context/decisions.md`. Git history keeps the report, so no resolved
    file stays in the tree and there is no resolved index to maintain.
- **Link it (no orphans):** reference every new issue from a governed doc — by
  default an **Open issues** bullet in `docs/context/intent-map.md`, or a Risk in
  `docs/context/current-state.md`. This `README` also links the live issues below,
  which satisfies the no-orphan rule.
- **Stage + reindex:** under `mode = "git"`, a new doc is invisible until it is
  `git add`ed. In the same turn, stage it, run `docgraph reindex`, and run
  `docgraph check --strict`. A new `dangling` blocks completion.
- **Template:** copy `TEMPLATE.md` in this folder. It is index-excluded (a
  top-of-file `<!-- docgraph: ignore -->` marker), so **do not markdown-link to
  it** from a governed doc — the link would dangle. Refer to it by path / inline
  code.

## Recommended structure

Use this section order:

1. Summary
2. Impact
3. Environment/versions
4. Evidence, including reproduction and diagnosis with commands and output
5. Ranked root-cause hypotheses
6. Defects to fix
7. Recommended next steps
8. What is NOT broken, which scopes the fix
9. Resolution

Lead with the **smallest decisive evidence**, separate **observation** from
**hypothesis**, and always include a **What is NOT broken** section.

## Cross-cut workspace items live here

Items affecting several `pdomain-*` repos are filed in this folder and linked
from the repos they affect. `ConcaveTrillion/ocr-container-meta` is no longer
the home for that work. Repo-local defects stay in their own repo.

## Remaining work

The open list is the [roadmap](../plans/roadmap.md). Shipped behavior is the [architecture index](../architecture/README.md). This file does not keep a second copy of that list, so the two cannot drift.

On 2026-11-12 the per-issue lines that were in this section moved into the roadmap and were grouped. Library work stays under "Open work in this library". Page-order, scannos, hyphen n-grams, and the table detector are under "Homes still to choose". Cross-repo CI and agent-pointer notes are under "Tracker items outside the library". The schema-emit line now matches its issue file: glyph schema emission and Block tuple restore are fixed, and the provenance-ownership sentence is still open.

Each issue file remains the evidence record. Add a new open issue to the roadmap in the same edit that adds the file.
