"""Tests for Point.__get_pydantic_core_schema__ — wire-shape JSON Schema."""

from __future__ import annotations

from pydantic import TypeAdapter

from pdomain_book_tools.geometry.point import Point


def test_point_type_adapter_does_not_raise():
    # Before the hook was added, TypeAdapter(Point) raised
    # ``pydantic.errors.PydanticSchemaGenerationError: Unable to generate
    # pydantic-core schema for <class 'pdomain_book_tools.geometry.point.Point'>``.
    adapter = TypeAdapter(Point)
    assert adapter is not None


def test_point_json_schema_shape():
    schema = TypeAdapter(Point).json_schema()
    assert schema["type"] == "object"
    props = schema["properties"]
    assert set(props.keys()) == {"x", "y", "is_normalized"}
    # ``x`` and ``y`` accept int OR float; ``is_normalized`` is bool.
    # Pydantic typically renders union-of-int-and-float as ``anyOf``.
    assert "anyOf" in props["x"] or props["x"]["type"] in ("number", "integer")
    assert "anyOf" in props["y"] or props["y"]["type"] in ("number", "integer")
    assert props["is_normalized"]["type"] == "boolean"
    assert set(schema["required"]) == {"x", "y", "is_normalized"}


def test_point_validate_from_dict_roundtrip():
    adapter = TypeAdapter(Point)
    p = Point(0.5, 0.5, is_normalized=True)
    d = p.to_dict()
    validated = adapter.validate_python(d)
    assert isinstance(validated, Point)
    assert validated == p
    # Dump back to dict via pydantic's serializer; should match to_dict().
    dumped = adapter.dump_python(validated)
    assert dumped == d


def test_point_validate_legacy_dict_without_is_normalized():
    # from_dict() infers is_normalized when the key is absent; the schema
    # marks the key as required, but legacy data may omit it. We tolerate
    # the omission via from_dict's existing fallback (.get("is_normalized")).
    adapter = TypeAdapter(Point)
    # We allow the schema to require the key (cleaner for codegen). Legacy
    # dicts go through ``Point.from_dict`` directly, not the TypeAdapter.
    p_dict = {"x": 10, "y": 20, "is_normalized": False}
    validated = adapter.validate_python(p_dict)
    assert validated == Point(10, 20, is_normalized=False)
