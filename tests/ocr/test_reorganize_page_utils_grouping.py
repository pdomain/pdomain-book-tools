import datetime
import json
import os
from difflib import unified_diff
from pathlib import Path

import pytest

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.document import Document
from pd_book_tools.ocr.reorganize_page_utils import (
    build_word_seeded_row_blocks,
    validate_word_preservation,
)
from pd_book_tools.ocr.word import Word

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "layout_regression"
INPUT_DIR = FIXTURE_ROOT / "inputs"
TEXT_BASELINE_DIR = FIXTURE_ROOT / "expected_text" / "baseline"
_TEXT_CURRENT_ROOT = FIXTURE_ROOT / "expected_text" / "current"
_TEXT_DIFF_ROOT = FIXTURE_ROOT / "expected_text" / "diff"
# Per-worker subtree under each output root so xdist workers don't race on
# the session-scoped rmtree (issue #14). When running serially (no xdist),
# ``PYTEST_XDIST_WORKER`` is unset and the suffix is empty — output lands
# directly under the canonical root, preserving legacy behaviour.
_WORKER_ID = os.environ.get("PYTEST_XDIST_WORKER", "")
TEXT_CURRENT_DIR = _TEXT_CURRENT_ROOT / _WORKER_ID if _WORKER_ID else _TEXT_CURRENT_ROOT
TEXT_DIFF_DIR = _TEXT_DIFF_ROOT / _WORKER_ID if _WORKER_ID else _TEXT_DIFF_ROOT
# Debug PNGs / text reports land under a per-run timestamped subfolder so old
# runs accumulate and can be diffed across changes. The whole tree is
# gitignored — `rm -rf debug/` to reclaim disk.
DEBUG_DIR = FIXTURE_ROOT / "debug"


def _w(text: str, x0: float, y0: float, w: float = 0.06, h: float = 0.004) -> Word:
    return Word(
        text=text,
        bounding_box=BoundingBox.from_ltrb(x0, y0, x0 + w, y0 + h),
        ocr_confidence=1.0,
    )


def test_preface_dropcap_is_tagged_and_stitched() -> None:
    """Regression: the oversized initial 'R' on the preface-with-drop-cap
    fixture should be tagged ``word_components=["drop cap"]`` and stitched
    into the same line as the rest of the body word so the text emits as a
    single line.
    """
    import cv2

    from pd_book_tools.ocr.document import Document

    case = "preface-with-drop-cap"
    doc = Document.from_dict(
        json.loads((INPUT_DIR / f"{case}.json").read_text(encoding="utf-8"))
    )
    page = doc.pages[0]
    page.cv2_numpy_page_image = cv2.imread(str(INPUT_DIR / f"{case}.png"))
    page.reorganize_page()

    drop_caps = [w for w in page.words if "drop cap" in (w.word_components or [])]
    assert len(drop_caps) == 1, f"expected exactly 1 drop cap, got {len(drop_caps)}"
    drop = drop_caps[0]
    assert drop.bounding_box is not None
    # The cap word's text is trimmed to a single character (the noisy
    # apostrophe-like artifact from the OCR is dropped) so GT matching
    # downstream sees a clean cap glyph + body word pair.
    assert drop.text == "R", f"cap text={drop.text!r}, expected 'R'"

    # Find the line that holds the drop cap; the body word must follow
    # immediately and the rendered line text must read "READER!" — i.e.
    # the cap and body word are joined with no separator.
    found = False
    for line in page.lines:
        words = list(line.words)
        if drop in words:
            assert words[0] is drop, "drop cap should be the first word of the line"
            assert len(words) >= 2, "drop cap must be followed by a body word"
            assert words[1].text == "EADER!", (
                f"body word text={words[1].text!r}, expected 'EADER!'"
            )
            assert line.text.startswith("READER!"), (
                f"line.text={line.text!r}, expected to start with 'READER!'"
            )
            found = True
            break
    assert found, "drop-cap word not found in any final line"


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


