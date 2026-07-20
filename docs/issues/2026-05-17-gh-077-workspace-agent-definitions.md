---
Status: active
Owner: CT
Created: 2026-05-17
Last verified: 2026-07-20
Kind: issue
Level: I1
---

# Verify the parent workspace-agent definition claim

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-20
- **Resolution:** Open
- **Severity:** Low — the reported workspace files are not locally verifiable
- **Affected version:** Workspace state reported on 2026-05-19
- **Read when:** deciding whether closed GitHub issue #77 can be deleted.
- **Search terms:** pd-ui agent, pd-ocr-ops agent, workspace routing definitions.
- **Relates to:** [GitHub issues migration ledger](../context/github-issues-migration-ledger.md)

## Summary

Closed GitHub issue #77 reports that the full-power `pd-ui` and `pd-ocr-ops`
agent definitions existed with complete workspace routing. This repository
cannot verify those external files, their owning commits, or their current
routing behavior.

The five child concerns now have separate governed records:

- [#94 — full-power pd-ui definition](2026-05-17-gh-094-pd-ui-agent-definition.md)
- [#95 — read-only pd-ui-docs definition](2026-05-17-gh-095-pd-ui-docs-agent-definition.md)
- [#96 — full-power pd-ocr-ops definition](2026-05-17-gh-096-pd-ocr-ops-agent-definition.md)
- [#97 — read-only pd-ocr-ops-docs definition](2026-05-17-gh-097-pd-ocr-ops-docs-agent-definition.md)
- [#98 — workspace routing table](2026-05-17-gh-098-workspace-routing-table.md)

## Impact

- Deleting the source would discard an unverified parent-level completion
  claim.
- Treating the claim as current could misroute workspace work.
- The uncertainty affects workspace orchestration, not this Python package.

## Environment / versions

```text
Source: ConcaveTrillion/pdomain-book-tools#77
Reported artifacts: .claude/agents/pd-ui.md and
  .claude/agents/pd-ocr-ops.md with full routing definitions
Created: 2026-05-17T10:36:04Z
Last source update: 2026-05-19T04:49:34Z
```

## Evidence

The source requests Claude subagent definitions and routing for `pd-ui` and
`pd-ocr-ops`. Its only comment says both full-power files existed in the
workspace with full routing definitions. The comment cites no commit, test,
current path, or governed successor.

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/77>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABCgbZAw`
- **Raw export:** `migration/github-issues/raw/issue-77.json`
- **Raw SHA-256:** `2da2187bd0a3ad5b0cb015e19811f6e29d49a2eb76181636eb0c7e79a09baee1`
- **Migration cutover:** `6842ec6b11c06c9b987b384b4abf7e9dc4699014`

## Root-cause hypotheses

1. **The definitions remain in workspace tooling.** The completion comment may
   still describe current files, but their commits and routing require proof.
2. **The artifacts moved or were replaced.** Later workspace conventions may
   have changed their paths, names, or ownership.

## Defects to fix

1. **Unverified parent claim.** Identify the current full-power definitions and
   their owning commits. (Primary)
2. **Unverified routing.** Confirm that workspace routing still delegates to
   both agents as reported.

## Next steps

1. Locate the current full-power definitions and routing source.
2. Verify the two roles and their routing behavior.
3. Cite the current files and commits before retiring the parent record.

## What is NOT broken

- No defect in `pdomain-book-tools` package behavior is claimed.
- The child records preserve their own paths, digests, and migration questions.

## Resolution

_Open._ The parent completion claim still needs independent verification. The
governed file and raw export retain that work after GitHub issue #77 is deleted.
