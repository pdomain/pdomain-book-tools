# Lint-rule Deviations — pd-book-tools

Standing suppressions and per-file rule overrides in this repo.
Each entry records: the rule, the tool, the file(s) affected, and
the justification. Update this file whenever a new suppression is added.

---

## 1. `reportMissingImports` — basedpyright

**Files:** `pd_book_tools/image_processing/cupy_processing/_cupy_compat.py`,
`contours.py`, `edge_finding.py`, `filters.py`, `morph.py`, `rescale.py`,
`rotate.py`

**Suppression form:** `# pyright: ignore[reportMissingImports]` on each
`import cupy` / `import cupyx.*` line inside the guarded `try` block.

**Justification.** `cupy` and `cupyx` are optional `[gpu]`-extra dependencies
(see `pyproject.toml`). The import is wrapped in `try/except ImportError`
so the module loads cleanly on CPU-only installs. `require_cupy()` in each
GPU function raises a clear `ImportError` with install instructions before
any of the guarded names are ever dereferenced. basedpyright 1.39.4 does not
accept `# type: ignore[import-not-found]` (a mypy-specific code) for this
diagnostic; `# pyright: ignore[reportMissingImports]` is the correct form.
The suppression is intentionally scoped to the import lines inside the
`try` block only — no other type checking is weakened.

---

## 2. `reportConstantRedefinition` — basedpyright

**Files:**

- `pd_book_tools/image_processing/cupy_processing/_cupy_compat.py`
  (`_CUPY_AVAILABLE`, `_CUPY_IMPORT_ERROR`)
- `pd_book_tools/image_processing/cv2_processing/perspective_adjustment.py`
  (local coordinate variables in ALL_CAPS)
- `pd_book_tools/layout/types.py` (LTRB field names)
- `pd_book_tools/ocr/cv2_tesseract.py` (`_pytesseract_available` once-per-process flag)

**Suppression form:** `# pyright: ignore[reportConstantRedefinition]` inline.

**Justification.** These names follow ALL_CAPS convention for domain reasons
(LTRB bounding-box coordinates are a well-established convention; the
`_CUPY_AVAILABLE` flag needs to be re-bound in the `except` block). They are
not true module-level constants — the assignments are intentional. Renaming
to lowercase would hurt readability in context.

---

## 3. `reportOptionalMemberAccess` — basedpyright

**Files:** `pd_book_tools/ocr/reorganize_page_utils.py` (15 occurrences)

**Suppression form:** `# pyright: ignore[reportOptionalMemberAccess]` inline.

**Justification.** The suppressed accesses are all guarded by explicit
`bounding_box is not None` filter steps earlier in the same function. The
type narrowing does not survive pyright's flow analysis across the helper
functions in this module (heavy imperative mutation on filtered lists). The
suppressions are named and carry "filtered above" comments where possible.
This module is in the annotation backlog; these suppressions should be
eliminated when the module is refactored with typed containers.

---

## 4. `reportAttributeAccessIssue` — basedpyright

**Files:** `pd_book_tools/ocr/page.py`, `pd_book_tools/ocr/document.py`,
`pd_book_tools/ocr/reorganize_page_utils.py`,
`pd_book_tools/image_processing/cupy_processing/color_to_gray.py`,
`pd_book_tools/utility/ipynb_widgets.py`

**Suppression form:** `# pyright: ignore[reportAttributeAccessIssue]` inline.

**Justification.** Several categories:

- `Page`/`Block` union: both have the same `.items` setter but pyright can't
  narrow across the union assignment pattern used in `page.py`.
- `_items` internal field assignment: dataclass pattern where the setter
  assigns outside `__init__`; structurally correct but pyright doesn't
  see through the property/InitVar setup.
- `OCRProvenance | None` declared for deserialization, coerced at init;
  pyright sees the raw union type.
- CuPy stubs in `color_to_gray.py`: CuPy's bundled stubs expose
  `ndarray` as a module attribute but not as a proper class annotation target.

---

## 5. `reportOptionalCall` / `reportGeneralTypeIssues` — basedpyright

**Files:** `pd_book_tools/image_processing/cupy_processing/` (contours, edge_finding,
morph, rotate)

**Suppression form:** `# pyright: ignore[reportOptionalCall]` and
`# pyright: ignore[reportOptionalCall,reportGeneralTypeIssues]` inline.

