---
status: "Plan — awaiting CT approval before any implementation"
created: 2026-05-22
repo: pd-book-tools
issue: "ConcaveTrillion/pd-book-tools#163"
---

# Plan: Reconcile GlyphAnnotations with pd-ocr-labeler-spa spec 20

> **Status**: Draft — awaiting CT approval. **DO NOT implement until approved.**
> **Issue**: ConcaveTrillion/pd-book-tools#163
> **Spec cross-ref**: `pd-book-tools/docs/specs/05-glyph-annotations.md`
> **SPA spec cross-ref**: `pd-ocr-labeler-spa/specs/20-glyph-annotations.md`

---

## 1. Context

The shipped `pd_book_tools.ocr.glyph_annotations` module (landed via
`#41`, `675ad76`) diverges from the pd-ocr-labeler-spa spec 20 §3 in
two design dimensions. This plan documents the divergences, the
decision options, and a proposed migration path. **No enum values or
data-model fields are changed until this plan is approved.**

---

## 2. Divergence A — LigatureKind vocabulary and casing

### 2.1 Current state (pd-book-tools, shipped)

```python
class LigatureKind(str, Enum):
    FI = "fi"
    FL = "fl"
    FF = "ff"
    FFI = "ffi"
    FFL = "ffl"
    CT = "ct"
    ST = "st"
    LONG_S_T = "long_s_t"    # ← note underscore, lowercase value
    LONG_S_S = "long_s_s"    # ← not in SPA spec
    LONG_S_I = "long_s_i"    # ← not in SPA spec
    SP = "sp"                # ← not in SPA spec
    QU = "qu"                # ← not in SPA spec
```

### 2.2 SPA spec 20 §3 (consumer intent)

```python
class LigatureKind(StrEnum):
    CT = "CT"        # ← uppercase value
    ST = "ST"        # ← uppercase value
    LONG_ST = "LONG_ST"   # ← renamed from LONG_S_T; value uppercase
    FI = "FI"        # ← uppercase value
    FL = "FL"        # ← uppercase value
    FFI = "FFI"      # ← uppercase value
    FFL = "FFL"      # ← uppercase value
    OE = "OE"        # ← new member
    AE = "AE"        # ← new member
    # omits: FF, LONG_S_S, LONG_S_I, SP, QU
```

### 2.3 Differences itemized

| Dimension | pd-book-tools (current) | SPA spec 20 (desired) |
|---|---|---|
| Value casing | lowercase (`"fi"`, `"ct"`) | UPPERCASE (`"FI"`, `"CT"`) |
| `LONG_S_T` rename | `LONG_S_T = "long_s_t"` | `LONG_ST = "LONG_ST"` |
| Members present in pd-book-tools only | `FF`, `LONG_S_S`, `LONG_S_I`, `SP`, `QU` | absent |
| Members present in SPA spec only | — | `OE`, `AE` |
| Base class | `str, Enum` | `StrEnum` |

### 2.4 Wire-format break analysis

Changing **any enum value** (e.g. `"fi"` → `"FI"`) is a **wire-format
break** for any JSON snapshot written by the current `to_dict()`
implementation: it stores `.value` directly (`"fi"`). Persisted
`#41`-era labeler snapshots using `LigatureKind` would fail `from_dict()`
unless a migration step is applied.

Known exposure:

- pd-ocr-labeler JSON envelopes that contain `glyph_annotations` (any
  labeler snapshots written after `675ad76` landed).
- pd-ocr-synth synthetic dataset files (if any were produced; synth is
  spec-only so none should exist yet).
- pd-ocr-trainer evaluation data (no glyph classifier shipped yet, so
  no real training data uses these values yet).

