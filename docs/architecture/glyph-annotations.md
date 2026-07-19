---
Status: built
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-19
Kind: architecture
---

# Glyph annotations preserve printed-form facts beside canonical text

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Read when:** changing `Word` glyph metadata, its serialized shape, ligature vocabulary, provenance, or validation behavior.
- **Search terms:** glyph annotations, ligature, long s, swash, Word serialization, glyph provenance.

## Printed-form facts are a side channel on `Word`

`Word.glyph_annotations` stores printed-form facts without changing `Word.ground_truth_text`. This field is optional. `None` means that glyph review is unknown or has not happened. `GlyphAnnotations()` means that review happened and found no annotations.

`GlyphAnnotations` contains `ligatures`, `long_s_positions`, `swash`, and object-level `source`. The `source` field accepts `human`, `predicted`, and `human_confirmed`. It defaults to `human`. Each `LigatureMark` has a controlled `LigatureKind` and an optional half-open `char_span`. A missing span records a known ligature with an unknown location.

The controlled ligature values are `FI`, `FL`, `FF`, `FFI`, `FFL`, `CT`, `ST`, `LONG_ST`, `LONG_S_S`, `LONG_S_I`, `SP`, `QU`, `OE`, and `AE`. During deserialization, legacy lowercase values and the former `LONG_S_T` name map to current values. Unknown kinds fail with `ValueError`.

## Serialization preserves unknown and reviewed-empty states

`GlyphAnnotations.to_dict()` emits all four fields. It converts ligature spans to JSON arrays and kinds to uppercase strings. During deserialization, missing annotation keys inside the envelope use field defaults.

`Word.to_dict()` omits `glyph_annotations` when the field is `None`. It includes the field when set, including an empty `GlyphAnnotations()` value. `Word.from_dict()` maps a missing or null field to `None`. It reconstructs an envelope when one is present. This behavior preserves the semantic difference between old or unreviewed data and reviewed data with no glyph facts.

The Pydantic `Word` boundary declares `glyph_annotations` as a nullable
`any_schema` field. This keeps the raw annotation mapping intact during
`TypeAdapter(Word).validate_python()`. Pydantic does not validate a standalone
strong glyph schema at that boundary. After the mapping passes through,
`Word.from_dict()` reconstructs the typed value with
`GlyphAnnotations.from_dict()`.

## Validation is explicit

Callers invoke `GlyphAnnotations.validate(word)` when they need to check the cross-field contract. Construction and assignment do not call it automatically. Validation rejects ground-truth text containing U+FB00 through U+FB06 or U+017F. It also rejects invalid or empty ligature spans, out-of-range long-s positions, and long-s positions that do not point to `s` or `S`. Separately, `GlyphAnnotations` construction rejects an unknown provenance source. Ligature deserialization rejects an unknown kind.

Automatic validation and tolerant handling of future annotation kinds remain product decisions in `docs/context/intent-map.md`. They are not part of the shipped architecture. Cross-repository adoption is also outside this repository's evidence.

## Evidence

- `pdomain_book_tools/ocr/glyph_annotations.py:32-44` defines the banned ground-truth codepoints.
- `pdomain_book_tools/ocr/glyph_annotations.py:52-123` defines the current ligature vocabulary and legacy aliases.
- `pdomain_book_tools/ocr/glyph_annotations.py:131-175` defines ligature serialization and fail-closed kind loading.
- `pdomain_book_tools/ocr/glyph_annotations.py:187-256` defines provenance, annotation defaults, and serialization.
- `pdomain_book_tools/ocr/glyph_annotations.py:258-308` implements caller-invoked cross-field validation.
- `pdomain_book_tools/ocr/word.py:102-106` records the `None` versus reviewed-empty contract.
- `pdomain_book_tools/ocr/word.py:670-696` conditionally serializes annotations.
- `pdomain_book_tools/ocr/word.py:698-750` deserializes annotations into `Word`.
- `tests/ocr/test_glyph_annotations.py:23-365` covers vocabulary, legacy migration, provenance, and annotation serialization.
- `tests/ocr/test_glyph_annotations.py:387-471` covers explicit validation.
- `tests/ocr/test_glyph_annotations.py:483-557` covers `Word` integration and the unknown/reviewed-empty distinction.
- `tests/ocr/test_word_pydantic_schema.py` covers non-empty, reviewed-empty, and
  absent glyph annotations across the Pydantic round trip.
