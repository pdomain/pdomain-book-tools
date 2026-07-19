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

## Twenty completed issues have durable or disposable destinations

This ledger reconciles closed GitHub issues #8, #9, #10, #11, #12, #13,
as well as #14, #18, #19, #21, and #22 through #31. Each issue appears exactly
once. The details below map every durable body and comment fact to current code,
tests, documentation, or an explicit disposable category.

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
| [#22](https://github.com/pdomain/pdomain-book-tools/issues/22) | `214878e7bb0218adb884b49dbec65ec2d4e0e589e20552bba72a63340b564aee` | This ledger; immutable raw export | Disposable decompose-and-ship lifecycle smoke; no current product artifact or requirement | Abandoned smoke child, closed | Deletion pending; merged cutover pending |
| [#23](https://github.com/pdomain/pdomain-book-tools/issues/23) | `e1d55565aa7301ec77e81b9ee4884494af6807d92d4a885410fa21a9871dbd67` | This ledger; `pyproject.toml` | Python remains bounded below 3.14; the lower bound has since advanced from 3.10 to 3.11 | Completed; commit `448409e`; lower bound later raised | Deletion pending; merged cutover pending |
| [#24](https://github.com/pdomain/pdomain-book-tools/issues/24) | `15f72df435ee2baaa15813bf5719df2c10633101119bd4f7b64d4a715e0a2f92` | This ledger; `docs/architecture/page-serialization.md`; `docs/context/decisions.md` | The Page-model spec was promoted to current serialization architecture and retired | Retired; commit `b88b62c` | Deletion pending; merged cutover pending |
| [#25](https://github.com/pdomain/pdomain-book-tools/issues/25) | `089c5fff11f8a0142ff002d99129310757d0f4b965a05fde0111456b007c5e1e` | This ledger; `docs/architecture/page-serialization.md`; `pdomain_book_tools/ocr/page.py`; `tests/test_page_model_doc.py` | `Page.to_dict()` behavior and its documentation drift gate remain implemented | Completed; architecture promotion in `b88b62c` | Deletion pending; merged cutover pending |
| [#26](https://github.com/pdomain/pdomain-book-tools/issues/26) | `eaad6d141658843270a6ccabf93e384756ce2e76819ad81e45feea3ebd1cf9f8` | This ledger; `docs/architecture/ocr-page-orientation.md`; `docs/context/decisions.md` | The orientation spec was promoted to current architecture and retired | Retired; commit `b88b62c` | Deletion pending; merged cutover pending |
| [#27](https://github.com/pdomain/pdomain-book-tools/issues/27) | `009444c330230e67d4f02ef3fd076efaf7e2e6a18b4c7914c0d4f2754e502929` | This ledger; `docs/architecture/reorganize-page-pipeline.md`; `docs/context/decisions.md` | The reorganize-pipeline spec was promoted to current architecture and retired | Retired; commit `b88b62c` | Deletion pending; merged cutover pending |
| [#28](https://github.com/pdomain/pdomain-book-tools/issues/28) | `8019b835f7022a85a7934e5adee3c6ed4b7fd545d8e50cc70a9fe81bae7d7e77` | This ledger; `docs/architecture/layout-regression-fixture-corpus.md`; `docs/context/decisions.md`; layout and reorganize fixture tests | The fixture-corpus spec was promoted to current architecture and retired | Retired; commit `b88b62c` | Deletion pending; merged cutover pending |
| [#29](https://github.com/pdomain/pdomain-book-tools/issues/29) | `5ad76da7c520fcd2148e8c68f61da3e5020969990296c1d0d7a78a93b7ad6c83` | This ledger; `docs/architecture/glyph-annotations.md`; `docs/context/decisions.md`; `pdomain_book_tools/ocr/glyph_annotations.py`; `tests/ocr/test_glyph_annotations.py` | The glyph-annotation spec was promoted to current architecture and retired | Retired; commit `b88b62c` | Deletion pending; merged cutover pending |
| [#30](https://github.com/pdomain/pdomain-book-tools/issues/30) | `20464714da37f45ba9b5ba1a7043b6a993f15f0f6a98c47aaa0404a18bd5aecb` | This ledger; `docs/architecture/ocr-page-orientation.md`; `pdomain_book_tools/ocr/rotation.py`; `pdomain_book_tools/ocr/document.py`; `tests/ocr/test_rotation.py` | Orientation detection and its `Document` integration remain implemented; current architecture supersedes the cited spec | Completed; architecture promotion in `b88b62c` | Deletion pending; merged cutover pending |
| [#31](https://github.com/pdomain/pdomain-book-tools/issues/31) | `d53cd5d3160317e54a3d6b10643404b643a67160d9a0fb69fe03c2fb783a644a` | This ledger; `docs/architecture/reorganize-page-pipeline.md`; `pdomain_book_tools/ocr/page.py`; `pdomain_book_tools/ocr/reorganize_page_utils.py`; reorganize tests | `Page.reorganize_page` and its pipeline remain implemented; current architecture supersedes the cited spec | Completed; architecture promotion in `b88b62c` | Deletion pending; merged cutover pending |

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

### Issue #22 was an abandoned lifecycle smoke child

Issue #22 pointed back to issue #19 and its temporary lifecycle-smoke spec. It
was a proposed decompose child with no acceptance criteria. Two claim records,
a hook-permission CI bounce, model and effort fields, the pre-claim SHA, and
retry instructions describe temporary automation state. The closing comment
calls it a smoke child rather than real work. No current repository artifact or
product contract comes from this issue.

### Issue #23 implemented the Python 3.14 upper bound

Issue #23 reported that Python 3.14 lacked a pre-built `regex` wheel at the
time, causing a Windows source build to require Microsoft Visual C++ 14.0 or
newer. It requested `requires-python = ">=3.10,<3.14"` as a stopgap and gave
Python 3.13 as the user workaround. Commit `448409e` implemented that bound in
`pyproject.toml`.

The current bound is `>=3.11,<3.14`. Raising the lower bound later superseded
the original Python 3.10 support floor, while the requested 3.14 ceiling
remains. The historical release condition and workaround are not current
installation guidance; `pyproject.toml` owns the supported range. The report
that another installer printed `Done!` after the dependency failure is an
out-of-repository historical symptom, not a contract for this library.

### Issues #24 and #25 became Page serialization architecture

Issue #24 backfilled the parent spec record for the Page model and tracked
child issue #25. Its only comment confirmed that `docs/specs/01-page-model.md`
then existed. Commit `b88b62c` later retired that spec and promoted the durable
serialization contract to `docs/architecture/page-serialization.md` and the
decision record.

Issue #25 required the `Page.to_dict()` JSON reference and its drift gate. The
closing comment marked the work complete and cited the former spec and
`tests/test_page_model_doc.py` as evidence. Current behavior lives in
`pdomain_book_tools/ocr/page.py`, the drift gate remains in the cited test, and
the architecture document now replaces the retired spec. Proposal-stage
boilerplate and duplicate spec pointers are disposable migration scaffolding.

### Issues #26 through #29 became four architecture records

Issues #26, #27, #28, and #29 were backfilled parent records for four existing
specs. Their closing comments only confirmed that the spec files were present.
Commit `b88b62c` later retired all four after promoting their durable contracts
to the orientation, reorganize-pipeline, layout-fixture, and glyph-annotation
architecture documents.

Issue #26 tracked implementation issue #30, and issue #27 tracked #31. The
issue #28 record pointed to #32, which is outside this batch. Issue #29 pointed
to parent feature request #41, and its first comment recorded that backfilled
chain.

Those tracking links are historical provenance. Current behavior is governed
by the architecture documents, implementation, and tests cited in the table.
Duplicate spec pointers and backfill boilerplate are disposable.

### Issues #30 and #31 remain implemented

Issue #30 closed because page-orientation detection had shipped. The comment
named an old package path, the `auto_rotate=True` default, the former spec, and
the roadmap. Current code uses `pdomain_book_tools/ocr/rotation.py` and
`pdomain_book_tools/ocr/document.py`; tests live in
`tests/ocr/test_rotation.py`. The current orientation architecture documents
the default, chosen-image frame, return values, and audit boundary. It
supersedes the retired spec and roadmap note.

Issue #31 closed because `Page.reorganize_page` and its pipeline had shipped.
Current code lives in `pdomain_book_tools/ocr/page.py` and
`pdomain_book_tools/ocr/reorganize_page_utils.py`. The reorganize architecture
records pipeline order, word preservation, outputs, and current evidence. Its
test references include the grouping, dropped-word reconciliation, diagnostic,
drop-cap, and layout suites. The broad claim that the pipeline had been core
since Phase 2 is historical commentary, not a separate current contract.
Proposal-stage boilerplate and the retired spec pointer are disposable.

## Cutover remains pending

These rows prove local reconciliation only. Deletion readiness requires a
default-branch merge, raw-digest reverification, and passing repository-wide
cutover gates. No retired per-issue documents are needed for these completed
rows.
