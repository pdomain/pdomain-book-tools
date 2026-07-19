---
Status: active
Owner: CT
Created: 2026-05-17
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Verify the external pd-ui and pd-ocr-ops agent definitions

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Low — reported workspace files are not locally verifiable
- **Affected version:** Workspace state reported on 2026-05-19
- **Read when:** deciding whether closed GitHub issue #77 can be deleted.
- **Search terms:** pd-ui agent, pd-ocr-ops agent, workspace routing definitions.
- **Relates to:** [GitHub issues migration ledger](../context/github-issues-migration-ledger.md)

## Summary

Closed issue #77 reports that two workspace agent definitions existed with full
routing. This repository contains neither file and cannot verify current
workspace state.

## Impact

- Deleting the raw source would leave an unverified workspace-state claim.
- Treating the files as current could misroute work if they moved or changed.
- The uncertainty affects workspace orchestration, not the Python package.

## Environment / versions

```text
Source: ConcaveTrillion/pdomain-book-tools#77
Reported complete: 2026-05-19
Historical agent paths: .claude/agents/pd-ocr-ops.md, .claude/agents/pd-ui.md
```

## Evidence

The source points to the spec
`docs/specs/2026-05-17-superpowers-gh-workflow-integration-design.md`; its plan
is `docs/plans/2026-05-16-workspace-agent-defs-pd-ui-pd-ocr-ops.md`.
The only comment says `.claude/agents/pd-ocr-ops.md` and
`.claude/agents/pd-ui.md` both existed in the workspace with full routing
definitions. It cites no commit, tests, or governed successor.

The immutable raw export at
`migration/github-issues/raw/issue-77.json` preserves the issue and comment. Its
SHA-256 digest is
`2da2187bd0a3ad5b0cb015e19811f6e29d49a2eb76181636eb0c7e79a09baee1`.

## Root-cause hypotheses

1. **The definitions remain in workspace tooling.** The comment reports their existence, but current files and routing checks are needed.
2. **The definitions moved or were replaced.** Later workspace conventions may have changed their paths or ownership.

## Defects to fix

1. **Unverified external files.** Identify the owning repository, current paths, and commit. (Primary)
2. **Unverified routing.** Confirm both definitions still provide the claimed full routing.

## Next steps

1. Locate both current definitions and the repository that owns them.
2. Verify their routing behavior and cite a commit or governed record.
3. Retire only with that evidence; retain raw #77 meanwhile.

## Resolution

_Open._ Owner verification of both external agent definitions is required.
