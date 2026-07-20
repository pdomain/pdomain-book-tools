---
Status: active
Owner: CT
Created: 2026-05-17
Last verified: 2026-07-20
Kind: issue
Level: I1
---

# Verify the external full-power pd-ocr-ops agent definition

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-20
- **Resolution:** Open
- **Severity:** Low — the reported workspace agent is not locally verifiable
- **Affected version:** Workspace state reported on 2026-05-17
- **Read when:** deciding whether closed GitHub issue #96 can be deleted.
- **Search terms:** pd-ocr-ops agent, full-power agent, workspace agent definition.
- **Relates to:** [Parent workspace-agent issue](2026-05-17-gh-077-workspace-agent-definitions.md)

## Summary

Closed GitHub issue #96 requested a full-power `.claude/agents/pd-ocr-ops.md`
definition. Its migration comment moved ownership to
`ConcaveTrillion/ocr-container-meta`, but it named no successor issue, current
file, implementation commit, or test. The external artifact therefore remains
unverified.

## Impact

- Deleting the source would remove the only retained tracker record for this
  unverified agent definition.
- Assuming the definition exists could misroute full-power OCR operations work.
- The uncertainty affects workspace orchestration, not this Python package.

## Environment / versions

```text
Source: ConcaveTrillion/pdomain-book-tools#96
Reported artifact: .claude/agents/pd-ocr-ops.md
Parent issue: #77
Created: 2026-05-17T10:41:51Z
Last source update: 2026-05-17T12:02:25Z
```

## Evidence

The issue body says `Approach: (see plan)`. It points to the historical plan
anchor `#write-claudeagentspd-ocr-opsmd-full-power-agent` and tracks #77. Its
only comment says cross-cut plans were moving to
`ConcaveTrillion/ocr-container-meta`; it does not identify the new record.

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/96>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABCgcJkA`
- **Raw export:** `migration/github-issues/raw/issue-96.json`
- **Raw SHA-256:** `b121ea1fb68ebcfdb26c694fd4fff648446b9d540c39c57fffe94708269db500`
- **Migration cutover:** `6842ec6b11c06c9b987b384b4abf7e9dc4699014`

## Root-cause hypotheses

1. **The definition moved to workspace tooling.** The migration comment names
   the meta repository, but the current path and successor record are missing.
2. **The definition was replaced.** Later workspace conventions may use a
   different operations agent or routing model.

## Defects to fix

1. **Unverified definition.** Locate the current full-power `pd-ocr-ops` agent
   and its owning commit. (Primary)
2. **Unverified successor.** Identify the meta-repository record that replaced
   issue #96.

## Next steps

1. Search the workspace tooling repository for the current `pd-ocr-ops`
   definition.
2. Verify its full-power role and routing behavior.
3. Cite the current file, commit, and successor record before retirement.

## What is NOT broken

- No defect in `pdomain-book-tools` package behavior is claimed.
- The parent #77 claim and the other four child concerns have separate records.

## Resolution

_Open._ Retain issue #96 until the external definition and migration
destination are verified.
