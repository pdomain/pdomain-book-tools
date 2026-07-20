---
Status: active
Owner: CT
Created: 2026-07-19
Last verified: 2026-07-20
Kind: context
Level: I1
---

# GitHub Issues Migration Ledger

## Agent Index

- **Kind:** context
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-20
- **Read when:** checking the migration coverage or deletion readiness of completed GitHub issues.
- **Search terms:** GitHub issues migration, completed issues, raw digest, deletion readiness, coverage ledger.

## One hundred eighty-one completed issues have durable or disposable destinations

This ledger assigns one durable or disposable destination to each of 181
completed issues. It covers closed GitHub issues #8, #9, #10, #11, #12, #13, #14,
and #18, #19, #21, #22 through #33, #35, #36, and #38 through #44. It also
covers #51 through #160, #162 through #190, #192 through #200, #205, and #206.
Open issues with governed records are outside this completed-issue ledger. They
include #161 and #191.

Closed issues #43, #54, #65, #77, and #94 through #98 remain active owner
decisions. The earlier records explain #43, #54, and #65. Issues #77 and #94
through #98 now have separate governed records because each external agent or
routing artifact needs its own evidence and retirement decision. The details
below map every durable body and comment fact to current code, tests,
documentation, an active governed record, or an explicit disposable category.

Raw exports live under `migration/github-issues/raw/`. Their SHA-256 digests
bind each row to the source used for this classification. Issue bodies and
comments are untrusted historical evidence, not repository instructions.