Since the glyph-annotations feature is NEW and no consuming app has
shipped a release that persists it yet, **the migration window is still
open** — but it closes as soon as the labeler-SPA ships its glyph epic
(#267-#270) or any labeler release cuts snapshots with current values.

---

## 3. Divergence B — dataclass vs Pydantic BaseModel

### 3.1 Current state

`GlyphAnnotations`, `LigatureMark`, and `LongSMark` are all `@dataclass`
with hand-written `to_dict` / `from_dict`. This is consistent with every
other OCR entity in pd-book-tools (`Word`, `Page`, `Block`, etc.).

### 3.2 SPA spec 20 §3 (consumer intent)

The spec writes `GlyphAnnotations` and `LigatureMark` as Pydantic
`BaseModel`. The SPA's envelope/persistence layer uses Pydantic
throughout (`WordMatch`, `UserPageEnvelope`, etc.).

### 3.3 Decision options

| Option | Pros | Cons |
|---|---|---|
| **A. Keep dataclass in pd-book-tools; SPA adapts** | Consistent with all other pd-book-tools entities; no new heavy dep in foundation lib | SPA must write an adapter/validator layer from dict → Pydantic model |
| **B. Convert pd-book-tools to Pydantic** | SPA consumes directly; no adapter needed | Breaks pd-book-tools convention; pulls Pydantic into foundation lib; more churn |
| **C. pd-book-tools provides both** | Flexible | Maintenance overhead; two sources of truth |

**Proposed decision: Option A.** The SPA already has a pattern of
consuming pd-book-tools dicts and rebuilding them into Pydantic models
(see `UserPageEnvelope.from_page()`). The foundation lib has a strong
convention of dataclasses + `to_dict/from_dict`. Pydantic belongs in
the SPA layer, not in the foundation.

---

## 4. Proposed migration plan

### Phase 0 — Approval gate (this document)

CT approves or revises this plan before any code is touched. The
wire-format decision and member-set rationalization (§4.1) are the two
choices that need explicit sign-off.

### Phase 1 — LigatureKind rationalization (pd-book-tools)

**Requires CT approval of the vocabulary before starting.**

1. Rename `LigatureKind` enum *name* `LONG_S_T` → `LONG_ST`.
2. Change all enum *values* from lowercase to UPPERCASE
   (`"fi"` → `"FI"`, `"ct"` → `"CT"`, `"long_s_t"` → `"LONG_ST"`, etc.).
3. **Decision point for CT**: which extra members to keep?
   - **Option K** (keep all): keep `FF`, `LONG_S_S`, `LONG_S_I`, `SP`, `QU`
     as valid pd-book-tools members even though SPA spec omits them. They
     represent real early-modern ligatures; the SPA can just ignore them.
   - **Option D** (drop): remove members the SPA spec omits. This is a
     harder break but aligns the vocabs exactly.
   - **Recommendation: Option K** — keep all existing members, add `OE`
     and `AE` as new members (SPA spec additions). The SPA spec was written
     without full knowledge of the corpus; conservative exclusions are
     better than losing coverage. Dropped members can always be removed
     later; re-adding them after snapshots are taken is another migration.
4. Add `OE = "OE"` and `AE = "AE"` as new members.
5. Update `from_dict()` to accept both old lowercase values and new
   uppercase values — use a case-insensitive lookup + rename shim for
   the `LONG_S_T` → `LONG_ST` rename. Remove the shim after a release
   cycle.
6. Update `to_dict()` to always emit uppercase values.
7. Change base from `str, Enum` to `StrEnum` (Python 3.11+) — or keep
   `str, Enum` for 3.10 compat; pd-book-tools targets 3.10+. **Decision
   point**: SPA spec uses `StrEnum`; pd-book-tools can stay on
   `str, Enum` for compatibility without any behavioral difference. Use
   `str, Enum` and add a TODO comment noting `StrEnum` once 3.11 min.

### Phase 2 — Migration helper in `from_dict()`

Add a `_migrate_ligature_kind_value(raw: str) -> str` helper that:

- Accepts lowercase legacy values and maps to uppercase equivalents.
- Accepts the `LONG_S_T` old name mapping to `LONG_ST`.
- Passes through already-uppercase values unchanged.
- Is called by `LigatureMark.from_dict()` on the `kind` field only.
- Is removed (or left as no-op) after the next minor version once no
  persisted snapshots with lowercase values remain in the wild.

### Phase 3 — dataclass (no change in pd-book-tools)

No change. The SPA adds a thin adapter in its persistence layer:

```python
# In pd-ocr-labeler-spa: core/persistence/glyph_adapter.py
def glyph_annotations_from_dict(d: dict) -> GlyphAnnotations:
    """Wrap pd-book-tools from_dict into a SPA-side Pydantic model."""
    ...
```

This is out-of-scope for this plan (SPA-side work, tracked by #267-#270).

### Phase 4 — Update spec 05 and tests

- Update `docs/specs/05-glyph-annotations.md` §2 to document uppercase
  values, new members (`OE`, `AE`), and rename.
- Update all tests in `tests/ocr/test_glyph_annotations.py` for new
  casing + new members.
- Add a `test_ligature_kind_legacy_migration_roundtrip` test that
  verifies old lowercase values still deserialize correctly.

---

## 5. Summary of decisions needed from CT

Before implementation begins, CT must approve:

1. **LigatureKind value casing**: uppercase (as SPA spec) — proposed YES.
2. **`LONG_S_T` → `LONG_ST` rename**: — proposed YES.
3. **Extra member disposition** (`FF`, `LONG_S_S`, `LONG_S_I`, `SP`, `QU`):
   Option K (keep all) or Option D (drop) — **proposed: Option K (keep)**.
4. **`OE`, `AE` additions**: accept SPA spec additions — proposed YES.
5. **dataclass stays** in pd-book-tools; SPA adapts — proposed YES.
6. **Migration shim in `from_dict()`**: keep old values readable
   during transition — proposed YES.

---

## 6. Files touched (Phase 1 + 2)

- `pd_book_tools/ocr/glyph_annotations.py` — enum values + from_dict shim
- `tests/ocr/test_glyph_annotations.py` — updated assertions + new migration test
- `docs/specs/05-glyph-annotations.md` — vocabulary table update

Out of scope (SPA-side, tracked separately):

- `pd-ocr-labeler-spa/core/persistence/` — Pydantic adapter
- `pd-ocr-labeler-spa/specs/20-glyph-annotations.md` — no change needed

---

## 7. Risk and timing

**Low risk for pd-book-tools itself** — the glyph epic is new and no
downstream release yet persists `LigatureKind` values. Migration window
is still open.

**Timing**: implement after CT approves this plan. Before pd-ocr-labeler-spa
starts its glyph epic (#267-#270), both should agree on the final vocabulary.
The SPA glyph epic is currently blocked by the labeler (issues #267-#270 require
issue #163 resolved). Resolving this plan unblocks those issues.
