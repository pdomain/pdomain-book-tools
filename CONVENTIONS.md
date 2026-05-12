# Conventions — pd-book-tools

<!-- workspace-conventions:start -->

## Rule: No comments explaining what code does

**The rule.** Don't add comments that restate what the code does;
well-named identifiers already do that. Only add a comment when the
WHY is non-obvious: a hidden constraint, a subtle invariant, or a
workaround for a specific bug.

**Why.** Comments rot when code changes and become misleading. The rule
also applies to docstrings — one short line max; no multi-paragraph
docstrings and no multi-line comment blocks.

**Common high-confidence violations** (bot auto-fix candidates)

- One-line summary comment immediately above a function that restates its name.
- `# returns the X` or `# sets the Y` before a return/assignment statement.
- Multi-line docstrings that explain every parameter with no non-obvious WHY.
- Section divider blocks: `# ---…---` / `# ===…===` multi-line banners used as
  navigation headers in test files — class names and blank lines already
  provide structure; remove the banner, keep the blank lines.
- Multi-paragraph module or class docstrings with a "Focus on:" / "Covers:"
  section — collapse to a single-line summary.

**Common judgment-call violations** (bot flags, CT decides)

- Comments that reference the PR, issue, or task that introduced the code — belongs in commit message, not source.
- Multi-line preamble that mixes WHY (worth keeping) with WHAT (worth removing).

## Rule: Unicode escape sequences for ruff-flagged ambiguous characters

**The rule.** Characters ruff flags under RUF001/002/003 (ambiguous Unicode —
curly quotes, en-dashes, em-dashes, multiplication signs, non-breaking spaces,
etc.) must be written as `\uXXXX` escape sequences in string and docstring
literals. In comments, replace with the plain ASCII equivalent. In every case
include a short inline comment naming the character, e.g.
`"""  # LEFT DOUBLE QUOTATION MARK`.

**Why.** Literal curly quotes and dashes are visually indistinguishable from
ASCII equivalents in most editors and diff views, making string comparisons and
grep silently fragile. Escape sequences make intent explicit and are safe across
all encodings. `# noqa: RUF00x` masks the problem instead of fixing it.

**Common high-confidence violations** (bot auto-fix candidates)

- A string literal containing `"hello – world"` written with the literal
  `–` character instead of the escape sequence.
- `# noqa: RUF001`, `# noqa: RUF002`, or `# noqa: RUF003` suppressions instead
  of escape sequences.
- `RUF002` or `RUF003` added to `[tool.ruff.lint] ignore` in `pyproject.toml`
  to paper over ambiguous characters.

**Common judgment-call violations** (bot flags, CT decides)

- Test strings that intentionally exercise curly-quote round-trip through the
  OCR pipeline and must contain the literal character — keep the literal with an
  explicit `# noqa: RUF001  # intentional: testing curly-quote round-trip`
  comment that names the character and states the reason.

## Rule: Use `uv run` for all Python and tool invocation

**The rule.** Invoke Python, pytest, ruff, mypy/pyright, and any project-local
CLI through `uv run`. Never call bare `python`, `python3`, `pytest`, or
`pre-commit` from a Makefile target, CI step, or hook.

**Why.** Direct invocation skips the project's `.venv` and the lockfile-pinned
toolchain; tests pass locally and fail in CI (or vice versa) because the bare
interpreter sees different installed package versions. `uv run` is uniformly
fast (<200 ms warm) and always selects the project venv.

**Common high-confidence violations** (bot auto-fix candidates)

- `python -m pytest` or `python3 script.py` in any `Makefile`, `*.sh`,
  `.github/workflows/*.yml`, or `.pre-commit-config.yaml` hook.
- `pre-commit run` (bare) instead of `uv run pre-commit run` in CI or scripts.
- `ruff check` or `pyright` (bare) in scripts that don't activate a venv first.

**Common judgment-call violations** (bot flags, CT decides)

- One-off REPL commands typed in CT's interactive shell — out of scope for this rule.

## Rule: Design spec files live in `docs/specs/` until the milestone ships

**The rule.** A design spec file produced by `/spec-from-issue` lives at
`docs/specs/<date>-<topic>-design.md` while the milestone's chore issues are open.
When the milestone's last chore closes and the implementation lands, move the file to
`docs/architecture/` in a housekeeping commit:

```bash
git mv docs/specs/<date>-<topic>-design.md docs/architecture/
git commit -m "docs: promote <topic> spec to architecture/ (milestone shipped)"
```

Update any `Spec: docs/specs/...` pointers in still-open issues after the move.

**Why.** `docs/specs/` is the active working area — implementing agents follow `Spec:`
pointers to find their instructions. `docs/architecture/` is the permanent design record
for shipped features. Mixing shipped and in-progress specs in one directory makes it
unclear which specs are still authoritative for ongoing work.

**Common high-confidence violations** (bot auto-fix candidates)

- A spec file remaining in `docs/specs/` after its milestone's last chore issue closes.

**Common judgment-call violations** (bot flags, CT decides)

- A milestone with one chore still open but all substantive work done — CT decides
  whether to move the spec early or wait for the final chore to close.

<!-- workspace-conventions:end -->

## Rule: Never silently drop OCR words

