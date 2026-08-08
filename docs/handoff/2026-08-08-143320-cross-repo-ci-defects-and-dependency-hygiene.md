---
kind: handoff
status: "active"
created: "2026-08-08"
created_at: "2026-08-08T14:33:20Z"
owner: CT
branch: master
scope: ci-and-dependency-hygiene
worktree: /workspaces/pdomain/pdomain-book-tools
base_commit: 58055a2
supersedes: ""
---

# Cross-repo CI defects found while fixing dependency hygiene

## Agent Index

- Kind: handoff
- Status: active
- Read when: resuming the 2026-08-08 workspace CI investigation, or deciding where cross-cut issues are filed
- Search terms: dep-refresh, actions disabled, required status checks, ruff skew, cross-cut, 2026-07-12 sweep

## Goal

Close the CI and dependency defects found across the `pdomain-*` workspace on
2026-08-08. Everything found is filed and pushed. What remains is two owner
decisions and the work those unblock.

## Done this session

Started as a review of open issues in this repo and expanded. Full detail is in
the filed reports; this is the index.

- Rebased 10 unpushed local commits onto `origin/master` after finding a
  three-week divergence, then consolidated: 18 stale remote branches retired, 2
  worktrees removed, 9 local branches deleted. Only `master` remains on origin.
- Fixed the `pre-commit-update` hook across all 9 repos that carry it. It
  rewrote pinned revisions then failed the run, so neither `git commit` nor
  `make ci` could pass on a clean tree. Now staged manual with a
  `make update-hooks` target.
- Upgraded 31 dependencies here and adapted to ruff 0.16: 20 library signatures
  made keyword-only for `PLR0917`, Markdown excluded from the formatter. Two
  downstream repos updated for the API change.
- Filed 11 dep-refresh reports, one per affected repo, plus a cross-cut stub.
- Repaired stale `.git/hooks/pre-commit` in 5 repos pointing at deleted
  worktrees.

## Open decisions, both blocking

1. **Was the 2026-07-12 sweep meant to disable Actions?** Five repos have had no
   CI since. If deliberate, five reports should stand down; if not, re-enable.
   See `docs/issues/2026-08-08-actions-disabled-five-repos.md`.
2. **Is `ConcaveTrillion/ocr-container-meta` retired?** The owner said it is
   gone, but it was live on 2026-08-08 with 23 open issues and same-day
   activity, so another session may still be filing there. Nine repos still
   instruct agents to use it.

## Not done

- The cross-cut stub is a stub. Expand after decision 1.
- Nine repos still point agents at the meta repo in `AGENTS.md` or `CLAUDE.md`.
- This repo's `CLAUDE.md` does not mention its own `docs/issues/` convention.
- Ruff skew remains in `pdomain-ocr-labeler-spa` only; other sessions closed it
  in `pdomain-prep-for-pgdp`.
- Unsatisfiable merge gates are filed but unfixed in 5 repos.
- Original deep-review work untouched: B3's five strict xfails, Theme E.
- Markdown-in-ruff was answered two ways across repos and is unsettled.

## Failed approaches

- `SKIP=` in the Makefile did not fix the hook problem. The git commit hook runs
  independently, so only manual staging works.
- Counting commits to judge whether a branch was merged is wrong here. Squashed
  PRs leave 12 to 37 "unmerged" commits with zero unique patches. Use
  `git log --cherry-pick --right-only`.
- Three of my own premises were wrong and caught by verification: `ocr-cli`'s
  gate is broken, `ocr-training`'s mismatch is one word not a format, and
  `index-pip`'s PRs were half batch-closed.

## Decisions

- Cross-cut workspace items are filed in `pdomain-book-tools/docs/issues/`.
- Rebase, not merge, for reconciling with origin.
- Fix lint findings properly rather than suppressing; the only `PLR0917`
  suppression is for `@patch`-decorated tests, which a signature change cannot
  fix.
- Markdown excluded from ruff here, to keep a second formatter out of governed
  specs.

## State

- All 11 repos committed and pushed. Nothing outstanding.
- `pdomain-prep-for-pgdp` holds 6 uncommitted frontend files from another
  session, deliberately untouched.
- Backup branches here: `backup/local-master-2026-07-17`,
  `backup/pre-rebase-2026-08-07`. Both redundant; drop in a few days.
- Deleted-branch recovery SHAs are in this session's scratchpad only and will
  not survive a reboot. All 18 were verified fully absorbed first.
- Four other Claude sessions were active in this workspace, two of them busy.
  Expect concurrent edits and a staging race in shared trees.

## Pointers

- `docs/issues/2026-08-08-actions-disabled-five-repos.md`
- `docs/issues/2026-08-08-dep-refresh-cannot-auto-land.md`
- `docs/issues/README.md`
- `../pdomain-ui/docs/specs/2026-07-16-dep-refresh-auto-land-design.md`
- `docs/plans/2026-07-21-continued-work-from-deep-review.md`
- `docs/process/lint-deviations.md`

## Resume steps

1. `git status` and `git log -3 --oneline`; confirm the tip is
   `docs(issues): stub the disabled-Actions finding and cross-cut home`.
2. Answer decision 1 by finding what committed across the workspace between
   10:08:58Z and 10:09:58Z on 2026-07-12. That should name the script.
3. Answer decision 2 with the owner, then update the nine repos' agent pointers
   if the meta repo is retired.
4. Expand the cross-cut stub with what step 2 finds.
5. Only then act on the five unsatisfiable merge gates and the dep-refresh
   redesign.

## Pickup prompt

After `/clear`, send:

Use the docgraph:pickup-handoff skill for scope "ci-and-dependency-hygiene" in worktree "/workspaces/pdomain/pdomain-book-tools".
