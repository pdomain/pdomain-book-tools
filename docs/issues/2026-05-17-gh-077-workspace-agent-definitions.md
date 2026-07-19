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
- **Read when:** deciding whether closed GitHub issues #77 or #94 through #98 can be deleted.
- **Search terms:** pd-ui agent, pd-ui-docs, pd-ocr-ops agent, pd-ocr-ops-docs, workspace CLAUDE routing.
- **Relates to:** [GitHub issues migration ledger](../context/github-issues-migration-ledger.md)

## Summary

Closed parent issue #77 reports that two workspace agent definitions existed
with full routing. Child issues #94 through #98 separately tracked four agent
files and the workspace `CLAUDE.md` routing table. This repository cannot verify
any of those external workspace artifacts.

## Impact

- Deleting the six raw sources would leave unverified workspace-state claims.
- Treating the files as current could misroute work if they moved or changed.
- The uncertainty affects workspace orchestration, not the Python package.

## Environment / versions

```text
Source: ConcaveTrillion/pdomain-book-tools#77
Children: #94, #95, #96, #97, #98
Reported complete: 2026-05-19
Child migration comments: 2026-05-17
Historical agent paths: .claude/agents/pd-ui.md, .claude/agents/pd-ui-docs.md,
  .claude/agents/pd-ocr-ops.md, .claude/agents/pd-ocr-ops-docs.md
Historical routing file: workspace CLAUDE.md
```

## Evidence

The source points to the spec
`docs/specs/2026-05-17-superpowers-gh-workflow-integration-design.md`; its plan
is `docs/plans/2026-05-16-workspace-agent-defs-pd-ui-pd-ocr-ops.md`.
The only comment says `.claude/agents/pd-ocr-ops.md` and
`.claude/agents/pd-ui.md` both existed in the workspace with full routing
definitions. It cites no commit, tests, or governed successor.

The five child bodies all use `Approach: (see plan)`, track #77, and point to
the historical
`docs/superpowers/plans/2026-05-16-workspace-agent-defs-pd-ui-pd-ocr-ops.md`.
Their anchors and requested artifacts are:

- #94 `#write-claudeagentspd-uimd-full-power-agent` — full-power
  `.claude/agents/pd-ui.md`.
- #95 `#write-claudeagentspd-ui-docsmd-read-only-haiku` — read-only Haiku
  `.claude/agents/pd-ui-docs.md`.
- #96 `#write-claudeagentspd-ocr-opsmd-full-power-agent` — full-power
  `.claude/agents/pd-ocr-ops.md`.
- #97 `#write-claudeagentspd-ocr-ops-docsmd-read-only-haik` — read-only Haiku
  `.claude/agents/pd-ocr-ops-docs.md`.
- #98 `#update-workspace-claudemd-routing-table` — workspace `CLAUDE.md`
  routing-table update.

Each child has one comment. All five comments say the cross-cut plans were
migrating to `ConcaveTrillion/ocr-container-meta`. The comments establish an
ownership move, but they do not identify successor issues, commits, tests, or
the current files.

The immutable raw export at
`migration/github-issues/raw/issue-77.json` preserves the issue and comment. Its
SHA-256 digest is
`2da2187bd0a3ad5b0cb015e19811f6e29d49a2eb76181636eb0c7e79a09baee1`.

The child exports preserve their individual provenance:

- [#94 raw](../../migration/github-issues/raw/issue-94.json) —
  `98293c518f692545b519272d981449923c06a60fc8446a6c82d7b0006cdb9826`.
- [#95 raw](../../migration/github-issues/raw/issue-95.json) —
  `1a88aaa5197922c7f8acfa34b46d2b6ef1a3121837841c0726a5cda7196a9701`.
- [#96 raw](../../migration/github-issues/raw/issue-96.json) —
  `b121ea1fb68ebcfdb26c694fd4fff648446b9d540c39c57fffe94708269db500`.
- [#97 raw](../../migration/github-issues/raw/issue-97.json) —
  `6d025564bf304b5b674fc9800a0b2cdfead6bd0541e41326b771fad676aa5edb`.
- [#98 raw](../../migration/github-issues/raw/issue-98.json) —
  `237aab0f102df336a7198638c1922b70620c97a3c4c47e6788a82cb1f0fbaa52`.

## Root-cause hypotheses

1. **The definitions and routing remain in workspace tooling.** The parent
   comment reports two files. Current files and routing checks are still needed
   for all five child concerns.
2. **The artifacts moved or were replaced.** Later workspace conventions may
   have changed their paths or ownership after the meta-repository migration.

## Defects to fix

1. **Unverified external files.** Identify the owning repository, current
   paths, and commits for all four agent definitions. (Primary)
2. **Unverified routing.** Confirm the workspace routing table delegates
   correctly to all four definitions.
3. **Unverified migration destination.** Identify the meta-repository successor
   records for #94 through #98.

## Next steps

1. Locate all four current definitions and the workspace routing table.
2. Verify full-power versus read-only Haiku roles and their routing behavior.
3. Cite the owning commits and any meta-repository successor records.
4. Retire only with that evidence; retain raws #77 and #94 through #98 meanwhile.

## Resolution

_Open._ Owner verification of all four external definitions, workspace routing,
and migration destinations is required.
