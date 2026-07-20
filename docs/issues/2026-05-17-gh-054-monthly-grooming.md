---
Status: active
Owner: CT
Created: 2026-05-17
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Decide whether monthly grooming remains part of the workspace workflow

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Low — recurring maintenance may be stale or untracked
- **Affected version:** Workspace workflow documented on 2026-05-17
- **Read when:** deciding whether to run, update, or retire the monthly grooming recurrence from closed GitHub issue #54.
- **Search terms:** monthly grooming, groom all, groom-auto-nightly, grooming report, judgment queue.
- **Relates to:** [GitHub issues migration ledger](../context/github-issues-migration-ledger.md)

## Summary

Closed GitHub issue #54 described a recurring monthly `/groom all` chore. This
repository does not prove that the recurrence still matches the current
workspace workflow. The record remains active until the owner decides whether
to retain, update, or retire it.

The historical procedure separated nightly automation from human judgment. A
nightly job handled deterministic state changes and maintained a Grooming report
issue. The monthly chore drained that report through an interactive skill.

## Impact

- A stale recurrence could direct maintainers to removed scripts, skills, paths, or status conventions.
- Dropping a still-current recurrence could leave judgment-only grooming items unresolved.
- The completed May 2026 run does not prove that a later recurrence was filed or executed.

## Environment / versions

```text
Source: ConcaveTrillion/pdomain-book-tools#54
Created: 2026-05-17
Closed result: 2026-05-17
Historical nightly time: 02:00
Historical script: scripts/groom-auto.py
Historical skill: .claude/skills/groom/SKILL.md
Historical spec: docs/superpowers/specs/2026-05-17-superpowers-gh-workflow-integration-design.md §7
```

## Evidence

### The source defines the old monthly procedure

The issue says `groom-auto-nightly` ran every night at 02:00. It removed
`status:blocked` when all blockers were closed and set the task to
`status:ready`. It marked complete plan documents and moved them to
`plans/archived/` when their milestones were fully closed.

The same job closed spec issues after all child tracking issues closed. It
closed decision issues after their decision documents appeared on disk. It
moved research files to `research/archived/` after a spec or decision referenced
them.

The nightly job also created or updated a Grooming report issue for items that
needed CT judgment. The source identified it as `#grooming-report`. Each month,
the operator checked for that report and ran `/groom all` when it existed. The
operator then chose keep, update, archive, delete, or skip for each item. A
report stating that no items required CT review completed the chore. The
operator then closed the recurrence or marked it `status:done`, with the
expectation that another monthly issue would be filed.

### The sole comment records one completed run

The closing comment says the groom-auto queue was empty on 2026-05-17. It also
says `STATUS.md` was deleted because it was a pre-workflow meta-index and that
strict-linting research was archived. The comment declares that month's chore
complete.

### Current evidence does not establish the recurrence

The repository lacks evidence that the historical recurrence remains current.
The procedure names workspace-owned scripts, skills, and a `docs/superpowers/`
design path. Current guidance routes cross-cut workflow tracking to
`ConcaveTrillion/ocr-container-meta`, but it does not establish that these exact
paths or status transitions remain valid.

The immutable raw export at
`migration/github-issues/raw/issue-54.json` preserves the full issue body,
comment, metadata, and event history. Its SHA-256 digest is
`d3e61adc8792f5589c9b5740e2f748e1e97668ca49338c0bf95ede2f1b70cf69`.

## Root-cause hypotheses

1. **The recurrence moved to the meta repository.** Current repository guidance routes cross-cut workflow tasks there, but this batch has no cited successor record for #54.
2. **The recurrence was replaced by newer docgraph governance.** The old archive paths and status changes may no longer match current lifecycle rules.
3. **The recurrence remains useful but lacks a current pointer.** The judgment queue may still exist under renamed tooling or documentation.

## Defects to fix

1. **Unknown current owner and location.** Identify the active recurrence or confirm that it ended. (Primary)
2. **Unverified commands and paths.** Confirm the current script, skill, report issue, archive policy, and supported status transitions.
3. **Unverified cadence.** Confirm whether monthly review is still required and where each recurrence is tracked.

## Next steps

1. Ask the owner whether monthly judgment-queue grooming remains required.
2. If it remains active, replace the historical procedure with current paths, commands, ownership, and tracking evidence.
3. If another governed record supersedes it, cite that record and retire this issue through `doc-retirer`.
4. If the recurrence ended, record the decision and rationale before retiring this issue.
5. Keep raw issue #54 until one of those outcomes is verified.

## What is NOT broken (to scope the decision)

- This record does not show a defect in the `pdomain_book_tools` Python package.
- The 2026-05-17 grooming run completed with an empty judgment queue.
- The absence of current local evidence does not prove that workspace grooming stopped.
- This migration does not reinstate the historical archive paths or status transitions as current policy.

## Resolution

_Open._ Owner decision required: retain, update, supersede, or retire the monthly
grooming recurrence. The governed file and raw export retain this decision after
its GitHub source is deleted.
