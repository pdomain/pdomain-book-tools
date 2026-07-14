# docs/issues — portable issue-report convention

A drop-in convention for keeping **governed, evidence-bearing issue reports** in a
repo's `docs/issues/` folder: bugs, silent failures, regressions, and
investigations that deserve a durable, citable record instead of a throwaway chat
summary or a per-machine memory file.

It is **repo-agnostic**. It works best in a docgraph-governed repo (the reports
become retrievable, linkable graph nodes), but the structure and template are
useful in any repo.

This was extracted from a real find: under `docgraph-mcp 0.5.3`, semantic search
silently fell back to lexical despite a fully-built embedding index — a
high-severity bug that reported *zero* errors and was only caught with a
hand-crafted discrimination query. A throwaway chat reply would have lost the
evidence chain. A governed issue doc keeps it.

## What's in this bundle

```text
docs-issues/
  README.md                      <- this guide (stays in extras)
  template/
    docs-issues-README.md        -> copy to  <repo>/docs/issues/README.md
    TEMPLATE.md                  -> copy to  <repo>/docs/issues/TEMPLATE.md
```

`template/` mirrors what lands in a target repo. Copy both files in, then adapt
the README's intro to the repo.

## The convention (summary)

- **Location / name:** `docs/issues/YYYY-MM-DD-short-slug.md` (creation date + terse slug).
- **One issue per file.** A report is a node you can link from specs, plans, and
  context docs.
- **Lead with the smallest decisive evidence.** Separate **observation** from
  **hypothesis**. Always include a **"What is NOT broken"** section so a reader can
  scope the fix without re-deriving it.
- **Structure:** Summary · Impact · Environment/versions · Evidence (reproduction
  & diagnosis, with commands + output) · Root-cause hypotheses (ranked) · Defects ·
  Recommended next steps · What is NOT broken · Resolution. (See `template/TEMPLATE.md`.)

## Install — docgraph-governed repo (recommended)

1. **Copy the two files:**

   ```bash
   mkdir -p <repo>/docs/issues
   cp template/docs-issues-README.md <repo>/docs/issues/README.md
   cp template/TEMPLATE.md           <repo>/docs/issues/TEMPLATE.md
   ```

2. **Adapt** `docs/issues/README.md`'s opening lines to the repo (owner, the
   "linked from" target — usually `intent-map.md` "Open issues" or
   `current-state.md` "Risks").
3. **Confirm the template stays out of the index.** `TEMPLATE.md` carries a
   top-of-file `<!-- docgraph: ignore -->` marker. If the repo's `docgraph.toml`
   uses an `exclude` list instead, add `docs/issues/TEMPLATE.md` there too. Do
   **not** markdown-link to `TEMPLATE.md` from a governed doc — a link into an
   index-excluded file `dangles` and fails `docgraph check --strict`. Reference it
   by path / inline code instead.
4. **Stage + reindex** (under `mode = "git"` a new doc is invisible until staged):

   ```bash
   git -C <repo> add docs/issues/
   docgraph reindex --repo <repo>
   docgraph check --repo <repo> --strict   # must be ok
   ```

### Governed status vs. issue state

docgraph's lifecycle is `draft → active → implemented → retired` — it has no
"open/closed". So express the **issue's** resolution as a separate `Resolution:`
line in the Agent Index and a final `## Resolution` section, and map the governed
`Status:` like this:

| Issue state | docgraph `Status:` | How |
|---|---|---|
| Open | `active` | a live, current-truth description of a real problem |
| Resolved / Won't fix / Duplicate | `retired` | route through `doc-retirer`; link the fixing commit/spec in `## Resolution` |

Keep frontmatter `Status:` and Agent Index `Status:` **identical** — a mismatch
trips a `field_conflict` (→ `status-reconciler`).

## Install — plain repo (no docgraph)

The convention still works without docgraph; you just lose graph retrieval/checks.

1. Copy both files into `docs/issues/` as above.
2. The frontmatter is harmless as plain YAML; treat `Resolution:` / `Status:` as
   human-readable fields.
3. Keep an "Open issues" / "Resolved issues" list in `docs/issues/README.md` by
   hand (no auto-index).
4. `TEMPLATE.md`'s ignore marker is inert here — harmless.

## Why a folder, not just GitHub issues

GitHub issues are great for tracking and discussion, but they live outside the
repo, aren't retrievable by in-repo agents, and rot independently of the code.
A `docs/issues/` report is **in the tree, versioned with the code, linkable from
the docs that explain the affected system, and retrievable by docgraph**. Use
both: the doc is the durable evidence record; the tracker is the workflow. Link
one to the other.
