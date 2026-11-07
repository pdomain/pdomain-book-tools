---
Status: active
Owner: CT
Created: 2026-05-21
Last verified: 2026-11-07
Kind: process
---

# Lint-rule Deviations — pdomain-book-tools

This document lists every standing suppression and per-file rule override in
this repository. It covers inline `# pyright: ignore[...]`, `# type: ignore`
and `# noqa` comments, file-level `# pyright: report...=false` directives, and
the rule ignores in `pyproject.toml` (`[tool.ruff]` and `[tool.basedpyright]`).
Each entry names the rule, the files and counts, and the reason. Update this
file whenever you add or remove a suppression.

**Counts on 2026-11-07.** The library carries 122 lines with a
`# pyright: ignore` comment and `scripts/` carries none. Rule counts below can
total more than 122 because some pragmas name two rules. Tests
carry 37 `# pyright: ignore` lines, 28 `# type: ignore` lines and 11 `# noqa`
lines. The library carries 14 `# noqa` lines and `scripts/` carries 2, plus 1
`# type: ignore` in `scripts/`. Library files also carry 56 file-level
`# pyright: report...=false` directives in 17 files.

## How to re-check

Run these from the repository root. Compare the counts with this file.

```bash
# inline pyright pragmas, one line per site (library and scripts, then tests)
rg -n '#\s*pyright:\s*ignore' pdomain_book_tools scripts -g '*.py'
rg -n '#\s*pyright:\s*ignore' tests -g '*.py'

# rule totals (a pragma naming two rules counts once per rule)
rg -o --no-filename '#\s*pyright:\s*ignore\[[^]]*\]' pdomain_book_tools -g '*.py' \
  | sed 's/.*\[//;s/\]//' | tr ',' '\n' | sed 's/ //g' | sort | uniq -c | sort -rn

# file-level directives
rg -n '#\s*pyright:\s*report' pdomain_book_tools scripts tests -g '*.py'

# type: ignore and noqa
rg -n 'type:\s*ignore' pdomain_book_tools scripts tests -g '*.py'
rg -n '#\s*noqa' pdomain_book_tools scripts tests -g '*.py'
```

Then read `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.ruff.lint.per-file-ignores]`
and `[tool.basedpyright]` in `pyproject.toml` for the config-level entries.

---

## 1. `reportMissingImports` — basedpyright

**Files (8 pragmas):**
`pdomain_book_tools/image_processing/cupy_processing/contours.py` (2, lines 52
and 55), `edge_finding.py:35`, `filters.py:27`, `morph.py:28`, `rescale.py:27`,
`rotate.py:26`, and
`pdomain_book_tools/geometry_correction/backends/dewarp/_uvdoc_model.py:55`.

**Suppression form:** Add `# pyright: ignore[reportMissingImports]` to each
`import cupy` or `import cupyx.*` line inside the guarded `try` block. For a
multiline parenthesised `from ... import (...)` statement, put the comment on
the `from` line. Basedpyright flags that line because it points to the module
path, not the imported names. A comment on an imported-name line inside the
parentheses does not suppress the diagnostic.

**Justification.** `cupy` and `cupyx` are optional dependencies in the `[gpu]`
extra (see `pyproject.toml`). The `try/except ImportError` wrapper lets the
module load cleanly on CPU-only installs. Each GPU function calls
`require_cupy()` before dereferencing a guarded name. That function raises a
clear `ImportError` with installation instructions. Basedpyright 1.39.4 does
not accept the mypy-specific `# type: ignore[import-not-found]` code for this
diagnostic. The correct form is
`# pyright: ignore[reportMissingImports]`. The suppression applies only to
import lines inside the `try` block, so it weakens no other type checking.

**`_uvdoc_model.py`.** `onnxruntime` is imported inside `run_uvdoc()`, so it
loads only when the dewarp extra is installed. The pragma has the comment
"lazy: only when the extra is installed".

