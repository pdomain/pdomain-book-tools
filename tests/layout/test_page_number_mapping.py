from __future__ import annotations

from pdomain_book_contracts.layout.types import RegionType

from pdomain_book_tools.layout._mappings import PP_DOCLAYOUT_TO_PGDP
from pdomain_book_tools.ocr.layout_aware_reorg import _REGION_TO_BLOCK_ROLE


def test_pp_doclayout_page_number_no_longer_becomes_a_footer() -> None:
    # This dict holds plain strings, not RegionType members.
    assert PP_DOCLAYOUT_TO_PGDP["page_number"] == "page_number"


def test_the_new_value_names_a_real_region_type() -> None:
    assert RegionType(PP_DOCLAYOUT_TO_PGDP["page_number"]) is RegionType.page_number


def test_the_page_number_region_carries_the_folio_role() -> None:
    assert _REGION_TO_BLOCK_ROLE[RegionType.page_number] == "page number"


def test_the_footer_role_is_unchanged() -> None:
    assert _REGION_TO_BLOCK_ROLE[RegionType.footer] == "page footer"
