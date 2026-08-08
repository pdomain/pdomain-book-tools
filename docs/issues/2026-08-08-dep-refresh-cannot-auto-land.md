---
Status: active
Owner: CT
Created: 2026-08-08
Last verified: 2026-08-08
Kind: issue
Level: I1
---

# No pull request can satisfy the required check, so dep-refresh never lands

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-08-08
- **Resolution:** Open
- **Severity:** High — the required status context is never produced, so auto-merge cannot land any pull request
- **Affected version:** pdomain-book-tools @ 2be7689
- **Read when:** a pull request will not merge, dep-refresh branches accumulate, or you are editing branch protection or ci.yml job names
- **Search terms:** required status check, branch protection, ci context, dep-refresh, auto-merge, stray branches, delete_branch_on_merge
- **Relates to:** [issues index](README.md), design spec at
  `../../../pdomain-ui/docs/specs/2026-07-16-dep-refresh-auto-land-design.md`

## Summary

Master branch protection requires one status context named `ci`, and nothing
produces a check by that name. The workflow file is named `ci`, but GitHub
reports one check per job, not per workflow, so the checks that actually appear
are `pre-commit`, `lint`, `typecheck`, `build`, `layout fork`, and
`test / py3.11` through `test / py3.13`.

The required context therefore stays pending forever. No pull request can
satisfy the gate, not even a fully green one. Auto-merge can never fire.

A second defect compounds it. The weekly dep-refresh opens a new dated branch
per run and the repository has `delete_branch_on_merge` off, so nothing is ever
cleaned up. Nine branches accumulated between 31 May and 2 August.

## Impact

- No pull request merges on its own. The only way anything lands is an
  administrator overriding the gate, which works because `enforce_admins` is
  false.
- Weekly dependency updates never reach master. The workflow runs and produces
  correct diffs, then the pull request sits until someone closes it.
- Two recent refresh pull requests, #241 and #242, were closed unmerged rather
  than landed, and their branches outlived them.
- Branch accumulation hid real work. The Actions pin updates those runs carried
  went unnoticed for over two months, because a `uv lock` never touches
  `.github/`, so nothing else would have surfaced them.

## Environment / versions

```text
pdomain-book-tools @ 2be7689
required contexts   ci
checks produced     pre-commit, lint, typecheck, build, layout fork,
                    test / py3.11, test / py3.12, test / py3.13
enforce_admins      false
delete_branch_on_merge  false
dep-refresh branch  dep-refresh/$(date +%Y-%m-%d)-$GITHUB_RUN_ID
```

## Evidence

### 1. The required context matches no produced check

```text
$ gh api repos/pdomain/pdomain-book-tools/branches/master/protection \
    --jq '.required_status_checks.contexts'
ci

$ gh api repos/pdomain/pdomain-book-tools/commits/<pr-head>/check-runs \
    --jq '[.check_runs[].name]|unique'
build, layout fork, lint, pre-commit,
test / py3.11, test / py3.12, test / py3.13, typecheck
```

`ci` is the workflow's `name:`, and `.github/workflows/ci.yml` defines jobs
`pre-commit`, `lint`, `typecheck`, `test`, `build`, and `layout-fork`. None is
named `ci`.

### 2. Merges only happen by administrator override

`enforce_admins` is false. Pull requests #237 through #240, the July issue
migration, all merged. Pull requests #241 and #242, both weekly dep refreshes,
are closed and unmerged. The pattern fits: work an administrator pushed through
landed, and work that depended on auto-merge did not.

### 3. Branches accumulated for two months

Nine `dep-refresh/<date>-<run-id>` branches existed, spanning 31 May to
2 August, one per run. They were deleted on 2026-08-08 after their only
unsuperseded content, the pinned action SHAs, was salvaged into commit
`2be7689`. The cause is untouched, so they will accumulate again.

### 4. The workflow itself is healthy

The five most recent dep-refresh runs all report `success`. The workflow
generates the update correctly. The failure is entirely in landing it.

## Root-cause hypotheses

1. **(Most likely) The required context was set from the workflow name.** A
   single context called `ci` reads like someone naming the workflow rather
   than a job. It would never have matched, and because administrators can
   bypass, the gap stayed invisible.
2. **Job names drifted after protection was configured.** If a job named `ci`
   once existed and was later split into the current six, the required context
   would have been left behind pointing at a name nothing emits.

Both produce the same state, and the fix is the same either way, so
distinguishing them is not required to act.

## Defects to fix

1. **The required context names a check that does not exist**, so the merge
   gate can never be satisfied. (Primary)
2. **`delete_branch_on_merge` is false**, so merged refresh branches survive.
3. **The refresh opens a new dated branch per run**, so red or unlanded weeks
   accumulate one branch at a time rather than reusing one.

## Next steps

1. Point the required context at checks CI actually produces, or add a single
   aggregating job named `ci` that depends on the others and succeeds only when
   all pass. The aggregating job is the sturdier choice: it survives changes to
   the job list, where an enumerated context list silently re-breaks.
2. Adopt parts B and C of the design spec at
   `/workspaces/pdomain/pdomain-ui/docs/specs/2026-07-16-dep-refresh-auto-land-design.md`:
   one reusable `dep-refresh` branch force-pushed from a fresh master each run,
   a pull request opened only when no open one exists, auto-merge re-armed, and
   `delete_branch_on_merge` enabled.
3. Land step 1 with an administrator bypass. A change that introduces a new
   required check cannot satisfy that check on its own merge, as the spec's
   rollout note records.

Steps 1 and 2 are independent, but doing 2 alone would only tidy the branches.
Refreshes still would not land.

## What is NOT broken

- The dep-refresh workflow runs on schedule and produces correct updates. Its
  last five runs all succeeded.
- Every individual CI job passes and fails correctly. The jobs are fine; the
  gate names the wrong thing.
- Auto-merge is already armed by the workflow, so no change is needed there.
- This is not specific to dependency updates. It blocks every pull request in
  the repository.

## Resolution

*Open.* When fixed: set frontmatter and Agent Index `Status: retired`, add the
resolving commit link here, and route the retirement through `doc-retirer`,
which deletes the report.