| GitHub issue | Raw digest | Governed destination | Architecture coverage | Local status | Cutover action |
| --- | --- | --- | --- | --- | --- |
| [#8](https://github.com/pdomain/pdomain-book-tools/issues/8) | `73be7f8298730f953655ec77c707e4c2d53691080d47353a07941a087f7afd5c` | This ledger; `tests/ocr/test_page_rendering_helpers_coverage.py` | Test coverage for existing page rendering, DocTR export, and debugging helpers; no new product contract | Completed; commit `8ecbe77` | Deleted and verified; see deletion journal |
| [#9](https://github.com/pdomain/pdomain-book-tools/issues/9) | `ef5d97c8e86d7764372344ebefa1f778d01f50af3fc9b5e6c1993ce7d7104263` | This ledger; `tests/ocr/test_page_training_set_generators.py` | Test coverage for existing detection and recognition training-set generators, including temporary-path writes | Completed; commit `8ecbe77` | Deleted and verified; see deletion journal |
| [#10](https://github.com/pdomain/pdomain-book-tools/issues/10) | `97f3d56fd63d4eb376a66842246f646172e74f93c866740fc081ab4236be658e` | This ledger; `tests/ocr/test_ground_truth_matching_coverage.py` | Test coverage for existing line-pairing and character-group fallback branches; no new product contract | Completed; commit `8ecbe77` | Deleted and verified; see deletion journal |
| [#11](https://github.com/pdomain/pdomain-book-tools/issues/11) | `42a1d34fa3111e025e524583c6ceb300e7e71c1c86f566949206bdc3773d22a4` | This ledger; `docs/architecture/tesseract-integration.md`; `tests/ocr/test_cv2_tesseract.py`; `pdomain_book_tools/ocr/cv2_tesseract.py` | Real-image integration tests skip when either `pytesseract` or the `tesseract` executable is absent; runtime OCR calls retain a clear missing-package error | Completed; merge `1d5859a` | Deleted and verified; see deletion journal |
| [#12](https://github.com/pdomain/pdomain-book-tools/issues/12) | `46ed69aee9312e925d85fb270f07ce273672db62e8d9daf805c8d5ed2a08637d` | This ledger; `pyproject.toml`; `Makefile`; `scripts/coverage_reporter.py`; coverage tests | The requested 80% hard gate shipped in `8ecbe77`; the current hard gate is 87%, while the soft target remains 88% | Completed; commit `8ecbe77`; threshold later raised | Deleted and verified; see deletion journal |
| [#13](https://github.com/pdomain/pdomain-book-tools/issues/13) | `04a7b69428b302b5b87d4317ec35e39a87ee3c940028cc7d53b0ccfab3d49992` | This ledger; `docs/specs/06a-word-reference-lines-audit.md`; `docs/specs/06b-word-reference-lines-api.md`; `docs/specs/06c-word-reference-lines-testing.md`; `docs/specs/_index.md` | The 914-line legacy spec was split into three focused documents below 800 lines and removed from the legacy allow-list | Completed; commit `f5acd19`; current index supersedes the initial forwarding parent | Deleted and verified; see deletion journal |
| [#14](https://github.com/pdomain/pdomain-book-tools/issues/14) | `63abf3d968c93d9b00d1f5dc4964e7ee0db2935a45f278edace861799b875c99` | This ledger; `tests/ocr/test_reorganize_page_utils_grouping.py` | Per-worker current and diff directories remove the documented xdist session-fixture deletion race | Completed; commit `cc553ad`, merged as `017800c` | Deleted and verified; see deletion journal |
| [#18](https://github.com/pdomain/pdomain-book-tools/issues/18) | `c4987a504213d2c9d2517962f97966d1256bb7d2da008161f653d6f8a9d61ce7` | This ledger; immutable raw export | Disposable lifecycle smoke: it validated a triage-to-spec-to-decompose chain and intentionally required no repository product change | Completed operational validation | Deleted and verified; see deletion journal |
| [#19](https://github.com/pdomain/pdomain-book-tools/issues/19) | `cd0fa4f2ab1ea6d1c434a0ce91c280d11d6cca44391973fefbed927daf9506b8` | This ledger; immutable raw export | Disposable child spec for the #18 lifecycle smoke; its design questions tested automation rather than defining product behavior | Completed operational validation | Deleted and verified; see deletion journal |
| [#21](https://github.com/pdomain/pdomain-book-tools/issues/21) | `a83905de9e99040e6010943055ffbe3353e23e475686eedbcb49ad4a6b574d46` | This ledger; immutable raw export | Disposable debugging placeholder for a parent pointer comment; no durable requirement or result | Abandoned placeholder, closed | Deleted and verified; see deletion journal |
| [#22](https://github.com/pdomain/pdomain-book-tools/issues/22) | `214878e7bb0218adb884b49dbec65ec2d4e0e589e20552bba72a63340b564aee` | This ledger; immutable raw export | Disposable decompose-and-ship lifecycle smoke; no current product artifact or requirement | Abandoned smoke child, closed | Deleted and verified; see deletion journal |
| [#23](https://github.com/pdomain/pdomain-book-tools/issues/23) | `e1d55565aa7301ec77e81b9ee4884494af6807d92d4a885410fa21a9871dbd67` | This ledger; `pyproject.toml` | Python remains bounded below 3.14; the lower bound has since advanced from 3.10 to 3.11 | Completed; commit `448409e`; lower bound later raised | Deleted and verified; see deletion journal |
| [#24](https://github.com/pdomain/pdomain-book-tools/issues/24) | `15f72df435ee2baaa15813bf5719df2c10633101119bd4f7b64d4a715e0a2f92` | This ledger; `docs/architecture/page-serialization.md`; `docs/context/decisions.md` | The Page-model spec was promoted to current serialization architecture and retired | Retired; commit `b88b62c` | Deleted and verified; see deletion journal |
| [#25](https://github.com/pdomain/pdomain-book-tools/issues/25) | `089c5fff11f8a0142ff002d99129310757d0f4b965a05fde0111456b007c5e1e` | This ledger; `docs/architecture/page-serialization.md`; `pdomain_book_tools/ocr/page.py`; `tests/test_page_model_doc.py` | `Page.to_dict()` behavior and its documentation drift gate remain implemented | Completed; architecture promotion in `b88b62c` | Deleted and verified; see deletion journal |
| [#26](https://github.com/pdomain/pdomain-book-tools/issues/26) | `eaad6d141658843270a6ccabf93e384756ce2e76819ad81e45feea3ebd1cf9f8` | This ledger; `docs/architecture/ocr-page-orientation.md`; `docs/context/decisions.md` | The orientation spec was promoted to current architecture and retired | Retired; commit `b88b62c` | Deleted and verified; see deletion journal |
| [#27](https://github.com/pdomain/pdomain-book-tools/issues/27) | `009444c330230e67d4f02ef3fd076efaf7e2e6a18b4c7914c0d4f2754e502929` | This ledger; `docs/architecture/reorganize-page-pipeline.md`; `docs/context/decisions.md` | The reorganize-pipeline spec was promoted to current architecture and retired | Retired; commit `b88b62c` | Deleted and verified; see deletion journal |
| [#28](https://github.com/pdomain/pdomain-book-tools/issues/28) | `8019b835f7022a85a7934e5adee3c6ed4b7fd545d8e50cc70a9fe81bae7d7e77` | This ledger; `docs/architecture/layout-regression-fixture-corpus.md`; `docs/context/decisions.md`; layout and reorganize fixture tests | The fixture-corpus spec was promoted to current architecture and retired | Retired; commit `b88b62c` | Deleted and verified; see deletion journal |
| [#29](https://github.com/pdomain/pdomain-book-tools/issues/29) | `5ad76da7c520fcd2148e8c68f61da3e5020969990296c1d0d7a78a93b7ad6c83` | This ledger; `docs/architecture/glyph-annotations.md`; `docs/context/decisions.md`; `pdomain_book_tools/ocr/glyph_annotations.py`; `tests/ocr/test_glyph_annotations.py` | The glyph-annotation spec was promoted to current architecture and retired | Retired; commit `b88b62c` | Deleted and verified; see deletion journal |
| [#30](https://github.com/pdomain/pdomain-book-tools/issues/30) | `20464714da37f45ba9b5ba1a7043b6a993f15f0f6a98c47aaa0404a18bd5aecb` | This ledger; `docs/architecture/ocr-page-orientation.md`; `pdomain_book_tools/ocr/rotation.py`; `pdomain_book_tools/ocr/document.py`; `tests/ocr/test_rotation.py` | Orientation detection and its `Document` integration remain implemented; current architecture supersedes the cited spec | Completed; architecture promotion in `b88b62c` | Deleted and verified; see deletion journal |
| [#31](https://github.com/pdomain/pdomain-book-tools/issues/31) | `d53cd5d3160317e54a3d6b10643404b643a67160d9a0fb69fe03c2fb783a644a` | This ledger; `docs/architecture/reorganize-page-pipeline.md`; `pdomain_book_tools/ocr/page.py`; `pdomain_book_tools/ocr/reorganize_page_utils.py`; reorganize tests | `Page.reorganize_page` and its pipeline remain implemented; current architecture supersedes the cited spec | Completed; architecture promotion in `b88b62c` | Deleted and verified; see deletion journal |
| [#32](https://github.com/pdomain/pdomain-book-tools/issues/32) | `2850570d7533e763a83aadd065d6b5b614391588b1a68a63a2cf57dc2fa5e35a` | This ledger; `docs/architecture/layout-regression-fixture-corpus.md`; layout and reorganize fixture tests | The fixture corpus, per-case artifacts, regeneration tools, and baseline policy remain implemented | Completed; architecture promotion in `b88b62c` | Deleted and verified; see deletion journal |
| [#33](https://github.com/pdomain/pdomain-book-tools/issues/33) | `51d4739b3034db307ea2eab185709ef1d9e1ee8a7a182d4f2f6a43f8811978e2` | This ledger; `docs/architecture/glyph-annotations.md`; issue #41 implementation evidence | Mislabeled duplicate of canonical feature request #41; the glyph contract shipped in `675ad76` | Superseded by #41 | Deleted and verified; see deletion journal |
| [#35](https://github.com/pdomain/pdomain-book-tools/issues/35) | `b3d590b69d90603afa5406e4e1b2ce215b69ebc9baadccebc399a48e8c2766eb` | This ledger; geometry repr implementation and tests | The request became spec #36; `BoundingBox.__repr__` now emits the spec's eval-safe `from_ltrb` form | Completed; commit `b4c5b8c` | Deleted and verified; see deletion journal |
| [#36](https://github.com/pdomain/pdomain-book-tools/issues/36) | `9b9917d8d6d772a2e6f00865e574054d1f189cfe30d5da8fc385b051dbe48b38` | This ledger; geometry repr implementation and tests | The repr contract chose eval-safe `BoundingBox.from_ltrb(...)`, positional `Point(...)`, and no other geometry types | Implemented; commit `b4c5b8c` | Deleted and verified; see deletion journal |
| [#38](https://github.com/pdomain/pdomain-book-tools/issues/38) | `7e3fdcf0cb3906d5cf10cb365bcbb0688e03fb7f0dc365e1c92fde6f33a391a4` | This ledger; `pdomain_book_tools/geometry/bounding_box.py`; repr tests | `BoundingBox.__repr__` uses the corrected `from_ltrb` contract rather than the issue body's invalid four-argument constructor form | Completed; commit `b4c5b8c` | Deleted and verified; see deletion journal |
| [#39](https://github.com/pdomain/pdomain-book-tools/issues/39) | `5424bd1958c4dbf8927f0f284b839e83cc7e869ef48966a680946e1e40fa2346` | This ledger; `pdomain_book_tools/geometry/point.py`; repr tests | `Point.__repr__` returns the requested positional form for integer and fractional coordinates | Completed; commit `b4c5b8c` | Deleted and verified; see deletion journal |
| [#40](https://github.com/pdomain/pdomain-book-tools/issues/40) | `b90696134e506158a1df97265e00bd7a3446df9459a73eaada62b5998377e974` | This ledger; `tests/test_geometry_repr.py`; geometry repr tests | The tests were absorbed into PR #50 after blocker #51 corrected the BoundingBox form | Completed in squash merge `b4c5b8c` | Deleted and verified; see deletion journal |
| [#41](https://github.com/pdomain/pdomain-book-tools/issues/41) | `ee2438437c67de6577ac92d9ef241007770cb6e70ec0a4d9f03fa8c5154bd9b5` | This ledger; `docs/architecture/glyph-annotations.md`; glyph implementation and tests | Glyph facts remain a side channel on `Word` and do not mutate canonical ground-truth text | Completed; merge `675ad76` | Deleted and verified; see deletion journal |
| [#42](https://github.com/pdomain/pdomain-book-tools/issues/42) | `dc421b541e3c7126516360015d77c9f06868e8f4e06c7c31cca8e555d652f007` | This ledger; `Makefile` | `make ci` now runs an unconditional full-repository Ruff format and check gate | Completed; commit `e57a52c` | Deleted and verified; see deletion journal |
| [#43](https://github.com/pdomain/pdomain-book-tools/issues/43) | `021ff1e31a1d5e3b6dd590d507f4e6def1f2ed03d1c2747156bab8ea3368e041` | This ledger; `docs/issues/2026-05-11-gh-043-style-review-detect-subprocess-failure.md` | The local issue only claims a refile to `ocr-container-meta#1`; this batch did not verify that external record or a fix | Needs owner decision; governed record remains active | Owner authorized Git-canonical source deletion; local record remains active |
| [#44](https://github.com/pdomain/pdomain-book-tools/issues/44) | `80abdf9870d18d98ca73ff442cee19bd906faac59271656ca6e81ebfdf93e058` | This ledger; immutable raw export; `ConcaveTrillion/ocr-container-meta#2` | The PR-body metadata bug belongs to cross-cut workspace tooling, not this library; AGENTS.md routes that work to the meta tracker | Superseded by meta-repository tracking | Deleted and verified; see deletion journal |
| [#51](https://github.com/pdomain/pdomain-book-tools/issues/51) | `ddcce13f3f64f8e5c425fa1c8f5e1de698d4d1b541b738b26242cf5205fd758d` | This ledger; `pdomain_book_tools/geometry/bounding_box.py`; `tests/test_geometry_repr.py`; `tests/geometry/test_bounding_box.py` | `BoundingBox.__repr__` emits the eval-safe `BoundingBox.from_ltrb(...)` form and the tests pin its format and round trip | Implemented; commit `2bec8db` | Deleted and verified; see deletion journal |
| [#52](https://github.com/pdomain/pdomain-book-tools/issues/52) | `c886d9b4f39387f9c0df368581d999b092ccc35bfc4f57c8d3bcc605d42e8490` | This ledger; `docs/architecture/ocr-model-and-schema-boundaries.md`; `docs/architecture/page-serialization.md`; review metadata code and tests | The requested top-level `Word.is_validated` and setter were rejected; persisted validation lives at `word.review.validated` to preserve `ReviewMetadata` encapsulation | Abandoned / won't do; superseded by commit `60d0fc8` contract | Deleted and verified; see deletion journal |
| [#53](https://github.com/pdomain/pdomain-book-tools/issues/53) | `c7f409ac8965db8ba397f948df60ed430f7072ea1b016db606d66c28b33cefb8` | This ledger; immutable raw export; existing line and page APIs | The current per-word workflow uses `Line.merge_word_left` / `merge_word_right`; pixel erasure can mutate the Page image and then call `finalize_page_structure` | Abandoned tracking request; no library change needed | Deleted and verified; see deletion journal |
| [#54](https://github.com/pdomain/pdomain-book-tools/issues/54) | `d3e61adc8792f5589c9b5740e2f748e1e97668ca49338c0bf95ede2f1b70cf69` | This ledger; `docs/issues/2026-05-17-gh-054-monthly-grooming.md` | The May 2026 run found an empty queue, deleted `STATUS.md`, and archived strict-linting research; no evidence proves that the named recurring automation remains current | Needs owner decision; governed record remains active | Owner authorized Git-canonical source deletion; local record remains active |
| [#55](https://github.com/pdomain/pdomain-book-tools/issues/55) | `f23e483e6a0ed1481533710cab55b8c28aa6ca1182aebb7c061a3cb06534838f` | This ledger; immutable raw export; meta-repository cross-cut tracking | Pipeline-foundation planning belongs to the workspace-wide workflow system named by AGENTS.md | Superseded by meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#56](https://github.com/pdomain/pdomain-book-tools/issues/56) | `08cd1949b1a73f3d75fad31c09a0eac07791a14aeec0ab732eb0797fb1c0e507` | This ledger; immutable raw export; meta-repository cross-cut tracking | Skill-prompt planning belongs to the workspace-wide workflow system named by AGENTS.md | Superseded by meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#57](https://github.com/pdomain/pdomain-book-tools/issues/57) | `e7e0ab33db019cbe59984ff2a9ee3ea175e147a79b37bb2351e0be139f3235af` | This ledger; immutable raw export; meta-repository cross-cut tracking | Grooming-system planning belongs to the workspace-wide workflow system named by AGENTS.md | Superseded by meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#58](https://github.com/pdomain/pdomain-book-tools/issues/58) | `8ff6df861e3ff25a7a09366b895f1e4f066d4231b80d608a10bc7aeb4d01d84e` | This ledger; immutable raw export; meta-repository cross-cut tracking | `ship-issue-pick.py` is cross-cut workflow tooling; its source issue was migrated to the meta repository | Superseded by meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#59](https://github.com/pdomain/pdomain-book-tools/issues/59) | `ab85ed796c243d0acef8658e584b8d38a873777a9f2b8c405288283ace95fe5b` | This ledger; immutable raw export; meta-repository cross-cut tracking | `decompose-spec-sync.py` is cross-cut workflow tooling; its source issue was migrated to the meta repository | Superseded by meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#60](https://github.com/pdomain/pdomain-book-tools/issues/60) | `49bfbbdb1fc05ac4a0adaaba520ecbb00303543ce8f8dcb38f9209479626dae0` | This ledger; immutable raw export; meta-repository cross-cut tracking | The plan-sync implementation belongs to cross-cut workflow tooling; commit `cc783c5` confirms that this repository routes such work to `ConcaveTrillion/ocr-container-meta` | Superseded by meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#61](https://github.com/pdomain/pdomain-book-tools/issues/61) | `bc2618bba4ee61b1c55564bc9baefb20fb2ca31cf3f190367b3d42aa392ffac1` | This ledger; immutable raw export; commits `167995f`, `66ea04f`, and `cc783c5`; meta-repository cross-cut tracking | The decision template was added locally, then removed after moving to organization-wide coverage; the remaining label and skill work is cross-cut | Superseded by organization-wide and meta-repository tracking; no claim that every requested slice shipped locally | Deleted and verified; see deletion journal |
| [#62](https://github.com/pdomain/pdomain-book-tools/issues/62) | `a47b902bbf474c4f9d134855eea7d68ee7a72c6bdaaa6cd137423b3536e56e0c` | This ledger; immutable raw export; meta-repository cross-cut tracking | The Plan A final integration check belongs to cross-cut workflow tooling; commit `cc783c5` confirms the later tracking destination | Superseded by meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#63](https://github.com/pdomain/pdomain-book-tools/issues/63) | `399d0b21f89f195086b727459093a95e76570605bf83cd0afbce8df7c4dbff6c` | This ledger; immutable raw export; meta-repository cross-cut tracking | The triage-skill outcome change belongs to cross-cut skill tooling; commit `cc783c5` confirms the later tracking destination | Superseded by meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#64](https://github.com/pdomain/pdomain-book-tools/issues/64) | `d451aa8ad88fc8808ec3e43996956fa9e4d6d03ffe70b9a7dc0ad62430bfe0cc` | This ledger; immutable raw export; meta-repository cross-cut tracking | The spec-from-issue convention change belongs to cross-cut skill tooling; commit `cc783c5` confirms the later tracking destination | Superseded by meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#65](https://github.com/pdomain/pdomain-book-tools/issues/65) | `a62915785c13f7e935d3fa8dbad7b79b0f560383add151be93b113f1a4ab4fb4` | This ledger; [active governed issue](../issues/2026-05-17-gh-065-decompose-spec-flags.md) | A contemporaneous comment reports completion of the decompose-spec flag change in an external workflow session, but this repository contains no corresponding artifact or independent proof | Needs owner decision; governed record remains active | Owner authorized Git-canonical source deletion; local record remains active |
| [#66](https://github.com/pdomain/pdomain-book-tools/issues/66) | `b264dcb22465d437ae61f3f0160d836aa8b13c4414d78a2b7891101225930785` | This ledger; immutable raw export; meta-repository cross-cut tracking | The ship-issue context-read change belongs to cross-cut skill tooling; commit `cc783c5` confirms the later tracking destination | Superseded by meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#67](https://github.com/pdomain/pdomain-book-tools/issues/67) | `76f5339307ccfa717bd324a3d5d1073b1d008e613e9a354594584fe0a5cc0283` | This ledger; immutable raw export; meta-repository cross-cut tracking | The eight-agent-prompt change belongs to cross-cut workflow tooling; no local implementation evidence was found | Superseded by meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#68](https://github.com/pdomain/pdomain-book-tools/issues/68) | `e3cc70843fce586157ac66f82e5bf7b450c191b7b97ab21fb1ecffd2fd9764c3` | This ledger; immutable raw export; meta-repository cross-cut tracking | The brainstorming-skill patch belongs to cross-cut skill tooling; commit `cc783c5` confirms the later tracking destination | Superseded by meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#69](https://github.com/pdomain/pdomain-book-tools/issues/69) | `fcbfb77f96229503747a7f7513e9697150081dec20201ab01cea3f1432485abd` | This ledger; immutable raw export; meta-repository cross-cut tracking | The groom-skill skeleton belongs to cross-cut skill tooling; commit `cc783c5` confirms the later tracking destination | Superseded by meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#70](https://github.com/pdomain/pdomain-book-tools/issues/70) | `e1669656401cee38d52686939e0ed6dcf8560dbb359d714e81bf2e94fa6c91c1` | This ledger; immutable raw export; meta-repository cross-cut tracking | The groom-auto test suite belongs to cross-cut workflow tooling and was explicitly migrated; no local implementation claim | Superseded by meta-repository tracking | Deleted and verified; see deletion journal |
| [#71](https://github.com/pdomain/pdomain-book-tools/issues/71) | `36f2fe97c2540c5f37a5ea76f7f0575373853c69a6aca91b5a885f990a5d9487` | This ledger; immutable raw export; meta-repository cross-cut tracking | The groom-auto script belongs to cross-cut workflow tooling and was explicitly migrated; no local implementation claim | Superseded by meta-repository tracking | Deleted and verified; see deletion journal |
| [#72](https://github.com/pdomain/pdomain-book-tools/issues/72) | `2e2399aaf03a39d21ca305b76629b4f0b0f1aad04cf23022099e40a2f0083508` | This ledger; immutable raw export; meta-repository cross-cut tracking | The coding-bot workflow and nightly schedule belong to cross-cut workflow tooling and were explicitly migrated; no local implementation claim | Superseded by meta-repository tracking | Deleted and verified; see deletion journal |
| [#73](https://github.com/pdomain/pdomain-book-tools/issues/73) | `c4e4fcb59cd1a7ec42af525d0d214916f55c5a2051c2fa87e6bbcef3f073716a` | This ledger; immutable raw export; meta-repository cross-cut tracking | The groom skill belongs to cross-cut workflow tooling and was explicitly migrated; no local implementation claim | Superseded by meta-repository tracking | Deleted and verified; see deletion journal |
| [#74](https://github.com/pdomain/pdomain-book-tools/issues/74) | `98786c5969aadf70c34c1a5dc406bb5a3e6ad857315eeef04f3191b268fe8ff0` | This ledger; immutable raw export; meta-repository cross-cut tracking | The recurring grooming chore belongs to cross-cut workflow tracking and was explicitly migrated; no local implementation claim | Superseded by meta-repository tracking | Deleted and verified; see deletion journal |
| [#75](https://github.com/pdomain/pdomain-book-tools/issues/75) | `f68ba6d89febf4f08ba6e68e07c3c922d0f7229f20ac64dc37680cad6e4146d5` | This ledger; [repository quality gates](../process/repository-quality-gates.md); `docs/architecture/type-checking.md` | The canonical stack shipped across child issues #79 through #86; current process and strict type-checking architecture supersede the initial rollout contract | Implemented; reference commit `f809701` and child commits | Deleted and verified; see deletion journal |
| [#76](https://github.com/pdomain/pdomain-book-tools/issues/76) | `d4423a93abcf698225164542fd5cb755d17a057cad24423f483bc1589bca7cef` | This ledger; `docs/architecture/ocr-model-and-schema-boundaries.md`; model hooks, schema CLI, and tests | Pydantic core schemas cover Point, BoundingBox, Character, Word, Block, and Page; the public schema emitter remains implemented | Implemented; commits `d973b91` through `ca84058`, `6377cc4`, and `d6ad9d2` | Deleted and verified; see deletion journal |
| [#77](https://github.com/pdomain/pdomain-book-tools/issues/77) | `2da2187bd0a3ad5b0cb015e19811f6e29d49a2eb76181636eb0c7e79a09baee1` | This ledger; [active governed issue](../issues/2026-05-17-gh-077-workspace-agent-definitions.md) | The completion comment names two workspace agent files, but this repository cannot verify their current contents or routing | Needs owner decision; governed record remains active | Owner authorized Git-canonical source deletion; local record remains active |
| [#78](https://github.com/pdomain/pdomain-book-tools/issues/78) | `0fa9aa67947d649c97ebbea57491674022af0a14b3ec54fdc5a1cee2c304c9c6` | This ledger; immutable raw export; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The shared React and TypeScript library belongs to the external `pd-ui` repository and is explicitly tracked in the meta repository | Superseded by external repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#79](https://github.com/pdomain/pdomain-book-tools/issues/79) | `a14c85034838fc509807ba925c143171bdf5e83e6d22bbb79d59025bf5449db5` | This ledger; [repository quality gates](../process/repository-quality-gates.md); `docs/architecture/type-checking.md`; configuration and Makefile | The Pyright-to-basedpyright migration shipped in standard and then recommended mode; current strict zero-diagnostic architecture supersedes both | Implemented; commits `4ab7a93` and `f809701`; later strengthened | Deleted and verified; see deletion journal |
| [#80](https://github.com/pdomain/pdomain-book-tools/issues/80) | `5319e06323c29eff144ab81e1db098643c5a2a66c5ab9d5397a9e2b5e0575a60` | This ledger; [repository quality gates](../process/repository-quality-gates.md); `.editorconfig` | The canonical editor configuration remains present | Implemented; commit `cbaa74a` | Deleted and verified; see deletion journal |
| [#81](https://github.com/pdomain/pdomain-book-tools/issues/81) | `cc20ed3a92dcc155e18a901599fa0d053a129245cdab94f76d7bf9999182b47d` | This ledger; [repository quality gates](../process/repository-quality-gates.md); development dependencies | Standalone isort and pylint were removed; Ruff owns their adopted lint functions | Implemented; commit `bd0de40` | Deleted and verified; see deletion journal |
| [#82](https://github.com/pdomain/pdomain-book-tools/issues/82) | `393485f39bce81cb61124ad2927dbe488b0d330cd7c9eca2c3baf4852369e8a9` | This ledger; [repository quality gates](../process/repository-quality-gates.md); `.pre-commit-config.yaml` | Gitleaks, file checks, debug detection, uv-lock checking, and the basedpyright hook remain configured | Implemented; commit `4a59ff2`; hook later strengthened | Deleted and verified; see deletion journal |
| [#83](https://github.com/pdomain/pdomain-book-tools/issues/83) | `88b05397084a420e70526e9d4d084b324685a216a079a29f77d0d950a3d621c3` | This ledger; [repository quality gates](../process/repository-quality-gates.md); `.gitlint`; pre-commit configuration | Gitlint remains installed on the commit-message stage | Implemented; commit `b742231` | Deleted and verified; see deletion journal |
| [#84](https://github.com/pdomain/pdomain-book-tools/issues/84) | `b6c9cd90dafecd00d47175e1fcff6c02ce55c68c231f1ad7a994e2fb93f9cd7a` | This ledger; [repository quality gates](../process/repository-quality-gates.md); Ruff configuration | The canonical Ruff selection and its dependency update shipped; current `pyproject.toml` owns the exact rule set | Implemented; commit `c500d91` | Deleted and verified; see deletion journal |
| [#85](https://github.com/pdomain/pdomain-book-tools/issues/85) | `a0ba77b7210b50d8bec7751cf4f053ba0f81aab4c5c5bde88fc113928bcf3d2d` | This ledger; [repository quality gates](../process/repository-quality-gates.md); pytest configuration | Pytest treats warnings as errors and measures branch coverage | Implemented; commit `2e11974` | Deleted and verified; see deletion journal |
| [#86](https://github.com/pdomain/pdomain-book-tools/issues/86) | `7ec219034dde610274342ef3d42342583c7a43d1857c79820619132a9e425069` | This ledger; `docs/architecture/type-checking.md`; [repository quality gates](../process/repository-quality-gates.md) | Basedpyright recommended mode and CI integration shipped; current strict zero-diagnostic mode supersedes the initial level | Implemented; commit `f809701`; later strengthened | Deleted and verified; see deletion journal |
| [#87](https://github.com/pdomain/pdomain-book-tools/issues/87) | `c7e47a18a8db146c751b0a9f581c9816ad21673b9d11076afa7ea8ea50d807c6` | This ledger; `docs/architecture/ocr-model-and-schema-boundaries.md`; Point hook, shared helpers, and tests | Point exposes its Pydantic core schema; the shared schema helpers introduced in the same slice remain used | Implemented; commit `d973b91` | Deleted and verified; see deletion journal |
| [#88](https://github.com/pdomain/pdomain-book-tools/issues/88) | `e56112bf8ba4e3e295797438273c07fae115eb70eb571c7b03887020aeeea910` | This ledger; `docs/architecture/ocr-model-and-schema-boundaries.md`; BoundingBox hook and tests | BoundingBox exposes its Pydantic core schema; shared helpers had already landed with #87 | Implemented; commit `6f7c620` | Deleted and verified; see deletion journal |
| [#89](https://github.com/pdomain/pdomain-book-tools/issues/89) | `89e46c9f1e2aeca587eb5b34e5b71c46414c895f1498b0b89077da4ecc5b555f` | This ledger; `docs/architecture/ocr-model-and-schema-boundaries.md`; Character hook and tests | Character exposes the wire-shape Pydantic core schema used by public schema emission | Implemented; commit `9f9fabd` | Deleted and verified; see deletion journal |
| [#90](https://github.com/pdomain/pdomain-book-tools/issues/90) | `c76338dd5886ae852926c17c004f68a5204c593cd1aa5de1d35313bc8d02586b` | This ledger; `docs/architecture/ocr-model-and-schema-boundaries.md`; Word hook and tests | Word exposes its Pydantic core schema for public schema emission | Implemented; commit `6eb07ad` | Deleted and verified; see deletion journal |
| [#91](https://github.com/pdomain/pdomain-book-tools/issues/91) | `897d31f4807beebdb99dad7f1ce3606ec577d88620ec01b3209fd2caec5bb488` | This ledger; `docs/architecture/ocr-model-and-schema-boundaries.md`; Block hook and tests | Block exposes its Pydantic core schema for public schema emission | Implemented; commit `4d7fa3a` | Deleted and verified; see deletion journal |
| [#92](https://github.com/pdomain/pdomain-book-tools/issues/92) | `57cff67b7ce11e8626b8f02a8d9fd9bcc0a960f1fd218ec6c1e9f515f611a0aa` | This ledger; `docs/architecture/ocr-model-and-schema-boundaries.md`; Page hook and tests | Page exposes its Pydantic core schema while respecting its serialization boundary | Implemented; commit `ca84058` | Deleted and verified; see deletion journal |
| [#93](https://github.com/pdomain/pdomain-book-tools/issues/93) | `2f6609bacd092dc347559ffcc49df9d7504b292cb3c3c2d81f7dd9bcd90ff11e` | This ledger; `docs/architecture/ocr-model-and-schema-boundaries.md`; schema emitter and tests | `PUBLIC_MODELS` again covers the full public model set, and tests prevent narrowing | Implemented; commit `d6ad9d2` | Deleted and verified; see deletion journal |
| [#94](https://github.com/pdomain/pdomain-book-tools/issues/94) | `98293c518f692545b519272d981449923c06a60fc8446a6c82d7b0006cdb9826` | [active governed issue](../issues/2026-05-17-gh-094-pd-ui-agent-definition.md) | The full-power `pd-ui` agent is an external workspace artifact absent here | Needs owner decision; governed record remains active | Owner authorized Git-canonical source deletion; local record remains active |
| [#95](https://github.com/pdomain/pdomain-book-tools/issues/95) | `1a88aaa5197922c7f8acfa34b46d2b6ef1a3121837841c0726a5cda7196a9701` | [active governed issue](../issues/2026-05-17-gh-095-pd-ui-docs-agent-definition.md) | The read-only Haiku `pd-ui-docs` agent is an external workspace artifact absent here | Needs owner decision; governed record remains active | Owner authorized Git-canonical source deletion; local record remains active |
| [#96](https://github.com/pdomain/pdomain-book-tools/issues/96) | `b121ea1fb68ebcfdb26c694fd4fff648446b9d540c39c57fffe94708269db500` | [active governed issue](../issues/2026-05-17-gh-096-pd-ocr-ops-agent-definition.md) | The full-power `pd-ocr-ops` agent is an external workspace artifact absent here | Needs owner decision; governed record remains active | Owner authorized Git-canonical source deletion; local record remains active |
| [#97](https://github.com/pdomain/pdomain-book-tools/issues/97) | `6d025564bf304b5b674fc9800a0b2cdfead6bd0541e41326b771fad676aa5edb` | [active governed issue](../issues/2026-05-17-gh-097-pd-ocr-ops-docs-agent-definition.md) | The read-only Haiku `pd-ocr-ops-docs` agent is an external workspace artifact absent here | Needs owner decision; governed record remains active | Owner authorized Git-canonical source deletion; local record remains active |
| [#98](https://github.com/pdomain/pdomain-book-tools/issues/98) | `237aab0f102df336a7198638c1922b70620c97a3c4c47e6788a82cb1f0fbaa52` | [active governed issue](../issues/2026-05-17-gh-098-workspace-routing-table.md) | The workspace `CLAUDE.md` routing update is external state absent here | Needs owner decision; governed record remains active | Owner authorized Git-canonical source deletion; local record remains active |
| [#99](https://github.com/pdomain/pdomain-book-tools/issues/99) | `e8718ae16046cbda4f5e156b0cf5f6e9387ec6413323b215449e0896b7feaa82` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The `pd-ui` repository bootstrap belongs to external tracking, not this library | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#100](https://github.com/pdomain/pdomain-book-tools/issues/100) | `41d8efb7748d74b94052262ddb7255a1d2ea37a04b962cc980c1a661268aded9` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The `pd-ui` package metadata belongs to the external repository plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#101](https://github.com/pdomain/pdomain-book-tools/issues/101) | `dff0c86cd6c1f5609f7a0819e9f89e0dcd42c04498c30198998cc6ac44fcc75a` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The strict TypeScript configuration belongs to the external repository plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#102](https://github.com/pdomain/pdomain-book-tools/issues/102) | `1f1305e1d6eee51c27b485b54e5711410eb0044a032dbcc59d477e5b70c72da2` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The Vite library-mode build configuration belongs to the external repository plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#103](https://github.com/pdomain/pdomain-book-tools/issues/103) | `f62160576568e14e642a95ca7bae3ef4dfa48620eb0e16319a328330ab94caf3` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The Vitest configuration belongs to the external repository plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#104](https://github.com/pdomain/pdomain-book-tools/issues/104) | `b3ac2cdb358b1dcfd114f276f62ab524eb1063a4882c90b8c21d36834db81bcc` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The ESLint flat configuration belongs to the external repository plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#105](https://github.com/pdomain/pdomain-book-tools/issues/105) | `db1d03402eced2e9b7b1901912b7b127788a41ec285f78358cb7552bc2a1b1f0` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The `pd-ui` Makefile and CI gate belong to the external repository plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#106](https://github.com/pdomain/pdomain-book-tools/issues/106) | `087bd3de9ae169ab9132f67864e8b30fb6cbd24f5c380f9ea34f99ebb86e88a2` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The first external commit and agent definitions belong to the `pd-ui` repository plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#107](https://github.com/pdomain/pdomain-book-tools/issues/107) | `0f620e4b4d8452d7c44a8b8d1bbefc158f2b7c5cf98725ed63906eccc1efe344` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The copied theme tokens and primitives belong to the external repository plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#108](https://github.com/pdomain/pdomain-book-tools/issues/108) | `a22d3a4924edab6ce327f9bcee561cce26a93be495d6f2862688766ecf3cf5b1` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The theme sync-back script belongs to the external repository plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#109](https://github.com/pdomain/pdomain-book-tools/issues/109) | `cf72bef9461ccd2f614e7d2b9fabead3a960dd75e5c3ec9f3e4ba5ffe837a706` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The theme sync-invariant CI gate belongs to the external repository plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#110](https://github.com/pdomain/pdomain-book-tools/issues/110) | `3365df35af916e52245de7dd640e29bb23f9ec10280a274d6fc0bf50c8d1dbe0` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | Theme CSS package-subpath exports belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#111](https://github.com/pdomain/pdomain-book-tools/issues/111) | `f748bad9706fd515713b1b8d75fdfe14cea7b36823eae2b1f54fae9db11b9dc8` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The primitives layout and class-name helper belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#112](https://github.com/pdomain/pdomain-book-tools/issues/112) | `71510fa66cde92031696930db894ff6f8ff7561da60dd86fc3a17301bf290845` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The non-Radix primitive set belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#113](https://github.com/pdomain/pdomain-book-tools/issues/113) | `6c2c002a705992689d11216d34b9833eba3eb7702609c1fbe4b952eb6174aad8` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The Radix-layered primitive set belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#114](https://github.com/pdomain/pdomain-book-tools/issues/114) | `d3fa5c36eca2e5404c6bf6088da422b6065b7110aa93d0514f6f14b591a5e270` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The primitives barrel and subpath export belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#115](https://github.com/pdomain/pdomain-book-tools/issues/115) | `6d90c192479956e4910d554d120f3a7e3ecc87562cf8d8a100bfa22a5774f0e2` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | Field and Form helper primitives belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#116](https://github.com/pdomain/pdomain-book-tools/issues/116) | `8670157e068204a516f64b57adb43837c842065b685410b4b3c37997ffebfcfb` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The curated Lucide re-export belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#117](https://github.com/pdomain/pdomain-book-tools/issues/117) | `b34f769a7b61d501c0224636748e63653dcbd4b8680c21d6c46c6fde4346f6a2` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The bespoke OCR-domain SVG stubs belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#118](https://github.com/pdomain/pdomain-book-tools/issues/118) | `0d565141d998dfa06e72b0f8c5368fda1b5f2741811c550b1a767b76403fad29` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The icons barrel and subpath export belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#119](https://github.com/pdomain/pdomain-book-tools/issues/119) | `b61fbf9726477000f6a6960027608465ea353e1645677d28529fb12d81afa666` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The pinned-wheel codegen fetch step belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#120](https://github.com/pdomain/pdomain-book-tools/issues/120) | `164b1bda932bf4d056e014c2594473ee02babc93941beb86f968058bd154b9f0` | This ledger; immutable raw export; parent #78; `docs/architecture/ocr-model-and-schema-boundaries.md`; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | This library supplies `schemas.emit`, but the external `pd-ui` invocation and JSON output task is not implemented here | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#121](https://github.com/pdomain/pdomain-book-tools/issues/121) | `ac80e19d55eec734e9efe6cb89e0cd01766872a59d2e329011fafeffee7af7a0` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | JSON Schema-to-TypeScript generation belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#122](https://github.com/pdomain/pdomain-book-tools/issues/122) | `7825c4d7490d896bbb6ba7137efe0fe91c692e0df42d2cefddfd512cd5e50e0a` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The codegen orchestrator and commit policy belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#123](https://github.com/pdomain/pdomain-book-tools/issues/123) | `58d07e578b908ec3010fc270b4b8abdaad89c72f02482bd5dcfbd49af91a9b0b` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The TypeScript types barrel and `*Like` reductions belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#124](https://github.com/pdomain/pdomain-book-tools/issues/124) | `50e11a24f3b10ebfa7eee2d0ab25e20ac6f0298089cb1c82c0f924514e232b0d` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The types subpath export belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#125](https://github.com/pdomain/pdomain-book-tools/issues/125) | `4d00a69fcbfe5609d30670ba8ee91bbc4f4dad19c0caed9a2a443722f4d8e22e` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The canvas slot API and types belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#126](https://github.com/pdomain/pdomain-book-tools/issues/126) | `dc288c7370e12200916f8f62170c9b7af1bd544211b2bd60ceac2c326fd46093` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The three canvas hooks belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#127](https://github.com/pdomain/pdomain-book-tools/issues/127) | `3c0918a77128e1dc62c2032d8b5ea1a1baffe65d53adc057f96fb73144158824` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The stage shell, image layer, and fixed layer order belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#128](https://github.com/pdomain/pdomain-book-tools/issues/128) | `f940769ce12125aa2b5b0672ceaff27b8c534f68069752bf9bc03ab48d0a313b` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The six canvas slot helpers belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#129](https://github.com/pdomain/pdomain-book-tools/issues/129) | `8de191ba21a287de045b65ada10514acbb50b2cdf788c894f59cd2f21064f4f9` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The canvas subpath export belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#130](https://github.com/pdomain/pdomain-book-tools/issues/130) | `99d5efe91c4f54c1ac0f17e59db6cd461df415e47239d753a377899e28ff180c` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | WordList API types and render-prop signatures belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#131](https://github.com/pdomain/pdomain-book-tools/issues/131) | `7ad06c7b9a943623ba127f785e37d06a07413ce3de915bc3fa06d08bab390295` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The virtualized list shell belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#132](https://github.com/pdomain/pdomain-book-tools/issues/132) | `ab064ed19af53a9e1aa14297e69b959bb77cbbd199f9c9e85a438f8d50181a48` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | LineList and PageList sibling shells belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#133](https://github.com/pdomain/pdomain-book-tools/issues/133) | `226b2c6978f652414879c6b39cb79de8189d3d3fe2c905a633fb4e224b658564` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | LineCard adapter documentation belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#134](https://github.com/pdomain/pdomain-book-tools/issues/134) | `fda5f278988fb90f39d019441cd2c729d25b06e55fd350d1c9a355176d216b72` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | Worklist filtering and sorting hooks belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#135](https://github.com/pdomain/pdomain-book-tools/issues/135) | `9fbe736f4877e2ecfb21d781be8d5baa9124b862623710f46c2d265586d5ecbf` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | StatusPip, ConfidenceBar, and MatchStatusChip belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#136](https://github.com/pdomain/pdomain-book-tools/issues/136) | `38d605c9165f767d2a4ad8d70b26ca6e747c00c14cba194b06112e23172edfac` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The worklist subpath export belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#137](https://github.com/pdomain/pdomain-book-tools/issues/137) | `c903e31eb7a923f1dc2a5c40877523c22cd960878a2fc89a204330602457e9fc` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | AppShell props and context types belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#138](https://github.com/pdomain/pdomain-book-tools/issues/138) | `b2d16fe5ed225966afdd59e27b65ec87f126a0fe1af3f3ae1dcf710f1ca029b5` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The AppShell grid skeleton belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#139](https://github.com/pdomain/pdomain-book-tools/issues/139) | `227d66a77918734140dcf8059e02e249dda692bdba659c6cc4783a4f2480d114` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | LauncherSlot and LauncherTile belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#140](https://github.com/pdomain/pdomain-book-tools/issues/140) | `8968dc907721b4e9e8a9ee09bf224b7b2a92fcfb7aa33e4e7e029e81682ab103` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | Breadcrumb, TopNav, Drawer, Rail, and RightPanel sub-shells belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#141](https://github.com/pdomain/pdomain-book-tools/issues/141) | `92239679a5724c89f93d79d4f98fb2c9bc66e715d4152b7cfda5030e72f95ee2` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The shell subpath export belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#142](https://github.com/pdomain/pdomain-book-tools/issues/142) | `b148826bfea6aded046802b1f5d09943ac4b125b954b568738e7efb53f21301f` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | Four state-store factories belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#143](https://github.com/pdomain/pdomain-book-tools/issues/143) | `05f5fc48d50498ce1b9624db41fecf4acd28c3c2e6b89ef6614fc3d95cab01d2` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | Context-bound selection, viewport, and worklist hooks belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#144](https://github.com/pdomain/pdomain-book-tools/issues/144) | `eae5dda409d0a170bef8872b5ce7eb4d3f4a5317e3afe8fe542cbb9364891f19` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | UI preference storage, provider, and theme/color hooks belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#145](https://github.com/pdomain/pdomain-book-tools/issues/145) | `49d4562af67d8c04dc787b69f77803fdfb40a7a16aecfd087a7a0fe92dbe9d0b` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | Suite-sibling context and hooks belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#146](https://github.com/pdomain/pdomain-book-tools/issues/146) | `faafa434f7a477f48667b957d3ac81dd4428ebf12fd33fd6670b4e8e05d5afe3` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | Stub-friendly `useStageCall` and `useLongJob` interfaces belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#147](https://github.com/pdomain/pdomain-book-tools/issues/147) | `f7f869b479b8db8a96187542eb5b1e431076be58850f629bbcb0e5abbd56f4ee` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | Canvas and worklist hook re-exports belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#148](https://github.com/pdomain/pdomain-book-tools/issues/148) | `d7e9074081ea71cf91f01b9f66f4c54515e5ab0dd91b0aff7e4498967ea252c8` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The stores subpath export belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#149](https://github.com/pdomain/pdomain-book-tools/issues/149) | `a9dbd7db983cbffc4d26e742bb7dce8ed320af84dddba39b07421baec1b67e5f` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The Storybook scaffold belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#150](https://github.com/pdomain/pdomain-book-tools/issues/150) | `8312adb6ae50548778d6a49b3e951558f1b50fe7c8416ae853a03f94b287d027` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | Primitive-component stories belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#151](https://github.com/pdomain/pdomain-book-tools/issues/151) | `32769c0e6069555619d594646227947da798a576fd9f5586e6bb8674b8c4ea5a` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | Canvas, Worklist, and Shell stories belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#152](https://github.com/pdomain/pdomain-book-tools/issues/152) | `be669161db8b3cbf8a8d53b3e2ec7f2e05c773a70302627d4446e036ebd88092` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | Icon stories belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#153](https://github.com/pdomain/pdomain-book-tools/issues/153) | `e8e444e3783aac8d3b8703f9aa5f817cbf1852a4773f22bc4fb54d5816b2a6c7` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The story-presence CI gate belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#154](https://github.com/pdomain/pdomain-book-tools/issues/154) | `04d4ef26d84343eef6cd8e65c3268eae48f822dce37c0ae7c0417ad21313bd44` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | Build-output completeness verification belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#155](https://github.com/pdomain/pdomain-book-tools/issues/155) | `d015a6e98a06cd901e76ccf6e5193a2cf7c8367396c7a0335de3345bfa0571f8` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The `0.1.0-alpha` version bump belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#156](https://github.com/pdomain/pdomain-book-tools/issues/156) | `e11fe705f1d4eda3c67af3fa583ce73f92b0be9a844be56789c27eb0fc7407d2` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | The publish dry run and temporary-consumer smoke install belong to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#157](https://github.com/pdomain/pdomain-book-tools/issues/157) | `b0c98220c30f907aa1760e60d7e55049099f9c4dc85417f512e52cb50f1f88f5` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | Publishing `0.1.0-alpha` belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#158](https://github.com/pdomain/pdomain-book-tools/issues/158) | `d7a29e5a7c635ab0a8f58044748244a4addd9c35cd80241daa6e57e145517e28` | This ledger; immutable raw export; parent #78; [`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12) | Release documentation belongs to the external `pd-ui` plan | Superseded by parent and meta-repository tracking; no local implementation claim | Deleted and verified; see deletion journal |
| [#159](https://github.com/pdomain/pdomain-book-tools/issues/159) | `070afa6c1a7a0881e8f958906c0e8eca0839adbc380a7ee9f48b742964cbf401` | This ledger; immutable raw export; parent #56; meta-repository cross-cut tracking | The decompose-spec default-sync and compatibility changes belong to cross-cut skill tooling | Superseded by meta-repository tracking; no local implementation claim or successor issue inferred | Deleted and verified; see deletion journal |
| [#160](https://github.com/pdomain/pdomain-book-tools/issues/160) | `541ba9a942a614fc08d8d7aeab1c4deda9aba70ed05d735bde170517b6293a60` | This ledger; immutable raw export | The one-time grooming report recorded seven `mark_complete` actions and no items for CT review | Abandoned as completed disposable workflow output; no product or implementation claim | Deleted and verified; see deletion journal |
| [#162](https://github.com/pdomain/pdomain-book-tools/issues/162) | `c5d65ff48b84ed09035aeba90dfc6abd762d0c57b0aef8db17c1ba7e6e6ac9fb` | This ledger; immutable raw export; commit `46be7aa`; `pdomain_book_tools/licenses`; focused tests | The shared data-driven SPDX allowlist and validator shipped | Implemented; downstream integration remains outside this issue | Deleted and verified; see deletion journal |
| [#163](https://github.com/pdomain/pdomain-book-tools/issues/163) | `7f441e6d436b2e88a95863124e180efaa63ee9976bd5f18f259dfdc09e1c609c` | This ledger; immutable raw export; commit `4d483ad`; glyph annotation code and tests | LigatureKind vocabulary and legacy wire-value migration shipped; the model remained a dataclass | Implemented; SPA-side adaptation was out of scope | Deleted and verified; see deletion journal |
| [#164](https://github.com/pdomain/pdomain-book-tools/issues/164) | `67e90f1f6f955d874d7c843ff3b4fd6c5b2e9030bb5200ca7cfb3f0d438014e7` | This ledger; immutable raw export; commit `3480c3a`; `tests/hf/test_hf.py` | Both Hugging Face exception import paths are mocked, removing the xdist import-order flake | Implemented and regression-tested | Deleted and verified; see deletion journal |
| [#165](https://github.com/pdomain/pdomain-book-tools/issues/165) | `58b2edf5b86baf582e826bc2793e134f5fa09fdd3945681bdb60faeeedc9d005` | This ledger; immutable raw export; [active governed issue](../issues/2026-05-22-gh-165-checkpoint-hardening.md); [shipped architecture](../architecture/checkpoint-loading-trust-boundary.md) | Commits `31137f1` and `e5cf913` shipped the safe default, injected loader, and state-dict validation; file-size, checksum, pinned-revision, `safetensors`, and local-path trust work remains | Partially implemented; governed residual remains active | Owner authorized Git-canonical source deletion; local record remains active |
| [#166](https://github.com/pdomain/pdomain-book-tools/issues/166) | `c45824601666ef0d2f6a721272ba770a0450c76fb0b8b90c333919e61ffa53e5` | This ledger; immutable raw export; commit `12baa82`; page export code and tests | DocTR training-set export now branches on normalized versus pixel-space boxes | Implemented and regression-tested | Deleted and verified; see deletion journal |
| [#167](https://github.com/pdomain/pdomain-book-tools/issues/167) | `07ff814b4a1290308b683073ca3c1a2fa444061ccbc712b8adf17b84b46ffcbe` | This ledger; immutable raw export; commit `cc965da`; detector registry tests | Failed `log_and_null` fallbacks no longer poison the detector cache | Implemented and regression-tested | Deleted and verified; see deletion journal |
| [#168](https://github.com/pdomain/pdomain-book-tools/issues/168) | `b47b53848f25d7e526b3dd77aa2846d34162c7baf2998cdbb2806304cf61ae1f` | This ledger; immutable raw export; commit `68917a8`; merge `7a3493d`; detector registry tests | Detector registration now always evicts cached entries for the key | Implemented and regression-tested | Deleted and verified; see deletion journal |
| [#169](https://github.com/pdomain/pdomain-book-tools/issues/169) | `afd74ff4245e0700c661e88a18c9d6fffa5bbc43bc4ee2ebc27a6eb463112e44` | This ledger; immutable raw export; commit `e6e31c9`; merge `72db9fe`; geometry and backend tests | Zero-overlap crops no longer become unrelated one-pixel edge strips | Implemented across BoundingBox, OpenCV, and CuPy paths | Deleted and verified; see deletion journal |
| [#170](https://github.com/pdomain/pdomain-book-tools/issues/170) | `fd6e1037661529afe0fbfbc6d9dfe04e848e7c6bc5c40c061a1b24ad161697a9` | This ledger; immutable raw export; commit `cd8485a`; merge `72db9fe`; image-op tests | Pixel-space float boxes now use floor-min, ceil-max, clamped integer ROI bounds | Implemented and regression-tested | Deleted and verified; see deletion journal |
| [#171](https://github.com/pdomain/pdomain-book-tools/issues/171) | `32719f09cb9e4a0af3e53f5ea396fcb1e19853a1b56ab384c11180ce98be8d51` | This ledger; immutable raw export; commit `48dcf7e` | The broken GPU job belonged to dead GitLab configuration in a GitHub-only repository | Disposed by deleting `.gitlab-ci.yml`; no GPU CI implementation claim | Deleted and verified; see deletion journal |
| [#172](https://github.com/pdomain/pdomain-book-tools/issues/172) | `5cf24a59f71bbd55277f6c95f2b3b921847433d93b7f95422cd991cd5221ccdd` | This ledger; immutable raw export; commit `48dcf7e` | The missing XML artifact belonged to the same unused GitLab pipeline | Disposed by deleting `.gitlab-ci.yml`; no XML coverage-report implementation claim | Deleted and verified; see deletion journal |
| [#173](https://github.com/pdomain/pdomain-book-tools/issues/173) | `41a53a1113df62ee77707fd567a4e3b565d63bbfe4fb7fea764f1740828ad269` | This ledger; immutable raw export; commits `e64abc5` and `48dcf7e`; packaging and CI configuration | The declared and tested Python range is 3.11 through 3.13 | Implemented with `>=3.11,<3.14`; no 3.14 support claim | Deleted and verified; see deletion journal |
| [#174](https://github.com/pdomain/pdomain-book-tools/issues/174) | `1d95164e586c9cbb9034255609b786b5405cdfed820e55dc907c2429b6b83d8b` | This ledger; immutable raw export; commit `c7b6962`; page generator tests | Training-set prefixes reject absolute paths, separators, and `..` before writes | Implemented path-escape prevention; no basename allowlist or resolved-containment claim | Deleted and verified; see deletion journal |
| [#175](https://github.com/pdomain/pdomain-book-tools/issues/175) | `238fbd90f601879a0c3d3ce1b2510482750c7eb1527e248fc5a4e6e9c246049f` | This ledger; immutable raw export; commit `32ea9ef`; schema-emission tests | `LayoutRegion` and `PageLayout` now appear in public schema emission | Implemented and regression-tested | Deleted and verified; see deletion journal |
| [#176](https://github.com/pdomain/pdomain-book-tools/issues/176) | `7fe3155b35b1590c5c6ef54ba537c93ab5fa14998a6b7b88fcec65742a65001e` | This ledger; immutable raw export; commit `66d36c9`; layout type tests | `LayoutRegion` coerces `RegionType` and requires finite confidence in `[0,1]` | Implemented and regression-tested | Deleted and verified; see deletion journal |
| [#177](https://github.com/pdomain/pdomain-book-tools/issues/177) | `27934ef13108961dc9fa3099ab230ae1dd680f27c12a1c1c0702fbd958c3bd9f` | This ledger; immutable raw export; commit `aed3962`; merge `165c55e`; adapter tests | The helper clips relevant out-of-range edges and drops degenerate boxes so emitted PP-DocLayout regions stay within image bounds | Implemented and regression-tested | Deleted and verified; see deletion journal |
| [#178](https://github.com/pdomain/pdomain-book-tools/issues/178) | `b708accb0ed91b0842fae24616a73fb48145d9e6981ff04d39cabbfb2fbbb523` | This ledger; immutable raw export; commit `71596a9`; merge `bad42d3`; [pipeline architecture](../architecture/reorganize-page-pipeline.md) | Shared caption-region identity is claimed once by the closest figure | Implemented closest-wins region deduplication; no global word-ID claim | Deleted and verified; see deletion journal |
| [#179](https://github.com/pdomain/pdomain-book-tools/issues/179) | `798d7337d2aa0768ad959aa2d0d81a4b4884558783cb07aff7dc7f21f58c72b9` | This ledger; immutable raw export; commit `cca69f0`; detector registry tests | Detector kwargs are checked for hashability before cache lookup | Implemented by rejecting unhashable kwargs with a contextual `TypeError` | Deleted and verified; see deletion journal |
| [#180](https://github.com/pdomain/pdomain-book-tools/issues/180) | `f6496290c5aea88da27e9a38d72467a6afd1d2c277db537354dc43c7e98732c5` | This ledger; immutable raw export; commit `6d812d8`; [glyph architecture](../architecture/glyph-annotations.md); Pydantic tests | The Word schema passes nullable glyph mappings through `any_schema`; `from_dict()` reconstructs them | Implemented round-trip preservation; no standalone strong glyph-schema claim | Deleted and verified; see deletion journal |
| [#181](https://github.com/pdomain/pdomain-book-tools/issues/181) | `a190cf80e79d8d7f5e8e24427793bf077342b755a48919219871a9491f3a6f86` | This ledger; immutable raw export; commit `75408db`; Block schema tests | The Block schema accepts integer-string pairs for unmatched ground-truth words | Implemented for Python tuples and JSON two-item arrays | Deleted and verified; see deletion journal |
| [#182](https://github.com/pdomain/pdomain-book-tools/issues/182) | `9ecfb178a3ba6248ea86bb86ef2aa6cb9ae94d1df79095cdecd3b53c06fa1294` | This ledger; immutable raw export; commit `b8a9f6a`; historical Page schema tests | Three provenance fields accepted string-keyed dictionaries while those fields existed | Implemented historically; fields were later removed, so no obsolete contract is promoted | Deleted and verified; see deletion journal |
| [#183](https://github.com/pdomain/pdomain-book-tools/issues/183) | `9232404ee4b68d4fe514777c6555906a466d776c88a2a0d7247756421a2065d9` | This ledger; immutable raw export; commit `8368a73`; [page serialization architecture](../architecture/page-serialization.md); scale tests | Document, Page, and Block scaling preserves current metadata while changing geometry | Implemented; removed historical Page fields are not revived | Deleted and verified; see deletion journal |
| [#184](https://github.com/pdomain/pdomain-book-tools/issues/184) | `9c4d83a57aad2f8dc6d3ed836a0e85556206d73abf72ed0aee8c8f44a1320cc9` | This ledger; immutable raw export; commit `2797f63`; CuPy canvas tests | GPU canvas allocation now supports grayscale and three-channel input | Implemented with CPU/GPU parity coverage | Deleted and verified; see deletion journal |
| [#185](https://github.com/pdomain/pdomain-book-tools/issues/185) | `e76662c56899128e480be660396502b94f7cc28046b558f8c80a7eb19f614fef` | This ledger; immutable raw export; commit `eb20ab0`; CuPy edge tests | GPU edge convolution now uses constant-zero padding to match CPU behavior | Implemented and regression-tested at the image border | Deleted and verified; see deletion journal |
| [#186](https://github.com/pdomain/pdomain-book-tools/issues/186) | `1919e65342071c92bacb563c379b5c7f514bf264e7ccd6c1a072aac1f36309be` | This ledger; immutable raw export; commit `aed3962`; pytest and Makefile configuration | Default tests exclude slow model downloads; `make test-slow` runs them intentionally | Implemented; no scheduled remote integration-job claim | Deleted and verified; see deletion journal |
| [#187](https://github.com/pdomain/pdomain-book-tools/issues/187) | `781d73068ae32295e7bdefcf283e0acf2af47f19291c338dd02b616fce9fec88` | This ledger; immutable raw export; commit `81a0a22`; dependency configuration | The DocTR Git source is pinned to immutable revision `390330ebe4fe25f214d84df89dc0f9b4dcdbf447` | Implemented with an explicit upgrade comment | Deleted and verified; see deletion journal |
| [#188](https://github.com/pdomain/pdomain-book-tools/issues/188) | `0773e73f51ce8ba23daa03b9f6f5f49e032c0f7005c322cd3dfaf2ca55c3f792` | This ledger; immutable raw export; commit `cfc6e66`; merge `7a3493d`; coverage documentation tests | The reporter reads `fail_under` from `pyproject.toml`, and README guidance is drift-tested | Implemented; current configuration remains authoritative | Deleted and verified; see deletion journal |
| [#189](https://github.com/pdomain/pdomain-book-tools/issues/189) | `8737079cc58b1035316e4b466d4db3b4ed23331ac577f31b83a50eb33eba1a2f` | This ledger; immutable raw export; commit `aed3962`; [quality-gates process](../process/repository-quality-gates.md) | Full GPU-capable coverage includes CuPy modules; CPU-only coverage omits unavailable GPU paths | Implemented as a source-set split with one threshold; no separate GPU CI threshold claim | Deleted and verified; see deletion journal |
| [#190](https://github.com/pdomain/pdomain-book-tools/issues/190) | `401ee83d5263e992b7c0529c9ca462c60420dd095bb25abe08389888accd1993` | This ledger; immutable raw export; commit `c5ca010`; merge `bad42d3`; [PP-DocLayout trust boundary](../architecture/pp-doclayout-trust-boundary.md) | The built-in source is pinned, custom remote repos require opt-in, and offline loading is supported | Implemented trust acknowledgment; allowlist, size, checksum, custom-source pinning, and local-artifact validation remain external | Deleted and verified; see deletion journal |
| [#192](https://github.com/pdomain/pdomain-book-tools/issues/192) | `d2262ba27fc270fc6a2cf6276d50f4c486aec38e12184863c076f30834aa4b53` | This ledger; immutable raw export; commit `bd99ad1`; merge `7a3493d`; CPU and GPU crop tests | Both crop backends reject negative edge values before slicing | Implemented and regression-tested | Deleted and verified; see deletion journal |
| [#193](https://github.com/pdomain/pdomain-book-tools/issues/193) | `db9e989c6af80f7e5deeccadabcbcbed923c54d10c452d07aa36ff1bf999f4c0` | This ledger; immutable raw export; commit `0101f31`; merge `7a3493d`; Word and Block tests | Constructors copy incoming mutable metadata dictionaries | Implemented shallow ownership isolation for the two reported dictionaries | Deleted and verified; see deletion journal |
| [#194](https://github.com/pdomain/pdomain-book-tools/issues/194) | `eb5d533ad760c28440060b04dc37a28c4bc2573331e8154075218373a1219102` | This ledger; immutable raw export; commit `59d7fbf`; merge `cb10703`; log-filter tests | The AI log filter reads at most 16 MiB and keeps the tail of larger logs | Implemented with bounded input memory | Deleted and verified; see deletion journal |
| [#195](https://github.com/pdomain/pdomain-book-tools/issues/195) | `96089dac72ca3f76582396f5e9a5fcaee61c6b2b16e11c2b92875600a73099e8` | This ledger; immutable raw export; commit `4f14e3e`; merge `cb10703`; Make-variable tests | Developer layout-fork targets validate SHA, repository IDs, and mirror paths before recipes run | Implemented with strict allowlist patterns | Deleted and verified; see deletion journal |
| [#196](https://github.com/pdomain/pdomain-book-tools/issues/196) | `565a1e60d4f89e84bb09734059647b7df0691bf858eb7d9a9121ac493af4fa18` | This ledger; immutable raw export; commit `81a0a22`; workflow and uv configuration | GitHub Actions and the CI uv version are pinned to immutable versions | Implemented for the release-critical workflow references; no all-dependency exact-pin claim | Deleted and verified; see deletion journal |
| [#197](https://github.com/pdomain/pdomain-book-tools/issues/197) | `08c84a29ab650c0aaacd932a732573384754258516c74ad5623039c8815afdff` | This ledger; immutable raw export; commit `7b8d4fa`; merge `cb10703`; `CONTRIBUTING.md` | Contributor setup uses `uv sync --group dev` for the dependency group | Implemented documentation correction | Deleted and verified; see deletion journal |
| [#198](https://github.com/pdomain/pdomain-book-tools/issues/198) | `b721cf8616b5ff2a877f2d80964568d46efd1fcc300dcc5eb48435a7001c0db0` | This ledger; immutable raw export; commit `86b6789`; merge `cb10703`; license tests | The vendored SPDX data has an adjacent notice naming source, vendor date, and CC0-1.0 | Implemented attribution metadata and package test | Deleted and verified; see deletion journal |
| [#199](https://github.com/pdomain/pdomain-book-tools/issues/199) | `863a8abb140437da390d4ea20aa1417acdc3588f04123dd9f39dd855173c7c3c` | This ledger; immutable raw export; commit and tag `2e815f3` / `v0.13.0`; `CHANGELOG.md` | Release `v0.13.0` made the reconciled glyph annotations available by tag | Implemented release and changelog entry | Deleted and verified; see deletion journal |
| [#200](https://github.com/pdomain/pdomain-book-tools/issues/200) | `d6085afb09065b86a29cd2527674d43d249ed506039aee9dc0bfb4a0da18f3c9` | This ledger; immutable raw export; commit `2b26ef3`; merge `bad42d3`; [local-dev architecture](../architecture/local-dev-mode.md) | Dependency upgrades detect local-dev state and refuse the clobbering path | Implemented guard, marker alignment, and local upgrade workflow | Deleted and verified; see deletion journal |
| [#205](https://github.com/pdomain/pdomain-book-tools/issues/205) | `0596fc57cd1dea7f86f438aadf19564bfbd9202bcd86f95b8958ed1a2703b922` | This ledger; immutable raw export; commit `31137f1`; [DocTR checkpoint architecture](../architecture/checkpoint-loading-trust-boundary.md); loader tests | The finetuned predictor exposes a keyword-only injected loader with a `weights_only=True` default | Implemented the narrow safe-loader request; #165 retains separate unresolved checkpoint hardening | Deleted and verified; see deletion journal |
| [#206](https://github.com/pdomain/pdomain-book-tools/issues/206) | `a928a04c2b3245ee43f5bd49fbb18e48c92f6035b4678e5effcec7497a4cdfd5` | This ledger; immutable raw export; investigation commit `401863f`; [durable decision](decisions.md); `pdomain_book_tools/py.typed` | The warnings arise from downstream `Any` payloads and `getattr()` resolver flows, not missing library annotations | Abandoned / not planned locally; downstream resolver narrowing is out of scope | Deleted and verified; see deletion journal |

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
provenance and asks the owner to confirm the external disposition before
retiring the local record. Its GitHub source copy was deleted after the
Git-only tracking decision.

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

### Issues #60 through #69 continued the migrated workflow plans

Issues #60, #61, and #62 were Plan A children of #55. Issue #60 proposed parsing
plan headings and loading open and closed milestone issues. It would index the
issues by slug from `Plan:` body lines, then apply create, update, close, and
reopen diffs. It also proposed returning counts and task lists for dry-run
reports.

Issue #61 proposed adding `kind:decision` after `kind:spec` in `label_seed.py`,
creating a decision issue template in the reference repository, and documenting
the decompose-spec `--sync` alias. Issue #62 named the plan's final integration
check without repeating its procedure. All three pointed to
`docs/superpowers/plans/2026-05-17-gh-workflow-plan-a-pipeline.md`, at anchors
`#sync-impl`, `#decision-label`, and `#integration-check`, respectively.

Issues #63 through #69 were Plan B children of #56. They respectively proposed
removing triage's direct-ship outcome; adding a cross-repository recommendation
to spec-from-issue; making decompose-spec `--sync` the default while retaining
`--one-shot` for backward compatibility; and giving ship-issue a two-step
context read. They also proposed adding a cross-repository recommendation block
to all eight `pd-*` agent prompts, extending `patch-brainstorming-skill.sh` with
that convention, and creating the groom skill skeleton.

The issue #65 title ends with a comma in the source. Its body points to the
historical Plan B `#slug` anchor despite naming the flag behavior more
specifically. All seven pointed to
`docs/superpowers/plans/2026-05-17-gh-workflow-plan-b-skills.md`, at anchors
`#triage-two-outcomes`, `#spec-from-issue-cross-repo`, `#slug`,
`#ship-issue-two-step-context`, `#agent-cross-repo-blocks`,
`#patch-brainstorming-cross-repo`, and `#groom-skill-skeleton`, respectively.

Every issue cites its historical plan path and parent through `Tracks: #55` or
`Tracks: #56`. Those paths and anchors preserve exact plan provenance, but the
plans moved out of this repository. For #60 through #64 and #66 through #69,
comments first reported completion in session `2026-05-17
(superpowers-gh-integration)`, then reported restoration from a 2026-05-17 plan
update, and finally said the cross-cut plans were migrating to
`ConcaveTrillion/ocr-container-meta`. Commit `cc783c5` later changed this
repository's issue guidance to that meta-repository. The ledger therefore
treats those issues as superseded cross-cut records and does not infer local
implementation from their completion comments.

Issue #61 has narrower local evidence. Commit `167995f` added the requested
decision issue template with `kind:decision,status:backlog`; commit `66ea04f`
removed it after moving the template to `ConcaveTrillion/.github` for
organization-wide coverage. These commits corroborate the template slice and
its later destination. They do not prove that the label seeding and skill
documentation slices shipped in this repository.

Issue #65 has only one comment: `Work completed in session 2026-05-17
(superpowers-gh-integration).` Unlike the other nine issues, it has no restore
or migration comment. This contemporaneous statement reports an external
outcome, but this repository has no matching artifact or independent proof of
the flag behavior. The active governed issue asks the owner to verify the
external implementation before retiring the local record. Its GitHub source
copy was deleted after the Git-only tracking decision. The proposal is not a
current local contract.

Issue #67 has no local implementation evidence for the requested update across
all eight agent prompts. Its completion, restoration, and migration comments
are preserved as historical provenance, while the broader implementation claim
remains superseded by the meta-repository migration.

Across the batch, the detailed or plan-referential approach, historical plan
locations, parent links, session and restoration notices, and migration notices
are preserved here as provenance. They are disposable as current instructions
once the raw exports are digest-bound and the cross-cut destination is
recorded.

### Issues #70 through #74 moved to cross-cut grooming tracking

Issues #70 through #74 were Plan C children of #57. Their anchors were
`#groom-auto-tests`, `#groom-auto-impl`, `#groom-auto-schedule`, `#groom-skill`,
and `#monthly-groom-chore` under
`docs/superpowers/plans/2026-05-17-gh-workflow-plan-c-grooming.md`. Each comment
sequence reports completion in session `2026-05-17
(superpowers-gh-integration)`, restoration from the same day's plan update, and
migration to `ConcaveTrillion/ocr-container-meta`. The comments identify the
cross-cut destination but cite no external commit or successor issue.

Issue #70 specified TDD coverage for five deterministic grooming actions and a
judgment queue. Its 15 named tests covered unblock decisions, milestone
archival, spec and decision closure, referenced-research archival, and stale or
orphan queue entries. The FakeGh API, historical directory tree, age thresholds,
and required red-bar command are preserved in its immutable raw export.

Issue #71 specified the corresponding `Groom` implementation. It also specified
an injectable GitHub adapter, JSON result, executable and help behavior, blocker
regex, PyYAML frontmatter parsing, and a two-directory research-reference scan.
Issue #72 specified the coding-bot state graph, script invocation, Markdown
report, issue update, and `groom-auto-nightly` schedule. Issue #73 specified
every groom subcommand and keep, update, archive, delete, and skip action.
Issue #74 specified the exact recurring title, repository, labels, body
requirements, and listing command. Their immutable raw exports preserve those
details without promoting them to current instructions.

No named script, test module, skill, coding-bot workflow, schedule, or recurring
issue is implemented in this repository. The explicit migration comments and
current repository routing supersede these local trackers without making local
implementation claims. Their detailed task behavior remains historical
provenance rather than current repository policy.

### Issues #75, #76, and #79 remain implemented

Issue #75 was the parent spec for child issues #79 through #86. Its closing
comment says every child closed and names `f809701` as the canonical reference
implementation. The requested stack combined basedpyright, Ruff, gitlint,
pre-commit, and CI. The historical spec and plan were
`docs/specs/2026-05-17-superpowers-gh-workflow-integration-design.md` and
`docs/plans/2026-05-17-pd-book-tools-strict-linting-rollout.md`.

Commit `f809701` established basedpyright recommended mode and wired it into
`make ci`. Neighboring child commits removed standalone isort and pylint,
expanded the canonical Ruff selection, and added gitlint, gitleaks, file checks,
debug-statement detection, uv-lock checking, and a basedpyright pre-commit hook.
The current repository has since strengthened type checking to strict mode over
the package, tests, and scripts with zero diagnostics. Current behavior belongs
to `docs/architecture/type-checking.md`; the original recommended-mode contract
is historical rather than current.

Issue #79 was the basedpyright child. Commit `4ab7a93` migrated configuration and
dependencies from Pyright to basedpyright in standard mode. Commit `f809701`
then raised it to recommended mode. Its comment also attributes `.editorconfig`,
`.gitlint`, gitleaks and uv-lock hooks, removal of standalone isort and pylint,
the canonical Ruff selection including ANN, BLE, TRY, LOG, and G families,
`filterwarnings=error`, and `--cov-branch` to the canonical rollout. Those
details map to the parent rollout and its child commits, not all to `f809701`
alone. Strict-mode architecture now supersedes the issue title's initial mode.

Issue #76 requested Pydantic core schemas for geometry and OCR models for JSON
code generation and validation. Commits `d973b91`, `6f7c620`, `9f9fabd`,
`6eb07ad`, `4d7fa3a`, and `ca84058` added schema hooks and focused tests for
Point, BoundingBox, Character, Word, Block, and Page. Commit `6377cc4` added the
schema-emission CLI, and `d6ad9d2` restored all public models to
`PUBLIC_MODELS`. Current code and tests remain covered by
`docs/architecture/ocr-model-and-schema-boundaries.md`.

### Issue #77 needs verification; issue #78 moved externally

Issue #77 pointed to the shared integration design and
`docs/plans/2026-05-16-workspace-agent-defs-pd-ui-pd-ocr-ops.md`. Its comment
says `.claude/agents/pd-ocr-ops.md` and `.claude/agents/pd-ui.md` existed with
full routing definitions. Those workspace files are absent here, and the source
cites no commit or tests. The active record keeps the claim pending owner
verification.

Issue #78 pointed to the same design and
`docs/plans/2026-05-16-pd-ui-new-repo.md`. It requested a shared React and
TypeScript component library for `pd-*` single-page applications. Its comment
says the task moved to the `pd-ui` repository and issue #12 in
`ocr-container-meta`, not this library. That explicit destination supersedes the
local tracker without claiming implementation in this repository.

### Issues #80 through #86 established the repository quality gates

Issues #80 through #86 were children of #75. Each body used `Approach: (see
plan)` and pointed to
`docs/plans/2026-05-17-pd-book-tools-strict-linting-rollout.md`. The bodies
named these anchors: `#add-canonical-editorconfig`,
`#remove-isort-and-pylint-from-dev-deps`,
`#expand-pre-commit-hooks-gitleaks-check-debug-state`,
`#add-gitlint-for-commit-message-hygiene`,
`#expand-ruff-select-to-the-full-proposed-set-bump-r`,
`#pytest-hardening-filterwarnings-error-cov-branch`, and
`#upgrade-basedpyright-to-recommended-mode-makefilec`.

Their identical completion comments summarize the whole rollout and say it was
implemented from `f809701` onward. The repository history provides
more precise attribution. Commit `cbaa74a` added `.editorconfig`; `bd0de40`
removed standalone isort and pylint; `4a59ff2` added gitleaks, the `check-*` and
debug-statement hooks, uv-lock checking, and a local basedpyright hook;
`b742231` added `.gitlint`, its dependency, and the commit-message hook;
`c500d91` expanded the Ruff selection and updated the lint toolchain;
`2e11974` adopted `filterwarnings=error` and `--cov-branch`; and `f809701`
raised basedpyright to recommended mode and integrated it with Make and CI.

Current configuration corroborates every outcome. `.editorconfig` and
`.gitlint` remain present. Isort and pylint are absent as standalone development
dependencies, while Ruff owns import sorting and its pylint subset. Pre-commit
still includes the named safety hooks. Pytest still treats warnings as errors
and measures branches. The exact current quality-gate contract lives in
`docs/process/repository-quality-gates.md`.

The basedpyright portion later strengthened beyond #86. Recommended mode is no
longer current: `docs/architecture/type-checking.md` records strict mode with
zero diagnostics over the package, tests, and scripts. The historical comment's
ANN, BLE, TRY, LOG, and G examples remain in the current Ruff selection.
However, `pyproject.toml` is authoritative for the complete present-day set.

### Issues #87 through #89 implemented the first schema hooks

Issues #87 through #89 were children of #76 and used `Approach: (see plan)`.
They pointed to `docs/plans/2026-05-17-pd-book-tools-pydantic-core-schemas.md`
at anchors `#add-getpydanticcoreschema-to-point`,
`#add-shared-schema-helpers-getpydanticcoreschema-to`, and
`#add-getpydanticcoreschema-to-character`.

Their identical comments say the core-schema method exists on Point,
BoundingBox, Character, Word, Block, and Page. That broad statement describes
the completed parent series. For these three child slices, commit `d973b91`
added Point's hook, the shared helper module, and focused tests; `6f7c620` added
BoundingBox's hook and tests; and `9f9fabd` added Character's wire-shape hook and
tests. The shared helpers therefore landed with #87 even though #88's title also
names them.

All three hooks and their tests remain in the current package. The later Word,
Block, and Page hooks complete the comment's broader list and are mapped under
issue #76. `docs/architecture/ocr-model-and-schema-boundaries.md` owns the
current public schema boundary, so no additional architecture promotion is
needed.

### Issues #90 through #93 completed the schema series

Issues #90 through #93 were the remaining children of #76. Each used
`Approach: (see plan)` and pointed to
`docs/plans/2026-05-17-pd-book-tools-pydantic-core-schemas.md`. Their anchors
were `#add-getpydanticcoreschema-to-word`,
`#add-getpydanticcoreschema-to-block`,
`#add-getpydanticcoreschema-to-page`, and
`#re-add-models-to-publicmodels-restore-narrowed-tes`.

The first three comments repeat the parent-series statement: Point,
BoundingBox, Character, Word, Block, and Page expose the core-schema method.
Commit `6eb07ad` added Word's hook and focused tests. Commit `4d7fa3a` added
Block's hook and tests, and `ca84058` added Page's wire-shape hook and tests.
Issue #93's comment says all subtasks were complete and cites `d6ad9d2`. That
commit restored all public model classes to `PUBLIC_MODELS` and restored the
full schema-emitter tests.

The hooks, public-model list, emitter, and tests remain present. Their current
contract is already covered by
`docs/architecture/ocr-model-and-schema-boundaries.md`, so this batch needs no
new architecture record.

### Issues #94 through #98 retain separate workspace evidence gates

Issues #94 through #98 were children of #77. They all used `Approach: (see
plan)`, tracked #77, and pointed to the historical
`docs/superpowers/plans/2026-05-16-workspace-agent-defs-pd-ui-pd-ocr-ops.md`.
Their respective anchors specified a full-power `pd-ui` agent, read-only Haiku
`pd-ui-docs` agent, full-power `pd-ocr-ops` agent, read-only Haiku
`pd-ocr-ops-docs` agent, and workspace `CLAUDE.md` routing-table update.

Each issue has one comment. All five comments say the cross-cut plans were
migrating to `ConcaveTrillion/ocr-container-meta`. No comment identifies a
successor issue, commit, test, or current file. All five tasks share one parent,
plan, and external ownership boundary, but each now has a separate governed
record and retirement decision. Those records preserve the requested path or
routing change, raw digest, and missing migration destination. The #77 record
preserves only the parent completion claim. Their GitHub source copies were
deleted after the Git-only tracking decision; all six local records remain
active until their individual evidence gates pass.

### Issue #99 moved with the pd-ui repository plan

Issue #99 was a child of #78. It used `Approach: (see plan)` and pointed to
`docs/superpowers/plans/2026-05-16-pd-ui-new-repo.md` at
`#create-directory-gitignore-license-readme-stub`. Its sole comment says the
cross-cut plans were migrating to `ConcaveTrillion/ocr-container-meta`.

Parent #78 explicitly places the shared React and TypeScript library in the
external `pd-ui` repository and points to
[`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12).
That parent destination supersedes this local bootstrap tracker. It does not
prove that the directory, `.gitignore`, license, or README stub shipped in this
repository.

### Issues #100 through #109 moved with the pd-ui repository plan

Issues #100 through #109 were children of #78. Every body uses `Approach: (see
plan)`, tracks #78, and points to the historical
`docs/superpowers/plans/2026-05-16-pd-ui-new-repo.md`. Their exact anchors and
scopes were:

- #100 `#packagejson-with-concavetrillion-metadata` — `package.json` with
  ConcaveTrillion metadata.
- #101 `#tsconfigjson-strict` — strict `tsconfig.json`.
- #102 `#vite-library-mode-build-config` — Vite library-mode build configuration.
- #103 `#vitest-config` — Vitest configuration.
- #104 `#eslint-flat-config` — ESLint flat configuration.
- #105 `#makefile-ci-gate` — Makefile and CI gate.
- #106 `#first-commit-agent-definitions` — first commit and agent definitions.
- #107 `#copy-tokenscss-and-primitivescss-into-pd-uitheme` — copy
  `tokens.css` and `primitives.css` into `pd-ui/theme/`.
- #108 `#sync-back-script-pd-ui-docsdesign-system` — sync-back from `pd-ui` to
  `docs/design-system`.
- #109 `#sync-invariant-ci-gate` — sync-invariant CI gate.

Each issue has one comment saying the cross-cut plans were migrating to
`ConcaveTrillion/ocr-container-meta`. Parent #78 supplies the precise successor,
[`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12),
and says `pd-ui` work does not belong to this library. The rows therefore treat
all ten children as superseded external trackers. Their raw exports preserve
the exact tasks and comments without claiming any local implementation or
creating active local records.

### Issues #110 through #119 continued the external pd-ui plan

Issues #110 through #119 were children of #78. Every body uses `Approach: (see
plan)`, tracks #78, and points to the historical
`docs/superpowers/plans/2026-05-16-pd-ui-new-repo.md`. Their exact anchors and
scopes were:

- #110 `#export-theme-css-via-package-subpaths` — export theme CSS through
  package subpaths.
- #111 `#primitives-folder-layout-classname-helper` — primitives folder layout
  and a `className` helper.
- #112 `#non-radix-primitives-button-input-textarea-badge-c` — Button, Input,
  Textarea, Badge, Chip, StatusPip, KeyCap, Card, Separator, and Progress.
- #113 `#radix-layered-primitives-dialog-alertdialog-popove` — Dialog,
  AlertDialog, Popover, Tooltip, DropdownMenu, Select, Tabs, ToggleGroup, and
  Accordion.
- #114 `#primitives-barrel-subpath-export` — primitives barrel and subpath export.
- #115 `#field-form-helper-primitives` — Field and Form helper primitives.
- #116 `#curated-lucide-subset-re-export` — curated Lucide subset re-export.
- #117 `#bespoke-ocr-domain-svg-stubs` — bespoke OCR-domain SVG stubs.
- #118 `#icons-barrel-subpath-export` — icons barrel and subpath export.
- #119 `#codegenfetch-install-pinned-wheels` — `codegen:fetch` pinned-wheel installation.

Issues #110 through #114 and #116 through #119 each have one comment saying the
cross-cut plans were migrating to `ConcaveTrillion/ocr-container-meta`. The
shorter comment on issue #115 reads,
`Migrating to ConcaveTrillion/ocr-container-meta.` The difference adds no local
implementation evidence.

Parent #78 points to
[`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12)
and says `pd-ui` work does not belong to this library. These ten child trackers
are therefore superseded. Their immutable raw exports preserve the precise
tasks, anchors, and comments without creating local product contracts or active
records.

### Issues #120 through #129 continued external codegen and canvas work

Issues #120 through #129 were children of #78. Every issue body tracks #78,
uses `Approach: (see plan)`, and points to the historical
`docs/superpowers/plans/2026-05-16-pd-ui-new-repo.md`. The issues used these
exact anchors and scopes:

- #120 `#codegenemit-invoke-schemasemit-write-json` — invoke `schemas.emit` and
  write JSON.
- #121 `#codegentsgen-json-schema-typescript` — generate TypeScript from JSON
  Schema.
- #122 `#codegen-orchestrator-commit-policy` — codegen orchestration and commit
  policy.
- #123 `#srctypesindexts-barrel-like-reductions` — `src/types/index.ts` barrel
  and `*Like` reductions.
- #124 `#types-subpath-export` — types subpath export.
- #125 `#canvas-slot-api-types` — canvas slot API and types.
- #126 `#hooks-usecanvascoords-useviewport-usecanvasselecti` —
  `useCanvasCoords`, `useViewport`, and `useCanvasSelection` hooks.
- #127 `#stage-shell-image-layer-fixed-layer-order` — stage shell, image layer,
  and fixed layer order.
- #128 `#slot-helpers-bboxlayer-wordhitlayer-marqueeselectl` — BBoxLayer,
  WordHitLayer, MarqueeSelectLayer, RotateTransformerLayer, EraseOverlayLayer,
  and CharRangeLayer.
- #129 `#canvas-subpath-export` — canvas subpath export.

Each issue has one comment saying the cross-cut plans were migrating to
`ConcaveTrillion/ocr-container-meta`. Parent #78 points to
[`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12)
and says `pd-ui` work does not belong to this library.

Issue #120 has a local producer boundary, but the task remains external. This
library implements `pdomain_book_tools.schemas.emit`.
`docs/architecture/ocr-model-and-schema-boundaries.md` documents that producer.
The issue asked `pd-ui` to invoke the producer and write its JSON artifact. The
local CLI does not prove that external invocation, output, or consumer
integration. The row therefore records useful local context without claiming a
local implementation.

All ten child trackers are superseded by the parent and meta-repository
destination. Their immutable raw exports preserve the exact tasks, anchors, and
comments without creating active local records.

### Issues #130 through #139 continued external worklist and shell work

Issues #130 through #139 were children of #78. Every body tracks #78 and uses
`Approach: (see plan)`. Each points to the historical
`docs/superpowers/plans/2026-05-16-pd-ui-new-repo.md`. Their exact anchors and
scopes were:

- #130 `#wordlist-api-types-render-prop-signatures` — WordList API types and
  render-prop signatures.
- #131 `#virtualized-list-shell` — virtualized list shell.
- #132 `#wordlist-sibling-shells-linelist-pagelist` — LineList and PageList
  sibling shells.
- #133 `#adapter-docs-for-linecard` — LineCard adapter documentation.
- #134 `#useworklistfilter-useworklistsort-hooks` — `useWorklistFilter` and
  `useWorklistSort` hooks.
- #135 `#status-row-primitives-statuspip-confidencebar-matc` — StatusPip,
  ConfidenceBar, and MatchStatusChip.
- #136 `#worklist-subpath-export` — worklist subpath export.
- #137 `#appshell-props-context-types` — AppShell props and context types.
- #138 `#appshell-grid-skeleton` — AppShell grid skeleton.
- #139 `#launcherslot-launchertile` — LauncherSlot and LauncherTile.

Each issue has one comment saying the cross-cut plans were migrating to
`ConcaveTrillion/ocr-container-meta`. Parent #78 points to
[`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12).
It says `pd-ui` work does not belong to this library. These ten child trackers
are therefore superseded. Their immutable raw exports preserve the precise
tasks, anchors, and comments. They do not create local implementation claims,
product contracts, or active records.

### Issues #140 through #149 continued external shell and store work

Issues #140 through #149 continued the external `pd-ui` work under parent #78.
Each body uses `Approach: (see plan)`, tracks #78, and points to the historical
`docs/superpowers/plans/2026-05-16-pd-ui-new-repo.md`. Their exact anchors and
scopes were:

- #140 `#breadcrumb-topnav-drawer-rail-rightpanel-sub-shell` — Breadcrumb,
  TopNav, Drawer, Rail, and RightPanel sub-shells.
- #141 `#shell-subpath-export` — shell subpath export.
- #142 `#createselectionstore-createviewportstore-createwor` —
  `createSelectionStore`, `createViewportStore`, `createWorklistStore`, and
  `createUIPrefsStore`.
- #143 `#useselection-useviewport-useworklist-context-bound` — context-bound
  `useSelection`, `useViewport`, and `useWorklist` hooks.
- #144 `#createuiprefsstore-uiprefsprovider-useuiprefs-uset` —
  `createUIPrefsStore`, `UIPrefsProvider`, `useUIPrefs`, `useTheme`,
  `useDensity`, `useLayerColor`, `useStatusColor`, and `useAccentColor`.
- #145 `#usesuitesiblings-suitesiblingsprovider` — `useSuiteSiblings` and
  `SuiteSiblingsProvider`.
- #146 `#usestagecall-uselongjob-interfaces-stub-friendly-i` — `useStageCall`
  and `useLongJob` interfaces with stub-friendly implementations.
- #147 `#usecanvascoords-useselection-useviewport-useworkli` — re-export
  `useCanvasCoords`, `useSelection`, `useViewport`, and `useWorklist` from
  `/canvas` and `/worklist`.
- #148 `#stores-subpath-export` — stores subpath export.
- #149 `#storybook-scaffold` — Storybook scaffold.

Each issue has one comment stating that the cross-cut plans were migrating to
`ConcaveTrillion/ocr-container-meta`. The comments are generic, but parent #78
supplies the exact successor:
[`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12).
The parent also says `pd-ui` work does not belong to this library.

These ten child trackers are therefore superseded. Their immutable raw exports
preserve the precise tasks, anchors, and comments without creating local
implementation claims, product contracts, architecture promotions, or active
records.

### Issues #150 through #158 moved with the external pd-ui release plan

Issues #150 through #158 tracked external `pd-ui` work under parent #78.
Each body uses `Approach: (see plan)`, tracks #78, and points to the historical
`docs/superpowers/plans/2026-05-16-pd-ui-new-repo.md`. Their exact anchors and
scopes were:

- #150 `#primitives-stories-button-input-chip-statuspip-key` — stories for
  Button, Input, Chip, StatusPip, KeyCap, Card, Separator, Progress, Badge, and
  Field primitives.
- #151 `#canvas-worklist-shell-stories` — Canvas, Worklist, and Shell stories.
- #152 `#icons-stories` — icon stories.
- #153 `#story-presence-ci-gate` — story-presence CI gate.
- #154 `#verify-build-output-completeness` — verify build-output completeness.
- #155 `#version-bump-to-010-alpha` — version bump to `0.1.0-alpha`.
- #156 `#publish-dry-run-smoke-install-in-tmp-consumer` — publish dry run and
  smoke install in a temporary consumer.
- #157 `#publish-010-alpha` — publish `0.1.0-alpha`.
- #158 `#document-the-release-in-changelogmd` — document the release in
  `CHANGELOG.md`.

Each issue has one comment stating that the cross-cut plans were migrating to
`ConcaveTrillion/ocr-container-meta`. Parent #78 supplies the exact successor:
[`ConcaveTrillion/ocr-container-meta#12`](https://github.com/ConcaveTrillion/ocr-container-meta/issues/12).
It also says `pd-ui` work does not belong to this library. These nine child
trackers are therefore superseded. Their immutable raw exports preserve the
precise tasks, anchors, and comments without creating local implementation
claims, product contracts, architecture promotions, or active records.

### Issue #159 moved decompose-spec skill work to cross-cut tracking

Issue #159 was a child of #56. Its body uses `Approach: (see plan)` and points
to the historical
`docs/superpowers/plans/2026-05-17-gh-workflow-plan-b-skills.md#decompose-spec-sync`.
It requested that `decompose-spec` use `--sync` by default, retain `--one-shot`
for compatibility, and require `{#slug}` in plan task headings.

Its one comment says the cross-cut plans were migrating to
`ConcaveTrillion/ocr-container-meta`, but neither the child nor parent #56
names a successor issue. The row therefore records only meta-repository
cross-cut tracking. It does not infer a successor issue, fold the work into the
`pd-ui` plan, or create a local implementation claim, product contract,
architecture promotion, or active record.

### Issue #160 was disposable grooming output

Issue #160 recorded a 2026-05-18 grooming run. It marked seven named plans
complete and reported that no items required CT review. Its only comment says
the actions were recorded when the issue was created and no further action was
needed. The immutable raw export preserves that one-time workflow result. It
does not establish a current product contract or implementation claim.

### Issues #162 through #164 shipped focused library and test fixes

Issue #162 requested one data-driven SPDX license source for downstream
consumers. Commit `46be7aa` added `pdomain_book_tools/licenses.py`, a vendored
SPDX JSON file, and `tests/test_licenses.py`. The public API exposes 518 exact,
case-sensitive identifiers as `SPDX_VALID_IDS` and provides
`is_valid_spdx_id()`. Non-string input returns `False`. The wheel test confirms
that the vendored data ships with the package. Downstream adoption remains
separate work.

Issue #163 identified a wire-format and model-shape mismatch with a downstream
SPA spec. Commit `4d483ad` uppercased `LigatureKind` values, renamed
`LONG_S_T` to `LONG_ST`, retained the existing members, and added `OE` and
`AE`. `LigatureMark.from_dict()` migrates legacy lowercase and old long-s
values, while `to_dict()` emits the current uppercase form. The shipped model
remains a dataclass; SPA-side adaptation was explicitly outside the commit's
scope. `tests/ocr/test_glyph_annotations.py` covers the vocabulary and legacy
migration.

Issue #164 tracked two Hugging Face sidecar tests that depended on xdist import
order. Commit `3480c3a` made both tests mock
`huggingface_hub.errors` and `huggingface_hub.utils`. The sentinel exception now
matches whichever supported import path production selects. The focused tests
in `tests/hf/test_hf.py` preserve that deterministic behavior.

### Issue #165 retains the unfinished checkpoint-hardening work

Issue #165 reported unsafe and mutable checkpoint-loading risks. Commit
`31137f1` made the injected, keyword-only `torch_load` callable default to
`torch.load(..., weights_only=True)`. Commit `e5cf913` added plain tensor
state-dict validation to both DocTR model-loading paths. Current code and tests
prove those safeguards, and the
[architecture record](../architecture/checkpoint-loading-trust-boundary.md)
defines only that shipped contract.

The original request also named maximum file sizes, checksums, immutable
Hugging Face revisions, `safetensors`, and the trust policy for local paths.
Those items remain unresolved. The
[governed issue](../issues/2026-05-22-gh-165-checkpoint-hardening.md) binds the
raw digest, delivered safeguards, and residual work. Its GitHub source copy was
deleted after the Git-only tracking decision, but the local record remains
active until the residual work is resolved.

### Issues #166 through #170 shipped correctness and cache fixes

Issue #166 showed that DocTR training export multiplied pixel-space coordinates
or tried to scale them as normalized values. Commit `12baa82` branches on
`BoundingBox.is_normalized` in detection and recognition export. Normalized
boxes keep the existing scaling path. Pixel-space boxes use clamped integer
bounds without multiplying by image dimensions. Tests in
`tests/ocr/test_page_training_set_generators.py` cover both export paths.

Issue #167 showed that a failed `log_and_null` detector build could cache a
`NullDetector` for later fail-fast calls. Commit `cc965da` stopped caching
fallback detectors. Three focused cases in `tests/layout/test_detector.py`
cover build-failure-then-raise, unknown-key-then-raise, and the no-cache
contract.

Issue #168 showed that first-time detector registration could leave a stale
cached fallback. Commit `68917a8`, merged in `7a3493d`, makes
`register_detector()` evict cached entries for the key on every registration.
The detector registry tests cover first registration as well as replacement.

Issue #169 showed that a crop entirely beyond an image edge could become an
unrelated one-pixel strip. Commit `e6e31c9`, merged in `72db9fe`, checks overlap
before clamping. `BoundingBox.crop_image()` returns `None` for zero overlap;
the OpenCV and CuPy rectangle backends retain their established invalid-crop
return convention. Geometry and backend tests cover right, below, exact-edge,
and partial-overlap cases.

Issue #170 showed that valid float pixel coordinates could reach NumPy slice
bounds. Commit `cd8485a`, also merged in `72db9fe`, added a shared ROI-bound
conversion. It floors minimums, ceils maximums, and clamps all bounds to image
dimensions. `tests/test_image_ops_free_functions.py` covers refinement, top and
bottom crops, and connected-component expansion with float coordinates.

### Issues #171 through #173 aligned CI files with supported systems

Issues #171 and #172 described a broken GitLab GPU job and a missing GitLab
coverage XML artifact. Commit `48dcf7e` deleted `.gitlab-ci.yml` because this is
a GitHub-only repository and no GitLab runner had been configured. That
deletion disposes of both dead-configuration findings. It does not claim that a
GPU CI job or XML coverage report was added elsewhere.

Issue #173 found that the declared Python 3.10 support conflicted with
`tomllib`, packaging tests, and the available CI runner. Commit `e64abc5`,
included in `48dcf7e`, raised `requires-python` to `>=3.11,<3.14` and expanded
the GitHub Actions matrix to Python 3.11, 3.12, and 3.13. The package supports
those three minor versions. This record makes no Python 3.14 support claim.

### Issues #174 through #177 hardened paths and public layout boundaries

Issue #174 showed that a caller-controlled training-set prefix could influence
write and delete paths. Commit `c7b6962` added early validation to both DocTR
training-set generators. It rejects absolute paths, path separators, and parent
traversal forms before filesystem writes. Focused generator tests cover unsafe
and accepted prefixes. The change does not define a character allowlist or
verify resolved-path containment under the output directory.

Issue #175 found that two documented public layout models were missing from
schema emission. Commit `32ea9ef` added `LayoutRegion` and `PageLayout` to
`PUBLIC_MODELS`. `tests/test_schemas_emit.py` covers their emitted fields, enum
values, and round-trip shapes.

Issue #176 found that direct `LayoutRegion` construction accepted invalid
types and confidence values. Commit `66d36c9` makes `__post_init__()` coerce
strings through `RegionType`. It also rejects non-finite confidence and values
outside the inclusive `[0.0, 1.0]` range. Constructor tests cover valid and
invalid inputs.

Issue #177 found that PP-DocLayout model boxes could exceed image bounds.
Commit `aed3962`, merged in `165c55e`, added a helper that clips relevant
out-of-range edges. The adapter drops boxes that become degenerate, so emitted
regions stay within image bounds. Unit and adapter tests in
`tests/layout/test_pp_doclayout.py` cover clipping and the post-processing path.

### Issues #178 through #180 preserved deduplication and extension data

Issue #178 showed that nearby figures could independently emit the same
caption region. Commit `71596a9`, merged in `bad42d3`, builds candidate pairs,
sorts them by geometric gap, and lets the closest figure claim each caption
region identity once. The regression test covers two figures sharing one wide
caption. The durable [pipeline
architecture](../architecture/reorganize-page-pipeline.md) records that
closest-wins region rule. Neither the implementation nor this migration claims
global word-ID deduplication across different regions.

Issue #179 found that unhashable detector kwargs failed during cache lookup
without useful context. Commit `cca69f0` adds `_assert_hashable_kwargs()` before
cache-key construction. It raises a contextual `TypeError` naming the kwarg.
The public API still requires hashable values; it does not recursively freeze
lists, dictionaries, or sets. Detector registry tests cover list and dictionary
rejection.

Issue #180 found that Pydantic validation silently dropped persisted glyph
annotations. Commit `6d812d8` adds a nullable `any_schema` field to the custom
`Word` schema, preserving the raw mapping until `Word.from_dict()` reconstructs
`GlyphAnnotations`. Tests cover non-empty, reviewed-empty, and absent values.
The [glyph architecture](../architecture/glyph-annotations.md) records this
round-trip boundary. It does not claim a standalone strong Pydantic schema for
`GlyphAnnotations`.

### Issues #181 through #183 aligned schemas and scaling with model data

Issue #181 found that the Block Pydantic schema rejected the
`unmatched_ground_truth_words` shape emitted by `to_dict()`. Commit `75408db`
added `INT_STR_PAIR_LIST_SCHEMA` and applied it to that field. The schema
accepts Python `(int, str)` tuples and JSON two-item arrays. A non-empty
round-trip test preserves the runtime shape.

Issue #182 found the same kind of mismatch for three Page provenance fields.
Commit `b8a9f6a` changed their schema from nullable strings to nullable
string-keyed dictionaries with arbitrary values. Those provenance fields were
later removed from Page in commit `f28746f`. The fix remains historical
provenance, but the removed fields are not promoted into current architecture
or revived as a compatibility promise.

Issue #183 showed that coordinate scaling dropped metadata from Document,
Page, and Block. Commit `8368a73` preserves every current metadata field while
changing page dimensions and bounding boxes. The focused tests cover
`Document.source_identifier`; Page identity, labels, name, and review fields;
and Block sort, ground-truth, attribute, and review fields. The
[page serialization architecture](../architecture/page-serialization.md)
records the current invariant and explicitly excludes removed historical Page
fields.

### Issues #184 through #189 aligned backends and quality gates

Issue #184 found that the GPU canvas always allocated two dimensions. Commit
`2797f63` now mirrors CPU allocation: grayscale input creates a two-dimensional
canvas and color input creates a three-channel canvas. CuPy tests cover shape,
pixel parity, and the white border.

Issue #185 found different convolution padding at image edges. Commit
`eb20ab0` changed the GPU path to constant-zero padding, matching CPU
`np.convolve(..., mode="same")` behavior. Its regression test covers content at
the image border that previously produced a false GPU detection.

Issue #186 found that default tests could download the roughly 132 MB
PP-DocLayout model. Commit `aed3962` excludes `slow` tests from the default
Pytest configuration and adds `make test-slow` for intentional network-backed
runs. It does not add or promise a scheduled remote integration job.

Issue #187 found that the DocTR Git source could move during dependency
upgrades. Commit `81a0a22` pins it to
`390330ebe4fe25f214d84df89dc0f9b4dcdbf447` and documents the upgrade location.
The lock and source declaration now name the same immutable revision.

Issue #188 found that coverage guidance said 80% while the configured gate was
87%. Commit `cfc6e66`, merged in `7a3493d`, makes the reporter read
`tool.coverage.report.fail_under` from `pyproject.toml`. README and focused
tests prevent the displayed threshold from drifting away from that authority.

Issue #189 found that CuPy modules were excluded even when GPU tests could run.
The configuration introduced with commit `aed3962` uses two source sets. Full
GPU-capable coverage includes CuPy modules in the common 87% gate. CPU-only or
CI coverage uses `.coveragerc.cpu` and omits unavailable GPU paths. The
[quality-gates record](../process/repository-quality-gates.md) documents that
split. It does not claim a separate GPU-only threshold or a required remote GPU
CI job.

### Issue #190 added a separate PP-DocLayout model trust boundary

Issue #190 concerns Hugging Face `from_pretrained()` for PP-DocLayout models,
not DocTR `.pt` state-dict deserialization. Commit `c5ca010`, merged in
`bad42d3`, keeps the built-in fork and revision pinned. It requires
`trust_remote_checkpoint=True` for a custom remote repository and forwards
`local_files_only=True` when callers require offline loading. Local paths and
the built-in source do not require the remote trust flag.

The [PP-DocLayout trust-boundary architecture](../architecture/pp-doclayout-trust-boundary.md)
records the shipped rules and their limits. The flag acknowledges trust; it
does not validate a repository. Custom-source pinning, allowlists,
artifact-size limits, checksums, and local-artifact inspection remain outside
the adapter.
The distinct
[DocTR checkpoint boundary](../architecture/checkpoint-loading-trust-boundary.md)
continues to own `torch.load`, `weights_only`, and state-dict validation.

### Issues #192 through #195 bounded mutable and developer inputs

Issue #192 found that negative `crop_edges()` arguments reached Python slicing.
Commit `bd99ad1`, merged in `7a3493d`, validates all four edge values in the
OpenCV and CuPy implementations. Both backend test suites cover negative input.
The existing dimension checks still handle crops larger than the image.

Issue #193 found that Word and Block constructors retained two caller-owned
dictionaries by reference. Commit `0101f31`, also merged in `7a3493d`, copies
`ground_truth_match_keys` and `additional_block_attributes` during
construction. Aliasing tests prove that later caller mutation does not change
model state. This is shallow ownership isolation for the reported dictionaries,
not a general deep-copy promise for every constructor input.

Issue #194 found that the AI log filter read an entire log before filtering.
Commit `59d7fbf`, merged in `cb10703`, caps input at 16 MiB. Smaller logs are
read whole; larger logs retain the tail, where CI failure context normally
appears. `tests/utility/test_ai_filter_log.py` covers both paths.

Issue #195 found shell-interpolation risk in developer layout-fork Make
targets. Commit `4f14e3e`, also merged in `cb10703`, validates Git SHAs as 7–40
lowercase hexadecimal characters, Hugging Face repository IDs as owner/name,
and mirror paths against shell metacharacters. Tests show rejected values do
not execute recipe bodies.

### Issues #196 through #200 completed supply-chain and local workflow work

Issue #196 requested stronger release-workflow pins. Commit `81a0a22` pins
`actions/checkout`, `astral-sh/setup-uv`, and uv itself to immutable versions.
It also pins the DocTR Git source tracked by issue #187. The issue is complete
for those release-critical references; broad runtime lower bounds were not all
converted to exact pins.

Issue #197 found contributor setup using optional-extra syntax for a dependency
group. Commit `7b8d4fa`, merged in `cb10703`, changes the command in
`CONTRIBUTING.md` to `uv sync --group dev`, matching the project declaration
and Makefile setup path.

Issue #198 found no visible attribution beside the vendored SPDX license data.
Commit `86b6789`, also merged in `cb10703`, adds
`pdomain_book_tools/data/THIRD-PARTY-NOTICES.md`. The notice names the upstream
project and repository, CC0-1.0 license, and vendor date. A package test ensures
the notice ships and retains its source and license statements.

Issue #199 requested a tagged release containing the reconciled glyph model.
Commit `2e815f3` added the `v0.13.0` changelog entry and was tagged `v0.13.0`.
That release includes the uppercased ligature vocabulary, `LONG_ST`, and the
`OE` and `AE` members needed by downstream consumers.

Issue #200 requested protection against dependency upgrades that silently
replace local-dev overrides. Commit `2b26ef3`, merged in `bad42d3`, adds the
two-tier probe to `upgrade-deps`, aligns marker creation, and tests marker and
GPU-extra detection. The evolved
[local-dev architecture](../architecture/local-dev-mode.md) records the current
target names, marker contract, guard scope, and remaining caveats.

### Issue #205 completed only the injectable safe-loader request

Issue #205 requested a public injection point for DocTR `.pt` loading. Commit
`31137f1` adds a keyword-only `torch_load` parameter to
`get_finetuned_torch_doctr_predictor()`. Its default is
`functools.partial(torch.load, weights_only=True)`, and the package's PyTorch
minimum needs no older-version fallback. Tests prove keyword-only placement,
custom-loader forwarding, and the safe default.

The [DocTR checkpoint architecture](../architecture/checkpoint-loading-trust-boundary.md)
records that shipped boundary. Issue #205 is narrower than issue #165. It does
not claim maximum-size checks, checksums, immutable default model revisions,
`safetensors`, or a complete local-path trust policy. Those residuals remain in
the active governed #165 record.

### Issue #206 was resolved as a downstream typing problem

Issue #206 investigated whether the published package lost attribute types for
`Page.lines`, `Page.words`, and ground-truth text. Investigation commit
`401863f` compared direct typed access, defensive `getattr()` access, and the
published wheel. Direct access on a `Page`-typed value produced no basedpyright
warnings. The wheel contained `pdomain_book_tools/py.typed` and annotated
source.

The confirmed warning chain originated downstream. An `Any`-typed
`PageLoadOutcome.payload` flowed through resolvers that returned `object |
None`. The downstream `getattr()` calls preserved the resulting `Any`. The
investigation also tried to cross-check two other downstream consumers, but
that check was inconclusive because the referenced paths were not found. The
[durable decision](decisions.md) therefore treats the warnings as downstream
resolver work, not a missing library annotation.

The issue closed as not planned for this repository. Narrowing the affected
downstream resolver to `Page | None` remains outside this library's scope. The
raw export and investigation commit preserve the historical report without
creating a local implementation or active-work claim.

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

## Every source issue was deleted only when its evidence gates passed

The migration and Git-only tracking decision were merged on `master`. All 214
source issues were permanently deleted and verified in 23 batches. The
append-only deletion journal records one pre-delete and one post-delete row for
each issue. The live count is zero, and GitHub Issues is disabled.

Ten records still have unresolved owner decisions or residual work:
issues #43, #54, #65, #77, #94 through #98, and #165. Their 10 governed records
remain active after GitHub source deletion. No retired per-issue documents are
needed for the 171 deleted completed rows.
