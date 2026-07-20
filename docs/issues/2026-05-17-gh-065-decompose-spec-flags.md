---
Status: active
Owner: CT
Created: 2026-05-17
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Verify the external decompose-spec flag implementation

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Low — a reported workflow change lacks verifiable implementation evidence
- **Affected version:** External workflow session on 2026-05-17
- **Read when:** deciding whether closed GitHub issue #65 can be deleted or verifying decompose-spec flag behavior.
- **Search terms:** decompose-spec, sync default, one-shot, backwards compatibility, superpowers-gh-integration.
- **Relates to:** [GitHub issues migration ledger](../context/github-issues-migration-ledger.md)

## Summary

Closed GitHub issue #65 reports that an external workflow session completed a
decompose-spec flag change. This repository contains no matching implementation
artifact or independent proof. The record remains active until the owner
verifies the external outcome.

The requested behavior made `--sync` the default and retained `--one-shot` for
backward compatibility. The issue body pointed to a historical cross-cut plan.
It did not specify local implementation files.

## Impact

- Deleting the raw source now would leave only an unverified completion claim.
- Treating the proposal as current could misstate the supported decompose-spec
  command interface.
- The uncertainty affects workspace tooling, not the `pdomain_book_tools` Python package.

## Environment / versions

```text
Source: ConcaveTrillion/pdomain-book-tools#65
Created: 2026-05-17
Closed: 2026-05-17
Historical session: 2026-05-17 (superpowers-gh-integration)
Historical plan: docs/superpowers/plans/2026-05-17-gh-workflow-plan-b-skills.md#slug
Parent tracking issue: #56
```

## Evidence

### The source proposes a cross-cut flag change

The issue title requests `--sync` as the default and `--one-shot` for backward
compatibility. Its body says `Approach: (see plan)`, points to the historical
Plan B `#slug` anchor, and says `Tracks: #56`.

### The sole comment reports completion

The only comment says `Work completed in session 2026-05-17
(superpowers-gh-integration).` It does not cite a repository, commit, changed
file, test, or command output.

### The local checkout cannot verify the implementation

This repository contains no corresponding decompose-spec implementation
artifact. Unlike neighboring migrated issues, #65 has no restoration or
meta-repository migration comment. The completion statement is therefore
historical evidence of a reported external outcome, not independent proof.

The immutable raw export at
`migration/github-issues/raw/issue-65.json` preserves the full issue body,
comment, metadata, and event history. Its SHA-256 digest is
`a62915785c13f7e935d3fa8dbad7b79b0f560383add151be93b113f1a4ab4fb4`.

## Root-cause hypotheses

1. **The change shipped in external workspace tooling.** The contemporaneous
   completion comment supports this possibility, but a commit and tests are
   still needed.
2. **The session completed planning or partial work only.** The comment gives no
   artifact-level detail to distinguish this from full implementation.

## Defects to fix

1. **Unverified external implementation.** Identify the owning repository,
   resolving commit, and tests for both flag behaviors. (Primary)
2. **Unknown current interface.** Confirm whether `--sync` remains the default
   and `--one-shot` remains supported.

## Next steps

1. Ask the owner to identify the external implementation and its current governed destination.
2. Verify the default `--sync` behavior and backward-compatible `--one-shot` behavior from code and tests.
3. If verified, cite the evidence and retire this record through `doc-retirer`.
4. If the proposal never shipped or was superseded, record that disposition before retirement.
5. Keep raw issue #65 until one of those outcomes is verified.

## What is NOT broken (to scope the decision)

- This record does not show a defect in the `pdomain_book_tools` Python package.
- The absence of local evidence does not prove that the external change failed to ship.
- The completion comment does not independently establish the current command interface.

## Resolution

_Open._ Owner decision required: verify, supersede, or reject the reported
external implementation. The governed file and raw export retain this work
after its GitHub source is deleted.