**Justification.** The guarded cupy/cupyx names (e.g. `find_objects`,
`convolve1d`, `sliding_window_view`) are assigned `None` in the
CPU-only `except` branch. Every GPU function calls `require_cupy()`
first, which raises before these names are ever called. Pyright cannot
trace the `require_cupy()` guard as a narrowing step. These are
intentional, guarded patterns — not accidental `None` calls.

The `reportGeneralTypeIssues` variant in `contours.py` additionally
covers cupyx stubs that mistype a return as `int` where a tuple is
returned at runtime.

---

## 6. `reportArgumentType` — basedpyright

**Files:** `pd_book_tools/layout/adapters/pp_doclayout.py`,
`pd_book_tools/ocr/cv2_tesseract.py`,
`pd_book_tools/image_processing/cupy_processing/rotate.py`,
`pd_book_tools/utility/ipynb_widgets.py`

**Suppression form:** `# pyright: ignore[reportArgumentType]` inline.

**Justification.** Third-party stub mismatches:

- `transformers` stubs require `TensorType` but `torch.Tensor` is accepted at runtime.
- `transformers` stubs type `**kwargs` spread narrower than the runtime accepts.
- `pytesseract` stubs return a wider type than the actual return at runtime; guarded
  by `_pytesseract_available`.
- `cupyx` stubs type the `offset` parameter as `float` but `list[float]` is valid
  at runtime.
- `ipynb_widgets.py`: argument type swap `(bounding_box, img) → (img, bounding_box)`
  is handled by an `isinstance` guard above the suppressed call.

---

## 7. `reportReturnType` / `reportAssignmentType` — basedpyright

**Files:** `pd_book_tools/image_processing/cv2_processing/morph.py`,
`pd_book_tools/image_processing/cv2_processing/contours.py`

**Suppression form:** `# pyright: ignore[reportReturnType]` and
`# pyright: ignore[reportAssignmentType]` inline.

**Justification.** `cv2` stubs type return values as `MatLike` (an opaque
union) rather than `np.ndarray`. At runtime, `ndarray` is the concrete type.
The annotations use `ndarray` for API clarity; the suppressions bridge the
gap between the cv2 stub types and the actual values.

---

## 8. `reportFunctionMemberAccess` / `reportPrivateImportUsage` — basedpyright

**Files:** `pd_book_tools/ocr/page.py`,
`pd_book_tools/hf/download.py`,
`pd_book_tools/layout/adapters/pp_doclayout.py`

**Suppression form:** `# pyright: ignore[reportFunctionMemberAccess]` and
`# pyright: ignore[reportPrivateImportUsage]` inline.

**Justification.**

- `page.py`: runtime `__signature__` injection via `FunctionType`; valid
  at runtime, but pyright rejects attribute write on a function.
- `download.py` and `pp_doclayout.py`: `torch.tensor` and some HuggingFace
  imports are public API in practice but their stubs mark them as private.

---

## 9. `type: ignore` (unscoped) — mypy-style — basedpyright / mypy

**Files:** `pd_book_tools/geometry/bounding_box.py` (~25 occurrences),
`pd_book_tools/geometry/point.py` (7 occurrences),
`pd_book_tools/ocr/page.py`, `pd_book_tools/ocr/block.py`,
`pd_book_tools/ocr/cv2_tesseract.py`,
`pd_book_tools/image_processing/cupy_processing/threshold.py`

**Suppression form:** `# type: ignore` or `# type: ignore[...]` inline.

**Status: needs review.** These are legacy mypy-style suppressions in files
that predate the basedpyright migration (`bounding_box.py`, `point.py`).
They are in the annotation / lint backlog (see `per-file-ignores` for both
files in `pyproject.toml`). They should be converted to
`# pyright: ignore[<specific-rule>]` with justifications as each file gets
a focused pass.

---

## 10. `E741` — ruff (ambiguous variable name)

**Config:** `pyproject.toml` `[tool.ruff.lint] ignore = ["E741"]` (project-wide)

**Justification.** `l` (lowercase L) is the canonical loop variable for
"line" throughout the OCR layout code. Renaming everywhere would be invasive
churn with no readability gain — the meaning is unambiguous from context.
See `CONVENTIONS.md § Rule: \`l\` is a valid loop variable for layout lines`.

