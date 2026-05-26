"""JSON-Schema emission for pdomain-book-tools public domain models.

The CLI entrypoint is ``python -m pdomain_book_tools.schemas.emit``. It
dumps a single JSON document on stdout with one key per public model
(Word, Block, Page, BoundingBox, ReviewMetadata, ...) and a JSON-Schema
document as the value, produced via :class:`pydantic.TypeAdapter` on
the stdlib ``@dataclass`` models.

Downstream consumers (pdomain-ocr-ops, pdomain-ui codegen) re-run this command
against a pinned wheel and feed the output to ``openapi-typescript`` or
equivalent.
"""
