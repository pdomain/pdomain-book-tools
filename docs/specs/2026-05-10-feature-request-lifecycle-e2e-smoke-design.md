# Feature-request lifecycle chain — end-to-end validation (smoke)

> **Status**: Draft
> **Last updated**: 2026-05-10
> **Spec-Issue**: ConcaveTrillion/pd-book-tools#19

## TL;DR

Two small unit-test gaps were discovered during the live smoke run of the triage → spec-from-issue → decompose-spec chain. This spec captures them as concrete children so the chain can produce decomposable work and ship-issue can claim one.

## Context

The feature-request lifecycle (workspace Plan 1) landed skills and helpers for `/triage`, `/spec-from-issue`, and `/decompose-spec`. The smoke run (parent issue #18) exercised the chain live and found two unit-test gaps:

1. `triage-fork.py` posts a pointer comment on the parent issue, but no unit test asserts this.
2. `spec-from-issue-finalize.py` with `--force` is supposed to replace a placeholder `Spec:` line (inserted by `triage-fork.py`) with the real path, but this code path had no test coverage.

Both gaps are in existing workspace scripts, not in pd-book-tools source. The tests live in `/workspaces/ocr-container/tests/scripts/`.

## Constraints

- Tests must use the existing `fake_gh` shim pattern (`tests/fakes/fake_gh.py`) and `importlib`-based loader.
- No changes to `triage-fork.py` or `spec-from-issue-finalize.py` source unless a bug is found.
- This spec is intentionally small (2 children). Do not expand scope.

## Decision

### Child A: test triage-fork.py pointer comment on parent

`tests/scripts/test_triage_fork.py` has tests for the child-issue creation path but no assertion that a `gh issue comment` call is made on the parent. Add a test that verifies the pointer comment (`"→ Filed child issue #<N>"` or similar) is posted on the parent when a child is created successfully.

Acceptance:

- New test in `tests/scripts/test_triage_fork.py`.
- `fake_gh` captures the `issue comment` call and asserts the parent number and a substring of the message.
- `pytest tests/scripts/test_triage_fork.py` passes.

### Child B: test spec-from-issue-finalize --force replaces placeholder Spec: line

`tests/scripts/test_spec_from_issue_finalize.py` covers the normal append path and the skip-if-present path, but not the `--force` replace-placeholder path. The issue body from `triage-fork.py` contains `Spec: (to be filled by /spec-from-issue)` — a line that matches `_SPEC_LINE` and causes a skip without `--force`. Add a test that verifies `--force` replaces it with the real path rather than skipping.

Acceptance:

- New test in `tests/scripts/test_spec_from_issue_finalize.py`.
- Test sets up a body with `Spec: (to be filled by /spec-from-issue)` and calls `plan_finalize` with `force=True`.
- Asserts `kind == "edit"` and that the resulting `new_body` contains the real spec path (not the placeholder).
- `pytest tests/scripts/test_spec_from_issue_finalize.py` passes.

## Contract / Acceptance

- [ ] `/triage` filed #19 from #18 with `triage:approved` + `triage:needs-spec` and a pointer comment (verified live)
- [ ] `/spec-from-issue` wrote this file and wired it to #19 via a draft PR
- [ ] `/decompose-spec` created milestone `spec: feature-request-lifecycle-e2e-smoke (#19)` with both children attached
- [ ] Child A and Child B both pass their new tests (`pytest tests/scripts/` green)
- [ ] ship-issue claims the armed child and opens a PR

## Trade-offs considered

| Decision | Pro | Con |
|---|---|---|
| Two test-gap children rather than synthetic "hello world" chores | Real coverage improvements; children are genuinely useful even if the smoke spec is later closed | Slightly more work than a trivial chore |
| Keep children in workspace `tests/scripts/` rather than pd-book-tools | The helpers live in the workspace; tests belong with the code | Children filed against pd-book-tools but tests are in workspace — ship-issue must be aware of the cross-repo path |

## Consequences

- After this spec's children ship, `test_triage_fork.py` and `test_spec_from_issue_finalize.py` will have complete coverage of the comment and force-replace paths.
- The placeholder `Spec:` pattern from `triage-fork.py` is documented here; future specs produced by `/triage` will always need `--force` on finalize.

## Open questions

1. Should `triage-fork.py` omit the placeholder `Spec:` line entirely (leaving only a `Spec:` sentinel with no value) so that `spec-from-issue-finalize.py` can append without `--force`? Deferred — change `triage-fork.py` only if the placeholder causes further friction.

## References

- `/workspaces/ocr-container/scripts/triage-fork.py`
- `/workspaces/ocr-container/scripts/spec-from-issue-finalize.py`
- `/workspaces/ocr-container/tests/scripts/test_triage_fork.py`
- `/workspaces/ocr-container/tests/scripts/test_spec_from_issue_finalize.py`
- Parent feature-request: `ConcaveTrillion/pd-book-tools#18`
- Spec issue: `ConcaveTrillion/pd-book-tools#19`
