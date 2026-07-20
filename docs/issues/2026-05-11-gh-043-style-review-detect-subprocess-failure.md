---
Status: active
Owner: CT
Created: 2026-05-11
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Verify the external disposition of the style-review subprocess failure

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Low — silent false-clean review result
- **Affected version:** R4 closeout workspace tooling on 2026-05-11
- **Read when:** deciding whether closed GitHub issue #43 can be deleted or investigating silent style-review failures.
- **Search terms:** style-review-detect, claude -p, empty findings, subprocess returncode, ocr-container-meta issue 1.
- **Relates to:** [GitHub issues migration ledger](../context/github-issues-migration-ledger.md)

## Summary

Closed GitHub issue #43 claims this workspace-tooling bug was refiled as
`ConcaveTrillion/ocr-container-meta#1`, but this migration batch did not verify
that external record or a fix. The governed record remains active until the
owner confirms the external issue's disposition.

The historical report says `scripts/style-review-detect.py` treated a failed
`claude -p --bare` subprocess as a clean review. The script passed an empty
response to `_parse_response("")`. That function returned `{"findings": []}` and
hid the failure.

## Impact

- Callers could not distinguish a clean detection run from a detector that did
  not run.
- R4 closeout required manual diff analysis to recover 11 findings for PR #17.
- The failure belongs to workspace tooling; this repository does not contain the named script.

## Environment / versions

```text
Source: ConcaveTrillion/pdomain-book-tools#43
Reported: 2026-05-11
Context: background agent without a usable TTY or Claude authentication
Command: uv run python scripts/style-review-detect.py --pr <N> --repo <repo>
Subprocess: claude -p --bare
Reported review agent: afec1b702bccfb635
```

## Evidence

### 1. The source report records a silent failure

The issue body says the subprocess returned a non-zero status in a background
agent context. The script then parsed an empty string and returned an empty
findings array without diagnostic stderr or a non-zero script exit.

The same report says PR #17's review subprocess returned exit 1 and manual diff
analysis found all 11 findings. This is historical evidence from the immutable
raw export, not a reproduction in this repository.

### 2. The local checkout cannot verify the implementation

`scripts/style-review-detect.py` is absent from this repository. No local code
or test can prove whether the workspace tool now checks
`CompletedProcess.returncode` or propagates authentication failures.

### 3. The closure comment proves only a claimed refile

The sole closing comment says the issue was misfiled and refiled as
`ConcaveTrillion/ocr-container-meta#1`. It provides no fixing commit, test, or
external resolution. The external issue was not verified during this batch.

## Root-cause hypotheses

1. **The historical caller ignored a non-zero subprocess status.** This matches
   the issue's direct account. The external implementation and its tests would
   confirm it.
2. **The external tool has since been replaced or fixed.** The closure comment
   points to another repository. Local evidence cannot distinguish an open
   refile from a completed fix.

## Defects to fix

1. **Unverified external disposition.** Confirm whether `ocr-container-meta#1`
   exists. Then confirm whether code and tests satisfy the original acceptance
   criteria. (Primary)
2. **Potential silent false-clean result.** If still present, make subprocess
   failure produce diagnostic stderr and a non-zero exit.
3. **Missing regression evidence.** Verify a mocked exit-1 test and the existing
   happy path.

## Next steps

1. Ask the owner to verify `ConcaveTrillion/ocr-container-meta#1`. Cite its
   current state, resolving commit, and tests.
2. If the external issue is fixed, retire this record through `doc-retirer`.
   Retain the external evidence in its resolution.
3. If the issue remains open or cannot be found, keep this record active. Do
   not delete raw issue #43.

## What is NOT broken (to scope the fix)

- This record does not show a defect in the `pdomain_book_tools` Python package.
- An empty findings result is not itself wrong when the detector runs successfully.
- The local absence of the workspace script does not prove that the external bug remains open.

## Resolution

_Open._ Owner decision required: verify the state and evidence for
`ConcaveTrillion/ocr-container-meta#1`. The governed file and raw export retain
this work after its GitHub source is deleted.