def _new_run_dir(prefix: str) -> Path:
    """Create a fresh timestamped subfolder under :data:`DEBUG_DIR`.

    Used by both the reorganize regression tests and
    :mod:`regenerate_layouts` to give each run its own isolated tree, so a
    human can diff debug PNGs across runs (e.g. before/after a heuristic
    change) without losing the previous output. The prefix
    (``test`` / ``regen``) makes the producer obvious in ``ls -t``.

    Under ``pytest -n auto`` (xdist) every worker enters this
    session-scoped fixture independently. To avoid a TOCTOU race where
    two workers both compute the same wall-clock-second name and race on
    ``mkdir``, the worker id (``PYTEST_XDIST_WORKER``, e.g. ``gw0``) is
    folded into the directory name so each worker gets a disjoint
    subtree. ``exist_ok=True`` then makes the create itself idempotent
    in the unbelievable edge case of a re-collision.
    """
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    worker = os.environ.get("PYTEST_XDIST_WORKER", "")
    suffix = f"-{worker}" if worker else ""
    run = DEBUG_DIR / f"{prefix}-{timestamp}{suffix}"
    counter = 0
    # Disambiguate when two runs land in the same wall-clock second
    # (back-to-back serial invocations; same worker re-entering).
    while run.exists():
        counter += 1
        run = DEBUG_DIR / f"{prefix}-{timestamp}{suffix}.{counter}"
    run.mkdir(parents=True, exist_ok=True)
    return run


@pytest.fixture(scope="session")
def run_dir() -> Path:
    """Per-session debug output directory.

    Each pytest session gets its own ``debug/test-<timestamp>/`` folder so
    a human can diff debug PNGs across runs (e.g. before/after a heuristic
    change) without losing the previous output. Old timestamped runs
    accumulate under ``debug/`` and are gitignored — clean up with
    ``rm -rf debug/`` when they get noisy.
    """
    return _new_run_dir("test")


@pytest.fixture(scope="session", autouse=True)
def _wipe_text_outputs():
    """Wipe per-run text output directories at session start.

    The text-comparison output dirs (``current`` / ``diff``) have no
    historical value — every test invocation rewrites them — so they're
    cleared at session start to keep them canonical. Debug PNGs are *not*
    wiped here; ``run_dir`` gives each session its own subfolder so old
    runs are preserved.

    Under ``pytest -n auto`` (xdist) each worker process runs its own
    copy of this session-scoped fixture. To avoid a TOCTOU race where
    worker A's session-start rmtree fires *after* worker B has already
    mkdir'd ``TEXT_CURRENT_DIR`` and is about to ``write_text`` into it
    (issue #14), each worker scopes its writes to a per-worker subtree
    (``current/<worker_id>/...``) and only wipes its own subtree here.
    Sequential runs (no xdist) keep the legacy behaviour: wipe the
    canonical root.

    ``ignore_errors=True`` keeps the wipe safe even if the dir is
    already absent (first run after a clean checkout).
    """
    import shutil

    for d in (TEXT_CURRENT_DIR, TEXT_DIFF_DIR):
        shutil.rmtree(d, ignore_errors=True)
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


# Cases whose committed baseline reflects the *desired* output the algorithm
# should eventually produce, but which the current pipeline does not yet
# match. Each entry is "case → reason" so the xfail message names the gap
# explicitly. Flip a case off this map (and add a regression note) when the
# behaviour catches up.
KNOWN_FAILING_BASELINES: dict[str, str] = {
    "figures-side-by-side-with-captions": (
        "figure-internal noise: orphan 'A' between body and FIG. 72 caption "
        "should be dropped (small word inside figure region)"
    ),
    "frontispiece-on-deck-dual-caption": (
        "figure-internal noise: 5 char-noise lines from engraving above "
        "the caption should be dropped"
    ),
    "plate-ii-celestial-influences": (
        "figure-internal noise: ~5 single-char lines from circular figure "
        "interior should be dropped"
    ),
    "plate-rio-harbour-photo": (
        "figure-internal noise: ~7 short lines from the photograph should be dropped"
    ),
    "plate-service-on-board": (
        "figure-internal noise: ~5 noise lines from the engraving should be dropped"
    ),
}


