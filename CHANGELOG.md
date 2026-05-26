# Changelog

All notable changes to `pdomain-book-tools` are documented here.

Version tags follow [Semantic Versioning](https://semver.org/).
GitHub Releases (with attached wheel + sdist) are at
<https://github.com/pdomain/pdomain-book-tools/releases>.

---

## [v0.14.1] — 2026-05-23

- **Python 3.11 compat** — `typing.override` import now falls back to
  `typing_extensions.override` on Python < 3.12 (`typing.override` was
  added in 3.12; importing it bare caused `ImportError` for any downstream
  package running on 3.11).

---

## [v0.14.0] — 2026-05-22

- **PEP 561 `py.typed` marker** — downstream consumers no longer require
  `# pyright: ignore[reportMissingTypeStubs]` on `from pdomain_book_tools...`
  imports. Part of workspace-wide `reportMissingTypeStubs` cleanup.

---

## [v0.13.0] — 2026-05-22

### Added

- **Glyph-level annotations data model** (`pdomain_book_tools.ocr.glyph_annotations`)
  — `GlyphAnnotations` dataclass with per-word side-channel metadata for
  ligatures, drop-caps, and special-character vocabulary. Closes #41.
  - `LigatureKind` enum with uppercased values; `LONG_ST` replaces the old
    `long_st` name; `OE` and `AE` entries added. Closes #163.
  - `source` provenance field on `GlyphAnnotations` (commit e0fb16d).
- **Shared SPDX license allowlist** (`pdomain_book_tools.licenses`) — common
  list of approved SPDX identifiers, shared across pd-* tooling. Closes #162.

### Fixed — security review batches (#176 / #179 / #181 / #182 / #192 / #193)

- `fix(ocr)`: copy caller-owned mutable dicts in `Word`/`Block` constructors
  to prevent aliasing mutations from callers.
- `fix(ocr)`: correct `Block` schema for `unmatched_ground_truth_words` field.
- `fix(ocr)`: correct `Page` schema for `provenance` dict fields.
- `fix(layout)`: always evict cached entries on `register_detector`.
- `fix(layout)`: validate detector kwargs are hashable before cache lookup.
- `fix(layout)`: validate `LayoutRegion` type/confidence at construction.
- `fix(crop)`: reject negative `crop_edges` values.
- `fix(coverage)`: make reporter read the real gate from `pyproject.toml`.

### Fixed — other

- `fix(coverage)`: repair 0% total under `pytest-xdist` (worktree omit glob
  was too broad).
- `fix(tests)`: make HF sidecar tests deterministic under xdist (#164).
- `fix(typecheck)`: correct CuPy import suppression for `basedpyright`.
- `fix(release)`: default `RELEASE_BRANCH` to `main`.

### Chores / housekeeping

- `chore`: validate untrusted variables in developer Makefile targets.
- `chore`: cap input size in AI log filter to bound memory.
- `chore`: add third-party attribution for vendored SPDX data.
- `chore`: gitignore `.worktrees/` (agent worktree directory).
- Synced cross-repo workspace conventions and process blocks.

---

## [v0.12.0] — (prior release)

See the [v0.12.0 GitHub Release](https://github.com/pdomain/pdomain-book-tools/releases/tag/v0.12.0)
for the full set of changes included in that tag.
