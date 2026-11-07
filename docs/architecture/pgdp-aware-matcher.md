---
Status: built
Owner: CT
Created: 2026-11-06
Last verified: 2026-11-06
Kind: architecture
---

# PGDP-aware matcher

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Last verified:** 2026-11-06
- **Read when:** changing OCR-to-source matching, PGDP continuation handling, legacy page projection, or the book labeling manifest.
- **Search terms:** matcher, MatchGraph, PGDP continuation, legacy projection, BookLabelingManifest.

`pdomain_book_tools.matching` is the public matching boundary. The matcher, the PGDP continuation decoder, and the legacy page projection are implemented in `pdomain_book_contracts.matching` and re-exported here.

`pdomain_book_tools.typography.book_manifest` re-exports `pdomain_book_contracts.typography.book_manifest`.

The matcher does not mutate the caller's documents. A caller who wants legacy `Page` fields uses the projection on purpose.

## Match graph and MatchPolicy

`match_documents` compares two immutable documents and returns a `MatchGraph`.

Documents, pages, lines, tokens, ranges, relations, operations, and alternatives are frozen. Nested containers stay immutable after a caller passes a mutable input.

`MatchPolicy` versions costs, the acceptance margin, search bounds, comparison normalization, and the tie-break rule.

The engine orders candidates by total cost, then by canonical relation bytes.

A tie, a margin below policy, or an exhausted search bound is quarantined with its alternatives. Quarantine does not fall through to a greedy accepted match.

Accepted relations cover a one-to-one match, one source token mapped onto physical fragments, and several physical fragments mapped onto one token.

Operations partition each relation's graphemes.

A token's `artifact_ranges` may be empty. Exact per-grapheme artifact ranges belong to PGDP fragments.

An insert is a `target_only` relation. A delete is a `source_only` relation.

For a resolved continuation whose tokens are in one of the documents, `match_documents` stores that document's stripped surface copy on the graph. It does not mutate the caller's documents.

## PGDP continuation decoding

`decode_pgdp_continuations` reads a PGDP `*` as one physical boundary: `same_line`, `line`, or `page`. It records the physical fragments and one marker record for each round that is present.

It does not always store both F2 and P3.

A single trailing hyphen, and not a double hyphen, stays `ambiguous` and keeps three logical candidates: join without the hyphen, keep the hyphen, and leave the parts separate.

Every other pair has one `preserve_punctuation` candidate, the two fragments concatenated.

The marker does not decide that a visible hyphen is discretionary.

The decoder quarantines orphan markers, nonadjacent markers, round conflicts, empty fragments, and source-range mismatches.

A round record or marker record that disagrees with the authoritative fragments raises `ValidationError`.

`build_pgdp_surface_document` removes inline and cross-page markers on a surface copy and leaves the input unchanged.

An ambiguous decision, or tokens that do not match the fragments, raises `ValueError`.

Hyphen n-gram lookup is not part of this decoding.

## Legacy page projection

`project_match_graph_onto_page` writes legacy page fields from an accepted graph. The graph keeps token IDs. Boxes stay on the legacy page.

If the live page text no longer matches the pre-projection document, the projection raises `ValueError`.

A one-to-one relation writes ground truth in place.

Same-line fragments combine. Cross-line visible-hyphen and missing-hyphen fragments stay unmerged. A manual split is not combined.

The projection also skips the topology merge when any fragment has review, typography annotations, or glyph annotations, and when the page or line is under review.

`legacy_page_to_match_document` builds a match document from a page.

## Book labeling manifest

`BookLabelingManifest` is separate from a page labeling bundle.

- Page indexes are contiguous from zero.
- The manifest requires one taxonomy identity.
- Page configuration hashes may differ.
- Page, bundle, and relation IDs are unique.
- A relation's `page_ids` must equal, in page order, the pages that list that relation.
- Every page relation id must exist on the manifest.

The manifest validates paths and hashes in memory. It does not read or write files.

## Code and tests checked on 2026-11-06

- Code: `pdomain_book_tools/matching/__init__.py`, `models.py`, `engine.py`, `pgdp_continuations.py`, and `legacy_projection.py` re-export `pdomain_book_contracts.matching`.
- Code: `pdomain_book_tools/typography/book_manifest.py` re-exports `pdomain_book_contracts.typography.book_manifest`.
- Tests named:
  - `test_nested_collections_are_deeply_immutable`
  - `test_documents_preserve_order_and_require_globally_stable_token_ids`
  - `test_matches_exact_tokens_without_mutating_documents`
  - `test_quarantines_equal_cost_paths_and_uses_canonical_path_order`
  - `test_decoder_keeps_real_physical_fragments_and_logical_candidates`
  - `test_decoder_quarantines_round_conflicts`
  - `test_continuation_rejects_round_fragments_that_disagree_with_primary`
  - `test_surface_document_rejects_ambiguous_and_tampered_evidence`
  - `test_graph_retains_original_page_topology_before_legacy_projection`
  - `test_graph_bridge_skips_visible_hyphen_fragments_across_lines`
  - `test_graph_bridge_skips_missing_hyphen_fragments_across_lines`
  - `test_real_pgdp_continuations_decode_match_and_preserve_exact_ranges`
  - `tests/typography/test_book_manifest.py`
- Verified: 2026-11-06 by reading modules and tests on master `0d8b9d40`.
- This docs pass did not re-run pytest.
- Also verified against the installed `pdomain_book_contracts` sources after the spec-design review:
  - `pgdp_continuations.py` `_logical_candidates` and boundary enum
  - `legacy_projection.py` `project_match_graph_onto_page`
  - `book_manifest.py` page-index and `page_ids` checks
  - `models.py` `artifact_ranges` and `source_only` / `target_only`
