# Deep Code and Security Review - 2026-05-22

Scope: `pdomain-book-tools` at `fba1657` (`Merge fix/hf-test-xdist-determinism...`).

Method: five read-only subagent reviews plus coordinating spot checks. The review covered OCR/domain models, image and geometry code, layout/schema/public API, external downloads/subprocesses, CI, packaging, and security posture. No production files were edited.

Verification limits:

- Most findings are static-review findings with direct code evidence.
- One subagent used `uv run python` probes for pydantic/schema and coordinate-export behavior.
- Full `make ci` was not run because this was a review-only request and several findings concern CI itself.

## Executive summary

The highest-risk issues are:

1. Finetuned DocTR checkpoints are loaded with unconstrained `torch.load()` from caller-provided or mutable downloaded paths.
2. Pixel-space OCR pages cannot be safely exported to DocTR training sets.
3. Layout detector fallback caching can silently poison later fail-fast calls.
4. Geometry/image crop code can return unrelated edge pixels for fully out-of-bounds crops and can crash on valid float pixel coordinates.
5. CI claims coverage/GPU/Python-version guarantees that are not actually enforced.

## Filed GitHub issues

The findings below were filed in `pdomain/pdomain-book-tools` on 2026-05-22 using the repo label taxonomy (`kind:*`, `status:backlog`, `priority:*`, `effort:*`, plus area labels where applicable). `bot:ship-issue-ready` was intentionally not applied; several issues need human triage before unattended pickup.

