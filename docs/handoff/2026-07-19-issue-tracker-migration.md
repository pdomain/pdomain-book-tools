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

# GitHub issue migration is ready for the final 43-source cutover

## Agent Index

- Kind: handoff
- Status: active
- Read when: completing or auditing the final GitHub issue cutover
- Search terms: GitHub migration, zero issue count, source deletion, deletion journal

## Goal

Delete and verify all 43 remaining GitHub source issues, then disable GitHub
Issues. Keep their governed Git records active until the underlying work is
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
- Verified the live tracker contains exactly 33 open issues and 10 held closed
  issues. That retained set matches the reconciliation table.

## Not done

- Delete and verify the remaining 43 GitHub source issues, then disable GitHub
  Issues.
- Keep the 43 governed records under `docs/issues/`; deletion of their source
  copies does not change their local resolution state.

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
- `migration/github-issues/deletion-journal.tsv` — 342-row deletion audit trail
- `docs/context/github-issues-migration-ledger.md` — completed-issue evidence
- `docs/issues/README.md` — 43 active governed records
- `docs/context/current-state.md` — live counts and current risk

## Resume steps

1. Merge the owner decision and the 43 deletion-ready reconciliation rows.
2. Delete closed sources first, then open sources, in batches of at most 10.
3. Commit and push pre-delete journal rows before each batch.
4. Verify the REST absence and deleted-page marker, then commit and push the
   matching post-delete rows before continuing.
5. Confirm the live count is zero, disable GitHub Issues, and verify the feature
   is disabled.
