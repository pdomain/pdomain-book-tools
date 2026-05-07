"""Drift gate for ``docs/architecture/page-model.md``.

The page-model doc is a user-facing reference for ``Page.to_dict()`` —
the JSON form that every downstream pd-* consumer reads back via
``Page.from_dict``. The vocabulary lists in the doc must stay in sync
with the source-of-truth ``ClassVar`` frozensets on ``Block`` and the
``RegionType`` enum, otherwise downstream authors learn from a stale
contract.

This test does NOT enforce prose freshness — only that every value the
code says is allowed is mentioned somewhere in the doc, and that the
top-level ``Page.to_dict()`` field set the doc enumerates matches what
the code actually emits for a minimal Page.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pd_book_tools.layout.types import RegionType
from pd_book_tools.ocr.block import Block
from pd_book_tools.ocr.page import Page

DOC_PATH = (
    Path(__file__).resolve().parent.parent / "docs" / "architecture" / "page-model.md"
)


@pytest.fixture(scope="module")
def doc_text() -> str:
    assert DOC_PATH.is_file(), f"missing doc: {DOC_PATH}"
    return DOC_PATH.read_text(encoding="utf-8")


def test_doc_exists_and_nonempty(doc_text: str) -> None:
    # A minimal sanity gate so an empty file doesn't pass the vocabulary
    # checks below by accident.
    assert len(doc_text) > 1000, "page-model doc looks suspiciously short"


def test_doc_lists_every_allowed_block_role_label(doc_text: str) -> None:
    """Every value in ``Block.ALLOWED_BLOCK_ROLE_LABELS`` must appear in
    the doc — backtick-quoted so it's visibly part of the vocabulary
    listing, not just an incidental prose mention.
    """
    missing: list[str] = []
    for label in sorted(Block.ALLOWED_BLOCK_ROLE_LABELS):
        if f"`{label}`" not in doc_text:
            missing.append(label)
    assert not missing, (
        "page-model doc is missing block_role_labels values "
        f"(must appear in backticks): {missing}"
    )


def test_doc_lists_every_allowed_line_role_label(doc_text: str) -> None:
    missing: list[str] = []
    for label in sorted(Block.ALLOWED_LINE_ROLE_LABELS):
        if f"`{label}`" not in doc_text:
            missing.append(label)
    assert not missing, f"page-model doc is missing line_role_labels values: {missing}"


def test_doc_lists_every_layout_region_type(doc_text: str) -> None:
    """The doc must disambiguate ``RegionType`` from ``block_role_labels``;
    listing every enum value is the lightest enforcement of that.
    """
    missing: list[str] = []
    for member in RegionType:
        if f"`{member.value}`" not in doc_text:
            missing.append(member.value)
    assert not missing, f"page-model doc is missing RegionType values: {missing}"


def test_doc_enumerates_top_level_page_fields(doc_text: str) -> None:
    """Every always-present key emitted by ``Page.to_dict()`` must be
    documented (backtick-quoted).

    Conditional metadata fields (``image_path``, ``rotation_applied``, …)
    are emitted only when set, so we exercise the well-known always-on
    subset rather than instantiating every variant.
    """
    page = Page(
        width=10,
        height=10,
        page_index=0,
        blocks=[],
        bounding_box=None,
    )
    emitted = page.to_dict()
    always_present = {
        "type",
        "width",
        "height",
        "page_index",
        "bounding_box",
        "items",
        "ocr_provenance",
    }
    # Sanity: the always-present subset is actually emitted.
    assert always_present.issubset(emitted.keys()), (
        f"Page.to_dict() no longer emits {always_present - set(emitted)}; "
        "update both the code and the doc test."
    )
    missing = [
        field for field in sorted(always_present) if f"`{field}`" not in doc_text
    ]
    assert not missing, f"page-model doc is missing top-level Page fields: {missing}"


def test_doc_mentions_canonical_apis(doc_text: str) -> None:
    """Sanity gates so the doc keeps pointing at real call sites."""
    for needle in (
        "Page.to_dict",
        "Page.from_dict",
        "PageLayout",
        "LayoutRegion",
        "block_role_labels",
        "BoundingBox",
    ):
        assert needle in doc_text, f"page-model doc no longer mentions `{needle}`"
