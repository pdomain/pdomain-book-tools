---
Status: built
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-13
Kind: architecture
---

# Glyph annotations preserve printed-form facts beside canonical text

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Read when:** changing `Word` glyph metadata, its serialized shape, ligature vocabulary, provenance, or validation behavior.
- **Search terms:** glyph annotations, ligature, long s, swash, Word serialization, glyph provenance.

## Printed-form facts are a side channel on `Word`

`Word.glyph_annotations` stores printed-form facts without changing `Word.ground_truth_text`. The field is optional. `None` means glyph review is unknown or has not happened; `GlyphAnnotations()` means review happened and found no annotations.

`GlyphAnnotations` contains `ligatures`, `long_s_positions`, `swash`, and object-level `source`. `source` accepts `human`, `predicted`, and `human_confirmed`, and defaults to `human`. Each `LigatureMark` has a controlled `LigatureKind` and an optional half-open `char_span`. A missing span records a known ligature whose location is unknown.

The controlled ligature values are `FI`, `FL`, `FF`, `FFI`, `FFL`, `CT`, `ST`, `LONG_ST`, `LONG_S_S`, `LONG_S_I`, `SP`, `QU`, `OE`, and `AE`. Deserialization also maps the legacy lowercase values and the former `LONG_S_T` name to current values. Unknown kinds fail with `ValueError`.

## Serialization preserves unknown and reviewed-empty states

`GlyphAnnotations.to_dict()` emits all four fields. Ligature spans become JSON arrays, and kinds become uppercase strings. Missing annotation keys inside the envelope use field defaults during deserialization.

`Word.to_dict()` omits `glyph_annotations` when the field is `None` and includes it when set, including an empty `GlyphAnnotations()` value. `Word.from_dict()` maps a missing or null field to `None` and reconstructs a present envelope. This preserves the semantic difference between old or unreviewed data and reviewed data with no glyph facts.

## Validation is explicit

Callers invoke `GlyphAnnotations.validate(word)` when they need the cross-field contract checked. Construction and assignment do not call it automatically. Validation rejects ground-truth text containing U+FB00 through U+FB06 or U+017F, invalid or empty ligature spans, out-of-range long-s positions, and long-s positions that do not point to `s` or `S`. `GlyphAnnotations` construction separately rejects an unknown provenance source, while ligature deserialization rejects an unknown kind.

Automatic validation and tolerant handling of future annotation kinds remain product decisions in `docs/context/intent-map.md`; they are not part of the shipped architecture. Cross-repository adoption is also outside this repository's evidence.

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