**The rule.** Word objects classified as footnote, header, footer, or
abandoned must receive a `role` label and stay in the output. They must
never be deleted from the OCR word list, even under opt-in flags.

**Why.** Silent drops are unrecoverable at review time; mislabels can be
corrected. The role-label approach lets downstream tools (trainer, labeler)
filter by role rather than losing data permanently.

**Common high-confidence violations** (bot auto-fix candidates)

- `del page.words[i]` or `words.pop(i)` calls inside a role-classifier or filter code path.
- List comprehension that re-assigns `page.words` filtering on role/confidence without preserving the full list elsewhere.

**Common judgment-call violations** (bot flags, CT decides)

- Rendering loops that skip role-labeled words — may be intentional for display but should be explicit and documented.
- Confidence-based filtering that incidentally removes role-labeled words as a side effect.

## Rule: Never silently coerce coordinate systems

**The rule.** Functions that merge, split, or union `BoundingBox` or
`Point` objects must fail explicitly when the `is_normalized` flag
differs between operands. Do not silently coerce one to match the other.

**Why.** Silent coercions have caused incorrect region calculations that
pass all tests because both coordinates happened to round to the same
bucket. The only safe path is to surface the mismatch and let the caller
decide which coordinate system is authoritative.

**Common high-confidence violations** (bot auto-fix candidates)

- `bbox_a | bbox_b` or `BoundingBox.union(...)` implementations that
  ignore `is_normalized` on one operand.

**Common judgment-call violations** (bot flags, CT decides)

- Utility wrappers that normalize before operating — acceptable if
  the wrapper name makes the coercion explicit (e.g., `normalized_union`).

## Rule: Use `to_dict` / `from_dict` for OCR entity transformations

**The rule.** Deep-copy-safe transformations of `Page`, `Block`, `Word`,
and related OCR entities must go through `to_dict` / `from_dict`. Do not
reach into another entity's private fields or construct entities from
raw field access across module boundaries.

**Why.** The dataclass refactor (R-02) made `Page` a full `@dataclass`;
`to_dict`/`from_dict` is the stable serialization contract that absorbs
field renames without requiring callers to change.

**Common high-confidence violations** (bot auto-fix candidates)

- `Page(blocks=other_page.blocks, ...)` construction copying internals
  without going through `from_dict(other_page.to_dict())`.

**Common judgment-call violations** (bot flags, CT decides)

- Test code that constructs minimal Page/Block/Word stubs from scratch —
  acceptable as long as it doesn't reach into private fields of production objects.

## Rule: `l` is a valid loop variable for layout lines

**The rule.** The name `l` (lowercase L) is accepted as a loop variable
throughout the layout and OCR code and must not be renamed. Ruff E741
is suppressed project-wide in `pyproject.toml`.

**Why.** The variable `l` universally means "line" in this codebase and
is always paired with `.bounding_box`, `.text`, or `.minX/minY/...`.
Renaming to `ln` or `line_` throughout would be invasive churn with no
readability benefit given the established convention.

**Common high-confidence violations** (bot auto-fix candidates)

- Renaming `l` to `ln` or `line_` in a layout loop without CT review.
- Adding `# noqa: E741` on an `l` loop variable (the project-wide ignore already covers it).

**Common judgment-call violations** (bot flags, CT decides)

- Using `l` as a variable name outside a layout/line-iteration context
  where "line" is not the obvious meaning.

## Rule: Drop-cap Words are training data, not noise

**The rule.** Words tagged as drop-cap (including `ocr_confidence=None`
entries from the cursive-cap fallback) must be included in trainer
output. `ocr_confidence=None` is a weight signal, not a filter. Only
"drop cap unrecovered" entries should be excluded from training ground truth.

**Why.** Excluding drop-cap Words inflates the gap between training and
real-world page data. The cursive-cap fallback explicitly sets
`ocr_confidence=None` to signal low certainty — downstream weighting
handles this; the trainer must not silently suppress the entry.

**Common high-confidence violations** (bot auto-fix candidates)

- `if word.ocr_confidence is None: continue` inside a trainer data-export loop.
- Filtering on `word.role == "drop cap"` to exclude rather than downweight.

**Common judgment-call violations** (bot flags, CT decides)

- Aggregate statistics that exclude `ocr_confidence=None` words from mean
  calculations — may be intentional if clearly scoped to "confidence reporting."

## Rule: GPU code paths are opt-in; never assume GPU in CPU test paths

**The rule.** The `[gpu]` install extra (CuPy, opencv-cuda) is optional.
All code paths that use GPU-specific libraries must be guarded by an
availability check or placed behind the `[gpu]` extra. Test code must
not import CuPy or CUDA-specific helpers unconditionally.

**Why.** CI runs CPU-only. The `make sync-gpu` / `make dev-local` workflow
exists precisely to add GPU extras locally without polluting the canonical
lockfile. Unconditional GPU imports break CI silently.

**Common high-confidence violations** (bot auto-fix candidates)

- `import cupy` or `import cv2.cuda` at module top-level outside a `try/except ImportError` guard.
- Test files that unconditionally use CuPy helpers without `@pytest.mark.cupy`.

**Common judgment-call violations** (bot flags, CT decides)

- Feature-detection blocks that fall back to CPU silently rather than
  logging — acceptable if the fallback is correct, but may mask misconfigured environments.
