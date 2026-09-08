from __future__ import annotations

import pytest

from pdomain_book_tools.ocr.block import Block

_ADDITIONS = frozenset(
    {
        "signature mark",
        "catchword",
        "press figure",
        "rule",
        "brace",
        "bracket",
        "group label",
        "plate",
        "speaker label",
        "stage direction",
        "interlinear gloss",
        "abandoned",
        "decorated initial",
        "unknown",
    }
)


def test_the_twenty_shipped_roles_survive() -> None:
    shipped = {
        "paragraph",
        "sidenote",
        "page header",
        "page footer",
        "page number",
        "printers mark",
        "blockquote",
        "poetry",
        "recovered",
        "illustration",
        "decoration",
        "caption",
        "figure",
        "table",
        "footnote",
        "title",
        "section",
        "list",
        "formula",
        "artefact",
    }
    assert shipped <= Block.ALLOWED_BLOCK_ROLE_LABELS


def test_the_fourteen_additions_are_accepted() -> None:
    assert _ADDITIONS <= Block.ALLOWED_BLOCK_ROLE_LABELS
    assert len(Block.ALLOWED_BLOCK_ROLE_LABELS) == 34


@pytest.mark.parametrize("role", sorted(_ADDITIONS))
def test_each_addition_normalizes_without_raising(role: str) -> None:
    block = Block(items=[], block_role_labels=[role])
    assert role in block.block_role_labels


def test_the_new_aliases_fold() -> None:
    assert Block(items=[], block_role_labels=["frontispiece"]).block_role_labels == [
        "plate"
    ]
    assert Block(items=[], block_role_labels=["signaturemark"]).block_role_labels == [
        "signature mark"
    ]