| Finding | Issue |
|---:|---|
| 1 | [pdomain/pdomain-book-tools#165](https://github.com/pdomain/pdomain-book-tools/issues/165) |
| 2 | [pdomain/pdomain-book-tools#166](https://github.com/pdomain/pdomain-book-tools/issues/166) |
| 3 | [pdomain/pdomain-book-tools#167](https://github.com/pdomain/pdomain-book-tools/issues/167) |
| 4 | [pdomain/pdomain-book-tools#168](https://github.com/pdomain/pdomain-book-tools/issues/168) |
| 5 | [pdomain/pdomain-book-tools#169](https://github.com/pdomain/pdomain-book-tools/issues/169) |
| 6 | [pdomain/pdomain-book-tools#170](https://github.com/pdomain/pdomain-book-tools/issues/170) |
| 7 | [pdomain/pdomain-book-tools#171](https://github.com/pdomain/pdomain-book-tools/issues/171) |
| 8 | [pdomain/pdomain-book-tools#172](https://github.com/pdomain/pdomain-book-tools/issues/172) |
| 9 | [pdomain/pdomain-book-tools#173](https://github.com/pdomain/pdomain-book-tools/issues/173) |
| 10 | [pdomain/pdomain-book-tools#174](https://github.com/pdomain/pdomain-book-tools/issues/174) |
| 11 | [pdomain/pdomain-book-tools#175](https://github.com/pdomain/pdomain-book-tools/issues/175) |
| 12 | [pdomain/pdomain-book-tools#176](https://github.com/pdomain/pdomain-book-tools/issues/176) |
| 13 | [pdomain/pdomain-book-tools#177](https://github.com/pdomain/pdomain-book-tools/issues/177) |
| 14 | [pdomain/pdomain-book-tools#178](https://github.com/pdomain/pdomain-book-tools/issues/178) |
| 15 | [pdomain/pdomain-book-tools#179](https://github.com/pdomain/pdomain-book-tools/issues/179) |
| 16 | [pdomain/pdomain-book-tools#180](https://github.com/pdomain/pdomain-book-tools/issues/180) |
| 17 | [pdomain/pdomain-book-tools#181](https://github.com/pdomain/pdomain-book-tools/issues/181) |
| 18 | [pdomain/pdomain-book-tools#182](https://github.com/pdomain/pdomain-book-tools/issues/182) |
| 19 | [pdomain/pdomain-book-tools#183](https://github.com/pdomain/pdomain-book-tools/issues/183) |
| 20 | [pdomain/pdomain-book-tools#184](https://github.com/pdomain/pdomain-book-tools/issues/184) |
| 21 | [pdomain/pdomain-book-tools#185](https://github.com/pdomain/pdomain-book-tools/issues/185) |
| 22 | [pdomain/pdomain-book-tools#186](https://github.com/pdomain/pdomain-book-tools/issues/186) |
| 23 | [pdomain/pdomain-book-tools#187](https://github.com/pdomain/pdomain-book-tools/issues/187) |
| 24 | [pdomain/pdomain-book-tools#188](https://github.com/pdomain/pdomain-book-tools/issues/188) |
| 25 | [pdomain/pdomain-book-tools#189](https://github.com/pdomain/pdomain-book-tools/issues/189) |
| 26 | [pdomain/pdomain-book-tools#190](https://github.com/pdomain/pdomain-book-tools/issues/190) |
| 27 | [pdomain/pdomain-book-tools#191](https://github.com/pdomain/pdomain-book-tools/issues/191) |
| 28 | [pdomain/pdomain-book-tools#192](https://github.com/pdomain/pdomain-book-tools/issues/192) |
| 29 | [pdomain/pdomain-book-tools#193](https://github.com/pdomain/pdomain-book-tools/issues/193) |
| 30 | [pdomain/pdomain-book-tools#194](https://github.com/pdomain/pdomain-book-tools/issues/194) |
| 31 | [pdomain/pdomain-book-tools#195](https://github.com/pdomain/pdomain-book-tools/issues/195) |
| 32 | [pdomain/pdomain-book-tools#196](https://github.com/pdomain/pdomain-book-tools/issues/196) |
| 33 | [pdomain/pdomain-book-tools#197](https://github.com/pdomain/pdomain-book-tools/issues/197) |
| 34 | [pdomain/pdomain-book-tools#198](https://github.com/pdomain/pdomain-book-tools/issues/198) |

## Critical / High

### 1. Unsafe PyTorch checkpoint deserialization

Evidence:

- `pdomain_book_tools/ocr/doctr_support.py:244`
- `pdomain_book_tools/ocr/doctr_support.py:275`
- `pdomain_book_tools/hf/models.py:37`
- `pdomain_book_tools/hf/download.py:89`

`get_finetuned_torch_doctr_predictor()` calls `torch_load(det_path, map_location=...)` and `torch_load(reco_path, map_location=...)` on caller-provided checkpoint files. The default Hugging Face OCR resolution also downloads `.pt` checkpoints with `revision=None`, so the default source is mutable.

Impact:

- Malicious `.pt` files can be code-execution risks depending on PyTorch loading behavior/version.
- Even with safer modern defaults, oversized or malformed checkpoints can exhaust memory or break runtime behavior.
- Mutable default model downloads can silently change OCR behavior across installs.

Remediation:

- Pass `weights_only=True` explicitly where supported.
- Validate the loaded object is a plain state dict with expected tensor-like values.
- Add max-size checks before load.
- Prefer `safetensors` for distributed checkpoints.
- Pin default OCR model downloads to immutable commits and optionally verify checksums.
- Document local checkpoint paths as trusted-input only until the loader is hardened.

### 2. Pixel-space pages corrupt/crash DocTR training-set export

Evidence:

- `pdomain_book_tools/ocr/page.py:3322`
- `pdomain_book_tools/geometry/bounding_box.py:118`
- `pdomain_book_tools/ocr/page.py:3433`

Detection export always calls `word.bounding_box.get_four_point_scaled_polygon_list(img_width, img_height)`, and that helper multiplies coordinates by image dimensions. Pixel-space boxes such as `(10,10)-(20,20)` on a 100px image become `(1000,1000)-(2000,2000)`. Recognition export unconditionally calls `bbox.scale(...)`, which is invalid for pixel-space boxes.

Impact:

- Training data generated from Tesseract or other pixel-space OCR is corrupt or crashes.
- Bad labels can poison downstream model training.

Remediation:

- Branch on `bbox.is_normalized`.
- Scale normalized boxes; pass pixel boxes through after clamping/casting.
- Add detection and recognition export tests using `is_normalized=False`.

### 3. Layout fallback cache poisoning

Evidence:

- `pdomain_book_tools/layout/registry.py:176`
- `pdomain_book_tools/layout/registry.py:179`
- `pdomain_book_tools/layout/registry.py:199`

When `get_detector(..., on_error="log_and_null")` catches a build failure, it caches a `NullDetector` under the same cache key used by later `on_error="raise"` calls.

Impact:

- A transient model download/OOM/build failure can make later fail-fast callers silently get no layout.
- Unknown-key fallbacks can likewise hide later valid configuration.

Remediation:

- Do not cache fallback detectors under normal success keys.
- Include the fallback policy in the cache key, or make `on_error="raise"` bypass cached fallbacks.
- Add regression tests for failure-then-raise and unknown-key-then-register flows.

### 4. Registering a detector after fallback can leave stale `NullDetector`

Evidence:

- `pdomain_book_tools/layout/registry.py:242`
- `pdomain_book_tools/layout/registry.py:245`

`register_detector()` only evicts cached entries when replacing a previous user factory. If `get_detector("custom-x", on_error="log_and_null")` ran before registration, a fallback can remain cached after the first real registration.

Impact:

- Newly registered detectors may never be used for that key.

Remediation:

- Always evict cached entries for `key` during registration, regardless of whether a previous factory existed.

### 5. Fully out-of-bounds crops can return unrelated edge strips

Evidence:

- `pdomain_book_tools/geometry/bounding_box.py:638`
- `pdomain_book_tools/image_processing/cv2_processing/crop.py:35`
- `pdomain_book_tools/image_processing/cupy_processing/crop.py:31`

`crop_image()` and both `crop_to_rectangle()` backends clamp `minX/minY` to `width - 1` / `height - 1` before testing final overlap. A box entirely beyond the right or bottom edge can become a 1-pixel strip at the image border.

Impact:

- OCR cleanup/layout code can silently process unrelated border pixels instead of reporting no overlap.

Remediation:

- Test overlap before clamping.
- Clamp to `[0, width]` / `[0, height]`.
- Return `None` or a clear invalid-crop result for zero-overlap crops.
- Add tests parallel to `test_clamp_to_image_returns_none_when_outside_image()`.

### 6. Valid pixel-space float boxes crash bbox image ops

Evidence:

- `pdomain_book_tools/geometry/image_ops.py:58`
- `pdomain_book_tools/geometry/image_ops.py:59`
- `pdomain_book_tools/geometry/image_ops.py:102`

Pixel-space `BoundingBox` supports float coordinates, and `refine(..., expand_beyond_original=True)` can produce them. `_extract_roi()` and `_connected_content_bbox_from_image_thresh()` use those floats directly as NumPy slice bounds.

Impact:

- Valid boxes can raise `TypeError: slice indices must be integers...` in `refine_bbox()`, `crop_top_bbox()`, `crop_bottom_bbox()`, and connected-component expansion.

Remediation:

- Convert pixel coordinates to integer ROI bounds with a documented rounding policy.
- Clamp bounds before slicing.
- Add tests for float pixel boxes and refine-then-crop flows.

### 7. GitLab GPU job is broken and skips GPU checks in CI

Evidence:

- `.gitlab-ci.yml:46`
- `.gitlab-ci.yml:49`
- `pyproject.toml:56`
- `tests/conftest.py:140`
- `tests/conftest.py:153`

The GPU job runs `uv sync --group dev` but does not install the `gpu` extra containing CuPy/OpenCV CUDA. It then imports `cupy`. Even if fixed, the test skip markers skip CUDA in CI.

Impact:

- GPU CI either fails before tests or gives false confidence.
- CUDA regressions can land without enforced testing.

Remediation:

- Use `uv sync --group dev --extra gpu` in the GPU job.
- Replace blanket CI skips with actual CUDA availability checks or an explicit `GPU_CI=1`.
- Decide whether GPU failures should remain `allow_failure`.

### 8. GitLab coverage artifact is declared but not generated

Evidence:

- `.gitlab-ci.yml:23`
- `.gitlab-ci.yml:27`
- `pyproject.toml:340`
- `pyproject.toml:347`

GitLab expects `coverage.xml`, but the configured pytest addopts generate terminal and HTML coverage, not XML.

Impact:

- Coverage artifact upload fails or silently disappears.

Remediation:

- Add `--cov-report=xml` to GitLab pytest or call `make coverage`.

### 9. Claimed Python 3.10 support conflicts with tests

Evidence:

- `pyproject.toml:17`
- `tests/test_packaging.py:22`
- `tests/test_packaging.py:78`
- `.github/workflows/ci.yml:17`

The package declares `>=3.10,<3.14`, but tests import stdlib `tomllib` and assert Python 3.11+. GitHub CI only tests Python 3.13.

Impact:

- Python 3.10 users can install a supported package whose test/development workflow fails.
- Runtime compatibility is not CI-validated across the advertised range.

Remediation:

- Either raise `requires-python` to `>=3.11` or add a `tomli` fallback and CI matrix across supported versions.

## Medium

### 10. Training-set `prefix` can escape output directories

Evidence:

- `pdomain_book_tools/ocr/page.py:3304`
- `pdomain_book_tools/ocr/page.py:3417`
- `pdomain_book_tools/ocr/page.py:3435`

Training-set image names are built directly from caller-provided `prefix`. Prefixes containing path separators or absolute-path syntax can affect where paths resolve. The recognition path also deletes matching files based on that prefix.

Impact:

- A hostile or accidental prefix can overwrite or delete files outside the intended image directory.

Remediation:

- Restrict `prefix` to a basename-safe character set.
- Reject path separators and absolute prefixes.
- Assert resolved output paths remain under the intended `images/` directory.

### 11. Public layout wire models are omitted from schema emission

Evidence:

- `docs/usage/public-api.md:52`
- `docs/usage/public-api.md:57`
- `pdomain_book_tools/schemas/emit.py:37`

`LayoutRegion` and `PageLayout` are documented public API and have `to_dict()`/`from_dict()`, but `PUBLIC_MODELS` omits them.

Impact:

- Downstream codegen receives schemas for OCR/geometry but not the public layout JSON shape.
- Layout sidecars can drift without schema tests catching it.

Remediation:

- Add `LayoutRegion` and `PageLayout` to schema emission.
- Add tests asserting enum values, fields, and round-trip shape.

### 12. LayoutRegion accepts invalid public construction inputs

Evidence:

- `pdomain_book_tools/layout/types.py:61`
- `pdomain_book_tools/layout/types.py:111`
- `pdomain_book_tools/layout/types.py:155`

Direct construction with `type="text"` succeeds, but `to_dict()` later expects `self.type.value`. Confidence accepts NaN, infinity, or out-of-range values.

Impact:

- Public construction can later crash serialization/rendering.
- Non-finite confidence can produce non-standard JSON or unstable sorting/filtering behavior.

Remediation:

- Coerce `self.type = RegionType(self.type)` in `__post_init__`.
- Validate finite `0 <= confidence <= 1`.
- Add constructor-level tests.

### 13. PP-DocLayout model boxes are not clipped to image bounds

Evidence:

- `pdomain_book_tools/layout/adapters/pp_doclayout.py:123`
- `pdomain_book_tools/layout/adapters/pp_doclayout.py:125`
- `pdomain_book_tools/layout/adapters/pp_doclayout.py:136`

The adapter converts model boxes directly into `LayoutRegion`. `LayoutRegion` clamps negative coordinates but not `R/B` beyond `image_width/image_height`.

Impact:

- Out-of-bounds model outputs can mis-tag words and produce invalid sidecar coordinates.

Remediation:

- Clip `x1/y1/x2/y2` to `[0,width]` and `[0,height]`.
- Drop/log degenerate boxes after clipping.
- Unit-test adapter post-processing with out-of-range model results.

### 14. Caption association can duplicate captions across nearby figures

Evidence:

- `pdomain_book_tools/ocr/layout_aware_reorg.py:840`
- `pdomain_book_tools/ocr/layout_aware_reorg.py:846`
- `pdomain_book_tools/ocr/layout_aware_reorg.py:879`

Each illustration region independently calls `caption_for_figure()`. Two nearby illustration regions can select the same caption words; words are purged once, then emitted multiple times as new caption blocks.

Impact:

- Downstream text/layout output can duplicate captions.

Remediation:

- Track consumed caption regions or word IDs.
- Assign each caption to one nearest or most-overlapping illustration.

### 15. Custom detector kwargs must be hashable but are not validated

Evidence:

- `pdomain_book_tools/layout/registry.py:163`
- `pdomain_book_tools/layout/registry.py:179`

Custom detector kwargs are folded into a tuple for cache lookup. Passing a dict/list value causes `_DETECTOR_CACHE.get(cache_key)` to raise `TypeError` before the factory sees it.

Impact:

- Public extension API has a confusing failure mode.

Remediation:

- Validate kwargs are hashable with a clear error, or recursively freeze common containers for cache keys.

### 16. Pydantic `Word` validation drops persisted glyph annotations

Evidence:

- `pdomain_book_tools/ocr/word.py:676`
- `pdomain_book_tools/ocr/word.py:1150`

`Word.to_dict()` serializes `glyph_annotations`, but the pydantic schema omits it. A subagent verified `TypeAdapter(Word).validate_python(w.to_dict())` accepts the extra key and returns a `Word` with `glyph_annotations is None`.

Impact:

- Pydantic/codegen consumers lose reviewed glyph metadata.

Remediation:

- Add a `GlyphAnnotations` pydantic core schema or explicit typed-dict schema.
- Include it in `Word.__get_pydantic_core_schema__`.
- Add non-empty round-trip tests.

### 17. Pydantic `Block` schema rejects its own `unmatched_ground_truth_words`

Evidence:

- `pdomain_book_tools/ocr/block.py:1053`
- `pdomain_book_tools/ocr/block.py:1288`

Runtime serialization emits `list[tuple[int, str]]`, but the schema declares a string list.

Impact:

- Valid serialized blocks from ground-truth matching fail advertised pydantic validation.

Remediation:

- Schema this as `list[tuple[int, str]]` or a list of two-item arrays.
- Add non-empty round-trip tests.

### 18. Pydantic `Page` schema rejects provenance dicts emitted by `to_dict()`

Evidence:

- `pdomain_book_tools/ocr/page.py:2726`
- `pdomain_book_tools/ocr/page.py:2728`
- `pdomain_book_tools/ocr/page.py:2730`
- `pdomain_book_tools/ocr/page.py:3557`

`Page.to_dict()` emits `provenance_live_ocr`, `provenance_saved_ocr`, and `provenance_saved` as dicts, but the pydantic schema declares nullable strings.

Impact:

- Public wire format and pydantic/codegen contract disagree.

Remediation:

- Use nullable `dict[str, Any]` schema fields or narrow runtime fields to strings.
- Add tests with dict provenance metadata.

### 19. `scale()` drops model metadata

Evidence:

- `pdomain_book_tools/ocr/document.py:85`
- `pdomain_book_tools/ocr/page.py:2685`
- `pdomain_book_tools/ocr/block.py:1006`

`Document.scale()` omits `source_identifier`; `Page.scale()` omits metadata such as image path/name/source/rotation/review/provenance/failure fields; `Block.scale()` omits sort override, unmatched GT words, additional attributes, base GT text, and review.

Impact:

- Coordinate conversion changes more than coordinates.
- Consumers can lose provenance/review metadata unexpectedly.

Remediation:

- Implement scale via `to_dict()`/`from_dict()` style deep-copy transforms, replacing only dimensions and bboxes.
- Add metadata-preservation tests.

### 20. GPU canvas supports only grayscale while CPU supports color

Evidence:

- `pdomain_book_tools/image_processing/cupy_processing/canvas.py:44`
- `pdomain_book_tools/image_processing/cupy_processing/canvas.py:55`
- `pdomain_book_tools/image_processing/cv2_processing/canvas.py:61`

CPU allocates a channel-aware canvas. GPU always allocates a 2-D canvas and assigns the input into it.

Impact:

- 3-channel CuPy images fail or require special backend handling.

Remediation:

- Mirror CPU canvas shape handling for 3-D input, or explicitly reject non-2-D input.
- Add CPU/GPU parity tests for color inputs.

### 21. CPU/GPU edge finding use different convolution boundary modes

Evidence:

- `pdomain_book_tools/image_processing/cv2_processing/edge_finding.py:48`
- `pdomain_book_tools/image_processing/cupy_processing/edge_finding.py:55`

CPU uses `np.convolve(..., mode="same")`, while GPU uses `convolve1d(..., mode="nearest")`.

Impact:

- Content touching image borders can produce different edge boxes across backends.

Remediation:

- Choose one boundary contract and implement it consistently.
- Add parity tests with content at all image edges.

### 22. Default CI/test run includes a network/model-download smoke test

Evidence:

- `tests/layout/test_pp_doclayout.py:26`
- `tests/layout/test_pp_doclayout.py:37`
- `pyproject.toml:340`
- `Makefile:70`

The slow PP-DocLayout smoke test downloads roughly 132 MB on a cold cache, but default test addopts and `make test` do not exclude slow tests.

Impact:

- Default CI can depend on Hugging Face availability and cache state.
- Cold starts are slow and potentially flaky.

Remediation:

- Exclude slow tests by default with `-m "not slow"`.
- Add a scheduled/manual integration job for model-download smoke tests.

### 23. Floating Git dependency weakens reproducibility

Evidence:

- `pyproject.toml:43`
- `pyproject.toml:85`

`python-doctr` is redirected to a Git URL without explicit revision in `pyproject.toml`. The lock pins a commit today, but `uv lock --upgrade` can move it to arbitrary upstream code.

Impact:

- Dependency upgrades can pull unreviewed source outside normal release-version review.

Remediation:

- Use a released `python-doctr` version if possible.
- Otherwise pin the Git source to an immutable tag/commit in `pyproject.toml` and document upgrade procedure.

### 24. Coverage threshold docs/tooling disagree with actual gate

Evidence:

- `pyproject.toml:114`
- `scripts/coverage_reporter.py:9`
- `README.md:117`

The real coverage gate is 87%, but the reporter and README state 80%.

Impact:

- Contributors get incorrect guidance about CI failures.

Remediation:

- Make the reporter read `tool.coverage.report.fail_under` from `pyproject.toml`.
- Update README and tests.

### 25. GPU modules are omitted from coverage despite GPU tests

Evidence:

- `pyproject.toml:100`
- `pyproject.toml:102`
- `.gitlab-ci.yml:55`

CuPy modules are omitted from coverage, and GPU CI is allowed to fail.

Impact:

- CUDA code can regress without affecting quality gates.

Remediation:

- Keep CPU coverage separate if needed, but add GPU coverage with its own threshold.

### 26. Custom layout checkpoint loading is an untrusted-model boundary

Evidence:

- `pdomain_book_tools/layout/adapters/pp_doclayout.py:70`
- `pdomain_book_tools/layout/adapters/pp_doclayout.py:85`
- `pdomain_book_tools/layout/adapters/pp_doclayout.py:86`

`checkpoint_path` can be a local directory or Hugging Face repo ID and is passed directly to `from_pretrained()`. `trust_remote_code` is not enabled, which helps, but model/config/artifact loading remains a trust and resource boundary.

Impact:

- External callers exposing this parameter can let users load large or maliciously shaped models.

Remediation:

- Document the trust boundary.
- Require explicit opt-in for remote custom repos.
- Support allowlists/pinned revisions and high-security `local_files_only=True` modes.
- Enforce artifact-size limits where practical.

### 27. Image validation accepts allowlisted extensions even when magic sniff fails

Evidence:

- `pdomain_book_tools/image_processing/formats.py:248`
- `pdomain_book_tools/image_processing/formats.py:251`

`is_image_file()` accepts a file by extension alone after warning.

Impact:

- If used for untrusted upload gating, arbitrary data named `.png` can pass into decoders and cause errors or resource consumption.

Remediation:

- Add strict mode requiring magic-byte agreement for untrusted inputs.
- Reserve extension-only acceptance for trusted local workflows.

## Low

### 28. Negative `crop_edges()` values are accepted

Evidence:

- `pdomain_book_tools/image_processing/cv2_processing/crop.py:90`
- `pdomain_book_tools/image_processing/cv2_processing/crop.py:93`
- `pdomain_book_tools/image_processing/cupy_processing/crop.py:87`
- `pdomain_book_tools/image_processing/cupy_processing/crop.py:90`

Negative edge values pass the dimension check and feed Python slicing.

Impact:

- Slice wraparound can return surprising crops or empty arrays.

Remediation:

- Validate all crop edge arguments are non-negative integers.
- Add CPU and GPU tests.

### 29. Constructors retain caller-owned mutable dicts

Evidence:

- `pdomain_book_tools/ocr/word.py:131`
- `pdomain_book_tools/ocr/block.py:227`

`Word.__init__` stores `ground_truth_match_keys` by reference, and `Block.__init__` stores `additional_block_attributes` by reference.

Impact:

- Caller mutation after construction changes model state unexpectedly.

Remediation:

- Copy or deep-copy incoming metadata dicts.
- Add aliasing tests.

### 30. Whole-log reads in AI log filter can consume excessive memory

Evidence:

- `scripts/ai_filter_log.py:72`

The script reads the entire log file before filtering.

Impact:

- Very large CI logs can consume excessive memory/CPU.

Remediation:

- Stream the file or cap accepted input size.

### 31. Developer Makefile targets interpolate untrusted variables

Evidence:

- `Makefile:234`
- `Makefile:240`
- `Makefile:257`
- `Makefile:263`

`HF_LAYOUT_UPSTREAM`, `HF_LAYOUT_FORK`, `HF_LAYOUT_MIRROR`, and `SHA` are interpolated into shell recipes.

Impact:

- If untrusted Make variables are supplied, developer-only targets can be command-injection surfaces.

Remediation:

- Validate variables with strict regexes, or move logic into Python using subprocess argument lists.

### 32. General supply-chain pins are incomplete

Evidence:

- `pyproject.toml:2`
- `pyproject.toml:18`
- `.github/workflows/ci.yml:23`
- `.github/workflows/ci.yml:25`

Build requirements and many runtime dependencies use broad lower bounds, and CI uses mutable action/tool references such as `astral-sh/setup-uv@v4` with `version: latest`.

Impact:

- Builds can change without reviewed repository diffs.

Remediation:

- Pin GitHub Actions to commit SHAs for release-critical workflows.
- Pin `uv` versions.
- Use lockfile/hash-enforced installs for releases.

### 33. Contributor setup docs use wrong uv dependency syntax

Evidence:

- `CONTRIBUTING.md:20`
- `pyproject.toml:61`

Docs say `uv sync --extra dev`, but dev dependencies are a dependency group.

Impact:

- Manual contributor setup fails.

Remediation:

- Change to `uv sync --group dev`.

### 34. Vendored SPDX data lacks visible third-party attribution metadata

Evidence:

- `pdomain_book_tools/licenses.py:15`
- `pdomain_book_tools/data/spdx_licenses.json:1`
- `LICENSE:1`

The module says SPDX data is vendored from `license-list-data`, but the data file begins directly with data and the repository license only covers the project.

Impact:

- Redistributors may not know the license/source/version of the vendored data.

Remediation:

- Add a third-party notice or adjacent metadata naming SPDX source, version/date, and license.

## Areas checked with no issue found

- `pdomain_book_tools/image_processing/external_tools.py` uses argument lists with `shell=False`; no direct shell injection was found in those subprocess calls.
- JSON file loading/saving uses `json`, not pickle; the security concern in those paths is path policy, not deserialization execution.
- `rebox_word`, `add_word_to_page`, `nudge_word_bbox`, and most `layout_aware_reorg` frame conversion paths explicitly branch on normalized versus pixel coordinates.

## Suggested fix order

1. Harden checkpoint/model loading and pin OCR model revisions.
2. Fix pixel-space training-set export and add regression tests.
3. Fix layout detector fallback cache behavior.
4. Fix crop/ROI handling for out-of-bounds and float pixel boxes.
5. Align pydantic schemas with `to_dict()` wire formats.
6. Repair GitLab/GitHub CI claims: Python version, coverage XML, GPU deps/skips, and slow test policy.
7. Address lower-severity API polish, docs, and supply-chain hardening.
