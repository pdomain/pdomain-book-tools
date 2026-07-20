---
Status: active
Owner: CT
Created: 2026-05-17
Last verified: 2026-07-20
Kind: issue
Level: I1
---

# Verify the external full-power pd-ui agent definition

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-20
- **Resolution:** Open
- **Severity:** Low — the reported workspace agent is not locally verifiable
- **Affected version:** Workspace state reported on 2026-05-17
- **Read when:** deciding whether closed GitHub issue #94 can be deleted.
- **Search terms:** pd-ui agent, full-power agent, workspace agent definition.
- **Relates to:** [Parent workspace-agent issue](2026-05-17-gh-077-workspace-agent-definitions.md)

## Summary

Closed GitHub issue #94 requested a full-power `.claude/agents/pd-ui.md`
definition. Its migration comment moved ownership to
`ConcaveTrillion/ocr-container-meta`, but it named no successor issue, current
file, implementation commit, or test. The external artifact therefore remains
unverified.

## Impact

- Deleting the source would remove the only retained tracker record for this
  unverified agent definition.
- Assuming the definition exists could misroute full-power UI work.
- The uncertainty affects workspace orchestration, not this Python package.

## Environment / versions

```text
Source: ConcaveTrillion/pdomain-book-tools#94
Reported artifact: .claude/agents/pd-ui.md
Parent issue: #77
Created: 2026-05-17T10:41:50Z
Last source update: 2026-05-17T12:02:22Z
```

## Evidence

The issue body says `Approach: (see plan)`. It points to the historical plan
anchor `#write-claudeagentspd-uimd-full-power-agent` and tracks #77. Its only
comment says cross-cut plans were moving to
`ConcaveTrillion/ocr-container-meta`; it does not identify the new record.

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/94>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABCgcJZQ`
- **Raw export:** `migration/github-issues/raw/issue-94.json`
- **Raw SHA-256:** `98293c518f692545b519272d981449923c06a60fc8446a6c82d7b0006cdb9826`
- **Migration cutover:** `6842ec6b11c06c9b987b384b4abf7e9dc4699014`

## Root-cause hypotheses

1. **The definition moved to workspace tooling.** The migration comment names
   the meta repository, but the current path and successor record are missing.
2. **The definition was replaced.** Later workspace conventions may use a
   different agent name or routing model.

## Defects to fix

1. **Unverified definition.** Locate the current full-power `pd-ui` agent and
   its owning commit. (Primary)
2. **Unverified successor.** Identify the meta-repository record that replaced
   issue #94.

## Next steps

1. Search the workspace tooling repository for the current `pd-ui` definition.
2. Verify its full-power role and routing behavior.
3. Cite the current file, commit, and successor record before retirement.

## What is NOT broken

- No defect in `pdomain-book-tools` package behavior is claimed.
- The parent #77 claim and the other four child concerns have separate records.

## Resolution

_Open._ The external definition and migration destination still need
verification. The governed file and raw export retain that work after GitHub
issue #94 is deleted.
