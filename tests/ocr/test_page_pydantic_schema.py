"""Tests for Page.__get_pydantic_core_schema__ — wire-shape JSON Schema."""

from __future__ import annotations

from pydantic import TypeAdapter

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point
from pd_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.word import Word


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
    schema = TypeAdapter(Page).json_schema()
    assert schema["type"] == "object"
    props = schema["properties"]
    # Page.to_dict produces these keys; some are omitted-when-default,
    # but the schema must list all of them.
    expected_keys = {
        "type",
        "width",
        "height",
        "page_index",
        "bounding_box",
        "items",
        "ocr_provenance",
        "image_path",
        "name",
        "source",
        "ocr_failed",
        "provenance_live_ocr",
        "provenance_saved_ocr",
        "provenance_saved",
        "rotation_applied",
        "review",
    }
    assert set(props.keys()) == expected_keys
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
    adapter = TypeAdapter(Page)
    page = Page(
        width=100,
        height=100,
        page_index=1,
        bounding_box=_bbox(),
        blocks=[_line()],
        image_path="/tmp/page-1.png",
        name="page-001",
        source="ocr-fixture",
        rotation_applied=90,
    )
    d = page.to_dict()
    validated = adapter.validate_python(d)
    assert isinstance(validated, Page)
    assert validated.to_dict() == d


def test_page_validate_provenance_dict_fields():
    # #182: provenance_live_ocr / provenance_saved_ocr / provenance_saved are
    # dict[str, Any] | None at runtime, but the pydantic schema previously
    # declared them as str | None. Validation of a Page.to_dict() payload
    # with provenance dicts must not raise.
    adapter = TypeAdapter(Page)
    prov_dict = {"engine": "tesseract", "version": "5.3.1", "lang": "eng"}
    page = Page(
        width=100,
        height=100,
        page_index=0,
        bounding_box=_bbox(),
        blocks=[_line()],
    )
    page.provenance_live_ocr = prov_dict
    page.provenance_saved_ocr = {"source": "sidecar.json"}
    page.provenance_saved = {"format": "v2"}
    d = page.to_dict()
    # The dict must contain the provenance dicts, not strings.
    assert isinstance(d.get("provenance_live_ocr"), dict)
    assert isinstance(d.get("provenance_saved_ocr"), dict)
    assert isinstance(d.get("provenance_saved"), dict)
    # Pydantic schema must accept these dict values without ValidationError.
    validated = adapter.validate_python(d)
    assert isinstance(validated, Page)
    # None values must also be accepted.
    d_none = dict(d)
    d_none["provenance_live_ocr"] = None
    d_none["provenance_saved_ocr"] = None
    d_none["provenance_saved"] = None
    validated_none = adapter.validate_python(d_none)
    assert isinstance(validated_none, Page)
