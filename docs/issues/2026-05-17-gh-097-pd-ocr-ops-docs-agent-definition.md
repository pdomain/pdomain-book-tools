---
Status: active
Owner: CT
Created: 2026-05-17
Last verified: 2026-07-20
Kind: issue
Level: I1
---

# Verify the external read-only pd-ocr-ops-docs agent definition

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-20
- **Resolution:** Open
- **Severity:** Low — the reported workspace agent is not locally verifiable
- **Affected version:** Workspace state reported on 2026-05-17
- **Read when:** deciding whether closed GitHub issue #97 can be deleted.
- **Search terms:** pd-ocr-ops-docs agent, read-only Haiku, workspace agent definition.
- **Relates to:** [Parent workspace-agent issue](2026-05-17-gh-077-workspace-agent-definitions.md)

## Summary

Closed GitHub issue #97 requested a read-only Haiku
`.claude/agents/pd-ocr-ops-docs.md` definition. Its migration comment moved
ownership to `ConcaveTrillion/ocr-container-meta`, but it named no successor
issue, current file, implementation commit, or test. The external artifact
therefore remains unverified.

## Impact

- Deleting the source would remove the only retained tracker record for this
  unverified agent definition.
- Assuming the definition exists could grant the wrong capabilities to OCR
  operations documentation work.
- The uncertainty affects workspace orchestration, not this Python package.

## Environment / versions

```text
Source: ConcaveTrillion/pdomain-book-tools#97
Reported artifact: .claude/agents/pd-ocr-ops-docs.md
Reported role: read-only Haiku
Parent issue: #77
Created: 2026-05-17T10:41:52Z
Last source update: 2026-05-17T12:02:27Z
```

## Evidence

The issue body says `Approach: (see plan)`. It points to the historical plan
anchor `#write-claudeagentspd-ocr-ops-docsmd-read-only-haik` and tracks #77.
Its only comment says cross-cut plans were moving to
`ConcaveTrillion/ocr-container-meta`; it does not identify the new record.

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/97>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABCgcJpQ`
- **Raw export:** `migration/github-issues/raw/issue-97.json`
- **Raw SHA-256:** `6d025564bf304b5b674fc9800a0b2cdfead6bd0541e41326b771fad676aa5edb`
- **Migration cutover:** `6842ec6b11c06c9b987b384b4abf7e9dc4699014`

## Root-cause hypotheses

1. **The definition moved to workspace tooling.** The migration comment names
   the meta repository, but the current path and successor record are missing.
2. **The role was replaced.** Later workspace conventions may use a different
   model or permission boundary for documentation work.

## Defects to fix

1. **Unverified definition.** Locate the current read-only `pd-ocr-ops-docs`
   agent and its owning commit. (Primary)
2. **Unverified successor.** Identify the meta-repository record that replaced
   issue #97.

## Next steps

1. Search the workspace tooling repository for the current `pd-ocr-ops-docs`
   definition.
2. Verify its read-only role, model choice, and routing behavior.
3. Cite the current file, commit, and successor record before retirement.

## What is NOT broken

- No defect in `pdomain-book-tools` package behavior is claimed.
- The parent #77 claim and the other four child concerns have separate records.

## Resolution

_Open._ The external definition and migration destination still need
verification. The governed file and raw export retain that work after GitHub
issue #97 is deleted.
