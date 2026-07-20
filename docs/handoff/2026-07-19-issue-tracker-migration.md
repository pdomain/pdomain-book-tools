---
kind: handoff
status: "complete"
created: "2026-07-19"
created_at: "2026-07-19T15:51:00Z"
owner: CT
branch: master
scope: issue-tracker-migration
worktree: /workspaces/pdomain/pdomain-book-tools
base_commit: e94e8a683fe41fc7070cfcb24aa5068dde9f446a
supersedes: docs/handoff/2026-07-17-issue-tracker-migration.md
---

# GitHub issue migration completed with a zero-issue cutover

## Agent Index

- Kind: handoff
- Status: complete
- Read when: auditing the completed GitHub issue cutover
- Search terms: GitHub migration, zero issue count, source deletion, deletion journal

## Goal

Preserve every source issue in Git, delete the remote copies, and disable
GitHub Issues. Keep governed Git records active until their underlying work is
actually resolved.

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
- Deleted and verified the final 43 source copies in five batches after the
  Git-only tracking decision merged.
- Verified all 214 issues have one pre-delete and one post-delete journal row.
- Verified the live issue count is zero and disabled GitHub Issues.

## Not done

- Resolve the 43 active governed records under `docs/issues/`. Remote source
  deletion did not change their local resolution state.

## Failed approach

GitHub GraphQL returns an error for a deleted issue instead of a successful
response containing `null`. Batch 1 stopped at that verification step after
all ten deletions had succeeded. Verification then used both the REST 404 and
the issue page's `This issue has been deleted` marker. The recovered batch and
all later batches have matching post-delete journal rows.

## Decisions

- Git files replace GitHub Issues as the sole tracker after the journaled
  cutover.
- Keep unresolved local records active even after their GitHub copies are
  deleted.
- Use the immutable raw exports and append-only journal as the deletion audit
  trail; do not recreate retired per-issue documents for completed work.

## Pointers

- `migration/github-issues/reconciliation.tsv` — authoritative per-issue gate
- `migration/github-issues/deletion-journal.tsv` — 428-row deletion audit trail
- `docs/context/github-issues-migration-ledger.md` — completed-issue evidence
- `docs/issues/README.md` — 43 active governed records
- `docs/context/current-state.md` — live counts and current risk

## Resume steps

1. Use `docs/issues/README.md` as the active work index.
2. Resolve each record through its technical or owner-decision workflow.
3. Use `doc-retirer` only when the local record's own evidence supports
   retirement; remote deletion alone is not resolution evidence.