**2026-07-15 update — local `typings/cupy` / `typings/cupyx` stubs added.**
Local stubs under `typings/` (basedpyright's default `stubPath`) now resolve
`cupy` and `cupyx.scipy.ndimage` regardless of whether the `[gpu]` extra is
actually installed, so most `reportMissingImports` suppressions on these
imports became unnecessary and were removed from
`_cupy_compat.py`, `denoise.py`, and
`pdomain_book_tools/geometry_correction/transforms.py`. The six `cupy_processing`
files above keep the pragma only because each one also carries a file-level
`# pyright: reportUnnecessaryTypeIgnoreComment=false` directive (see section
18). That directive hides basedpyright's own check of whether the pragma is
still needed, so it cannot be verified as unnecessary from tool output and is
left in place rather than removed on assumption. Re-evaluate these once the
file-level directives are narrowed or removed.

---

## 2. `reportConstantRedefinition` — basedpyright

**Files (4 pragmas):**

- `pdomain_book_tools/image_processing/cupy_processing/_cupy_compat.py:41-42`
  (`_CUPY_AVAILABLE`, `_CUPY_IMPORT_ERROR`)
- `pdomain_book_tools/image_processing/cupy_processing/color_to_gray.py:110`
  (`_RGBA_NOTICE_LOGGED`)
- `pdomain_book_tools/ocr/cv2_tesseract.py:72` (`_RGBA_NOTICE_LOGGED`)

Tests add 1 more (see section 22).

**Suppression form:** `# pyright: ignore[reportConstantRedefinition]` inline.

**Justification.** These names use ALL_CAPS but are not true constants. The
`except ImportError` block in `_cupy_compat.py` rebinds the two cupy flags. The
two `_RGBA_NOTICE_LOGGED` flags are set once per process, after the first
notice is logged. Lowercase names would hide that they are module-level state.

---

## 3. `reportOptionalMemberAccess` — basedpyright

**Files (20 pragmas):** `pdomain_book_tools/ocr/reorganize_page_utils.py` (18:
lines 548, 549, 559, 560, 568, 569, 596, 597, 607, 615, 616, 1699, 2532-2535,
3755, 3756), `pdomain_book_tools/ocr/cv2_tesseract.py` (2: lines 96 and 102).

**Suppression form:** `# pyright: ignore[reportOptionalMemberAccess]` inline.

**Justification.** In `reorganize_page_utils.py`, an earlier step in the same
function filters out items whose `bounding_box` is `None`, and every suppressed
access relies on that filter. Pyright's flow analysis does not carry the
narrowing through the filtered lists. The pragmas carry comments such as
"filtered to non-None above" or "same filter". The module remains in the
annotation backlog. Refactoring it with typed containers should remove these.
In `cv2_tesseract.py`, `pytesseract` is `None` when it is not installed, and
the `_pytesseract_available` check above each call guards it.

---

## 4. `reportOptionalCall` — basedpyright

**Files (20 pragmas):** under
`pdomain_book_tools/image_processing/cupy_processing/`: `contours.py` (4: lines
105, 109, 180, 195), `filters.py` (3: 64, 85, 107), `denoise.py` (2: 110, 117),
`morph.py` (2: 57, 89), `rotate.py` (2: 93, 103), `rescale.py` (2: 98, 101),
`edge_finding.py` (2: 81, 82). Also
`pdomain_book_tools/image_processing/grayscale_pipeline/ops_gpu.py:164` and
`pdomain_book_tools/ocr/cv2_tesseract.py` (2: lines 92, 98).

**Suppression form:** `# pyright: ignore[reportOptionalCall]` inline. Lines 105
and 180 in `contours.py` also name `reportOperatorIssue`, counted in section 5.

**Justification.** The CPU-only `except` branch assigns `None` to guarded
cupy/cupyx names such as `find_objects`, `convolve1d`, and
`sliding_window_view`. Every GPU function first calls `require_cupy()`, which
raises before any of these names can be called. Pyright cannot treat that
guard as a narrowing step. In `cv2_tesseract.py` the guard is the
`_pytesseract_available` check above the call. These calls are intentionally
guarded, not accidental calls to `None`.

---

## 5. `reportOperatorIssue` — basedpyright

**Files (28 pragmas):** `cupy_processing/threshold.py` (12: lines 47, 48, 49,
98, 115, 215, 261, 263, 266, 307, 308, 311), `color_to_gray.py` (6: 38, 39,
137, 141, 146, 150), `denoise.py` (2: 114, 129),
`edge_finding.py` (2: 84, 85), `contours.py` (2: 105, 180), `invert.py:25`,
`textline_dewarp.py:284`, and
`grayscale_pipeline/ops_gpu.py` (2: 167, 168). All paths are under
`pdomain_book_tools/image_processing/`.

**Suppression form:** `# pyright: ignore[reportOperatorIssue]` inline. The two
`contours.py` lines combine it with `reportOptionalCall`.

**Justification.** The local CuPy stubs type arrays as an NDArray-like alias
that does not declare the arithmetic and comparison operators. CuPy supports
them at runtime. Most pragmas say "CuPy arithmetic on NDArray-like alias" or
"CuPy comparison on NDArray-like alias". `textline_dewarp.py:284` points to the
CuPy stub module docstring. The `denoise.py` and `threshold.py` lines without a
comment (denoise 114 and 129; threshold 215, 261, 263, 266, 307, 308, 311)
are the same pattern: `**`, `-` or `*` on CuPy arrays.

---

## 6. `reportArgumentType` and `reportCallIssue` — basedpyright

**Files:** 12 `reportArgumentType` and 4 `reportCallIssue` pragmas.

| File | Line | Rules | Reason |
|---|---|---|---|
| `layout/registry.py` | 137, 160 | ArgumentType | A `**kwargs` spread of mixed float/int detector parameters cannot be checked statically. |
| `ocr/block.py` | 1142 | ArgumentType | Accepts the serialized bbox dict shape. |
| `ocr/page.py` | 3294 | ArgumentType | Accepts the serialized bbox dict shape. |
| `ocr/word.py` | 736, 743 | ArgumentType | Accepts the serialized bbox dict shape. |
| `utility/ipynb_widgets.py` | 144 | ArgumentType | The `(bounding_box, img)` to `(img, bounding_box)` swap is handled by an `isinstance` guard above the call. |
| `image_processing/cupy_processing/color_to_gray.py` | 51, 63 | CallIssue, ArgumentType | CuPy advanced indexing is broader than the NumPy alias. |
| `image_processing/cupy_processing/color_to_gray.py` | 156 | ArgumentType | Same CuPy indexing reason. |
| `image_processing/cupy_processing/denoise.py` | 135 | ArgumentType, CallIssue | `keep[labels_raw]` fancy indexing works in CuPy; the NumPy stubs do not model it. |
| `image_processing/cupy_processing/textline_dewarp.py` | 252 | CallIssue, ArgumentType | Generic-dtype fallback array; see the CuPy stub module docstring. |

All paths are under `pdomain_book_tools/`. **Suppression form:** inline
`# pyright: ignore[...]`.

---

## 7. `reportAttributeAccessIssue` — basedpyright

**Files (2 pragmas):** `pdomain_book_tools/ocr/page.py:937` and `:982`. Both
also name `reportPrivateUsage` (section 8). Tests add 19 more (section 22).

**Suppression form:** `# pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]`.

**Justification.** `Block._items` can hold `Block` or `Word`, and the fallback
code mutates `Page` or `Block` storage directly. Pyright cannot narrow the
union at that point.

---

## 8. `reportPrivateUsage` — basedpyright

**Files (6 pragmas):** `pdomain_book_tools/ocr/page.py:937` and `:982` (with
section 7), `ocr/block.py:1429` and `:1430`, `ocr/reorganize_page_utils.py:496`,
`geometry/bounding_box.py:28`.

**Justification.**

- `block.py`: shared internal tree-mutation helper reads `block._items`.
- `reorganize_page_utils.py`: the purge must operate on the live top-level
  block list.
- `page.py`: see section 7.
- `bounding_box.py`: imports `_BoundingBoxDict` from
  `pdomain_book_contracts.geometry.bounding_box`. Reason not recorded in the
  code; the name is private in the contracts package.

The tests execution environment turns this rule off (section 19).

---

## 9. `reportPrivateImportUsage` — basedpyright

**Files (2 pragmas):** `pdomain_book_tools/hf/download.py:109`
(`EntryNotFoundError` from `huggingface_hub.utils`) and
`pdomain_book_tools/image_processing/formats.py:65`
(`_pillow_heif.register_heif_opener()`, with `reportUnknownMemberType`).

**Justification.** `huggingface_hub.utils` and `pillow_heif` expose these names
at runtime but do not list them in `__all__`, so pyright treats them as
private. For `formats.py` the code comment says `pillow_heif.as_plugin`
declares no `__all__` and is typed `(**kwargs: Unknown) -> None`. The
`download.py` pragma has no comment (reason not recorded).

---

## 10. `reportUnnecessaryComparison` — basedpyright

**Files (7 pragmas):** `pdomain_book_tools/geometry/image_ops.py` (109, 263),
`pdomain_book_tools/ocr/image_utilities.py` (161, 191, 199, 209, 217).

**Justification.** `cv2.findNonZero` returns `None` at runtime when no pixel is
non-zero, but the cv2 stubs type it as non-optional. The `image_utilities.py`
checks are defensive: `BoundingBox.refine` is typed to return a non-optional
`BoundingBox`, yet tests monkey-patch it to return `None`, and
`word.bounding_box` may be `None` despite the declared type.

---

## 11. `reportUnreachable` — basedpyright

**Files (4 pragmas):** `pdomain_book_tools/hf/download.py:27`,
`pdomain_book_tools/layout/registry.py:334`,
`pdomain_book_tools/ocr/image_utilities.py` (192, 210).

**Justification.** The suppressed lines are defensive branches that the declared
types say cannot run: the `typing_extensions` fallback import for older Python
in `download.py`, the `callable(factory)` check in `register_detector`, and the
`bounding_box is None` guards in `image_utilities.py` (paired with section 10).
They protect callers who violate the types at runtime.

---

## 12. `reportUnnecessaryIsInstance` — basedpyright

**Files (2 pragmas):** `pdomain_book_tools/layout/registry.py:326`,
`pdomain_book_tools/ocr/page.py:1654`.

**Justification.** Defensive runtime guards. `register_detector` validates a
`key` that callers could pass with the wrong type, and the `page.py` check
confirms each entry in `lines` is a `Block`. The type checker proves both
redundant statically; the code keeps them as protection against runtime misuse.

---

## 13. `reportImplicitOverride` — basedpyright

**Files (3 pragmas):** `pdomain_book_tools/ocr/page.py` (213, 226),
`pdomain_book_tools/ocr/block.py:279`.

**Justification.** These are dunder methods (`__eq__` and similar) that
override `object`. `pyproject.toml` enables `reportImplicitOverride = true`,
and these methods carry the pragma instead of an `@override` decorator. The
`page.py:226` and `block.py:279` lines also carry a `# pragma: no cover`
comment. Reason for choosing the pragma over `@override` is not recorded.

---

## 14. `reportMissingTypeStubs` — basedpyright

**Files (3 pragmas):** `pdomain_book_tools/ocr/block.py:12`,
`pdomain_book_tools/ocr/word.py:13` (both `thefuzz.fuzz`, "no upstream stubs"),
`pdomain_book_tools/image_processing/formats.py:73` (`pillow_avif`).

**Justification.** The third-party package ships no type stubs. The file-level
`reportMissingTypeStubs=false` directives in the cupy files are listed in
section 18.

---

## 15. `reportUnusedImport` — basedpyright

**Files (3 pragmas):** `pdomain_book_tools/ocr/image_utilities.py:8`,
`pdomain_book_tools/ocr/word.py:18` (both import `image_ops`),
`pdomain_book_tools/image_processing/formats.py:73` (`pillow_avif`).

**Justification.** Import for side effect. Importing `geometry.image_ops`
registers the `BoundingBox` image-ops provider that `refine()`, `crop_bottom()`
and `crop_top()` dispatch through. Importing `pillow_avif` registers the AVIF
plugin. The first two lines also carry `# noqa: F401` (section 32).

---

## 16. `reportUnknownVariableType` — basedpyright

**Files (3 pragmas):** `pdomain_book_tools/ocr/block.py:13`,
`pdomain_book_tools/ocr/word.py:14` (`ratio` from `thefuzz.fuzz`, "no upstream
stubs"), `pdomain_book_tools/hf/download.py:76` (`hf_hub_download` from
`huggingface_hub`).

**Justification.** The imported name has no usable type information. The
`download.py` pragma has no comment (reason not recorded).

---

## 17. `reportUnknownMemberType` — basedpyright

**Files (1 pragma):** `pdomain_book_tools/image_processing/formats.py:65`,
together with `reportPrivateImportUsage` (section 9).

**Justification.** `pillow_heif.register_heif_opener` is typed
`(**kwargs: Unknown) -> None`, as the code comment above it explains.

---

## 18. File-level `# pyright: report…=false` directives — basedpyright

**Files (17 files, 56 directives).** All use the form
`# pyright: reportXxx=false` at the top of the file.

| File (under `image_processing/`) | Rules turned off |
|---|---|
| `cupy_processing/contours.py` | Any, MissingTypeStubs, UnknownArgumentType, UnknownMemberType, UnknownVariableType, UnnecessaryCast, UnnecessaryTypeIgnoreComment |
| `cupy_processing/threshold.py` | Any, ImplicitStringConcatenation, UnknownArgumentType, UnknownMemberType, UnknownVariableType |
| `cupy_processing/edge_finding.py` | MissingTypeStubs, UnknownArgumentType, UnknownMemberType, UnknownVariableType, UnnecessaryTypeIgnoreComment |
| `cupy_processing/filters.py` | MissingTypeStubs, UnknownMemberType, UnknownVariableType, UnnecessaryCast, UnnecessaryTypeIgnoreComment |
| `cupy_processing/rescale.py` | Any, MissingTypeStubs, UnknownMemberType, UnknownVariableType, UnnecessaryTypeIgnoreComment |
| `cupy_processing/morph.py` | MissingTypeStubs, UnknownMemberType, UnknownVariableType, UnnecessaryTypeIgnoreComment |
| `cupy_processing/rotate.py` | MissingTypeStubs, UnknownMemberType, UnknownVariableType, UnnecessaryTypeIgnoreComment |
| `cupy_processing/denoise.py` | MissingTypeStubs, UnknownMemberType, UnknownVariableType |
| `cupy_processing/colors.py` | UnknownMemberType, UnnecessaryCast |
| `cupy_processing/color_to_gray.py` | UnknownArgumentType, UnknownMemberType |
| `cupy_processing/canvas.py`, `deskew.py`, `invert.py`, `split.py`, `whitespace.py` | UnknownMemberType, UnknownVariableType |
| `cupy_processing/crop.py` | UnknownMemberType |
| `grayscale_pipeline/ops_gpu.py` | UnknownMemberType, UnknownVariableType, UnnecessaryCast |

Rule names above drop the `report` prefix.

**Justification.** CuPy and cupyx do not ship complete type information. The
local `typings/` stubs cover only part of the API, so calls into them yield
unknown member and variable types, and strict mode would flag each one. The
directives keep these modules at zero diagnostics. `reportAny=false` appears
where code passes CuPy values through `Any`. `reportUnnecessaryCast=false`
appears where casts to the `CuPyArray` alias look redundant to the checker.

`reportUnnecessaryTypeIgnoreComment=false` (in `contours.py`, `edge_finding.py`,
`filters.py`, `morph.py`, `rescale.py`, `rotate.py`) is different: it stops
basedpyright from reporting stale pragmas. It is the reason the section 1
pragmas cannot be verified as needed. Reason for adding it to each file is not
recorded beyond the section 1 note. `threshold.py` also turns off
`reportImplicitStringConcatenation`; reason not recorded.

---

## 19. `reportPrivateUsage` — basedpyright (tests only)

**Files:** all of `tests/` (execution-environment override in
`pyproject.toml`, `[[tool.basedpyright.executionEnvironments]]` `root = "tests"`).

**Suppression form:** `reportPrivateUsage = "none"` in the tests execution
environment — no inline pragmas.

**Justification.** Unit tests legitimately exercise private helpers
(`_normalize_label`, `_detect_columns`, and similar) to pin behavior that
has no public entry point. Requiring public re-exports for test access
would widen the library's API surface for no consumer benefit. The
override is scoped to `tests/`; library and script code keep
`reportPrivateUsage` at strict's error level. Added 2026-07-15 as part of
the recommended→strict migration.

---

## 20. `reportMissingModuleSource` — basedpyright

- `pdomain_book_tools/geometry_correction`
- `pdomain_book_tools/image_processing/cupy_processing`
- `pdomain_book_tools/image_processing/grayscale_pipeline`
- `tests`

**Suppression form:** `reportMissingModuleSource = "none"` in only those
execution environments; no inline pragmas.

**Justification.** The `[gpu]` extra is optional, so CPU-only CI does not
install the CuPy runtime. Local `typings/cupy` and `typings/cupyx` stubs still
provide the checked API surface, but basedpyright reports a warning when it
cannot also find runtime source. With `failOnWarnings = true`, that expected
warning made the CPU-only gate fail even though type resolution succeeded.

The three source roots contain the optional GPU integration points. Tests also
import CuPy to select or skip GPU-only cases. Outside those roots, the
missing-runtime-source diagnostic remains enabled for mandatory dependencies.
Within them, missing imports, unknown or incompatible types, and every other
strict diagnostic stay enabled. GPU runtime behavior remains covered by the
opt-in GPU dependency and test paths. Added 2026-07-19 after reproducing the
protected CI failure.

---

## 21. `reportImportCycles` — basedpyright

**Config:** `reportImportCycles = "none"` under `[tool.basedpyright]`
(project-wide).

**Justification.** Import cycles are structural (geometry and OCR protocol
types) and are resolved with `TYPE_CHECKING` guards. A real import-order
problem would surface as a runtime `ImportError`.

---

## 22. Deliberate-invalid-input pragmas in tests — basedpyright

**Files (37 pragmas across 14 files under `tests/`):**
`reportAttributeAccessIssue` (19), `reportArgumentType` (13),
`reportCallIssue` (4), `reportConstantRedefinition` (1). The most pragmas are
in `tests/ocr/test_word_coverage.py` (9), `tests/ocr/test_block.py` (5),
`tests/test_page_behavior_pin.py` (3), `tests/ocr/test_page_coverage_ops.py`
(3), `tests/ocr/test_ground_truth_matching_coverage.py` (3) and
`tests/geometry/test_point.py` (3).

**Suppression form:** one narrow inline pragma per call site.

**Justification.** Some tests intentionally pass statically-invalid values
to exercise a runtime guard or a back-compat coercion (for example a
`TypeError` raise on a wrong-typed argument, `OCRProvenance.__post_init__`
coercing a list to a tuple, or monkey-patching a non-optional attribute to
`None`). The static error is real and correct; the test's purpose is the
runtime path behind it. Pragmas are per-line, never file-level, and
`reportUnnecessaryTypeIgnoreComment = true` deletes any that go stale.
Added 2026-07-15 during the recommended→strict migration.

---

## 23. `type: ignore` — mypy-style

**Files (29 lines):**

- `scripts/check_layout_fork.py:25` — `[reportPrivateImportUsage,no-redef]`. The
  fallback import of `HfHubHTTPError` from the older `huggingface_hub.utils`
  path (comment: "older versions").
- `tests/` (28 lines): `[arg-type]` (11), `[assignment]` (7), bare
  `# type: ignore` (4, all in `tests/geometry/test_point.py`), `[union-attr]`
  (2), `[list-item]` (2), `[call-arg]` (1), `[attr-defined]` (1).

**Justification.** The library has none. Basedpyright honors `# type: ignore`,
so these silence the same errors a `# pyright: ignore` would. In tests they
mark deliberately wrong arguments or assignments that exercise a runtime check
(`point_factory("1", 2)`, `w.bounding_box = None`, `Page(blocks=["notablock"])`).
The `[union-attr]` lines in `test_scale_metadata_preservation.py` access
`.review.validated` on an optional field.

**History.** An earlier audit removed every unscoped `# type: ignore` from
`pdomain_book_tools/` after `basedpyright … --level error` produced 0 errors
without them. None remain in the library. New code should prefer a scoped
`# pyright: ignore[rule]`.

---

## 24. `E741` — ruff (ambiguous variable name)

**Config:** `pyproject.toml` `[tool.ruff.lint] ignore = ["E741"]` (project-wide)

**Justification.** `l` (lowercase L) is the canonical loop variable for
"line" throughout the OCR layout code. Renaming everywhere would be invasive
churn with no readability gain — the meaning is unambiguous from context.
See `CONVENTIONS.md § Rule: \`l\` is a valid loop variable for layout lines`.

---

## 25. `E501` — ruff (line too long)

**Config:** project-wide ignore.

**Justification.** Many long docstrings, error messages, and URLs; enforcing
88-char wrapping everywhere adds noise without improving readability.

---

## 26. `PLC0415` (import-not-at-top-level) — ruff

**Config:** project-wide ignore.

**Justification.** Deferred imports are used to break circular dependency
chains (e.g. `block ↔ page` protocol types) and to avoid loading
optional-heavy modules (`cupy`, `math`, `warnings`) until needed. Moving
these to the top level would require architectural refactors not warranted
by the linting rollout.

---

## 27. Other project-wide ruff ignores

**Config:** `[tool.ruff.lint] ignore` in `pyproject.toml`. Sections 24, 25 and
26 cover E741, E501 and PLC0415. The rest:

| Rules | Reason |
|---|---|
| `PLR0913` | OCR and image functions legitimately take many parameters. |
| `PLR0912`, `PLR0911`, `PLR0915` | OCR pipeline functions have high branch, return and statement counts. Enforcing them needs invasive refactors. |
| `PLR2004` | Magic-value comparisons are common in OCR geometry and threshold code. |
| `D203`, `D212` | Each conflicts with its pair (`D211`, `D213`); one of each pair is kept. |
| `D100`, `D104`, `D107`, `D105` | Missing docstrings on modules, packages, `__init__` and magic methods. Add incrementally. |
| `D205` | Blank line after the docstring summary is too noisy to enforce across the backlog. |
| `TRY003` | Too noisy for a library that uses f-string error messages. |
| `COM812` | Conflicts with the ruff formatter. |
| `ANN401` | Some functions legitimately accept or return `Any` (JSON readers, dispatch helpers). |

---

## 28. Per-file rule bundles — ruff

**Config:** `[tool.ruff.lint.per-file-ignores]` in `pyproject.toml`, 71
entries on 2026-11-07. Re-read the table in `pyproject.toml` for the full
list. Every entry has a comment or sits under one that explains it.

| File(s) | Rules suppressed | Reason |
|---------|-----------------|--------|
| `typings/**/*.pyi` | `N801` | Stubs must mirror the real library's names, such as lowercase `cupy.ndarray`. |
| `tests/**/*.py` | `S101, S105, S106, S311, T201, ANN, D, PLR2004, PT011, S108, PLR0133, PLW2901, PERF401, PLR0917` | Test idioms: assert, magic numbers, no annotation requirement, fixture secrets. `PLR0917` is in section 36. |
| 17 named test files | `N802, N803, N806, N814, N818, B017, E402, F401, T201` | Camel-case coordinate API names, an import placed after `importorskip`, intentional broad `Exception`, debug prints; each line in `pyproject.toml` has its reason. |
| `scripts/*.py` | `T201, D, S607` | Scripts use `print()`; `S607` covers partial executable paths. |
| `**/__init__.py` | `D104, F401, TC` | Re-export modules; `F401` is the public API surface mechanism. |
| `**/_*.py` | `D` | Private modules; docstring debt deferred. |
| 48 library files in `ocr/`, `geometry/`, `hf/`, `pgdp/`, `layout/`, `utility/` and `image_processing/` | Mix of `ANN, D, G003, G004, BLE001, TRY, PERF401, N8xx, S108, E402, F401` | Annotation, docstring and logging-format debt backlog; naming conventions that pre-date the style rules. Add files individually as each gets a focused pass. |
| `pdomain_book_tools/ocr/ground_truth_matching.py` | `ANN, D, ERA, G003, G004, BLE001, TRY, PERF401, PLW0603` | Same backlog; also covers the commented-out example code and a global flag. |
| `pdomain_book_tools/image_processing/external_tools.py` | `N803, ANN, D, G003, G004, BLE001, S607, S603` | Wraps optipng and gegl; both calls pass `shell=False` with an argv list, so there is no shell to inject into. |
| `pdomain_book_tools/pgdp/pgdp_page_image.py` | `ANN, D, G003, G004, BLE001, TRY, S314, S307` | Backlog bundle that also covers XML parsing and `eval`; reason for `S314` and `S307` not recorded. |
| `pdomain_book_tools/hf/download.py` | `N806, ANN, D, G003, G004, BLE001, TRY, S110` | Backlog bundle; `S110` covers a silent `except ... pass`. |
| `pdomain_book_tools/ocr/ground_truth_matching_helpers/character_groups.py` | `RUF012` | Enum members are list-typed values; `RUF012` incorrectly flags them. |

---

## 29. `N802` — ruff (inline)

**Files (4 noqa):** `pdomain_book_tools/ocr/reorganize_page_utils.py` (94, 97,
100, 103).

**Justification.** `_BBoxLike` is a `Protocol` whose properties `minX`, `minY`,
`maxX` and `maxY` must match `BoundingBox`'s camelCase attribute names. Renaming
them would break the structural match. Tests that use this API are covered by
per-file ignores in section 28.

---

## 30. `PLW0603` — ruff (global-statement)

**Files (4 noqa):** `pdomain_book_tools/ocr/cv2_tesseract.py:67` and
`pdomain_book_tools/image_processing/cupy_processing/color_to_gray.py:103`
(`_RGBA_NOTICE_LOGGED`, "once-per-process notice flag"),
`pdomain_book_tools/image_processing/cupy_processing/colors.py:31`
(`_bgr2gray_weights_cache`, "lazy singleton — avoids CuPy import on module
load"), `pdomain_book_tools/geometry_correction/registry.py:78`
(`_defaults_loaded`; no comment). `ocr/ground_truth_matching.py` is covered by
a per-file ignore instead of an inline comment.

**Justification.** Each global is a module-level once-only flag or lazy cache.
The `registry.py` flag guards the idempotent `ensure_defaults()` call.

---

## 31. `ERA001` — ruff (commented-out code)

**Files (2 noqa in the library):** `pdomain_book_tools/ocr/image_utilities.py:136`
("function name references, not dead code"),
`pdomain_book_tools/image_processing/cupy_processing/colors.py:22`
("mathematical formula, not dead code"). Tests add 3 (section 34).
`ocr/ground_truth_matching.py` has `ERA` in its per-file ignores.

**Justification.** These comments are documentation, not code awaiting deletion.

---

## 32. `F401` — ruff (unused import, inline)

**Files (2 noqa):** `pdomain_book_tools/ocr/image_utilities.py:8`,
`pdomain_book_tools/ocr/word.py:18`.

**Justification.** The `image_ops` import registers the `BoundingBox` image-ops
provider that `refine()`, `crop_bottom()` and `crop_top()` dispatch through.
These lines also carry `reportUnusedImport` (section 15).

---

## 33. Single-site ruff `noqa` in the library and scripts

| Rule | Site | Reason |
|---|---|---|
| `S110` | `pdomain_book_tools/hf/models.py:122` | Absence of the optional `transformers` package is ignored on purpose; the block silently does nothing. |
| `S314` | `scripts/coverage_reporter.py:45` | The XML source is the local, CI-generated `coverage.xml`, not user input. |
| `BLE001` | `scripts/coverage_reporter.py:51` | Final fallback: any parse failure returns `None`. |
| `SIM103` | `pdomain_book_tools/layout/adapters/pp_doclayout.py:103` | Windows drive-letter check kept as `if ... return True` / `return False`. No comment in code; the form is readable as written. |

---

## 34. `noqa` in tests

**Files (11 noqa under `tests/`):** `ERA001` (3: `ocr/test_word.py:62`,
`ocr/test_ground_truth_matching_coverage.py:367`,
`image_processing/cv2_processing/test_whitespace.py:47`), `E402` (2:
`geometry_correction/test_protocols_registry.py:47-48`), `S603`
(`utility/test_makefile_var_validation.py:23`), `S307`
(`test_geometry_repr.py:11`), `RUF012`
(`ocr/test_ground_truth_matching_coverage.py:78`), `N803`
(`utility/test_timing.py:29`), `B018` (`test_public_api.py:145`), `B009`
(`geometry/test_point.py:325`).

**Justification.** Each line carries or sits next to its reason: section-header
or arithmetic comments that look like code; imports after a guard; a
deliberately dynamic `getattr` or bare attribute access that triggers
`__getattr__`; `eval(repr(bb))` to prove repr is eval-safe; a mutable default
in a test stub. `S603` and `E402` have no comment (reason not recorded for
`S603`).

---

## 35. Markdown excluded from the formatter — ruff

**Config:** `extend-exclude = ["*.md"]` under `[tool.ruff]` in `pyproject.toml`.

**Justification.** Ruff 0.16 began formatting Python code fences inside
Markdown. On this repo that reached nine files and no Python at all: `README.md`,
`GPU_TESTING.md`, `docs/usage/geometry-correction.md`, and six specs under
`docs/specs/`.

Those fences are written to be read, not run. Several align trailing comments
so a reader can scan them, and the formatter collapses that alignment. Six of
the nine are governed specs still carrying unresolved owner decisions, so
reformatting them would put tooling churn into documents that are under review.

Markdown in this repo is already owned by markdownlint and docgraph. A second
formatter with a different idea of correct style produces recurring diffs for
no gain in shipped code. Added 2026-08-08, during the ruff 0.15 → 0.16 upgrade.

---

## 36. `PLR0917` — ruff (too-many-positional-arguments), tests only

**Justification.** Ruff 0.16 promoted `PLR0917` from preview to stable, and it
fired 37 times. The 20 hits in library code were fixed properly, by making the
excess parameters keyword-only rather than suppressing the rule. Nothing in
`pdomain_book_tools/` suppresses it.

The suppression covers one case that a signature change cannot fix. In
`tests/ocr/test_cv2_tesseract.py`, eight test methods stack three or four
`@patch` decorators, and `unittest.mock` injects one positional mock argument
per decorator. The positional count is a consequence of the decorators, not a
choice the test author can reduce.

The other nine test hits were fixed properly and are not covered by this entry.
Added 2026-08-08, during the ruff 0.15 → 0.16 upgrade.

---

## 37. `PLR0124` — ruff (comparison-to-itself) — RESOLVED

**Files (historical):** `pdomain_book_tools/ocr/document.py` (2 occurrences)

**Resolution.** The two suppressed comparisons were `val != val` and
`f != f` in `Document._tesseract_text` and
`Document._tesseract_confidence`. They used the classic NaN test. Both sites now
use `math.isnan(...)`, which is clearer and needs no suppression. Regression
tests cover NaN handling for both helpers in `tests/ocr/test_document.py`
(`test_tesseract_confidence_treats_nan_as_none`,
`test_tesseract_text_treats_nan_as_empty_string`). No `PLR0124` remains.

---

## Needs a reason

These suppressions have no comment in the code and no reason that the code makes
certain. Add a comment at the site or remove the suppression.

- `pdomain_book_tools/ocr/page.py:213` — `reportImplicitOverride` on `__eq__`
  (why a pragma rather than `@override`).
- `pdomain_book_tools/ocr/page.py:226`, `pdomain_book_tools/ocr/block.py:279` —
  same question for the other dunder overrides.
- `pdomain_book_tools/geometry/bounding_box.py:28` — `reportPrivateUsage` on
  `_BoundingBoxDict`.
- `pdomain_book_tools/hf/download.py:76`, `:109`, `:27` — no comment on the
  three pragmas.
- `pdomain_book_tools/image_processing/cupy_processing/threshold.py` — file-level
  `reportImplicitStringConcatenation=false`.
- The `reportUnnecessaryTypeIgnoreComment=false` directive in six cupy files
  (section 18).
- `pdomain_book_tools/pgdp/pgdp_page_image.py` — per-file `S314` and `S307`.
- `tests/utility/test_makefile_var_validation.py:23` — `S603`.
- `pdomain_book_tools/geometry_correction/registry.py:78` and
  `pdomain_book_tools/layout/adapters/pp_doclayout.py:103` — `noqa` with no
  comment.
