"""Tests for BoundingBox.__get_pydantic_core_schema__ — wire-shape JSON Schema."""

from __future__ import annotations

from pydantic import TypeAdapter

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.geometry.point import Point


def _bbox() -> BoundingBox:
    return BoundingBox(
        top_left=Point(0, 0, is_normalized=False),
        bottom_right=Point(10, 10, is_normalized=False),
    )


def test_bounding_box_type_adapter_does_not_raise() -> None:
    adapter = TypeAdapter(BoundingBox)
    assert adapter is not None


def test_bounding_box_json_schema_shape() -> None:
    schema = TypeAdapter(BoundingBox).json_schema()
    assert schema["type"] == "object"
    props = schema["properties"]
    assert set(props.keys()) == {"top_left", "bottom_right", "is_normalized"}
    # top_left and bottom_right are themselves Point-shaped dicts; either
    # inlined or referenced via $ref/$defs.
    for corner_key in ("top_left", "bottom_right"):
        corner = props[corner_key]
        if "$ref" in corner:
            # Inlined via $defs — verify it resolves to a Point-shaped dict.
            defs = schema.get("$defs", {})
            ref_name = corner["$ref"].split("/")[-1]
            assert ref_name in defs
            target = defs[ref_name]
            assert set(target["properties"].keys()) == {"x", "y", "is_normalized"}
        else:
            assert set(corner["properties"].keys()) == {"x", "y", "is_normalized"}
    assert set(schema["required"]) == {"top_left", "bottom_right", "is_normalized"}


def test_bounding_box_validate_from_dict_roundtrip() -> None:
    adapter = TypeAdapter(BoundingBox)
    bb = _bbox()
    d = bb.to_dict()
    validated = adapter.validate_python(d)
    assert isinstance(validated, BoundingBox)
    assert validated == bb
    dumped = adapter.dump_python(validated)
    assert dumped == d
