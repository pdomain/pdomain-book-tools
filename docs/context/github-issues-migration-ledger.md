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

## Thirty-nine completed issues have durable or disposable destinations

This ledger gives each of 39 completed issues one durable or disposable
destination. It covers closed GitHub issues #8, #9, #10, #11, #12, #13, #14,
issues #18, #19, #21, #22 through #33, #35, #36, #38 through #44, and #51
through #59.

Closed issues #43 and #54 remain active owner decisions. Issue #43 lacks
verified evidence for its external disposition. Issue #54 lacks evidence that
the recurring grooming chore still matches the current workspace workflow. The
details below map every durable body and comment fact to current code, tests,
documentation, an active governed record, or an explicit disposable category.

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
| [#32](https://github.com/pdomain/pdomain-book-tools/issues/32) | `2850570d7533e763a83aadd065d6b5b614391588b1a68a63a2cf57dc2fa5e35a` | This ledger; `docs/architecture/layout-regression-fixture-corpus.md`; layout and reorganize fixture tests | The fixture corpus, per-case artifacts, regeneration tools, and baseline policy remain implemented | Completed; architecture promotion in `b88b62c` | Deletion pending; merged cutover pending |
| [#33](https://github.com/pdomain/pdomain-book-tools/issues/33) | `51d4739b3034db307ea2eab185709ef1d9e1ee8a7a182d4f2f6a43f8811978e2` | This ledger; `docs/architecture/glyph-annotations.md`; issue #41 implementation evidence | Mislabeled duplicate of canonical feature request #41; the glyph contract shipped in `675ad76` | Superseded by #41 | Deletion pending; merged cutover pending |
| [#35](https://github.com/pdomain/pdomain-book-tools/issues/35) | `b3d590b69d90603afa5406e4e1b2ce215b69ebc9baadccebc399a48e8c2766eb` | This ledger; geometry repr implementation and tests | The request became spec #36; `BoundingBox.__repr__` now emits the spec's eval-safe `from_ltrb` form | Completed; commit `b4c5b8c` | Deletion pending; merged cutover pending |
| [#36](https://github.com/pdomain/pdomain-book-tools/issues/36) | `9b9917d8d6d772a2e6f00865e574054d1f189cfe30d5da8fc385b051dbe48b38` | This ledger; geometry repr implementation and tests | The repr contract chose eval-safe `BoundingBox.from_ltrb(...)`, positional `Point(...)`, and no other geometry types | Implemented; commit `b4c5b8c` | Deletion pending; merged cutover pending |
| [#38](https://github.com/pdomain/pdomain-book-tools/issues/38) | `7e3fdcf0cb3906d5cf10cb365bcbb0688e03fb7f0dc365e1c92fde6f33a391a4` | This ledger; `pdomain_book_tools/geometry/bounding_box.py`; repr tests | `BoundingBox.__repr__` uses the corrected `from_ltrb` contract rather than the issue body's invalid four-argument constructor form | Completed; commit `b4c5b8c` | Deletion pending; merged cutover pending |
| [#39](https://github.com/pdomain/pdomain-book-tools/issues/39) | `5424bd1958c4dbf8927f0f284b839e83cc7e869ef48966a680946e1e40fa2346` | This ledger; `pdomain_book_tools/geometry/point.py`; repr tests | `Point.__repr__` returns the requested positional form for integer and fractional coordinates | Completed; commit `b4c5b8c` | Deletion pending; merged cutover pending |
| [#40](https://github.com/pdomain/pdomain-book-tools/issues/40) | `b90696134e506158a1df97265e00bd7a3446df9459a73eaada62b5998377e974` | This ledger; `tests/test_geometry_repr.py`; geometry repr tests | The tests were absorbed into PR #50 after blocker #51 corrected the BoundingBox form | Completed in squash merge `b4c5b8c` | Deletion pending; merged cutover pending |
| [#41](https://github.com/pdomain/pdomain-book-tools/issues/41) | `ee2438437c67de6577ac92d9ef241007770cb6e70ec0a4d9f03fa8c5154bd9b5` | This ledger; `docs/architecture/glyph-annotations.md`; glyph implementation and tests | Glyph facts remain a side channel on `Word` and do not mutate canonical ground-truth text | Completed; merge `675ad76` | Deletion pending; merged cutover pending |
| [#42](https://github.com/pdomain/pdomain-book-tools/issues/42) | `dc421b541e3c7126516360015d77c9f06868e8f4e06c7c31cca8e555d652f007` | This ledger; `Makefile` | `make ci` now runs an unconditional full-repository Ruff format and check gate | Completed; commit `e57a52c` | Deletion pending; merged cutover pending |
| [#43](https://github.com/pdomain/pdomain-book-tools/issues/43) | `021ff1e31a1d5e3b6dd590d507f4e6def1f2ed03d1c2747156bab8ea3368e041` | This ledger; `docs/issues/2026-05-11-gh-043-style-review-detect-subprocess-failure.md` | The local issue only claims a refile to `ocr-container-meta#1`; this batch did not verify that external record or a fix | Needs owner decision; governed record remains active | Do not delete until external disposition is verified |
| [#44](https://github.com/pdomain/pdomain-book-tools/issues/44) | `80abdf9870d18d98ca73ff442cee19bd906faac59271656ca6e81ebfdf93e058` | This ledger; immutable raw export; `ConcaveTrillion/ocr-container-meta#2` | The PR-body metadata bug belongs to cross-cut workspace tooling, not this library; AGENTS.md routes that work to the meta tracker | Superseded by meta-repository tracking | Deletion pending; merged cutover pending |
| [#51](https://github.com/pdomain/pdomain-book-tools/issues/51) | `ddcce13f3f64f8e5c425fa1c8f5e1de698d4d1b541b738b26242cf5205fd758d` | This ledger; `pdomain_book_tools/geometry/bounding_box.py`; `tests/test_geometry_repr.py`; `tests/geometry/test_bounding_box.py` | `BoundingBox.__repr__` emits the eval-safe `BoundingBox.from_ltrb(...)` form and the tests pin its format and round trip | Implemented; commit `2bec8db` | Deletion pending; merged cutover pending |
| [#52](https://github.com/pdomain/pdomain-book-tools/issues/52) | `c886d9b4f39387f9c0df368581d999b092ccc35bfc4f57c8d3bcc605d42e8490` | This ledger; `docs/architecture/ocr-model-and-schema-boundaries.md`; `docs/architecture/page-serialization.md`; review metadata code and tests | The requested top-level `Word.is_validated` and setter were rejected; persisted validation lives at `word.review.validated` to preserve `ReviewMetadata` encapsulation | Abandoned / won't do; superseded by commit `60d0fc8` contract | Deletion pending; merged cutover pending |
| [#53](https://github.com/pdomain/pdomain-book-tools/issues/53) | `c7f409ac8965db8ba397f948df60ed430f7072ea1b016db606d66c28b33cefb8` | This ledger; immutable raw export; existing line and page APIs | The current per-word workflow uses `Line.merge_word_left` / `merge_word_right`; pixel erasure can mutate the Page image and then call `finalize_page_structure` | Abandoned tracking request; no library change needed | Deletion pending; merged cutover pending |
| [#54](https://github.com/pdomain/pdomain-book-tools/issues/54) | `d3e61adc8792f5589c9b5740e2f748e1e97668ca49338c0bf95ede2f1b70cf69` | This ledger; `docs/issues/2026-05-17-gh-054-monthly-grooming.md` | The May 2026 run found an empty queue, deleted `STATUS.md`, and archived strict-linting research; no evidence proves that the named recurring automation remains current | Needs owner decision; governed record remains active | Do not delete until the recurrence is reconciled |
| [#55](https://github.com/pdomain/pdomain-book-tools/issues/55) | `f23e483e6a0ed1481533710cab55b8c28aa6ca1182aebb7c061a3cb06534838f` | This ledger; immutable raw export; meta-repository cross-cut tracking | Pipeline-foundation planning belongs to the workspace-wide workflow system named by AGENTS.md | Superseded by meta-repository tracking; no local implementation claim | Deletion pending; merged cutover pending |
| [#56](https://github.com/pdomain/pdomain-book-tools/issues/56) | `08cd1949b1a73f3d75fad31c09a0eac07791a14aeec0ab732eb0797fb1c0e507` | This ledger; immutable raw export; meta-repository cross-cut tracking | Skill-prompt planning belongs to the workspace-wide workflow system named by AGENTS.md | Superseded by meta-repository tracking; no local implementation claim | Deletion pending; merged cutover pending |
| [#57](https://github.com/pdomain/pdomain-book-tools/issues/57) | `e7e0ab33db019cbe59984ff2a9ee3ea175e147a79b37bb2351e0be139f3235af` | This ledger; immutable raw export; meta-repository cross-cut tracking | Grooming-system planning belongs to the workspace-wide workflow system named by AGENTS.md | Superseded by meta-repository tracking; no local implementation claim | Deletion pending; merged cutover pending |
| [#58](https://github.com/pdomain/pdomain-book-tools/issues/58) | `8ff6df861e3ff25a7a09366b895f1e4f066d4231b80d608a10bc7aeb4d01d84e` | This ledger; immutable raw export; meta-repository cross-cut tracking | `ship-issue-pick.py` is cross-cut workflow tooling; its source issue was migrated to the meta repository | Superseded by meta-repository tracking; no local implementation claim | Deletion pending; merged cutover pending |
| [#59](https://github.com/pdomain/pdomain-book-tools/issues/59) | `ab85ed796c243d0acef8658e584b8d38a873777a9f2b8c405288283ace95fe5b` | This ledger; immutable raw export; meta-repository cross-cut tracking | `decompose-spec-sync.py` is cross-cut workflow tooling; its source issue was migrated to the meta repository | Superseded by meta-repository tracking; no local implementation claim | Deletion pending; merged cutover pending |

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

Issue #26 tracked implementation issue #30, and issue #27 tracked #31. Issue #28
pointed to corpus implementation issue #32, which the dedicated section below
reconciles. Issue #29 pointed to parent feature request #41. Its first comment
recorded that backfilled chain.

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

### Issue #32 remains an implemented fixture corpus

Issue #32 requested the layout-regression corpus described by parent spec #28.
Its closing comment reported 30 cases and 120 files. It also recorded the corpus
structure and three regeneration scripts.

The current corpus has grown to 31 page cases. Its `inputs/` directory contains
31 PNGs, 31 OCR JSON files, 31 layout JSON files, and 27 optional proofread
references, for 120 input files. The current architecture records the exact
artifact shape, tests, baseline policy, scripts, and remaining coverage gaps.
Commit `b88b62c` promoted that contract and retired the source spec. Adding cases
remains maintenance rather than a new deliverable.

### Issues #33 and #41 converge on the shipped glyph contract

Issue #33 was a mislabeled proposal-layer duplicate. Its closing comment names
issue #41 as the canonical feature request for spec #29. Issue #41 was the
retroactive R2 Phase B backfill for the same chain. It was pre-approved because
the spec already existed.

The requested foundation-library behavior stores ligatures, long-s
substitutions, swashes, and related printed-form facts beside canonical
ground-truth text. It does not mutate that text. Merge `675ad76` added the data
model, `Word` integration, and tests. The current architecture and tests preserve
that contract. The raw cross-repository consumer list records historical scope;
it does not prove that those downstream repositories adopted the feature.

### Issues #35, #36, #38, #39, and #40 implemented the repr contract

Issue #35 began as an R2 workflow smoke and a request for readable
`BoundingBox` assertion failures. Triage created spec issue #36 to decide scope,
format, and consistency across geometry primitives. The resulting contract made
`BoundingBox.__repr__` eval-safe through `BoundingBox.from_ltrb(x0, y0, x1, y1)`,
used positional `Point(x, y)`, omitted `is_normalized`, and excluded other
geometry types from this slice. The current implementation and
`tests/test_geometry_repr.py` match that decision. This corrects the invalid
four-scalar primary-constructor form in the bodies of #35 and #38.

Issues #38 and #39 supplied the two implementation slices. Their first bot runs
were skipped because each issue had multiple `status:*` labels. Later claim
comments record model `haiku`, effort `low`, their spec path, pre-claim SHAs
`8ecbe77e414c0c52e4fbe156b9ec0cc7f8271884` and
`764f8c3c009ca36534c5757e6df33837151a7058`, and no separate acceptance text.
Those automation facts explain execution history but do not define product
behavior.

Issue #40 requested the combined repr tests and was blocked by #51 while that
issue corrected the BoundingBox form. Its comments record one multi-status skip,
temporary disarming, re-arming after spec PR #37, three blocked runs, a later
`haiku`/`low` claim at pre-claim SHA
`a2472baf388fe4c2d30f72387dc496870471aa47`, and final zero-delta handling. The
closing comment says PR #50 had already absorbed `tests/test_geometry_repr.py`
during issue #38's TDD slice. Squash merge `b4c5b8c` contains the two repr
implementations and tests, including #51's corrected `from_ltrb` form.

### Issue #42 closed the full-repository lint gap

Issue #42 recorded three bot-generated coverage tests that passed local
`make ci` during R4 B6 stress but failed GitHub CI. Ruff formatting found extra
blank lines. B007 also found an unused `i` in
`test_page_training_set_generators.py`.

The issue attributed the mismatch to incremental or cached pre-commit behavior.
It also noted that the orchestrator lacked a CI retry loop. It named manual
branch commits `76388aa` and `b61a23f`. Those objects are not present in this
repository, so the raw report is their only evidence here.

The durable remediation is commit `e57a52c`. It added the read-only, full-repo
`lint-check` target and wired it into `make ci`, closing the local-versus-GitHub
scope gap. This implemented the outcome common to the issue's three proposed
options without preserving transient skill or `success.sh` instructions as
repository policy. The affected issues #8, #9, and #10 remain mapped to their
coverage tests above. The original severity was Low.

### Issue #43 requires an owner decision outside this repository

Issue #43 reported a silent subprocess failure in the workspace
`scripts/style-review-detect.py`. When `claude -p --bare` lacked a TTY or
authentication, the subprocess could return exit 1. The caller then parsed an
empty response as `{"findings": []}`.

The R4 closeout report said PR #17 review agent `afec1b702bccfb635` required
manual analysis to recover 11 findings. The requested outcome was a non-zero
exit with diagnostic stderr, a mocked failure regression test, and unchanged
happy-path tests.

This repository does not contain that script or evidence of the fix. The only
closure comment says the workspace-tooling bug was refiled as
`ConcaveTrillion/ocr-container-meta#1`. This batch did not verify the external
issue or its resolution. The active governed issue record preserves the full
provenance and asks the owner to confirm the external disposition before raw
deletion.

### Issues #44 and #55 through #59 moved to cross-cut tracking

Issue #44 reported that the ship-issue bot added an unrelated `Closes #22`
section to pull request #17 while shipping issues #8, #9, #10, and #12. The
already-closed target made GitHub's reprocessing a no-op, but the metadata still
proved that the bot selected the wrong issue. PR #17's R4 closeout static review
recorded this as finding J-4. The
source says `gh pr view 17 -R ConcaveTrillion/pd-book-tools --json body --jq
.body` showed the orphan section before R4 cleanup on 2026-05-11. It suspected
stale `ISSUE_JSON`, an environment variable, or `.ship-issue-tmp/` state from an
aborted cycle. It proposed validating in `scripts/ship-issue-success.sh` that
the issue belongs to the current repository and remains open before appending
PR metadata. It also requested regression tests for closed and cross-repository
issues, diagnostic stderr, and an orchestrator bounce. The closing comment
classifies the bug as misfiled workspace tooling and points to
`ConcaveTrillion/ocr-container-meta#2`. AGENTS.md now confirms that cross-cut
workflow work belongs in that repository, so this local record is superseded.

Issues #55, #56, and #57 were parent records for three parts of a shared GitHub
workflow design: pipeline foundations, skill-prompt updates, and automated
grooming. Each cited
`docs/superpowers/specs/2026-05-17-superpowers-gh-workflow-integration-design.md`.
They respectively cited plans
`2026-05-17-gh-workflow-plan-a-pipeline.md`,
`2026-05-17-gh-workflow-plan-b-skills.md`, and
`2026-05-17-gh-workflow-plan-c-grooming.md` under the historical
`docs/superpowers/plans/` path. Issue #55 named the eligibility picker and
idempotent plan-to-GitHub sync. Issue #56 named prompt changes for triage,
ship-issue, decompose-spec, spec-from-issue, and groom. Issue #57 named
`groom-auto.py`, its deterministic nightly behavior, and the coding-bot
workflow. Their closure comments say all children were closed. The paths and
closure statements are superseded cross-cut provenance, not local
implementation evidence.

Issues #58 and #59 described two Plan A tasks. Issue #58 specified eligibility
and closing-keyword behavior for `ship-issue-pick.py` under the historical
Plan A `#ship-issue-pick` anchor. Its proposed `is_eligible` fast-path checked
labels, parsed `Blocked-by:` lines, optionally queried blockers through a `gh`
seam, and short-circuited on `virtually_closed`. Its proposed closing-keyword
parser used one regex over GitHub's documented keyword set. Issue #59 specified
seven FakeGh-based tests under Plan A's `#sync-tests` anchor: create a new slug,
skip a matching slug, update a changed body, close a removed task, reopen a
re-added task, write `synced:` and `milestone:` frontmatter, and resolve blocker
slugs to `Blocked by: #N`. Their comments first claimed completion in session
`2026-05-17 (superpowers-gh-integration)` and restoration from a plan update.
Issue #58 also required a real `argparse` help section. Issue #59 proposed
copying the FakeGh pattern from `test_decompose_spec_apply.py`. Those
implementation suggestions are superseded cross-cut plan detail, not evidence
of local delivery.
They then explicitly migrated the cross-cut plans to
`ConcaveTrillion/ocr-container-meta`. This ledger preserves that sequence and
classifies the historical plan pointers as disposable without claiming that
either tool shipped in this repository.

### Issue #51 fixed the BoundingBox repr contract

Issue #51 corrected an earlier implementation that emitted the invalid
four-scalar primary-constructor form. Commit `2bec8db` changed
`BoundingBox.__repr__` to emit `BoundingBox.from_ltrb(x0, y0, x1, y1)` and
updated tests. `tests/test_geometry_repr.py` pins both the exact format and
`eval(repr(bb)) == bb` for a box without `is_normalized`.

The source says spec #36 landed through pull request #37 as commit `c3b0e8f7`.
It says issue #38's earlier implementation was commit `764f8c3` on
`wip/ship-issue` in pull request #50. Those references explain why the fix was
needed; commit `2bec8db` and current tests prove the corrected local outcome.

The issue's arm and claim comments record model `haiku`, effort `low`, spec
`docs/specs/08-geometry-repr.md`, and pre-claim SHA
`40ab3e9157b14d3e991b690f1c14442633342fae`. Those facts explain execution
history. The implementation, tests, and commit provide the durable evidence.

### Issue #52 was rejected in favor of ReviewMetadata encapsulation

Issue #52 requested a top-level `Word.is_validated` field and a
`Word.set_validated(bool)` setter. It aimed to persist labeler validation through
`to_dict()` and `from_dict()` instead of a parallel SPA map that lost state on
envelope reload.

The requested field defaulted to `False`, and the setter would return `True`
only when the value changed. Those proposed additive semantics were rejected
with the top-level API; they are not promises of the replacement contract.

The source located the legacy flag at
`pd_ocr_labeler/models/word_match_model.py:34` and the SPA flag at
`pd_ocr_labeler_spa/core/models.py:174`. It cited
`pd-ocr-labeler-spa/specs/23-page-payload-backend.md` section 9 and SPA issue
SPA issue `#315`. Its temporary `PageState.validated_words` map keyed entries by
`(line_index, word_index)`. Those external paths and the workaround describe
the rejected consumer design; they do not define this library's current API.

The closing comment rejects that API because it would expose a nested review
field directly on `Word`. Commit `60d0fc8` established the replacement
`ReviewMetadata.validated` contract. Current `Word`, `Block`, and `Page`
serialization persists optional review metadata, and current architecture
documents that boundary. Consumers use `word.review.validated`; the requested
top-level field and setter remain intentionally absent.

### Issue #53 closed after its existing-API workarounds were accepted

Issue #53 tracked possible collective wrappers rather than requesting an
immediate feature. The current SPA endpoint already maps naturally to
`Line.merge_word_left` and `Line.merge_word_right`. Its pixel-erasure workaround
mutates `page.cv2_numpy_page_image` and calls `page.finalize_page_structure()`,
matching the legacy labeler's operation shape.

The source cited the per-line methods at historical `pd_book_tools/ocr/block.py`
lines 737, 785, and 789. It cited the legacy inline erasure at
`pd_ocr_labeler/state/page_state.py:1802`, which filled the selected rectangle
and called `_finalize_bbox_edit(page)`. It also pointed to SPA issues #315 and
SPA issue `#316` and the page-payload spec's section 9. These line numbers and external
pointers are historical consumer provenance, not current local contracts.

The closing comment confirms both workarounds and says to reopen only if a
future SPA milestone adds a collective endpoint. No unresolved local product
contract remains, and this migration does not claim that `Page.merge_words` or
`Page.erase_pixels` was implemented.

### Issue #54 needs a current owner decision on monthly grooming

Issue #54 described a monthly `/groom all` chore layered on a nightly
`groom-auto-nightly` job. Its only comment records the 2026-05-17 result: the
queue was empty, `STATUS.md` was deleted as a pre-workflow meta-index, and
strict-linting research was archived.

The nightly workflow was also expected to create or update a Grooming report
issue identified in the source as `#grooming-report`. The active governed issue
record preserves that identifier with the remaining historical procedure.

The source names old workspace paths and promises that a new recurrence will be
filed, but local evidence does not verify either current behavior. The active
governed issue record preserves the full procedure and asks the owner whether
to retain, update, or retire the recurrence before deleting the raw export.

## Cutover remains pending

These rows prove local reconciliation only. Deletion readiness requires a
default-branch merge, raw-digest reverification, and passing repository-wide
cutover gates. No retired per-issue documents are needed for these completed
rows.
