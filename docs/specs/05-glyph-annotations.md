# Spec: Glyph-Level Side-Channel Annotations on `Word`

> **Status**: Active
> **Last updated**: 2026-05-10
> **Spec-Issue**: ConcaveTrillion/pd-book-tools#29

Status: spec only — no implementation yet. Decision-oriented; intended
to be green-lit, pushed back on, or revised before code is written.

Author intent: add a *parallel* annotation structure to `Word` that
records glyph-level facts about the printed page (ligatures, long-s
substitutions, swash forms, eventually small caps inside lowercase
runs, italic inside roman, blackletter runs, etc.) **without** mutating
the canonical / semantic ground-truth string.

This is the **foundation-library half** of a workspace-wide feature.
Four sibling repos are downstream consumers of the model defined here:

- `pd-ocr-synth` — emits `glyph_annotations` when synthesizing pages
  whose recipe specifies ligatures, long-s, swash, etc., so the
  trainer has supervised signal.
- `pd-ocr-trainer` — consumes `glyph_annotations` for evaluation
  slicing (e.g. CER conditioned on ligature presence) and for
  curriculum sampling.
- `pd-ocr-labeler` (NiceGUI, legacy) — surfaces the annotations in
  the per-word panel; reads/writes them in saved snapshots.
- `pd-ocr-labeler-spa` (FastAPI + React, in spec) — uses
  `glyph_annotations` in its JSON envelope; needs the field shape
  pinned before milestones referencing it can land.

The shape needs to be stable before the consumers start. This spec
locks it down.

---

## 1. Core invariants

These are the load-bearing rules. Implementation, validation, and
review all hang off them.

### 1.1 GT text stays canonical

`Word.ground_truth_text` is the **semantic** text of the word. It is
the string a downstream PGDP / book reader is expected to consume.

It MUST NOT contain Unicode presentation-form ligature codepoints. The
banned range is the Alphabetic Presentation Forms ligatures block:

- `U+FB00` LATIN SMALL LIGATURE FF
- `U+FB01` LATIN SMALL LIGATURE FI
- `U+FB02` LATIN SMALL LIGATURE FL
- `U+FB03` LATIN SMALL LIGATURE FFI
- `U+FB04` LATIN SMALL LIGATURE FFL
- `U+FB05` LATIN SMALL LIGATURE LONG S T (`ﬅ`)
- `U+FB06` LATIN SMALL LIGATURE ST (`ﬆ`)

It also MUST NOT contain `U+017F` LATIN SMALL LETTER LONG S (`ſ`) —
long-s is recorded via `long_s_positions`, never in the GT string.

Stated as an invariant: **GT text is normalized; presentation is
side-channel.**

This invariant is enforced at two layers:

- A `Word.ground_truth_text` setter check (raises / logs) — implementation detail, not specced here.
- The `glyph_annotations` validator (see §6) refuses to accept a
  `Word` whose GT contains banned codepoints.

The rationale: ligature codepoints are fragile across fonts, search
engines, accessibility tools, and PGDP's own pipelines. By treating
them as a presentation fact we keep GT lossless-but-clean and let
ligature-aware consumers reconstruct the printed form when they need
to.

### 1.2 Annotations never modify GT text

The annotation pipeline is **read-only with respect to GT**. Setting
or updating `glyph_annotations` does not, ever, alter
`ground_truth_text`. This is a hard rule, not a default.

If a consumer wants to render the ligature-bearing form, it composes
GT + annotations at render time. The library will eventually grow a
`render_with_glyphs(word)` helper; it is out of scope for this spec.

### 1.3 `None` vs empty `GlyphAnnotations()` semantics

This distinction matters for downstream consumers and is part of the
contract.

| Value | Meaning |
|---|---|
| `glyph_annotations is None` | Nobody has looked at this word for annotations yet. Annotations status is **unknown**. |
| `glyph_annotations == GlyphAnnotations()` (all fields empty/false) | Someone (human labeler or annotator pass) **looked**, and there are no glyph annotations to record for this word. |

Concrete consumers that need this distinction:

- **labeler progress %** — `None` words are "unreviewed for glyphs";
  empty-but-set words count as reviewed. Without the distinction, a
  fresh page and a fully-reviewed all-roman page look identical.
