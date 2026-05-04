import json
from difflib import unified_diff
from pathlib import Path

import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.document import Document
from pd_book_tools.ocr.reorganize_page_utils import (
    _split_group_second_pass,
    build_word_seeded_row_blocks,
    validate_word_preservation,
)
from pd_book_tools.ocr.word import Word

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "layout_regression"
INPUT_DIR = FIXTURE_ROOT / "inputs"
TEXT_BASELINE_DIR = FIXTURE_ROOT / "expected_text" / "baseline"
TEXT_CURRENT_DIR = FIXTURE_ROOT / "expected_text" / "current"
TEXT_DIFF_DIR = FIXTURE_ROOT / "expected_text" / "diff"
# Debug PNGs / text reports for each pipeline step land here, one folder per
# fixture case. Keeping the location alongside baseline/current/diff makes the
# entire reorganize pipeline state inspectable after every test run.
DEBUG_DIR = FIXTURE_ROOT / "debug"


def _w(text: str, x0: float, y0: float, w: float = 0.06, h: float = 0.004) -> Word:
    return Word(
        text=text,
        bounding_box=BoundingBox.from_ltrb(x0, y0, x0 + w, y0 + h),
        ocr_confidence=1.0,
    )


def test_seeded_row_blocks_keep_single_word_component() -> None:
    """Regression: a single-word connected component (e.g. a centered chapter
    heading like ``PREFACE.`` sitting in its own vertical band) must not be
    dropped by the seeded row-block grouping.

    Before this guard, ``build_word_seeded_row_blocks`` filtered components
    with ``len(comp) >= 2``, which silently lost any standalone heading and
    caused ``Page.reorganize_page`` to omit it from ``page.text``.
    """
    pre_words = [
        # Standalone heading with a wide gap to the body below.
        _w("PREFACE.", x0=0.40, y0=0.10, w=0.20, h=0.025),
    ]
    # Build a small body block well below the heading. Enough words to clear
    # the seeded-row-block threshold (needs >= 10 words total) while sharing
    # only one connected component with each other.
    for row_y in (0.30, 0.33, 0.36):
        for col, txt in enumerate(("the", "quick", "brown", "fox")):
            pre_words.append(_w(txt, x0=0.10 + 0.08 * col, y0=row_y, w=0.07, h=0.020))

    row_blocks = build_word_seeded_row_blocks(
        pre_words, page_width=1000, page_height=1000
    )

    assert row_blocks is not None
    post_words = [
        word
        for paragraph in row_blocks.items
        for line in paragraph.lines
        for word in line.words
    ]
    drops = validate_word_preservation(pre_words, post_words)
    assert drops == [], drops
    assert any((w.text or "") == "PREFACE." for w in post_words), (
        "PREFACE. dropped by seeded row-block grouping"
    )


def test_step1b_does_not_split_when_only_left_side_breaks() -> None:
    """Regression guard for one-sided gap boundaries around embedded figure bands.

    The left side disappears across one inter-band boundary while the right side
    remains vertically continuous. Step 1b should keep this as one group.
    """

    words: list[Word] = []

    # Band 0 (full width)
    y0 = 0.100
    words.extend(
        [
            _w("b0l1", 0.06, y0),
            _w("b0l2", 0.14, y0),
            _w("b0r1", 0.76, y0),
            _w("b0r2", 0.84, y0),
        ]
    )

    # Band 1 (full width)
    y1 = 0.105  # gap from band 0: 0.001
    words.extend(
        [
            _w("b1l1", 0.06, y1),
            _w("b1l2", 0.14, y1),
            _w("b1r1", 0.76, y1),
            _w("b1r2", 0.84, y1),
        ]
    )

    # Band 2 (right side only)
    # gap from band 1: 0.005 (large enough to be a hard-gap candidate)
    y2 = 0.114
    words.extend(
        [
            _w("b2r1", 0.76, y2),
            _w("b2r2", 0.84, y2),
            _w("b2r3", 0.90, y2),
        ]
    )

    # Band 3 (full width continuation)
    y3 = 0.119  # gap from band 2: 0.001
    words.extend(
        [
            _w("b3l1", 0.06, y3),
            _w("b3l2", 0.14, y3),
            _w("b3r1", 0.76, y3),
            _w("b3r2", 0.84, y3),
        ]
    )

    split = _split_group_second_pass(words, coord_width=1.0)

    assert len(split) == 1
    assert len(split[0]) == len(words)


