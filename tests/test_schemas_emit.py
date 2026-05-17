"""Tests for ``pd_book_tools.schemas.emit``: JSON-Schema emission CLI."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from typing import TYPE_CHECKING

from pd_book_tools.schemas.emit import PUBLIC_MODELS, emit_schemas, main

if TYPE_CHECKING:
    import pytest


def _run_emit() -> dict:
    """Invoke the CLI in the current uv environment, parse JSON stdout."""
    proc = subprocess.run(
        [sys.executable, "-m", "pd_book_tools.schemas.emit"],
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
    # Sanity check: ``python -m pd_book_tools.schemas.emit`` produces
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
