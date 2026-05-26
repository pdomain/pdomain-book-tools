"""Tests for ``pdomain_book_tools.layout._mappings``.

Asserts the contract of ``PP_DOCLAYOUT_TO_PGDP``: native PP-DocLayout
labels for header / footer / page_number / footnote are preserved as
typed regions (``RegionType.header`` / ``footer`` / ``footnote``), not
dropped.

L-11 regression lock: the misleading ``"Page chrome — dropped before
reorg"`` comment claimed these labels were dropped at this layer. The
mapping actually preserves them; the drop (if any) happens at the call
site. This test fails if the mapping ever flips to ``None`` for any of
those four labels, AND grep-asserts the comment text is no longer the
incorrect form.
"""

from pathlib import Path

import pytest

from pdomain_book_tools.layout._mappings import PP_DOCLAYOUT_TO_PGDP
from pdomain_book_tools.layout.types import RegionType


@pytest.mark.parametrize(
    ("raw_label", "expected"),
    [
        ("header", RegionType.header),
        ("footer", RegionType.footer),
        ("page_number", RegionType.footer),
        ("footnote", RegionType.footnote),
    ],
)
def test_page_chrome_labels_are_preserved_not_dropped(raw_label, expected):
    """Page chrome regions are role-labeled, never silently dropped here."""
    mapped = PP_DOCLAYOUT_TO_PGDP[raw_label]
    assert mapped is not None, (
        f"PP-DocLayout label {raw_label!r} must NOT be mapped to None at this "
        "layer — drop decisions belong to the call site, not the mapping. "
        "L-11 regression: see docs/review/bugs-low.md."
    )
    assert RegionType(mapped) is expected


def test_reference_label_is_not_mapped_to_list():
    """L-12: PP-DocLayout's ``reference`` is a bibliography citation item.

    Mapping it to ``RegionType.list`` causes PGDP-aware tools to apply
    list (bullet/numbered) formatting to bibliography entries. ``text``
    is the correct generic destination until a dedicated
    ``RegionType.reference`` is introduced.
    """
    mapped = PP_DOCLAYOUT_TO_PGDP["reference"]
    assert mapped != "list", (
        "L-12 regression: PP-DocLayout 'reference' (bibliography item) must "
        "not map to RegionType.list — list formatting on citations is wrong."
    )
    assert RegionType(mapped) is RegionType.text


def test_mappings_module_comment_does_not_claim_dropped():
    """L-11: the page-chrome comment must not claim the regions are dropped here."""
    src = Path("pdomain_book_tools/layout/_mappings.py").read_text(encoding="utf-8")
    assert "dropped before reorg" not in src, (
        "L-11 regression: the 'Page chrome — dropped before reorg' comment is "
        "false because the mapping preserves header/footer/footnote as typed "
        "regions. Rewrite the comment to describe the actual behavior."
    )
