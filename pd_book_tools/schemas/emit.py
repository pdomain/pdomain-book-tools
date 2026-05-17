"""JSON-Schema emitter for pd-book-tools public domain models.

Invocation: ``python -m pd_book_tools.schemas.emit``

Emits a single JSON document on stdout, keyed by model class name, with
each value being a JSON-Schema document produced by
``pydantic.TypeAdapter(<dataclass>).json_schema()``.

Adding a new public model: import it below and add it to ``PUBLIC_MODELS``.

NOTE — models excluded from the current PUBLIC_MODELS list due to
non-pydantic-serializable field types:
  - BoundingBox: contains Point, which has no pydantic core schema
    (Point uses custom __slots__ and no Pydantic annotations)
  - Word: contains BoundingBox (depends on Point); also has
    ndarray/cv2-typed fields via Character
  - Block: is a plain class (not @dataclass), which pydantic cannot
    introspect for JSON schema
  - Page: contains InitVar[Collection] and ndarray cache fields

A follow-up plan should add `__get_pydantic_core_schema__` to Point
and BoundingBox (or introduce separate Pydantic-friendly view models),
at which point BoundingBox / Word / Block / Page can be re-added here.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from pydantic import TypeAdapter

from pd_book_tools.ocr.review import ReviewMetadata

# The single source of truth for what counts as a "public" model.
# Order is intentional: simple leaf types first, composite types after.
PUBLIC_MODELS: tuple[type, ...] = (
    ReviewMetadata,
    # BoundingBox excluded: Point has no pydantic core schema
    # Word excluded: depends on BoundingBox (Point)
    # Block excluded: plain class, not @dataclass
    # Page excluded: InitVar[Collection] not pydantic-serializable
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
