"""Drop-cap recognition regression tests for ``pd_book_tools.ocr.dropcap``.

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

Iteration B: the recovered cap is its own ``Word`` tagged
``word_components=["drop cap"]`` (the iteration-A ``"drop cap inferred"``
tag was consolidated away — the inferred-vs-OCR distinction is carried
by ``ocr_confidence=None`` on synthesised caps instead).
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
    """Cap glyph OCR'd as ``"-"``; body word ``"UPERSTITIONS"`` → inferred
    ``"S"``, kept as its own ``Word`` tagged ``["drop cap"]`` at the front
    of the same line. ``Block.text``'s empty-string-join contract fuses
    cap + body so the rendered line still starts with ``"SUPERSTITIONS"``.
    """
    page = _load_and_reorganize("chapter-head-credulities")
    drop_caps = [w for w in page.words if "drop cap" in (w.word_components or [])]
    assert len(drop_caps) == 1, (
        f"expected exactly 1 drop-cap-tagged Word, got {len(drop_caps)}: "
        f"{[(w.text, w.word_components) for w in drop_caps]}"
    )
    cap = drop_caps[0]
    assert cap.text == "S", f"cap text={cap.text!r}, expected 'S'"
    # Synthesised / inferred caps signal their origin via ocr_confidence=None
    # (the iteration-A "drop cap inferred" tag was consolidated away).
    assert cap.ocr_confidence is None, (
        f"recovered cap should have ocr_confidence=None, got {cap.ocr_confidence}"
    )
    # Structural shape: cap is its own Word, sitting at the front of
    # the line, and the next Word holds the body text.
    line, words = _line_holding(page, lambda w: w is cap)
    assert line is not None, "cap word missing from final lines"
    assert words[0] is cap, "cap should be the first word in the line"
    body = words[1]
    assert body.text == "UPERSTITIONS", f"body word={body.text!r}"
    assert "drop cap" not in (body.word_components or []), (
        "body word must NOT carry the drop cap tag — only the cap itself"
    )
    # The cap bbox must sit to the LEFT of the body word's bbox.
    assert cap.bounding_box.maxX <= body.bounding_box.minX + 0.01, (
        f"cap bbox should be left of body bbox: cap maxX={cap.bounding_box.maxX:.4f}, "
        f"body minX={body.bounding_box.minX:.4f}"
    )
    # Rendering contract: empty-string join → "SUPERSTITIONS".
    assert line.text.startswith("SUPERSTITIONS"), (
        f"line.text={line.text!r}, expected to start with 'SUPERSTITIONS'"
    )


def test_filial_duty_cursive_cap_O_recovered():
    """Cap glyph skipped by OCR; body word ``"NCE"`` → inferred ``"O"``,
    new Word synthesised at the CC bbox, ``Word.ocr_confidence`` is None.
    """
    page = _load_and_reorganize("chapter-head-filial-duty")
    drop_caps = [w for w in page.words if "drop cap" in (w.word_components or [])]
    assert len(drop_caps) == 1, (
        f"expected exactly 1 drop-cap-tagged Word, got {len(drop_caps)}: "
        f"{[(w.text, w.word_components) for w in drop_caps]}"
    )
    cap = drop_caps[0]
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
    assert "drop cap" not in (body.word_components or [])
    assert line.text.startswith("ONCE"), f"line.text={line.text!r}"


def test_footnotes_stacked_cursive_cap_unrecovered():
    """Cap glyph skipped by OCR; body word ``"BELIEF"`` is already a
    valid English word, so single-letter prepend inference is ambiguous
    (multiple lexicon hits or none). The geometric trigger fires but
    the letter resolver gives up — closest body Word receives the
    ``"drop cap unrecovered"`` tag and no text rewrite happens.
    """
    page = _load_and_reorganize("footnotes-stacked-with-anchor")
    drop_caps = [w for w in page.words if "drop cap" in (w.word_components or [])]
    unrecovered = [
        w for w in page.words if "drop cap unrecovered" in (w.word_components or [])
    ]
    assert drop_caps == [], (
        f"BELIEF case should not produce a recovered cap; got "
        f"{[(w.text, w.word_components) for w in drop_caps]}"
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
    opener) must not grow phantom drop caps.
    """
    page = _load_and_reorganize("body-running-header-page-number")
    drop_caps = [w for w in page.words if "drop cap" in (w.word_components or [])]
    unrecovered = [
        w for w in page.words if "drop cap unrecovered" in (w.word_components or [])
    ]
    assert drop_caps == [], (
        f"body page should have no drop caps, got "
        f"{[(w.text, w.word_components) for w in drop_caps]}"
    )
    assert unrecovered == [], (
        f"body page should not flag any unrecovered caps, got "
        f"{[(w.text, w.word_components) for w in unrecovered]}"
    )


# Iteration B structural assertion: every fixture in the regression set
# that has a recovered drop cap must produce exactly one Word tagged
# ``["drop cap"]`` AND that Word must be a separate Word (not a body
# word with the cap letter prepended). The tuple is the (case_name,
# expected_cap_text, expected_body_text_after_cap) triple — the body
# word is what the cap fuses to under Block.text's empty-string-join
# rule, so cap "R" + body "EADER!" renders as "READER!".
_DROP_CAP_FIXTURES = [
    ("preface-with-drop-cap", "R", "EADER!"),
    ("chapter-head-credulities", "S", "UPERSTITIONS"),
    ("chapter-head-filial-duty", "O", "NCE"),
]


@pytest.mark.parametrize(
    ("case", "expected_cap", "expected_body"),
    _DROP_CAP_FIXTURES,
    ids=[case for case, *_ in _DROP_CAP_FIXTURES],
)
def test_known_drop_cap_fixture_keeps_cap_as_separate_word(
    case: str, expected_cap: str, expected_body: str
):
    """Iteration B structural contract: the cap is its own ``Word`` tagged
    ``["drop cap"]``; the body Word that follows is untouched (NOT prepended
    with the cap letter); ``Block.text`` fuses them under the empty-string-
    join rule so the rendered text reads as one logical word.

    Asserting per fixture proves the structural shape AND the rendering
    contract simultaneously: same data, two complementary checks.
    """
    page = _load_and_reorganize(case)
    drop_caps = [w for w in page.words if "drop cap" in (w.word_components or [])]
    assert len(drop_caps) == 1, (
        f"{case}: expected exactly 1 drop-cap-tagged Word, got {len(drop_caps)}: "
        f"{[(w.text, w.word_components) for w in drop_caps]}"
    )
    cap = drop_caps[0]
    assert cap.text == expected_cap, (
        f"{case}: cap text={cap.text!r}, expected {expected_cap!r}"
    )
    # Find the line and verify the body word is its own Word, untouched.
    line, words = _line_holding(page, lambda w: w is cap)
    assert line is not None, f"{case}: cap word missing from final lines"
    assert words[0] is cap, f"{case}: cap should be the first Word in its line"
    assert len(words) >= 2, f"{case}: cap must be followed by a body Word"
    body = words[1]
    assert body.text == expected_body, (
        f"{case}: body Word text={body.text!r}, expected {expected_body!r} "
        f"(must NOT include the cap letter — the cap is a SEPARATE Word)"
    )
    assert "drop cap" not in (body.word_components or []), (
        f"{case}: body Word must not carry the drop cap tag"
    )
    # Rendering contract — the line text reads "<cap><body>..." without a
    # space between cap and body (Block.text's empty-string-join rule).
    fused = expected_cap + expected_body
    assert line.text.startswith(fused), (
        f"{case}: line.text={line.text!r}, expected to start with {fused!r}"
    )
