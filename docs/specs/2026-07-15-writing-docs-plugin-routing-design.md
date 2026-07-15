---
Status: implemented
Owner: CT
Created: 2026-07-15
Last verified: 2026-07-15
Kind: spec
---

# Route writing guidance through the writing-docs plugin

## Agent Index

- **Kind:** spec
- **Status:** implemented
- **Read when:** changing repository writing guidance or agent prose workflows.
- **Search terms:** writing style, writing-docs, write-readably, edit-for-readability.

## Goal

The repository will make the `writing-docs` plugin its only writing-style
authority. Its instructions will route new durable prose through
`writing-docs:write-readably` and existing prose through
`writing-docs:edit-for-readability`. Short conversational prose will use the
plugin's inline readability standard without a durable-document workflow.

## Changes

- Remove `docs/process/writing-style.md`; Git history will preserve it.
- Replace the `AGENTS.md` reference to that file with direct plugin routing.
- Remove the stale local-style reference from `docs/context/intent-map.md`.
- Update any other live inbound references found by docgraph or repository
  search.

## Boundaries

This change will not alter product behavior or rewrite unrelated
documentation. It will not duplicate the plugin's readability rules in
another repository file. The managed `repo-setup:writing-and-review` section
remains the canonical routing record.

The migration requires both `writing-docs:write-readably` and
`writing-docs:edit-for-readability` in the active agent environment. Agents
must stop with a missing-skill error when either route is unavailable; they
must not recreate a local fallback. Deleting the old path intentionally breaks
external bookmarks or automation that bypass repository guidance. Git history
is the accepted recovery source.

## Verification

The change must leave no live inbound reference to
`docs/process/writing-style.md`. Specs and plans may retain the path as a
historical migration record:

```bash
rg -n 'docs/process/writing-style\.md' AGENTS.md docs \
  --glob '!docs/specs/**' --glob '!docs/plans/**'
```

`AGENTS.md` must contain both exact skill routes, and the active agent catalog
must expose both skills. Run Markdown lint through the repository hooks, then
run the graph and repository gates:

```bash
rg -q 'writing-docs:write-readably' AGENTS.md
rg -q 'writing-docs:edit-for-readability' AGENTS.md
find "${CODEX_HOME:-$HOME/.codex}/plugins/cache" \
  -path '*/writing-docs/*/skills/write-readably/SKILL.md' -print -quit | grep -q .
find "${CODEX_HOME:-$HOME/.codex}/plugins/cache" \
  -path '*/writing-docs/*/skills/edit-for-readability/SKILL.md' -print -quit | grep -q .
uv run pre-commit run markdownlint-cli2 --all-files
git diff --check
docgraph reindex --repo .
docgraph check --strict --repo .
make ci AI=1
```

## Rollback

Keep the deletion and all inbound-reference updates in one dedicated commit.
Revert that commit to restore the local file and its links, then rerun the
reference search, docgraph reindex, strict docgraph check, and repository CI.

## Adversarial Review

The first protocol attempt found four gaps: plugin availability and exact-route
verification, atomic rollback, concrete gate commands, and the external path
break. The second attempt confirmed those gaps were addressed and found three
medium-severity follow-ups. This final revision excludes historical specs and
plans from the live-reference search, preserves the plugin's inline rule for
short prose, and adds executable checks for both routes and cached skills. No
critical or high-severity finding remains.
