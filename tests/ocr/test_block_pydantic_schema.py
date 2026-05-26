"""Tests for Block.__get_pydantic_core_schema__ — wire-shape JSON Schema."""

from __future__ import annotations

from pydantic import TypeAdapter

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.geometry.point import Point
from pdomain_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pdomain_book_tools.ocr.word import Word


def _bbox() -> BoundingBox:
    return BoundingBox(
        top_left=Point(0, 0, is_normalized=False),
        bottom_right=Point(10, 10, is_normalized=False),
    )


def _word(text: str = "hello") -> Word:
    return Word(text=text, bounding_box=_bbox())


def test_block_type_adapter_does_not_raise():
    adapter = TypeAdapter(Block)
    assert adapter is not None


def test_block_json_schema_shape():
    schema = TypeAdapter(Block).json_schema()
    # definitions_schema wraps the object under $defs when the schema is
    # recursive; the root may be a $ref pointing into $defs.
    if "$defs" in schema and "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        block_schema = schema["$defs"][ref_name]
    elif "$defs" in schema and "Block" in schema["$defs"]:
        block_schema = schema["$defs"]["Block"]
    else:
        block_schema = schema
    assert block_schema.get("type") == "object"
    props = block_schema["properties"]
    expected_keys = {
        "type",
        "child_type",
        "block_category",
        "block_labels",
        "block_role_labels",
        "block_position_labels",
        "line_role_labels",
        "line_position_labels",
        "baseline",
        "bounding_box",
        "items",
        "override_page_sort_order",
        "unmatched_ground_truth_words",
        "additional_block_attributes",
        "base_ground_truth_text",
        "review",
    }
    assert set(props.keys()) == expected_keys


def test_block_validate_from_dict_roundtrip_line_of_words():
    adapter = TypeAdapter(Block)
    block = Block(
        items=[_word("hello"), _word("world")],
        bounding_box=_bbox(),
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )
    d = block.to_dict()
    validated = adapter.validate_python(d)
    assert isinstance(validated, Block)
    assert validated.to_dict() == d


def test_block_validate_from_dict_roundtrip_nested_blocks():
    adapter = TypeAdapter(Block)
    line1 = Block(
        items=[_word("hello")],
        bounding_box=_bbox(),
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )
    line2 = Block(
        items=[_word("world")],
        bounding_box=_bbox(),
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )
    paragraph = Block(
        items=[line1, line2],
        bounding_box=_bbox(),
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
    )
    d = paragraph.to_dict()
    validated = adapter.validate_python(d)
    assert isinstance(validated, Block)
    assert validated.to_dict() == d


def test_block_validate_unmatched_ground_truth_words():
    # #181: Block.unmatched_ground_truth_words is list[tuple[int, str]] at
    # runtime, but the pydantic schema previously declared it as list[str].
    # Validation of a dict emitted by to_dict() must now accept the
    # [(int, str), ...] shape that ground-truth matching produces.
    adapter = TypeAdapter(Block)
    block = Block(
        items=[_word("hello")],
        bounding_box=_bbox(),
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
        unmatched_ground_truth_words=[(0, "hello"), (1, "world")],
    )
    d = block.to_dict()
    # The dict contains list-of-lists because JSON tuples serialize as arrays.
    assert d["unmatched_ground_truth_words"] == [(0, "hello"), (1, "world")]
    # Pydantic must accept both the tuple form (Python round-trip) and the
    # list form (JSON deserialization).
    validated = adapter.validate_python(d)
    assert isinstance(validated, Block)
    # Also accept the JSON-deserialized form ([int, str] lists instead of tuples).
    d_json_form = dict(d)
    d_json_form["unmatched_ground_truth_words"] = [[0, "hello"], [1, "world"]]
    validated_json = adapter.validate_python(d_json_form)
    assert isinstance(validated_json, Block)
