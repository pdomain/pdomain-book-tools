---
Status: active
Owner: CT
Created: 2026-08-22
Last verified: 2026-08-22
Kind: spec
---

# PGDP-aware matcher

## Agent Index

- **Kind:** spec
- **Status:** active
- **Owner:** CT
- **Last verified:** 2026-08-22
- **Read when:** changing OCR-to-source matching or PGDP continuation handling.
- **Search terms:** matcher, OCR ground truth, PGDP, hyphen, continuation, alignment graph.

## Preserve source text and physical words

Create one public immutable boundary in `pdomain_book_tools.matching`. It
accepts source-neutral ordered documents, so later Gutenberg text, HTML, and
ebook adapters can reuse it. PGDP is the first adapter.

The matcher never changes OCR token topology. It returns an ordered match graph
with exact token IDs, source ranges, comparison operations, best and runner-up
paths, margins, warnings, and policy identity. A compatibility adapter may
project that graph onto legacy `Page` objects.

`MatchPolicy` versions every cost, acceptance margin, merge bound, state limit,
transition limit, comparison normalization, and tie-break rule. Ordering is
deterministic by total cost and then canonical relation bytes. Ties, exhausted
search limits, and margins below policy enter quarantine. They retain their
alternatives and never fall back to a greedy accepted match.

## Decode PGDP continuations without deciding too early

PGDP `*` controls prove that a physical line or page boundary was removed. They
do not prove that a visible hyphen is discretionary. The adapter must always
retain physical fragments and both logical candidates until OCR evidence,
optional period-aware n-grams, or review chooses one.

Each continuation edge records F2 and P3 marker presence; exact byte and
grapheme ranges; page and line boundaries; surface fragments; candidate logical
forms; evidence; and one decision. The decision is one of: join without hyphen;
keep hyphen; leave separate; preserve punctuation; or ambiguous. N-gram access
uses the existing unimplemented `HyphenNgramsClient` design as optional
evidence. It is not part of continuation decoding.

The first real fixture is `projectID643ab41f2b9e6`. Required cases include
same-page `bread-*winners`, cross-page `sim-*` plus `*plicity`, `ad-*` plus
`*vantages`, punctuation `Tam--*` plus `*far`, and asymmetric F2/P3 markers.
Orphans, nonadjacent joins, round conflicts, empty fragments, and low-margin
alternatives enter quarantine.

## Keep page and book duties separate

Page-level `LabelingBundle` remains page-scoped. It contains physical OCR words,
geometry, projected source text, and local match evidence. Cross-page relations
live in a separate `BookLabelingManifest`; affected page bundles reference the
relation ID.

The book manifest orders and hashes page bundle materializations. It has a
stable book ID and a content-addressed manifest ID. It requires one taxonomy
identity across pages, but page configuration hashes may differ.

The shared model validates contiguous page order and confined relative paths.
It also validates unique page, bundle, and relation IDs; exact page relation
references; and the stable/content-addressed ID split. Filesystem no-follow and
hash checks remain the responsibility of source-data and the SPA.

Source-data produces matching evidence, page bundles, and the book manifest
from one pinned audit. The SPA validates and opens the manifest and never parses
raw F2 or P3.

## Suggestions require review

Matcher output is an immutable suggestion. It never sets text validation or
typography review state. Physical OCR token IDs and boxes remain authoritative
for training. Synthetic joined words retain parent provenance but never replace
the physical samples.

## Bound the first release

Phase one supports one-to-one matches and one source token mapped to two
physical tokens. It also supports same-line and line-boundary splits, one
adjacent page boundary, Unicode extended grapheme ranges, and explicit
ambiguity. Whole-book optimization, Gutenberg adapters, HTML extraction,
language corpora, and book-level correction manifests follow behind the same
contracts.

Tests must prove exact F2 byte preservation, stable IDs, visible and missing
dashes, lexical hyphens, double dashes, punctuation, false OCR splits, runner-up
ties, and cross-page joins. They must also prove exact source mapping for every
accepted grapheme.

## Adversarial Review

Independent review must challenge source reversibility, stable identities,
ambiguous continuation handling, deterministic policy limits, legacy
compatibility, and the page-to-book contract. High or medium findings block the
release until they are fixed and rechecked.