@pytest.fixture(scope="session", autouse=True)
def _wipe_debug_outputs():
    """Clear the debug + per-run text/diff output trees before any tests run.

    The reorganize regression tests write debug PNGs, the layout debug report,
    and the unified diff into ``tests/fixtures/layout_regression/``. Wiping the
    output trees once per pytest session keeps the directory canonical: a
    removed test case never leaves a stale folder behind, a renamed pipeline
    step doesn't leave behind an old PNG, and the diff against baseline always
    reflects the current run.
    """
    import shutil

    for d in (DEBUG_DIR, TEXT_CURRENT_DIR, TEXT_DIFF_DIR):
        if d.exists():
            shutil.rmtree(d)
    yield


def _load_fixture_page(case_name: str):
    doc_dict = json.loads((INPUT_DIR / f"{case_name}.json").read_text(encoding="utf-8"))
    page = Document.from_dict(doc_dict).pages[0]
    page.name = case_name
    page.image_path = INPUT_DIR / f"{case_name}.png"

    cv2 = pytest.importorskip("cv2")
    image = cv2.imread(str(INPUT_DIR / f"{case_name}.png"))
    assert image is not None, f"Failed to load fixture image for {case_name}"
    page.cv2_numpy_page_image = image
    page.refine_bounding_boxes()
    return page


@pytest.mark.parametrize("case_name", ["test1", "test2", "test3"])
def test_reorganize_page_expected_text_outputs(
    case_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    TEXT_CURRENT_DIR.mkdir(parents=True, exist_ok=True)
    TEXT_DIFF_DIR.mkdir(parents=True, exist_ok=True)

    # Always write per-step debug PNGs and the layout debug text report
    # into a per-case folder so a failing diff can be inspected visually
    # without re-running with environment variables set by hand. The
    # session-scoped fixture above wipes the debug tree once per run, so we
    # only need to recreate the case folder here.
    case_debug_dir = DEBUG_DIR / case_name
    case_debug_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("PD_OCR_LAYOUT_DEBUG", "1")
    monkeypatch.setenv("PD_OCR_LAYOUT_DEBUG_DIR", str(case_debug_dir))
    # Strict mode: any future regression that drops an OCR word during
    # reorganize must raise here rather than silently auto-recover.
    monkeypatch.setenv("PD_OCR_REORGANIZE_STRICT", "1")
    # Force the debug text path to a stable filename inside the case dir so
    # all PNG suffixes (e.g. .stepE.png) land next to it deterministically.
    monkeypatch.setenv(
        "PD_OCR_LAYOUT_DEBUG_FILE",
        str(case_debug_dir / "layout-debug.txt"),
    )

    page = _load_fixture_page(case_name)
    page.reorganize_page()
    current_text = (page.text or "").rstrip() + "\n"

    baseline_path = TEXT_BASELINE_DIR / f"{case_name}.reorganize.txt"
    current_path = TEXT_CURRENT_DIR / f"{case_name}.reorganize.txt"
    diff_path = TEXT_DIFF_DIR / f"{case_name}.reorganize.diff.txt"

    current_path.write_text(current_text, encoding="utf-8")
    assert baseline_path.exists(), (
        f"Missing expected text baseline. Create it at: {baseline_path}"
    )

    expected_text = baseline_path.read_text(encoding="utf-8")
    diff_text = "".join(
        unified_diff(
            expected_text.splitlines(keepends=True),
            current_text.splitlines(keepends=True),
            fromfile=str(baseline_path),
            tofile=str(current_path),
        )
    )
    diff_path.write_text(diff_text, encoding="utf-8")

    assert current_text == expected_text
