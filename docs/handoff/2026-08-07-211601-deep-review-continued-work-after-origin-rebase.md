---
kind: handoff
status: "active"
created: "2026-08-07"
created_at: "2026-08-07T21:16:01Z"
owner: CT
branch: master
scope: deep-review-continued-work
worktree: /workspaces/pdomain/pdomain-book-tools
base_commit: 6b8e61023b187cdf4e609262e386d5a5a9cf27cf
supersedes: docs/handoff/2026-07-21-143246-deep-review-continued-work.md
---

# Deep review continued work — rebased onto the completed issue migration

## Agent Index

- Kind: handoff
- Status: active
- Read when: resuming the 2026-07-21 deep-review plan, or reconciling the two issue record sets
- Search terms: deep review, continued work, rebase, origin divergence, duplicate issue records, B3 xfail

## Goal

Execute the continued-work plan from the 2026-07-21 deep code review. Close
confirmed correctness and CI-truth gaps first, then layout test debt and
dual-path hardening, using the governed issue records as the work queue.

## Done this session

- Found that local `master` had diverged from `origin/master` at `a7bff12`
  (2026-07-17): 10 local commits ahead, 86 behind. None of the local deep-review
  work had been pushed.
- Rebased the 10 local commits onto `origin/master` (`28c9e02`). Resolved four
  conflicts: `.pre-commit-config.yaml` (identical on both sides),
  `docs/issues/TEMPLATE.md` (kept the local fenced-`text` version),
  `docs/issues/README.md` (merged both indexes), `docs/context/intent-map.md`
  (kept origin, which had already dropped the stale spec-07 line).
- Merged the two `docs/issues/` indexes into one README: 43 migrated `gh-NNN`
  records, 20 open reports, 8 resolved.
- Filed `docs/issues/2026-08-07-duplicate-issue-records-after-rebase.md` for the
  24 migrated records that duplicate four deep-review reports and two deferred
  plan items.
- Removed the untracked `tmp/github-issues-migration/` scratch. Its batch lists
  are covered by `docs/context/github-issues-migration-ledger.md` and the
  journaled deletion commits on origin.
- Verified `basedpyright` strict, ruff check, ruff format, markdownlint, and
  `uv.lock` sync all pass after the rebase.

## Prior sessions (carried forward)

Theme A and the first half of Theme B already landed and are still on the
branch after the rebase:

- A1 dual-domain reorganize band thresholds.
- A2 early-return reconcile, A3 soft recover, A4 GPU textline polarity.
- A5 README orientation examples, D3 roadmap/intent-map backlog sync.
- B1 layout-fed regression harness, B2 default-mode baseline track.

## Not done

- B3: the five strict xfails in `KNOWN_FAILING_BASELINES` are still open. This
  is the only High-severity item and is next in sequence.
- B4 branch-targeted reorg unit tables; Themes C and D untouched.
- Theme E owner decision pack not run. Themes G, H, and I stay blocked on it.
- The two issue record sets are not yet reconciled.
- Nothing pushed. The branch is 11 commits ahead of `origin/master`.

## Failed approaches

- `make ci AI=1` cannot complete on a clean tree. The `pre-commit-update` hook
  bumps `.pre-commit-config.yaml` and fails the run, and `pre-commit-check`
  hardcodes `SKIP=basedpyright`, so an outer `SKIP` is discarded. Workaround:
  `git checkout -- .pre-commit-config.yaml`, then run
  `SKIP=pre-commit-update uv run pre-commit run --all-files` plus the remaining
  make targets directly. This is a pre-existing condition, not rebase fallout.
- A background pre-commit run overlapped a subagent editing a tracked file. The
  `check-added-large-files` hook reported "files were modified by this hook".
  It passes in isolation; do not run the gate while an agent is editing.

## Decisions

- Rebase, not merge, chosen by the owner for reconciling with origin.
- Origin's README prose wins where the two versions said the same thing; it is
  the readability-edited copy.
- The stale spec-07 promotion note stays dropped. Origin removed it during the
  migration, so the local D3 fix was redundant.
- Both issue record sets stay live until reconciled one cluster at a time. No
  bulk retirement.
- Safety branches kept at the divergence point and at the pre-rebase tip.

## State

- Branch `master` is 11 ahead of `origin/master` and 0 behind, tipped by
  `docs: reconcile issue records and handoffs after origin rebase`. Working
  tree clean.
- Backup branches: `backup/local-master-2026-07-17`,
  `backup/pre-rebase-2026-08-07`.
- `git rerere` is now enabled in this repo's config.

## Pointers

- `docs/plans/2026-07-21-continued-work-from-deep-review.md`
- `docs/issues/README.md`
- `docs/issues/2026-07-21-reorganize-known-failing-baselines-xfail.md`
- `docs/issues/2026-08-07-duplicate-issue-records-after-rebase.md`
- `docs/research/2026-07-21-deep-code-review-findings.md`
- `docs/context/github-issues-migration-ledger.md`
- `docs/handoff/2026-07-19-issue-tracker-migration.md`
- `docs/context/intent-map.md`

## Resume steps

1. `git status` and `git log -3 --oneline`. Confirm the tip is `docs: reconcile
   issue records and handoffs after origin rebase` or later, and that the branch
   is 0 behind `origin/master`.
2. Start B3: for each case in `KNOWN_FAILING_BASELINES`, either fix behavior to
   meet the baseline or revise the baseline with a dated owner accept. Do not
   leave a permanent strict xfail.
3. Run Theme E alongside B3. It needs no code and unblocks six open records.
4. Reconcile the duplicate record clusters one at a time, per the recommended
   steps in the 2026-08-07 issue report.
5. Verify with `SKIP=pre-commit-update uv run pre-commit run --all-files`, not
   `make ci`, until the hook conflict is fixed.
6. Decide whether to push. The branch has never been pushed.

## Pickup prompt

After `/clear`, send:

Use the docgraph:pickup-handoff skill for scope "deep-review-continued-work" in worktree "/workspaces/pdomain/pdomain-book-tools".
