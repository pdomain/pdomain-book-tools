"""Iteration A regression tests for ``pd_book_tools.ocr.dropcap``.

Exercises the cursive / decorative drop-cap fallback against the three
known fixtures where the geometric block-cap stitcher fails because
DocTR doesn't recognise the oversized serif glyph as a letter:

* ``chapter-head-credulities`` — cap "S", body word OCR'd as "UPERSTITIONS"
  (the glyph itself was OCR'd as a stray ``"-"`` token).
* ``chapter-head-filial-duty`` — cap "O", body word OCR'd as "NCE";
  the glyph was skipped entirely (no Word at the cap location).
* ``footnotes-stacked-with-anchor`` — cap "A", body word OCR'd as
  "BELIEF"; the glyph was skipped. ``"A"`` cannot be uniquely inferred
  from ``"BELIEF"`` alone (BELIEF is already a valid word), so this
  fixture exercises the ``"drop cap unrecovered"`` failure path.

Plus a negative test: a body page (no drop cap, just a regular indent)
must NOT get a false-positive prepend.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pd_book_tools.ocr.document import Document

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "layout_regression"
INPUT_DIR = FIXTURE_ROOT / "inputs"


def _load_and_reorganize(case: str):
    cv2 = pytest.importorskip("cv2")
    doc = Document.from_dict(
        json.loads((INPUT_DIR / f"{case}.json").read_text(encoding="utf-8"))
    )
    page = doc.pages[0]
    page.cv2_numpy_page_image = cv2.imread(str(INPUT_DIR / f"{case}.png"))
    page.refine_bounding_boxes()
    page.reorganize_page(drop_layout_words=True)
    return page


def _line_holding(page, predicate):
    for line in page.lines:
        words = list(line.words)
        if any(predicate(w) for w in words):
            return line, words
    return None, None


def test_credulities_cursive_cap_S_recovered():
    """Cap glyph OCR'd as ``"-"``; body word ``"UPERSTITIONS"`` →
    inferred ``"S"``, prepended into the same line so it renders as
    ``"SUPERSTITIONS"``.
    """
    page = _load_and_reorganize("chapter-head-credulities")
    inferred = [
        w for w in page.words if "drop cap inferred" in (w.word_components or [])
    ]
    assert len(inferred) == 1, (
        f"expected exactly 1 inferred drop cap, got {len(inferred)}: "
        f"{[(w.text, w.word_components) for w in inferred]}"
    )
    cap = inferred[0]
    assert cap.text == "S", f"cap text={cap.text!r}, expected 'S'"
    # The cap word should also carry the existing ``"drop cap"`` tag so
    # ``Block.text`` joins it to the next word with no separator (matches
    # the block-cap stitcher's contract).
    assert "drop cap" in cap.word_components
    # The cap bbox must sit to the LEFT of the body word's bbox.
    line, words = _line_holding(page, lambda w: w is cap)
    assert line is not None, "cap word missing from final lines"
    assert words[0] is cap, "cap should be the first word in the line"
    body = words[1]
    assert body.text == "UPERSTITIONS", f"body word={body.text!r}"
    assert cap.bounding_box.maxX <= body.bounding_box.minX + 0.01, (
        f"cap bbox should be left of body bbox: cap maxX={cap.bounding_box.maxX:.4f}, "
        f"body minX={body.bounding_box.minX:.4f}"
    )
    assert line.text.startswith("SUPERSTITIONS"), (
        f"line.text={line.text!r}, expected to start with 'SUPERSTITIONS'"
    )


def test_filial_duty_cursive_cap_O_recovered():
    """Cap glyph skipped by OCR; body word ``"NCE"`` → inferred ``"O"``,
    new Word synthesised at the CC bbox, ``Word.ocr_confidence`` is None.
    """
    page = _load_and_reorganize("chapter-head-filial-duty")
    inferred = [
        w for w in page.words if "drop cap inferred" in (w.word_components or [])
    ]
    assert len(inferred) == 1, (
        f"expected exactly 1 inferred drop cap, got {len(inferred)}: "
        f"{[(w.text, w.word_components) for w in inferred]}"
    )
    cap = inferred[0]
    assert cap.text == "O", f"cap text={cap.text!r}, expected 'O'"
    # Synthesised cap (no OCR) → confidence None.
    assert cap.ocr_confidence is None, (
        f"synthesised cap should have ocr_confidence=None, got {cap.ocr_confidence}"
    )
    line, words = _line_holding(page, lambda w: w is cap)
    assert line is not None
    assert words[0] is cap
    body = words[1]
    assert body.text == "NCE", f"body word={body.text!r}"
    assert line.text.startswith("ONCE"), f"line.text={line.text!r}"


def test_footnotes_stacked_cursive_cap_unrecovered():
    """Cap glyph skipped by OCR; body word ``"BELIEF"`` is already a
    valid English word, so single-letter prepend inference is ambiguous
    (multiple lexicon hits or none). The geometric trigger fires but
    the letter resolver gives up — closest body Word receives the
    ``"drop cap unrecovered"`` tag and no text rewrite happens.
    """
    page = _load_and_reorganize("footnotes-stacked-with-anchor")
    inferred = [
        w for w in page.words if "drop cap inferred" in (w.word_components or [])
    ]
    unrecovered = [
        w for w in page.words if "drop cap unrecovered" in (w.word_components or [])
    ]
    assert inferred == [], (
        f"BELIEF case should not produce a confident inference; got {[(w.text, w.word_components) for w in inferred]}"
    )
    assert len(unrecovered) >= 1, (
        "expected at least one body Word tagged 'drop cap unrecovered' "
        "near the unresolved cap glyph"
    )
    # The closest body word to the cap region is "BELIEF". It must still
    # appear in the page text (never silently drop OCR words).
    assert "BELIEF" in page.text


def test_body_page_no_false_positive():
    """Negative control. A plain body page (no drop cap, no chapter
    opener) must not grow phantom inferred caps.
    """
    page = _load_and_reorganize("body-running-header-page-number")
    inferred = [
        w for w in page.words if "drop cap inferred" in (w.word_components or [])
    ]
    unrecovered = [
        w for w in page.words if "drop cap unrecovered" in (w.word_components or [])
    ]
    assert inferred == [], (
        f"body page should have no inferred caps, got "
        f"{[(w.text, w.word_components) for w in inferred]}"
    )
    assert unrecovered == [], (
        f"body page should not flag any unrecovered caps, got "
        f"{[(w.text, w.word_components) for w in unrecovered]}"
    )