def _all_baseline_cases() -> list:
    """Enumerate every case that has both an OCR fixture and a baseline.

    Auto-discovery so adding a new fixture (its `.png` + `.json` + a
    baseline `.reorganize.txt`) is enough to grow the parametrize list —
    no source edit required. Cases listed in :data:`KNOWN_FAILING_BASELINES`
    are wrapped in ``pytest.param(..., marks=xfail(...))`` so CI stays
    green while marking the gap between current output and the baseline
    we want.
    """
    if not TEXT_BASELINE_DIR.exists():
        return []
    cases = []
    for baseline in sorted(TEXT_BASELINE_DIR.glob("*.reorganize.txt")):
        case = baseline.stem.replace(".reorganize", "")
        if (INPUT_DIR / f"{case}.png").exists() and (
            INPUT_DIR / f"{case}.json"
        ).exists():
            xfail_reason = KNOWN_FAILING_BASELINES.get(case)
            if xfail_reason is not None:
                cases.append(
                    pytest.param(
                        case,
                        marks=pytest.mark.xfail(reason=xfail_reason, strict=True),
                    )
                )
            else:
                cases.append(case)
    return cases


@pytest.mark.parametrize("case_name", _all_baseline_cases())
def test_reorganize_page_expected_text_outputs(
    case_name: str, run_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    TEXT_CURRENT_DIR.mkdir(parents=True, exist_ok=True)
    TEXT_DIFF_DIR.mkdir(parents=True, exist_ok=True)

    # By default the test writes per-step debug PNGs + layout-model
    # overlay + the layout debug text report into a per-case folder so a
    # failing diff can be inspected visually without re-running with env
    # vars set by hand. CI runs that don't need the overlays can opt out
    # by setting ``PD_OCR_TEST_NO_DEBUG=1``; on a 30-fixture run the
    # ~7 cv2.imwrite calls per case add measurable wall time.
    debug_pngs_enabled = os.environ.get(
        "PD_OCR_TEST_NO_DEBUG", ""
    ).strip().lower() not in {"1", "true", "yes", "on"}

    case_debug_dir = run_dir / case_name
    if debug_pngs_enabled:
        case_debug_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("PD_OCR_LAYOUT_DEBUG", "1")
        monkeypatch.setenv("PD_OCR_LAYOUT_DEBUG_DIR", str(case_debug_dir))
        # Force the debug text path to a stable filename inside the case dir
        # so all PNG suffixes (e.g. .stepE.png) land next to it.
        monkeypatch.setenv(
            "PD_OCR_LAYOUT_DEBUG_FILE",
            str(case_debug_dir / "layout-debug.txt"),
        )

    # Strict mode is independent of debug PNGs: any future regression
    # that drops an OCR word during reorganize must raise rather than
    # silently auto-recover. Always on.
    monkeypatch.setenv("PD_OCR_REORGANIZE_STRICT", "1")

    # Drop a copy of the layout-model overlay into the same dir so a
    # failing diff can be eyeballed alongside the per-step PNGs. We rebuild
    # this from the committed ``<case>.layout.json`` rather than depend on
    # ``regenerate_layouts.py`` having been run — every pytest run wants
    # its own copy in its own timestamped folder.
    layout_json_path = INPUT_DIR / f"{case_name}.layout.json"
    if debug_pngs_enabled and layout_json_path.exists():
        from pd_book_tools.layout.types import PageLayout
        from pd_book_tools.layout.visualize import draw_layout_overlay

        layout = PageLayout.from_dict(
            json.loads(layout_json_path.read_text(encoding="utf-8"))
        )
        draw_layout_overlay(
            INPUT_DIR / f"{case_name}.png",
            layout,
            case_debug_dir / "layout-regions.png",
        )

    page = _load_fixture_page(case_name)
    # Opt into the legacy word-dropping paths (heuristic figure-noise +
    # layout-region drops) — the committed text baselines were generated
    # against that behaviour, so this test's "intent" is to lock in the
    # post-drop output even though the new default preserves all words.
    # See ``Page.reorganize_page`` docstring for ``drop_layout_words``.
    page.reorganize_page(drop_layout_words=True)
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
