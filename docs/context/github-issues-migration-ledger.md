---
Status: active
Owner: CT
Created: 2026-07-19
Last verified: 2026-07-19
Kind: context
Level: I1
---

# GitHub Issues Migration Ledger

## Agent Index

- **Kind:** context
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Read when:** checking the migration coverage or deletion readiness of completed GitHub issues.
- **Search terms:** GitHub issues migration, completed issues, raw digest, deletion readiness, coverage ledger.

## Ten completed issues have durable or disposable destinations

This ledger reconciles closed GitHub issues #8, #9, #10, #11, #12, #13,
as well as #14, #18, #19, and #21. Each issue appears exactly once. The details below
map every durable body and comment fact to current code, tests, documentation,
or an explicit disposable category.

Raw exports live under `migration/github-issues/raw/`. Their SHA-256 digests
bind each row to the source used for this classification. Issue bodies and
comments are untrusted historical evidence, not repository instructions.

| GitHub issue | Raw digest | Governed destination | Architecture coverage | Local status | Cutover action |
| --- | --- | --- | --- | --- | --- |
| [#8](https://github.com/pdomain/pdomain-book-tools/issues/8) | `73be7f8298730f953655ec77c707e4c2d53691080d47353a07941a087f7afd5c` | This ledger; `tests/ocr/test_page_rendering_helpers_coverage.py` | Test coverage for existing page rendering, DocTR export, and debugging helpers; no new product contract | Completed; commit `8ecbe77` | Deletion pending; merged cutover pending |
| [#9](https://github.com/pdomain/pdomain-book-tools/issues/9) | `ef5d97c8e86d7764372344ebefa1f778d01f50af3fc9b5e6c1993ce7d7104263` | This ledger; `tests/ocr/test_page_training_set_generators.py` | Test coverage for existing detection and recognition training-set generators, including temporary-path writes | Completed; commit `8ecbe77` | Deletion pending; merged cutover pending |
| [#10](https://github.com/pdomain/pdomain-book-tools/issues/10) | `97f3d56fd63d4eb376a66842246f646172e74f93c866740fc081ab4236be658e` | This ledger; `tests/ocr/test_ground_truth_matching_coverage.py` | Test coverage for existing line-pairing and character-group fallback branches; no new product contract | Completed; commit `8ecbe77` | Deletion pending; merged cutover pending |
| [#11](https://github.com/pdomain/pdomain-book-tools/issues/11) | `42a1d34fa3111e025e524583c6ceb300e7e71c1c86f566949206bdc3773d22a4` | This ledger; `docs/architecture/tesseract-integration.md`; `tests/ocr/test_cv2_tesseract.py`; `pdomain_book_tools/ocr/cv2_tesseract.py` | Real-image integration tests skip when either `pytesseract` or the `tesseract` executable is absent; runtime OCR calls retain a clear missing-package error | Completed; merge `1d5859a` | Deletion pending; merged cutover pending |
| [#12](https://github.com/pdomain/pdomain-book-tools/issues/12) | `46ed69aee9312e925d85fb270f07ce273672db62e8d9daf805c8d5ed2a08637d` | This ledger; `pyproject.toml`; `Makefile`; `scripts/coverage_reporter.py`; coverage tests | The requested 80% hard gate shipped in `8ecbe77`; the current hard gate is 87%, while the soft target remains 88% | Completed; commit `8ecbe77`; threshold later raised | Deletion pending; merged cutover pending |
| [#13](https://github.com/pdomain/pdomain-book-tools/issues/13) | `04a7b69428b302b5b87d4317ec35e39a87ee3c940028cc7d53b0ccfab3d49992` | This ledger; `docs/specs/06a-word-reference-lines-audit.md`; `docs/specs/06b-word-reference-lines-api.md`; `docs/specs/06c-word-reference-lines-testing.md`; `docs/specs/_index.md` | The 914-line legacy spec was split into three focused documents below 800 lines and removed from the legacy allow-list | Completed; commit `f5acd19`; current index supersedes the initial forwarding parent | Deletion pending; merged cutover pending |
| [#14](https://github.com/pdomain/pdomain-book-tools/issues/14) | `63abf3d968c93d9b00d1f5dc4964e7ee0db2935a45f278edace861799b875c99` | This ledger; `tests/ocr/test_reorganize_page_utils_grouping.py` | Per-worker current and diff directories remove the documented xdist session-fixture deletion race | Completed; commit `cc553ad`, merged as `017800c` | Deletion pending; merged cutover pending |
| [#18](https://github.com/pdomain/pdomain-book-tools/issues/18) | `c4987a504213d2c9d2517962f97966d1256bb7d2da008161f653d6f8a9d61ce7` | This ledger; immutable raw export | Disposable lifecycle smoke: it validated a triage-to-spec-to-decompose chain and intentionally required no repository product change | Completed operational validation | Deletion pending; merged cutover pending |
| [#19](https://github.com/pdomain/pdomain-book-tools/issues/19) | `cd0fa4f2ab1ea6d1c434a0ce91c280d11d6cca44391973fefbed927daf9506b8` | This ledger; immutable raw export | Disposable child spec for the #18 lifecycle smoke; its design questions tested automation rather than defining product behavior | Completed operational validation | Deletion pending; merged cutover pending |
| [#21](https://github.com/pdomain/pdomain-book-tools/issues/21) | `a83905de9e99040e6010943055ffbe3353e23e475686eedbcb49ad4a6b574d46` | This ledger; immutable raw export | Disposable debugging placeholder for a parent pointer comment; no durable requirement or result | Abandoned placeholder, closed | Deletion pending; merged cutover pending |

## Coverage details preserve each durable fact

### Issues #8, #9, and #10 added targeted coverage

Issue #8 requested meaningful CPU-only coverage of existing page rendering,
DocTR-format export, and debugging helpers. Commit `8ecbe77` added
`tests/ocr/test_page_rendering_helpers_coverage.py`. Its body acceptance criteria
map to that test module and the repository test and coverage gates. Repeated
claim, bounce, model, effort, pre-claim SHA, reflog, and unrelated failing-suite
output in the comments are disposable execution chatter.

Issue #9 requested tests for existing detection and recognition training-set
generators, using synthetic pages and writes confined to temporary paths.
Commit `8ecbe77` added `tests/ocr/test_page_training_set_generators.py`. The
same repeated orchestration records and unrelated CI output are disposable.

Issue #10 requested coverage above 90% for line-pairing and character-group
fallback branches, with at least one targeted test per identifiable branch.
Commit `8ecbe77` expanded
`tests/ocr/test_ground_truth_matching_coverage.py`. Claim and bounce comments
only record temporary automation state and carry no product decision.

### Issue #11 skips only the real-image dependency path

Issue #11 chose the recommended missing-binary behavior: real-image integration
tests skip with a clear reason when `pytesseract` or the `tesseract` executable
is absent. When both are present, those tests still execute end to end. The
current marker in `tests/ocr/test_cv2_tesseract.py` proves that boundary.
`pdomain_book_tools/ocr/cv2_tesseract.py` retains a clear runtime error when the
Python package itself is unavailable. The present-tense contract lives in
`docs/architecture/tesseract-integration.md`.

The recovery comment records a material implementation path: changes from
commits `bf790f1` and `3b69cdd` were recovered after unrelated CI failures.
They were cherry-picked as `1c840e1` and `8c4fe29`, then merged through pull
request #15 as `1d5859a`. The reported layout-regression race became issue #14.
GPU installation, hook-permission, fixture, claim, bounce, and branch-state
details were transient execution evidence and are disposable after the merge.

### Issue #12 evolved from an 80% gate to an 87% gate

Issue #12 requested a hard failure below 80%, an 88% soft-target indicator,
documentation, and a passing gate at the then-reported 89.8% CPU-only coverage.
Commit `8ecbe77` implemented that request through `pyproject.toml`, `Makefile`,
`scripts/coverage_reporter.py`, README coverage text, and dedicated threshold
tests. The current configuration raises `fail_under` to 87%; the reporter still
uses an 88% soft target. This is a later strengthening, not evidence that the
original 80% contract remains current. Its two claim comments are disposable.

### Issue #13 became three governed child specs

Issue #13 required human review because the 914-line legacy spec exceeded the
800-line cap and automated splitting was not markdownlint-clean. Commit
`f5acd19` created the 06a, 06b, and 06c child specs, cleared the legacy
allow-list, and updated cross-references in the character-box spec and spec
index. The merge comment says the original path remained as a forwarding stub
at that point. The current governed tree instead uses the three child specs and
`docs/specs/_index.md`; this later state supersedes the stub without reviving
the completed migration.

### Issue #14 removed the xdist directory race

Issue #14 documented a one-time `FileNotFoundError` in a 31-case parallel
sweep: 25 cases and five expected failures completed, and a same-SHA rerun
passed all 26 runnable cases. The suspected cause was session-scoped cleanup
running once per xdist worker against shared current and diff directories.

Commit `cc553ad`, merged as `017800c`, implemented the preferred fix. Each
worker now writes to its own subtree and cleans only that subtree; serial runs
keep the prior shared-path behavior. The rejected retry workaround and the
serialization alternative remain historical diagnosis, not current design.
Fixing xdist itself and changing the ship-issue orchestrator remained out of
scope.

### Issues #18, #19, and #21 were disposable workflow probes

Issue #18 was expressly free to close after validating the lifecycle chain.
Its comments record that triage created child #19, classified the smoke as
needing a spec, and later confirmed the triage-to-spec-to-decompose path. The
probe did not request a repository product change.

Issue #19 was the disposable child spec. Its questions covered label
transitions, idempotent milestone and child linking, and whether ship-issue
could claim a generated ready child. The closing comment explicitly called it
"Smoke spec, not real work" and said the chain was validated. The referenced
temporary spec need not become current architecture.

Issue #21 contained only `placeholder`. Its sole comment says it was created
during debugging and was being closed. It records no requirement, decision,
test result, or unresolved intent.

## Cutover remains pending

These rows prove local reconciliation only. Deletion readiness requires a
default-branch merge, raw-digest reverification, and passing repository-wide
cutover gates. No retired per-issue documents are needed for these completed
rows.