- **trainer eval slicing** — when computing "CER on words known to
  contain no ligatures," the trainer must include empty-but-set
  words and exclude `None` words (which carry no signal either way).
- **synth ingest** — synth always emits `GlyphAnnotations()` (possibly
  empty) for every word it generates, signalling "this is the
  authoritative glyph truth, not a missing label."

### 1.4 Backwards compatibility

`glyph_annotations` is an **optional** field on `Word`. Documents
serialized before this field existed:

- Deserialize with `glyph_annotations = None` (the missing-key path).
- Round-trip cleanly: re-serializing a loaded old document does not
  introduce a `glyph_annotations` key (we only emit it when it is
  not `None`, see §4.2).
- Are not retroactively "annotated" — they remain in the
  unknown / unreviewed state, which is the correct semantics.

No existing call site of `Word.__init__`, `Word.to_dict`, or
`Word.from_dict` breaks.

---

## 2. Data model

`Word` is a `@dataclass` (see `pd_book_tools/ocr/word.py:30`) with a
hand-rolled `__init__` and `to_dict` / `from_dict`. The new types
follow that convention — plain `@dataclass` with `to_dict` /
`from_dict`, not pydantic, not attrs. This keeps the dependency
surface unchanged and matches `BoundingBox` and the existing `Word`
shape exactly.

### 2.1 `LigatureKind` enum

A `str`-valued `Enum` (so JSON serialization is the bare string, and
older readers that hand-decode JSON see human-meaningful values).

```python
class LigatureKind(str, Enum):
    # Latin ligatures common in early-modern printing
    FI       = "fi"        # U+FB01 in print, "fi" in GT
    FL       = "fl"        # U+FB02
    FF       = "ff"        # U+FB00
    FFI      = "ffi"       # U+FB03
    FFL      = "ffl"       # U+FB04
    CT       = "ct"        # decorative ct ligature, no Unicode codepoint
    ST       = "st"        # U+FB06 in print, "st" in GT
    LONG_S_T = "long_s_t"  # ſt, U+FB05 in print, "st" in GT
    LONG_S_S = "long_s_s"  # ſs, "ss" in GT
    LONG_S_I = "long_s_i"  # ſi, "si" in GT  (less common, included for completeness)
    SP       = "sp"        # decorative sp ligature
    QU       = "qu"        # decorative Qu ligature

    # Reserved namespace — see §2.4 for "how to add a value"
```

### 2.2 `LigatureMark`

```python
@dataclass
class LigatureMark:
    kind: LigatureKind
    char_span: tuple[int, int] | None = None
    # [start, end) char indices into Word.ground_truth_text.
    # None = "we know this ligature is somewhere in the word but
    # don't know exactly where" (e.g. coarse-grained synth labels).
```

### 2.3 `GlyphAnnotations`

```python
@dataclass
class GlyphAnnotations:
    ligatures: list[LigatureMark] = field(default_factory=list)
    long_s_positions: list[int] = field(default_factory=list)
    # Char indices in GT where a printed ſ (U+017F) was normalized to s.
    # Indices refer to the GT (post-normalization) string.
    # Example: GT "shall" with long_s_positions=[0] means the printed
    # form was "ſhall".
    swash: bool = False
    # True iff at least one glyph in the word is a swash variant
    # (decorative tail/flourish, typically initial caps in chapter
    # openings). Coarse for now — see §2.4 for how to refine to
    # per-glyph if needed.

    # Reserved for future expansion — adding a field is additive and
    # backwards-compatible (missing key on load → default value).
    # Anticipated future fields (NOT in v1):
    #
    #   small_caps_in_lc: list[tuple[int, int]] = []
    #   italic_in_roman:  list[tuple[int, int]] = []
    #   blackletter_run:  list[tuple[int, int]] = []
    #
    # Each would be a list of [start, end) GT spans. These are
    # documented here so v1 authors don't accidentally repurpose the
    # field names for something else.
```

### 2.4 Adding new `LigatureKind` values or `GlyphAnnotations` fields

**Controlled vocabulary.** `LigatureKind` is a closed enum, not a
free-form string. Adding a value requires a PR with:

- The printed form (with image / fixture reference) the new kind
  represents.
