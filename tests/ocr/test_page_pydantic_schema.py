"""Tests for Page.__get_pydantic_core_schema__ — wire-shape JSON Schema."""

from __future__ import annotations

from pydantic import TypeAdapter

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.geometry.point import Point
from pdomain_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pdomain_book_tools.ocr.page import Page
from pdomain_book_tools.ocr.word import Word


def _bbox() -> BoundingBox:
    return BoundingBox(
        top_left=Point(0, 0, is_normalized=False),
        bottom_right=Point(100, 100, is_normalized=False),
    )


def _word(text: str = "hello") -> Word:
    return Word(text=text, bounding_box=_bbox())


def _line() -> Block:
    return Block(
        items=[_word()],
        bounding_box=_bbox(),
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )


def test_page_type_adapter_does_not_raise():
    adapter = TypeAdapter(Page)
    assert adapter is not None


def test_page_json_schema_shape():
    """Task 4: Removed operational fields from schema.

    Only OCR content + identity + name + review remain in the pydantic schema.
    """
    schema = TypeAdapter(Page).json_schema()
    assert schema["type"] == "object"
    props = schema["properties"]
    # Page.to_dict produces these keys; the schema must list all of them.
    expected_keys = {
        "type",
        "page_id",
        "width",
        "height",
        "page_index",
        "bounding_box",
        "items",
        "page_labels",
        "name",
        "review",
        "image_blob_hash",
        "thumbnail_blob_hash",
        "gt_orphans",
    }
    assert set(props.keys()) == expected_keys
    # Removed operational fields must NOT appear in the wire schema.
    for removed_field in (
        "ocr_provenance",
        "image_path",
        "source",
        "ocr_failed",
        "provenance_live_ocr",
        "provenance_saved_ocr",
        "provenance_saved",
        "rotation_applied",
    ):
        assert removed_field not in props
    # NDArray cache fields must NOT appear in the wire schema.
    for cache_field in (
        "_cv2_numpy_page_image",
        "_cv2_numpy_page_image_page_with_bbox",
        "image_array",
        "blocks",
    ):
        assert cache_field not in props


def test_page_validate_from_dict_roundtrip_minimal():
    adapter = TypeAdapter(Page)
    page = Page(
        width=100,
        height=100,
        page_index=0,
        bounding_box=_bbox(),
        blocks=[_line()],
    )
    d = page.to_dict()
    validated = adapter.validate_python(d)
    assert isinstance(validated, Page)
    assert validated.to_dict() == d


def test_page_validate_from_dict_roundtrip_with_metadata():
    """Task 4: Removed operational fields; only name remains as optional metadata."""
    adapter = TypeAdapter(Page)
    page = Page(
        width=100,
        height=100,
        page_index=1,
        bounding_box=_bbox(),
        blocks=[_line()],
        name="page-001",
    )
    d = page.to_dict()
    validated = adapter.validate_python(d)
    assert isinstance(validated, Page)
    assert validated.to_dict() == d


def test_page_validate_provenance_dict_fields():
    """Task 4: provenance fields removed from Page; schema handles to_dict output."""
    adapter = TypeAdapter(Page)
    page = Page(
        width=100,
        height=100,
        page_index=0,
        bounding_box=_bbox(),
        blocks=[_line()],
    )
    d = page.to_dict()
    # Pydantic schema must accept to_dict output without ValidationError.
    validated = adapter.validate_python(d)
    assert isinstance(validated, Page)
    # Removed fields must not be in to_dict output
    assert "provenance_live_ocr" not in d
    assert "provenance_saved_ocr" not in d
    assert "provenance_saved" not in d
    assert "ocr_provenance" not in d
