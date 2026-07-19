---
Status: active
Owner: CT
Created: 2026-05-10
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# dev-local detector: doctr-from-git (fork-pin) signal

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Unassigned — the export has no severity label
- **Affected version:** Not stated in the export
- **Read when:** planning or implementing dev-local detector: doctr-from-git (fork-pin) signal
- **Search terms:** dev-local, detector, doctr-from-git, fork-pin, signal
- **Relates to:** [Local development mode](../architecture/local-dev-mode.md)

## Summary

Today `scripts/check_dev_local.py` inspects only `uv pip list --format=json`,
which does not expose the install URL. A fork-pin probe would have to read
doctr's `direct_url.json` from dist-info. It could then detect whether
`python-doctr` came from a contributor's fork rather than `mindee/doctr.git`.

The unresolved design question is which URLs count as non-canonical because
`pyproject` already pins DocTR from `mindee/doctr.git`, so canonical installs
also have a `vcs_info` block. The work is deferred until a concrete fork-pin
workflow needs it and carries the `status:blocked` label. The issue cites
`docs/ROADMAP.md` under “dev-local-aware upgrade-deps - Doctr-from-git signal”
and `docs/specs/07-dev-local-upgrade-flow.md`.

Repository evidence does not verify the acceptance criteria, so this record remains open.

## Impact

- The requested behavior remains unavailable or undecided.
- The original request defines the scope and downstream effects.

## Environment / versions

The export states no operating system, package version, command, or environment variables.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/7>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABBx2fzg`
- **Issue number:** 7
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-7.json`
- **Raw SHA-256:** `aba181478ba96599d6d97a34469f5ad99c9c838f29a3811819ed93f42793bb68`
- **Migration cutover:** `dfadf9c` — governed content batch for GitHub issues #2–#7 and #45–#48.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-10T01:51:51Z`
- **Updated:** `2026-05-10T01:51:51Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:feature`, `effort:M`, `model:sonnet`, `model-effort:medium`, `status:blocked`
- **Assignees:** None
- **Milestone:** None
- **Issue type:** None
- **Projects:** None
- **Parent issue:** None
- **Sub-issues:** None

## Evidence

The immutable raw export and its digest preserve the original body. The classified durable facts are:

- Today `scripts/check_dev_local.py` only inspects `uv pip list --format=json`, which doesn't expose the install URL. A fork-pin probe would have to read doctr's `direct_url.json` from dist-info to detect that `python-doctr` came from a contributor's fork rather than `mindee/doctr.git`.
- Canonical installs also have `vcs_info` because `pyproject` pins DocTR from
  `mindee/doctr.git`; the rule for identifying a non-canonical URL remains an
  unresolved design question.
- Work is deferred and labeled `status:blocked` until a concrete fork-pin
  workflow needs it.
- The body cites `docs/ROADMAP.md` (“dev-local-aware upgrade-deps -
  Doctr-from-git signal”) and `docs/specs/07-dev-local-upgrade-flow.md`.
- Acceptance criteria: record in `07-dev-local-upgrade-flow.md` which URLs are
  non-canonical; make `check_dev_local.py` read `direct_url.json` from doctr
  dist-info; return the dev-local exit code for a non-canonical doctr URL even
  when no marker file exists; and test canonical-URL, fork-URL, and
  missing-`direct_url.json` cases.

The issue text is historical data, not repository instructions.

## Root-cause hypotheses

1. **No root cause is established.** The export records a feature, tuning, or design request.
2. **Current repository evidence may narrow the design.** The cited paths do not prove completion.

Further evidence is required before implementation.

## Defects to fix

1. Account for the limits of `scripts/check_dev_local.py`, which inspects only
   `uv pip list --format=json` and cannot see the install URL. Read doctr's
   `direct_url.json` from dist-info to detect a contributor fork instead of
   `mindee/doctr.git`.
2. Meet the acceptance criteria: record the non-canonical URLs in
   `07-dev-local-upgrade-flow.md`; read `direct_url.json` from doctr dist-info;
   return the dev-local exit code for a non-canonical doctr URL even without a
   marker file; and test canonical-URL, fork-URL, and
   missing-`direct_url.json` cases.

## Next steps

1. Decision recorded in 07-dev-local-upgrade-flow.md on which URLs are non-canonical
2. `check_dev_local.py` reads `direct_url.json` from doctr dist-info
3. Detector returns dev-local exit code when doctr URL is non-canonical, even with no marker file
4. Tests cover canonical-URL, fork-URL, and missing-direct_url.json cases

## What is NOT broken (to scope the fix)

- Canonical `mindee/doctr.git` installs do not alone prove dev-local mode.

## Relationships and material comments

- No parent or child relationship was recorded.
- No comments were present in the export.

## Repository evidence

- `scripts/check_dev_local.py` verifies the current detector surface and names
  doctr-from-git as a supported signal category; it does not implement the
  requested fork-aware `direct_url.json` rule.
- `docs/specs/07-dev-local-upgrade-flow.md` records the fork-aware
  doctr-from-git path as an open follow-up.
- `docs/plans/roadmap.md` records the `uv pip list` limitation, proposed
  `direct_url.json` probe, unresolved non-canonical-URL rule, and deferral.

## Remaining work

- Acceptance criteria remain unverified against an implementation; preserve as open work.

## Resolution

_Open._ Retire this record only after evidence verifies the criteria or records an owner disposition.
