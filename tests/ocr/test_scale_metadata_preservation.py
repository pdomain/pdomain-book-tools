"""Tests that scale() preserves metadata on Document, Page, and Block.

Regression tests for issue #183: scale() was constructing new instances
with only geometry fields, silently dropping provenance/review/metadata.
"""

from __future__ import annotations

from pathlib import Path

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.geometry.point import Point
from pdomain_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pdomain_book_tools.ocr.document import Document
from pdomain_book_tools.ocr.page import Page
from pdomain_book_tools.ocr.review import ReviewMetadata
from pdomain_book_tools.ocr.word import Word

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _norm_bbox() -> BoundingBox:
    return BoundingBox(
        top_left=Point(0.1, 0.1, is_normalized=True),
        bottom_right=Point(0.9, 0.9, is_normalized=True),
    )


def _word(text: str = "hello") -> Word:
    return Word(
        text=text,
        bounding_box=BoundingBox(
            top_left=Point(0.1, 0.1, is_normalized=True),
            bottom_right=Point(0.3, 0.2, is_normalized=True),
        ),
        ocr_confidence=0.9,
    )


def _line_block(text: str = "hello") -> Block:
    return Block(
        items=[_word(text)],
        bounding_box=_norm_bbox(),
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )


def _page_with_metadata(page_index: int = 0) -> Page:
    """Task 4: operational metadata fields removed from Page.
    Only page_labels, name, and review remain as OCR-content metadata.
    """
    return Page(
        width=100,
        height=100,
        page_index=page_index,
        blocks=[_block_with_metadata()],
        bounding_box=_norm_bbox(),
        page_labels=["chapter"],
        name="page-0",
        review=ReviewMetadata(validated=True, reviewer_note="checked"),
    )


def _block_with_metadata() -> Block:
    """Block with all metadata fields that scale() used to drop."""
    return Block(
        items=[_line_block()],
        bounding_box=_norm_bbox(),
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
        block_labels=["paragraph"],
        block_role_labels=["paragraph"],
        block_position_labels=["center"],
        line_role_labels=["body line"],
        line_position_labels=["center"],
        baseline={"m": 0.0, "b": 5.0, "source": "ocr"},
        override_page_sort_order=3,
        unmatched_ground_truth_words=[(0, "lost-word")],
        additional_block_attributes={"custom_key": "custom_val"},
        base_ground_truth_text="hello world",
        review=ReviewMetadata(validated=True, reviewer_note="block ok"),
    )


# ---------------------------------------------------------------------------
# Document.scale() — issue #183 finding: source_identifier dropped
# ---------------------------------------------------------------------------


class TestDocumentScalePreservesMetadata:
    def test_scale_preserves_source_identifier(self):
        """Document.scale() must preserve source_identifier (closes #183)."""
        page = Page(
            width=100,
            height=100,
            page_index=0,
            blocks=[_line_block()],
        )
        doc = Document(
            source_lib="tesseract",
            source_path=Path("/some/path.png"),
            pages=[page],
            source_identifier="my-scan-identifier",
        )
        scaled = doc.scale(200, 200)
        assert scaled.source_identifier == "my-scan-identifier", (
            "Document.scale() dropped source_identifier"
        )

    def test_scale_preserves_source_lib_and_path(self):
        page = Page(width=100, height=100, page_index=0, blocks=[_line_block()])
        doc = Document(
            source_lib="doctr",
            source_path=Path("/img/scan.png"),
            pages=[page],
            source_identifier="id-42",
        )
        scaled = doc.scale(300, 400)
        assert scaled.source_lib == "doctr"
        assert scaled.source_path == Path("/img/scan.png")


# ---------------------------------------------------------------------------
# Page.scale() — issue #183 finding: many metadata fields dropped
# ---------------------------------------------------------------------------


class TestPageScalePreservesMetadata:
    """Task 4: operational fields removed from Page.

    scale() now preserves: page_labels, name, review.
    Removed: image_path, source, ocr_failed, provenance_*, rotation_applied, ocr_provenance.
    """

    def _scaled_page(self) -> tuple[Page, Page]:
        p = _page_with_metadata()
        return p, p.scale(200, 200)

    def test_scale_preserves_page_labels(self):
        original, scaled = self._scaled_page()
        assert scaled.page_labels == original.page_labels, (
            "Page.scale() dropped page_labels"
        )

    def test_scale_preserves_name(self):
        original, scaled = self._scaled_page()
        assert scaled.name == original.name, "Page.scale() dropped name"

    def test_scale_preserves_review(self):
        original, scaled = self._scaled_page()
        assert scaled.review is not None, "Page.scale() dropped review"
        assert scaled.review.validated == original.review.validated  # type: ignore[union-attr]

    def test_scale_removed_fields_not_present(self):
        """Task 4: Removed operational fields must not be present on scaled page."""
        _, scaled = self._scaled_page()
        for removed in (
            "image_path",
            "source",
            "ocr_failed",
            "provenance_live_ocr",
            "provenance_saved_ocr",
            "provenance_saved",
            "rotation_applied",
            "ocr_provenance",
        ):
            assert not hasattr(scaled, removed), (
                f"Page.scale() carried through removed field: {removed}"
            )


# ---------------------------------------------------------------------------
# Block.scale() — issue #183 finding: sort override, unmatched GT words, etc.
# ---------------------------------------------------------------------------


class TestBlockScalePreservesMetadata:
    def _scaled_block(self) -> tuple[Block, Block]:
        b = _block_with_metadata()
        return b, b.scale(200, 200)

    def test_scale_preserves_override_page_sort_order(self):
        original, scaled = self._scaled_block()
        assert scaled.override_page_sort_order == original.override_page_sort_order, (
            "Block.scale() dropped override_page_sort_order"
        )

    def test_scale_preserves_unmatched_ground_truth_words(self):
        original, scaled = self._scaled_block()
        assert (
            scaled.unmatched_ground_truth_words == original.unmatched_ground_truth_words
        ), "Block.scale() dropped unmatched_ground_truth_words"

    def test_scale_preserves_additional_block_attributes(self):
        original, scaled = self._scaled_block()
        assert (
            scaled.additional_block_attributes == original.additional_block_attributes
        ), "Block.scale() dropped additional_block_attributes"

    def test_scale_preserves_base_ground_truth_text(self):
        original, scaled = self._scaled_block()
        assert scaled.base_ground_truth_text == original.base_ground_truth_text, (
            "Block.scale() dropped base_ground_truth_text"
        )

    def test_scale_preserves_review(self):
        original, scaled = self._scaled_block()
        assert scaled.review is not None, "Block.scale() dropped review"
        assert scaled.review.validated == original.review.validated  # type: ignore[union-attr]
