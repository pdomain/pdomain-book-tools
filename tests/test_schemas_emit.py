"""Tests for ``pdomain_book_tools.schemas.emit``: JSON-Schema emission CLI."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from typing import TYPE_CHECKING

from pdomain_book_tools.schemas.emit import PUBLIC_MODELS, emit_schemas, main

if TYPE_CHECKING:
    import pytest


def _run_emit() -> dict:
    """Invoke the CLI in the current uv environment, parse JSON stdout."""
    proc = subprocess.run(
        [sys.executable, "-m", "pdomain_book_tools.schemas.emit"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert proc.stderr == "" or proc.stderr.startswith("WARNING"), (
        f"unexpected stderr: {proc.stderr!r}"
    )
    return json.loads(proc.stdout)


def test_emit_returns_top_level_dict():
    out = _run_emit()
    assert isinstance(out, dict)


def test_emit_includes_review_metadata_schema():
    out = _run_emit()
    assert "ReviewMetadata" in out
    sch = out["ReviewMetadata"]
    # Pydantic TypeAdapter returns a JSON-Schema-shaped dict with at least
    # these standard keys for an object type.
    assert sch["type"] == "object"
    assert "properties" in sch
    assert set(sch["properties"].keys()) == {
        "validated",
        "reviewer_note",
        "flagged_for_attention",
    }


def test_emit_review_metadata_field_types():
    out = _run_emit()
    props = out["ReviewMetadata"]["properties"]
    assert props["validated"]["type"] == "boolean"
    # reviewer_note is `str | None` — JSON Schema represents this as
    # anyOf [string, null] (or oneOf depending on Pydantic version).
    note_schema = props["reviewer_note"]
    assert "anyOf" in note_schema or note_schema.get("type") == "string"
    assert props["flagged_for_attention"]["type"] == "boolean"


def test_public_models_includes_full_set():
    names = {cls.__name__ for cls in PUBLIC_MODELS}
    assert names == {
        "Point",
        "BoundingBox",
        "LayoutRegion",
        "PageLayout",
        "ReviewMetadata",
        "OCRModelProvenance",
        "OCRProvenance",
        "Character",
        "Word",
        "Block",
        "Page",
    }


def test_emit_schemas_returns_dict_keyed_by_class_name():
    schemas = emit_schemas()
    for cls in PUBLIC_MODELS:
        assert cls.__name__ in schemas, f"missing schema for {cls.__name__}"
        assert isinstance(schemas[cls.__name__], dict)


def test_emit_word_schema_has_review_field():
    schemas = emit_schemas()
    word_schema = schemas["Word"]
    props = word_schema.get("properties", {})
    assert "review" in props, (
        "Word's wire schema must expose the optional ``review`` field "
        "(added in plan #1)."
    )


def test_emit_block_schema_has_review_field():
    schemas = emit_schemas()
    block_schema = schemas["Block"]
    # Block uses definitions_schema so root may be $ref into $defs
    if "$defs" in block_schema and "$ref" in block_schema:
        ref_name = block_schema["$ref"].split("/")[-1]
        inner = block_schema["$defs"][ref_name]
    elif "$defs" in block_schema and "Block" in block_schema["$defs"]:
        inner = block_schema["$defs"]["Block"]
    else:
        inner = block_schema
    props = inner.get("properties", {})
    assert "review" in props


def test_emit_page_schema_has_review_field():
    schemas = emit_schemas()
    page_schema = schemas["Page"]
    props = page_schema.get("properties", {})
    assert "review" in props


def test_emit_includes_word_block_page():
    schemas = emit_schemas()
    for required in ("Word", "Page"):
        assert required in schemas
        assert schemas[required].get("type") == "object"
    # Block uses definitions_schema — root may be $ref/$defs shape
    assert "Block" in schemas


def test_main_writes_json_to_stdout(capsys: pytest.CaptureFixture[str]):
    rc = main([])
    assert rc == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert "ReviewMetadata" in parsed
    assert "Word" in parsed
    assert "Block" in parsed
    assert "Page" in parsed


def test_main_runs_via_python_dash_m(tmp_path: object):
    # Sanity check: ``python -m pdomain_book_tools.schemas.emit`` produces
    # parseable JSON. We don't shell out here — main([]) is already
    # tested above — but we verify json.dump's output is deterministic
    # by emitting twice and comparing.
    buf1 = io.StringIO()
    buf2 = io.StringIO()
    schemas1 = emit_schemas()
    schemas2 = emit_schemas()
    json.dump(schemas1, buf1, indent=2, sort_keys=True)
    json.dump(schemas2, buf2, indent=2, sort_keys=True)
    assert buf1.getvalue() == buf2.getvalue()


# ---------------------------------------------------------------------------
# #175: LayoutRegion and PageLayout must be present in PUBLIC_MODELS
# ---------------------------------------------------------------------------


def test_public_models_includes_layout_region():
    """LayoutRegion is a documented public API and must appear in PUBLIC_MODELS."""
    names = {cls.__name__ for cls in PUBLIC_MODELS}
    assert "LayoutRegion" in names, (
        "LayoutRegion is documented public API (docs/usage/public-api.md) "
        "but is missing from PUBLIC_MODELS in schemas/emit.py"
    )


def test_public_models_includes_page_layout():
    """PageLayout is a documented public API and must appear in PUBLIC_MODELS."""
    names = {cls.__name__ for cls in PUBLIC_MODELS}
    assert "PageLayout" in names, (
        "PageLayout is documented public API (docs/usage/public-api.md) "
        "but is missing from PUBLIC_MODELS in schemas/emit.py"
    )


def test_emit_layout_region_schema_has_expected_fields():
    """LayoutRegion schema exposes L, R, T, B, type, confidence, raw_label."""
    schemas = emit_schemas()
    assert "LayoutRegion" in schemas
    props = schemas["LayoutRegion"].get("properties", {})
    for field in ("L", "R", "T", "B", "type", "confidence", "raw_label"):
        assert field in props, f"LayoutRegion schema missing field {field!r}"


def test_emit_page_layout_schema_has_expected_fields():
    """PageLayout schema exposes regions, image_width, image_height, detector."""
    schemas = emit_schemas()
    assert "PageLayout" in schemas
    props = schemas["PageLayout"].get("properties", {})
    for field in ("regions", "image_width", "image_height", "detector"):
        assert field in props, f"PageLayout schema missing field {field!r}"


def test_emit_layout_region_roundtrip():
    """LayoutRegion round-trips through to_dict/from_dict correctly."""
    from pdomain_book_tools.layout.types import LayoutRegion, RegionType

    region = LayoutRegion(
        type=RegionType.text, L=10, R=200, T=20, B=100, confidence=0.9
    )
    d = region.to_dict()
    restored = LayoutRegion.from_dict(d)
    assert restored.type == RegionType.text
    assert restored.L == 10
    assert restored.R == 200
    assert restored.T == 20
    assert restored.B == 100
    assert abs(restored.confidence - 0.9) < 1e-9


def test_emit_page_layout_roundtrip():
    """PageLayout round-trips through to_dict/from_dict correctly."""
    from pdomain_book_tools.layout.types import LayoutRegion, PageLayout, RegionType

    layout = PageLayout(
        regions=[LayoutRegion(type=RegionType.text, L=0, R=100, T=0, B=50)],
        image_width=800,
        image_height=1200,
        detector="test-detector",
        inference_ms=42,
    )
    d = layout.to_dict()
    restored = PageLayout.from_dict(d)
    assert restored.image_width == 800
    assert restored.image_height == 1200
    assert restored.detector == "test-detector"
    assert len(restored.regions) == 1
    assert restored.regions[0].type == RegionType.text