---

## 11. `E501` — ruff (line too long)

**Config:** project-wide ignore.

**Justification.** Many long docstrings, error messages, and URLs; enforcing
88-char wrapping everywhere adds noise without improving readability.

---

## 12. `PLC0415` (import-not-at-top-level) — ruff

**Config:** project-wide ignore.

**Justification.** Deferred imports are used to break circular dependency
chains (e.g. `block ↔ page` protocol types) and to avoid loading
optional-heavy modules (`cupy`, `math`, `warnings`) until needed. Moving
these to the top level would require architectural refactors not warranted
by the linting rollout.

---

## 13. `PLR0913/PLR0912/PLR0911/PLR0915` — ruff (complexity)

**Config:** project-wide ignore.

**Justification.** OCR pipeline and image-processing functions legitimately
have many arguments and high branch/return counts. Enforcing these would
require invasive config-object refactors not warranted by the linting rollout.

---

## 14. Per-file rule bundles — ruff

**Config:** `[tool.ruff.lint.per-file-ignores]` in `pyproject.toml`.

Summary of the most significant bundles:

| File(s) | Rules suppressed | Reason |
|---------|-----------------|--------|
| `tests/**/*.py` | `S101, ANN, D, PLR2004, PT011, PERF401, …` | Test idioms: assert, magic numbers, no annotation requirement |
| `scripts/*.py` | `T201, D, S607` | Scripts use `print()`; `S607` covers partial executable paths |
| `**/__init__.py` | `D104, F401, TC` | Re-export modules; `F401` is the public API surface mechanism |
| `**/_*.py` | `D` | Private modules; docstring debt deferred |
| `pd_book_tools/ocr/page.py` | `ANN, D, G, BLE001, TRY, PERF401, …` | Heavy OCR pipeline file; annotation/docstring/logging debt backlog |
| `pd_book_tools/ocr/reorganize_page_utils.py` | Same + `N803/N806/N815` | Same backlog; naming convention pre-dates style rules |
| `pd_book_tools/geometry/bounding_box.py` | `N802, F401, ANN, D, G, S108` | Pre-migration file; full annotation pass deferred |
| `pd_book_tools/image_processing/cv2_processing/perspective_adjustment.py` | `N806, ANN, D, G, BLE001, TRY, S108` | ALL_CAPS coordinate variables; annotation debt |
| `pd_book_tools/ocr/ground_truth_matching_helpers/character_groups.py` | `RUF012` | Enum members are list-typed values; `RUF012` incorrectly flags them |

---

## 15. `PERF203` — ruff (try-in-loop)

**Files:** `pd_book_tools/ocr/word.py` (3 occurrences),
`pd_book_tools/ocr/page.py` (1 occurrence)

**Suppression form:** `# noqa: PERF203` inline with comment.

**Justification.** Per-item isolation: the `try` blocks inside these loops
are intentional — one bad item must not abort the full pass. The performance
cost is acceptable for the correctness guarantee.

---

## 16. `PLR0124` — ruff (comparison-to-itself)

**Files:** `pd_book_tools/ocr/document.py` (2 occurrences)

**Suppression form:** `# noqa: PLR0124` inline.

**Status: needs review.** These suppressions predate the strict-linting
rollout. The comparisons should be audited — a comparison-to-itself is
either dead code or an identity check that should use `is`/`is not`.

---

## 17. `PLW0603` — ruff (global-statement)

**Files:** `pd_book_tools/ocr/cv2_tesseract.py` (1 occurrence),
`pd_book_tools/ocr/ground_truth_matching.py` (allowed via per-file-ignores)

**Suppression form:** `# noqa: PLW0603` inline.

**Justification.** Once-per-process notice flag: the global is assigned
exactly once at first import to record whether `pytesseract` is available.
This is the canonical pattern for optional-dependency discovery flags.

---

## 18. `ERA001` — ruff (commented-out code)

**Files:** `pd_book_tools/ocr/image_utilities.py`,
`pd_book_tools/ocr/ground_truth_matching.py`

**Suppression form:** `# noqa: ERA001` inline.

**Justification.** These are function name references and alternative
implementations kept as documented examples, not dead code awaiting
deletion. The comments are intentional and load-bearing as documentation.
