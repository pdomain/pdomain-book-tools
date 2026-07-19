---
kind: handoff
status: "active"
created: "2026-07-19"
created_at: "2026-07-19T15:51:00Z"
owner: CT
branch: master
scope: issue-tracker-migration
worktree: /workspaces/pdomain/pdomain-book-tools
base_commit: e94e8a683fe41fc7070cfcb24aa5068dde9f446a
supersedes: docs/handoff/2026-07-17-issue-tracker-migration.md
---

# GitHub issue migration retains 43 gated source issues

## Agent Index

- Kind: handoff
- Status: active
- Read when: resolving the retained GitHub issues after the documentation migration
- Search terms: GitHub migration, deletion holds, retained issues, deletion journal

## Goal

Finish the remaining issue cleanup only when each governed record's evidence
gate permits it. Do not treat a zero GitHub issue count as the current goal.

## Done

- Migrated all 214 source issues into governed documentation and immutable raw
  exports in PR #234.
- Recorded migration commit
  `6842ec6b11c06c9b987b384b4abf7e9dc4699014` in every reconciliation row in
  PR #235.
- Classified all source issues with doc-migrator, promoted shipped behavior to
  architecture, retired one implemented spec, and refreshed authored context.
- Permanently deleted and verified 171 completed issues in 18 batches.
- Merged 171 matching `pre_delete` and `post_delete_verification` journal rows
  in PR #236.
- Verified the live tracker contains exactly 33 open issues and 10 held closed
  issues. That retained set matches the reconciliation table.

## Not done

- GitHub Issues remains enabled because 43 source issues are intentionally
  retained.
- Closed issues #43, #54, #65, #77, #94 through #98, and #165 remain. Their
  reconciliation rows prohibit deletion until external evidence, owner
  decisions, or residual implementation work resolves the named gate.
- The 33 open issues remain active work represented by governed records under
  `docs/issues/`.

## Failed approach

GitHub GraphQL returns an error for a deleted issue instead of a successful
response containing `null`. Batch 1 stopped at that verification step after
all ten deletions had succeeded. Verification then used both the REST 404 and
the issue page's `This issue has been deleted` marker. The recovered batch and
all later batches have matching post-delete journal rows.

## Decisions

- Keep GitHub Issues enabled while any governed source issue remains.
- Never bypass a reconciliation row whose cutover action starts with
  `Do not delete`.
- Use the immutable raw exports and append-only journal as the deletion audit
  trail; do not recreate retired per-issue documents for completed work.

## Pointers

- `migration/github-issues/reconciliation.tsv` — authoritative per-issue gate
- `migration/github-issues/deletion-journal.tsv` — 342-row deletion audit trail
- `docs/context/github-issues-migration-ledger.md` — completed-issue evidence
- `docs/issues/README.md` — 38 active governed records
- `docs/context/current-state.md` — live counts and current risk

## Resume steps

1. Read the relevant governed record and reconciliation row before changing a
   retained issue.
2. Resolve the exact external-evidence, owner-decision, or residual-work gate.
3. Update the governed record, authored context, and reconciliation action.
4. If deletion becomes eligible, repeat the journal-before-delete and
   journal-after-verification sequence from the migration runbook.
5. Disable GitHub Issues only after the live count reaches zero through valid
   per-record decisions.
