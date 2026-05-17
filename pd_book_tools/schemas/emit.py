"""JSON-Schema emitter for pd-book-tools public domain models.

Invocation: ``python -m pd_book_tools.schemas.emit``

Emits a single JSON document on stdout, keyed by model class name, with
each value being a JSON-Schema document produced by
``pydantic.TypeAdapter(<cls>).json_schema()``.

Adding a new public model: import it below and add it to ``PUBLIC_MODELS``.
Classes that are not natively pydantic-introspectable (plain classes,
__slots__ types, dataclasses with InitVar / ndarray fields) declare a
``__get_pydantic_core_schema__`` classmethod that mirrors their
``to_dict()`` wire shape — see ``pd_book_tools/geometry/point.py`` for
the canonical pattern.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from pydantic import TypeAdapter

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.geometry.point import Point
from pd_book_tools.ocr.block import Block
from pd_book_tools.ocr.character import Character
from pd_book_tools.ocr.page import Page
from pd_book_tools.ocr.provenance import OCRModelProvenance, OCRProvenance
from pd_book_tools.ocr.review import ReviewMetadata
from pd_book_tools.ocr.word import Word

# The single source of truth for what counts as a "public" model.
# Order is intentional: leaf geometry types first, OCR review/provenance
# next, then composite OCR models.
PUBLIC_MODELS: tuple[type, ...] = (
    Point,
    BoundingBox,
    ReviewMetadata,
    OCRModelProvenance,
    OCRProvenance,
    Character,
    Word,
    Block,
    Page,
)


def emit_schemas() -> dict[str, dict[str, Any]]:
    """Build {ModelName: json_schema} for every public model."""
    out: dict[str, dict[str, Any]] = {}
    for cls in PUBLIC_MODELS:
        out[cls.__name__] = TypeAdapter(cls).json_schema()
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint. argv is accepted for testability but unused today."""
    schemas = emit_schemas()
    json.dump(schemas, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
