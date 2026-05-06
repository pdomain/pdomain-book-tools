"""Per-adapter native-label → :class:`RegionType` mappings.

PP-DocLayout_plus-L emits 20 native categories. The rest of the pipeline
cares about a smaller, PGDP-flavoured taxonomy (see :class:`RegionType`).
``None`` means "drop this region entirely" — the adapter detected it,
the consumer ignores it.
"""

# Mapping is intentionally exposed as a plain dict so users / pd-prep-for-pgdp
# can override per-book via ``ProjectConfig.layout_category_overrides``.
PP_DOCLAYOUT_TO_PGDP: dict[str, str | None] = {
    # Body text — kept as text regions, no special handling
    "paragraph_title": "section",
    "doc_title": "title",
    "text": "text",
    "abstract": "text",
    # Figures and decorative content
    "image": "figure",
    "chart": "figure",
    "figure_title": "caption",
    # Tables
    "table": "table",
    "table_title": "caption",
    # Math
    "formula": "formula",
    "formula_number": None,  # subsumed by adjacent formula
    # Page chrome — preserved as typed regions; whether they are
    # subsequently dropped, kept, or annotated is a call-site decision
    # (e.g. ``layout_aware_reorg`` / ``ProjectConfig`` filters), not a
    # property of this mapping. ``page_number`` collapses into ``footer``
    # because PGDP treats it as part of the bottom-margin chrome.
    "header": "header",
    "footer": "footer",
    "page_number": "footer",
    "footnote": "footnote",
    # Lists & navigation
    "list_of_references": "list",
    # PP-DocLayout ``reference`` is a single bibliography citation item,
    # not a generic list entry — mapping to ``list`` would make PGDP-aware
    # consumers apply bullet/numbered formatting to citations. Until a
    # dedicated ``RegionType.reference`` is introduced, send it to ``text``.
    "reference": "text",
    "sidebar_text": "abandoned",
    "algorithm": "text",
    # Stamps / seals (engraved insignia)
    "seal": "decoration",
}