- The GT decomposition (e.g. "this ligature decomposes to `qu` in
  GT").
- A note on which corpus / book it appeared in — we are not adding
  values speculatively.

Ad-hoc strings are explicitly disallowed; consumers who encounter an
unknown `kind` value in JSON SHOULD raise on load (see §6.4) rather
than silently dropping the mark.

**New `GlyphAnnotations` fields.** Additive only. Each new field gets:

- A default value (so missing-key load → default, preserving §1.4).
- An entry in this spec under §2.3.
- Updates to §3 (JSON shape) and §6 (validation).
- A roadmap note (see ROADMAP.md entry) so downstream consumers know
  to look for the new field.

---

## 3. Serialization

### 3.1 JSON shape

The JSON shape is the canonical interchange format (used by the
labeler-spa envelope, by snapshot files, and by any future export).
The pickle / dataclass-`asdict` form mirrors it 1:1.

```json
{
  "glyph_annotations": {
    "ligatures": [
      {"kind": "ct", "char_span": [2, 4]},
      {"kind": "long_s_t", "char_span": [0, 2]}
    ],
    "long_s_positions": [0],
    "swash": false
  }
}
```

Field-level rules:

- `ligatures` — array of objects; empty array if none. Always present
  inside the envelope.
- `long_s_positions` — array of ints; empty array if none.
- `swash` — bool; defaults to `false`.
- Future fields (small_caps_in_lc, italic_in_roman, …) — added as
  optional keys; missing key on load = default value.

### 3.2 Nesting into existing `Word` JSON

`Word.to_dict` (currently at `pd_book_tools/ocr/word.py:637`) returns a
flat dict. The new key is added at the top level alongside `text`,
`bounding_box`, `text_style_labels`, etc.:

```json
{
  "text": "stand",
  "ground_truth_text": "stand",
  "bounding_box": { ... },
  "ocr_confidence": 0.97,
  "text_style_labels": [],
  "glyph_annotations": {
    "ligatures": [{"kind": "st", "char_span": [0, 2]}],
    "long_s_positions": [],
    "swash": false
  }
}
```

### 3.3 Emit-when-non-None policy

`Word.to_dict` only emits the `glyph_annotations` key when
`self.glyph_annotations is not None`. When it is `None`, the key is
absent. This is what preserves the "old documents round-trip clean"
property of §1.4 — loading and re-saving a pre-annotation document
does not introduce noise into diffs.

```python
# Pseudocode for to_dict (not the implementation):
out = { ... existing fields ... }
if self.glyph_annotations is not None:
    out["glyph_annotations"] = self.glyph_annotations.to_dict()
return out
```

`Word.from_dict` mirrors:

```python
ga_data = data.get("glyph_annotations")  # missing key → None
glyph_annotations = (
    GlyphAnnotations.from_dict(ga_data) if ga_data is not None else None
)
```

### 3.4 Pickle / snapshot format

`pd-book-tools` consumers also pickle / cloudpickle `Document` and
`Page` objects (see snapshot use in the labeler). Because `Word`,
`GlyphAnnotations`, and `LigatureMark` are all plain dataclasses with
JSON-friendly fields, pickle Just Works. No custom `__getstate__` /
`__setstate__` is needed.

The `LigatureKind(str, Enum)` choice means pickled values are stable
across Python versions and survive a pickle-load in code that has the
enum defined.

---

## 4. Validation rules

The `GlyphAnnotations.validate(word)` method (or equivalent free
function) checks:

### 4.1 GT text invariants (preconditions)

- `word.ground_truth_text` MUST NOT contain any of `U+FB00`–`U+FB06`.
- `word.ground_truth_text` MUST NOT contain `U+017F` (`ſ`).

If either fails, `validate` raises before checking annotation
internals. (This catches the case where someone built a `Word` with
ligature-bearing GT and tried to attach annotations to it.)

### 4.2 `LigatureMark` bounds

For each `mark` in `ligatures`:

- If `mark.char_span` is not `None`:
  - `0 <= start <= end <= len(word.ground_truth_text)`
  - `start < end` (empty spans are disallowed; use `None` to express
    "unknown location")
- `mark.kind` is a valid `LigatureKind` enum value (raised by enum
  construction during deserialization).

### 4.3 `long_s_positions` bounds

- Each index `i` satisfies `0 <= i < len(word.ground_truth_text)`.
- The character at `word.ground_truth_text[i]` is `s` or `S` (the
  normalized form of `ſ`). If the index points at any other
  character, validation fails — this is almost always a caller bug.
- The list is permitted to be unsorted, but consumers SHOULD sort it
  on emit for reproducible diffs. (Soft rule; not enforced.)

### 4.4 Unknown `kind` values on load

When loading JSON, an unknown `kind` string (one not in
`LigatureKind`) MUST raise. Silent-drop semantics would mask schema
drift across repos and is exactly the failure mode the controlled
vocabulary is designed to prevent.

### 4.5 What is NOT validated

- We do not require `ligatures` to be sorted.
- We do not require `ligatures` spans to be non-overlapping (a `ct`
  ligature inside a `LONG_S_T` capture is contrived but not
  forbidden).
- We do not validate against the printed-form image — that's a
  trainer / labeler concern, not a data-model concern.

---

## 5. Cross-repo consumer expectations

This section is informative — it documents what each downstream repo
needs from the model, so future changes don't accidentally break a
consumer.

| Consumer | Reads | Writes | Needs |
|---|---|---|---|
| `pd-ocr-synth` | — | full `GlyphAnnotations` | Stable JSON shape; `LigatureKind` covers everything the recipes can render. |
| `pd-ocr-trainer` | `GlyphAnnotations`, `None` distinction | — | Eval slicing depends on `None` ≠ `GlyphAnnotations()` (see §1.3). |
| `pd-ocr-labeler` (NiceGUI) | full | full | Snapshot pickle round-trip; per-word UI panel. |
| `pd-ocr-labeler-spa` | full | full | JSON envelope round-trip; field shape pinned before envelope spec lands. |

If a future change would alter the JSON shape (rename a field, change
a type), it is a **breaking** change for the SPA envelope and
requires a coordinated bump across all four consumers.

---

## 6. Out of scope (for v1)

- `render_with_glyphs(word) -> str` — composing GT + annotations into
  a printed-form string. Useful, separate, follow-up.
- Per-glyph small-caps / italic / blackletter spans (the reserved
  fields in §2.3). Anticipated, not v1.
- `LigatureKind` values beyond the §2.1 list. Add with PR + rationale.
- Image-level ligature *detection* (an OCR-time pass that infers
  ligatures from glyph images). v1 is a data model only; population
  is a downstream concern (synth knows; trainer learns; labeler
  hand-edits).
- Migration tooling for old documents that already have ligature
  codepoints in GT. If we discover such corpora, a one-shot
  normalizer becomes a follow-up roadmap item.

---

## 7. Open questions (to resolve before implementation)

1. **Should `swash` be coarse (bool) or per-glyph (list of indices)?**
   v1 spec is bool. Per-glyph would parallel `long_s_positions` and
   is the more honest representation. Bool is enough for trainer
   slicing today; revisit if the labeler UI grows a per-glyph swash
   marker.
2. **`LigatureKind.LONG_S_I` — keep or drop?** Long-s + i is rare in
   the corpora we've sampled. Keep it for now as future-proofing;
   easy to remove with a deprecation if it's never used.
3. **Validator location** — free function in
   `pd_book_tools/ocr/glyph_annotations.py`, or method on
   `GlyphAnnotations`? Implementation detail; lean toward method
   for symmetry with `BoundingBox.validate`-style helpers if any
   exist; otherwise free function.

These are flagged for the implementation PR, not blockers for the
spec.

## TL;DR

Not yet captured during the B3 mechanical migration.

## Context

Not yet captured during the B3 mechanical migration.

## Constraints

Not yet captured during the B3 mechanical migration.

## Decision

Not yet captured during the B3 mechanical migration.

## Contract / Acceptance

Not yet captured during the B3 mechanical migration.

## Trade-offs considered

Not yet captured during the B3 mechanical migration.

## Consequences

Not yet captured during the B3 mechanical migration.

## Open questions

Not yet captured during the B3 mechanical migration.

## References

Not yet captured during the B3 mechanical migration.
