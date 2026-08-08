---
Status: active
Owner: CT
Created: 2026-08-08
Last verified: 2026-08-08
Kind: issue
Level: I1
---

# Five workspace repos have had no CI since a scripted sweep on 2026-07-12

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-08-08
- **Resolution:** Open
- **Severity:** High — five repositories have merged code with no checks for nearly a month
- **Affected version:** workspace-wide as of 2026-08-08
- **Read when:** a workflow will not fire, a repo reports no check runs, or you are deciding where cross-cut work is tracked
- **Search terms:** actions disabled, no CI, dep-refresh never ran, 2026-07-12 sweep, cross-cut, workspace-wide
- **Relates to:** [issues index](README.md),
  [dep-refresh cannot auto-land](2026-08-08-dep-refresh-cannot-auto-land.md)

## Summary

**This is a stub.** It records a confirmed finding and the decision about where
cross-cut work now lives, so neither is lost. It needs expansion before anyone
acts on it.

GitHub Actions is disabled at the repository level in five workspace repos:
`pdomain-ocr-labeler-spa`, `pdomain-ocr-synth`, `pdomain-ocr-trainer-spa`,
`pdomain-ocr-training`, and `pdomain-prep-for-pgdp`. All five stopped within a
sixteen-second window on 2026-07-12. They have had no CI of any kind since, so
everything merged there in that time merged unchecked.

## Impact

- Five of twelve repos run no checks on any pull request or push.
- Their required status checks can never be satisfied, because no check runs at
  all, so nothing can merge without an administrator override.
- The weekly dep-refresh has never fired in any of the five, which is how the
  gap stayed invisible.

## Environment / versions

```text
verified 2026-08-08
disabled  ocr-labeler-spa 10:08:58Z · ocr-synth 10:09:02Z
          ocr-trainer-spa 10:09:06Z · ocr-training 10:09:09Z
          prep-for-pgdp   10:09:14Z          (all 2026-07-12, last run of any workflow)
enabled   book-tools, index-npm, index-pip, ocr-cli, simple-gui, ops, ui
          (all still running weekly through 2026-08-02)
```

## Evidence

`gh api repos/pdomain/<repo>/actions/permissions --jq '.enabled'` returns
`false` for all five and `true` for the other seven.

The five stopped in strict four-second sequence, then the same sweep continued
into closing stale dependency pull requests elsewhere: `index-pip` #22–#25 at
10:09:50–51Z and `simple-gui` #41–#44 at 10:09:56–58Z. One script iterating the
workspace, running about a minute end to end. The `main` to `master`
default-branch rename carries the same date.

## Root-cause hypotheses

1. **(Confirmed) A single scripted sweep on 2026-07-12 disabled Actions in five
   repos.** The timing rules out five separate manual actions.
2. **(Open) Whether disabling was intended is unknown.** A cleanup pass that
   meant only to close stale PRs and rename the default branch could have
   disabled Actions as a side effect. Repository-scoped data cannot separate
   the two.

## Defects to fix

1. **Five repos have no CI.** (Primary)
2. **The cause is unidentified.** The script that ran has not been located.
3. **Nothing detects this.** No check reports that a repo's Actions are off.

## Next steps

1. Establish whether the disabling was deliberate. Search the workspace for what
   committed in the 10:08:58–10:09:58Z window on 2026-07-12; that should name
   the script.
2. If accidental, re-enable Actions in all five and expect the dep-refresh
   backlog to fire.
3. If deliberate, say so here and stand down the five per-repo dep-refresh
   reports, which currently recommend a restore.
4. Expand this stub with whatever step 1 finds.

## What is NOT broken

- The seven enabled repos are unaffected and running weekly.
- No workflow file is at fault. The crons are identical across all twelve.
- This is separate from the unsatisfiable-merge-gate defect, which affects a
  different and partly overlapping set of repos.

## Resolution

*Open, and a stub.* Expand before acting.

## Cross-cut convention

`ConcaveTrillion/ocr-container-meta` is no longer the home for cross-cut work.
Workspace-wide items are filed here, in `pdomain-book-tools/docs/issues/`, and
linked from the affected repos.

Note for whoever picks this up: the meta repo was still live and in use on
2026-08-08, with 23 open issues and activity that same day, so other sessions
may still be filing there. Nine repos still instruct agents to use it, in
`AGENTS.md` for `pdomain-book-tools`, `pdomain-ocr-cli`, `pdomain-ui`, and
`pdomain-ocr-labeler-spa`, and in `CLAUDE.md` for four more. Those pointers need
updating or the convention will not hold.
