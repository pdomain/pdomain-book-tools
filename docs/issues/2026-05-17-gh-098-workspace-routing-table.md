---
Status: active
Owner: CT
Created: 2026-05-17
Last verified: 2026-07-20
Kind: issue
Level: I1
---

# Verify the external workspace agent routing table

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-20
- **Resolution:** Open
- **Severity:** Low — the reported workspace routing is not locally verifiable
- **Affected version:** Workspace state reported on 2026-05-17
- **Read when:** deciding whether closed GitHub issue #98 can be deleted.
- **Search terms:** workspace CLAUDE.md, agent routing table, pd-ui, pd-ocr-ops.
- **Relates to:** [Parent workspace-agent issue](2026-05-17-gh-077-workspace-agent-definitions.md)

## Summary

Closed GitHub issue #98 requested an update to the workspace `CLAUDE.md`
routing table for the `pd-ui` and `pd-ocr-ops` agents. Its migration comment
moved ownership to `ConcaveTrillion/ocr-container-meta`, but it named no
successor issue, current routing file, implementation commit, or test. The
external routing remains unverified.

## Impact

- Deleting the source would remove the only retained tracker record for this
  unverified routing change.
- Missing or stale routing could send work to the wrong agent or permission
  profile.
- The uncertainty affects workspace orchestration, not this Python package.

## Environment / versions

```text
Source: ConcaveTrillion/pdomain-book-tools#98
Reported artifact: workspace CLAUDE.md routing table
Parent issue: #77
Created: 2026-05-17T10:41:52Z
Last source update: 2026-05-17T12:02:29Z
```

## Evidence

The issue body says `Approach: (see plan)`. It points to the historical plan
anchor `#update-workspace-claudemd-routing-table` and tracks #77. Its only
comment says cross-cut plans were moving to
`ConcaveTrillion/ocr-container-meta`; it does not identify the new record.

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/98>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABCgcJxQ`
- **Raw export:** `migration/github-issues/raw/issue-98.json`
- **Raw SHA-256:** `237aab0f102df336a7198638c1922b70620c97a3c4c47e6788a82cb1f0fbaa52`
- **Migration cutover:** `6842ec6b11c06c9b987b384b4abf7e9dc4699014`

## Root-cause hypotheses

1. **The routing moved to workspace tooling.** The migration comment names the
   meta repository, but the current file and successor record are missing.
2. **The routing model changed.** Later workspace conventions may no longer use
   the historical `CLAUDE.md` table.

## Defects to fix

1. **Unverified routing.** Locate the current routing source and confirm entries
   for all four reported agents. (Primary)
2. **Unverified successor.** Identify the meta-repository record that replaced
   issue #98.

## Next steps

1. Locate the current workspace routing source.
2. Verify routing to the full-power and read-only agent pairs.
3. Cite the current file, commit, and successor record before retirement.

## What is NOT broken

- No defect in `pdomain-book-tools` package behavior is claimed.
- The four agent definitions and parent #77 claim have separate records.

## Resolution

_Open._ Retain issue #98 until the external routing and migration destination
are verified.
