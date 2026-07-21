"""A2/A3: early-return reconcile and soft recover path coverage.

- A2: empty row-block path must still run ``reconcile_dropped_words``.
- A3: non-strict soft recover (default production) must land a recovered
  block, warn on stderr, and keep words on the page.
- Empty-bbox words are intentional filter noise before soft recover.
"""

from __future__ import annotations

import pytest

from pdomain_book_tools.geometry.bounding_box import BoundingBox
from pdomain_book_tools.geometry.point import Point
from pdomain_book_tools.ocr.block import Block, BlockCategory, BlockChildType
from pdomain_book_tools.ocr.page import Page
from pdomain_book_tools.ocr.reorganize_page_utils import (
    ReorganizeDroppedWordsError,
    _meaningful_words,
    build_recovered_words_block,
    find_dropped_words,
    reconcile_dropped_words,
)
from pdomain_book_tools.ocr.word import Word


def _bbox(
    left: float,
    top: float,
    right: float,
    bottom: float,
    *,
    normalized: bool = True,
) -> BoundingBox:
    return BoundingBox(
        top_left=Point(left, top, is_normalized=normalized),
        bottom_right=Point(right, bottom, is_normalized=normalized),
        is_normalized=normalized,
    )


def _word(
    text: str,
    left: float,
    top: float,
    right: float,
    bottom: float,
    *,
    normalized: bool = True,
) -> Word:
    return Word(
        text=text,
        bounding_box=_bbox(left, top, right, bottom, normalized=normalized),
        ocr_confidence=0.95,
    )


def _line(words: list[Word]) -> Block:
    return Block(
        items=words,
        child_type=BlockChildType.WORDS,
        block_category=BlockCategory.LINE,
    )


def _para(lines: list[Block]) -> Block:
    return Block(
        items=lines,
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.PARAGRAPH,
    )


def _page_with_header_and_body() -> Page:
    """Page with a top header line and mid-page body so Step E peels a band."""
    header = _para([_line([_word("TITLE", 0.2, 0.02, 0.8, 0.05)])])
    body = _para(
        [
            _line(
                [
                    _word("Body", 0.15, 0.40, 0.35, 0.44),
                    _word("text", 0.40, 0.40, 0.60, 0.44),
                    _word("here", 0.65, 0.40, 0.85, 0.44),
                ]
            )
        ]
    )
    return Page(width=1000, height=2000, page_index=0, blocks=[header, body])


def test_early_return_soft_recovers_body_words(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Empty row blocks + band-only emit must soft-recover body words."""
    monkeypatch.delenv("PD_OCR_REORGANIZE_STRICT", raising=False)

    def _empty_rows(
        page: Page,
        body_lines: list[Block],
        body_words: list[Word],
        debug_sections: object,
    ) -> Block:
        return Block(items=[], block_category=BlockCategory.BLOCK)

    monkeypatch.setattr(
        "pdomain_book_tools.ocr.reorganize_page_utils.run_step_f_row_blocks",
        _empty_rows,
    )

    page = _page_with_header_and_body()
    pre_texts = {w.text for w in page.words if (w.text or "").strip()}
    page.reorganize_page(capture_diagnostics=False)

    post_texts = {w.text for w in page.words if (w.text or "").strip()}
    assert "Body" in post_texts
    assert "text" in post_texts
    assert "here" in post_texts
    assert pre_texts <= post_texts

    recovered = [b for b in page.items if "recovered" in (b.block_role_labels or [])]
    assert recovered, "soft recover must append a recovered-role block"
    err = capsys.readouterr().err
    assert "WARNING: reorganize dropped" in err


def test_early_return_strict_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Strict mode must raise when the empty-row path would drop body words."""
    monkeypatch.setenv("PD_OCR_REORGANIZE_STRICT", "1")

    def _empty_rows(
        page: Page,
        body_lines: list[Block],
        body_words: list[Word],
        debug_sections: object,
    ) -> Block:
        return Block(items=[], block_category=BlockCategory.BLOCK)

    monkeypatch.setattr(
        "pdomain_book_tools.ocr.reorganize_page_utils.run_step_f_row_blocks",
        _empty_rows,
    )

    page = _page_with_header_and_body()
    with pytest.raises(ReorganizeDroppedWordsError) as excinfo:
        page.reorganize_page(capture_diagnostics=False)
    assert any(
        "Body" in msg or "text" in msg or "here" in msg for msg in excinfo.value.errors
    )


def test_soft_recover_path_without_strict_env(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Forced drop with STRICT unset → recovered block + stderr + words on page."""
    monkeypatch.delenv("PD_OCR_REORGANIZE_STRICT", raising=False)

    kept = [
        _word("alpha", 0.10, 0.10, 0.20, 0.12),
        _word("beta", 0.25, 0.10, 0.35, 0.12),
    ]
    dropped_word = _word("gamma", 0.40, 0.10, 0.50, 0.12)
    pre_words = [*kept, dropped_word]

    line = _line(list(kept))
    outer = Block(
        items=[line],
        child_type=BlockChildType.BLOCKS,
        block_category=BlockCategory.BLOCK,
    )
    page = Page(width=1000, height=1000, page_index=0, blocks=[outer])

    result = reconcile_dropped_words(page, pre_words, [outer])
    assert any("recovered" in (b.block_role_labels or []) for b in result)
    recovered_texts = {
        w.text
        for b in result
        if "recovered" in (b.block_role_labels or [])
        for w in b.words
    }
    assert "gamma" in recovered_texts
    err = capsys.readouterr().err
    assert "WARNING: reorganize dropped" in err
    assert "gamma" in err


def test_empty_bbox_words_filtered_before_soft_recover() -> None:
    """Bbox-less words are intentional filter, not a soft-recover product path."""
    from typing import cast

    with_bbox = _word("keep", 0.1, 0.1, 0.2, 0.12)
    # Public Word requires a BoundingBox; use a stand-in for the filter contract.
    no_bbox = cast("Word", type("W", (), {"text": "ghost", "bounding_box": None})())
    meaningful = _meaningful_words([with_bbox, no_bbox])
    assert [w.text for w in meaningful] == ["keep"]

    dropped = find_dropped_words([with_bbox, no_bbox], [])
    assert [w.text for w in dropped] == ["keep"]

    recovered = build_recovered_words_block([no_bbox])
    assert recovered is None


def test_multiset_duplicate_signature_detects_partial_drop() -> None:
    """Two identical text+bbox words: dropping one must still be reported."""
    a1 = _word("dup", 0.1, 0.1, 0.2, 0.12)
    a2 = _word("dup", 0.1, 0.1, 0.2, 0.12)
    kept = _word("dup", 0.1, 0.1, 0.2, 0.12)
    dropped = find_dropped_words([a1, a2], [kept])
    assert len(dropped) == 1
    assert dropped[0].text == "dup"
