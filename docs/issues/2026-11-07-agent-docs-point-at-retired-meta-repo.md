---
Status: active
Owner: CT
Created: 2026-11-07
Last verified: 2026-11-07
Kind: issue
Level: I1
---

# Seven pdomain repos still send agents to the retired ocr-container-meta tracker

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-11-07
- **Resolution:** Open
- **Severity:** Low — agents look for issues in a repo no one uses
- **Affected version:** master of each repo listed below, 2026-11-07
- **Read when:** editing a pdomain repo's AGENTS.md or CLAUDE.md, or when an agent asks where issues live
- **Search terms:** ocr-container-meta, GH issues, agent pointers, tracker, AGENTS.md, CLAUDE.md
- **Relates to:** [issues index](README.md)

## Summary

`ConcaveTrillion/ocr-container-meta` was the issue tracker for the old
`/workspaces/ocr-container` workspace. Its last push was 2026-06-06. This repo's
`AGENTS.md` was fixed on 2026-11-07 to say so. Seven other repos still tell
agents to file and read issues there. The 2026-08-08 CI handoff counted nine;
two have since been fixed or removed.

## Impact

- Agents in those repos look for open work in the wrong place and may file new
  issues there.
- Not a code or CI defect.

## Environment / versions

```text
Checked 2026-11-07 on omarchy-main, in /mnt/work/projects/pdomain.
```

## Evidence

### 1. Repos whose agent docs name ocr-container-meta

```text
for r in */; do for f in AGENTS.md CLAUDE.md; do grep -c ocr-container-meta "$r$f"; done; done
pdomain-ocr-cli/AGENTS.md: 4
pdomain-ocr-labeler-spa/AGENTS.md: 4
pdomain-ocr-simple-gui/CLAUDE.md: 8
pdomain-ocr-synth/CLAUDE.md: 4
pdomain-prep-docs-consolidation/CLAUDE.md: 4
pdomain-prep-for-pgdp/CLAUDE.md: 4
pdomain-ui/AGENTS.md: 4
```

`pdomain-prep-docs-consolidation` is a second checkout of
`pdomain-prep-for-pgdp` on a branch, so six repositories need the fix.
`pdomain-book-tools/AGENTS.md` still names the meta repo once, on purpose, to
say it is retired.

## Root-cause hypotheses

1. **(Most likely) The agent docs were written from the old workspace template**
   and never updated when issues moved into each repo's `docs/issues/`.

## Defects to fix

1. In each repo, replace the meta-repo issue section with a pointer to that
   repo's `docs/issues/` folder, and to this repo's folder for cross-cut items.

## Next steps

1. Apply the same wording as this repo's `AGENTS.md` "Issues" section to each
   repo, one commit per repo.

## What is NOT broken

- This repo's own `AGENTS.md`, fixed in `b73311e`.

## Resolution

*Open.* When fixed: set frontmatter + Agent Index `Status: retired`, link the
resolving commits here, and route retirement through `doc-retirer`.
