"""Regenerate cached PageLayout JSON for every fixture image.

Tests load these JSONs (via :meth:`PageLayout.from_dict`) instead of running
the model — so the test suite stays fast and doesn't need GPU, network, or a
132 MB checkpoint download. Run this script when:

  * a new fixture image is added to ``inputs/``
  * the layout adapter / pinned model SHA changes
  * the ``PP_DOCLAYOUT_TO_PGDP`` mapping changes

Outputs land in ``inputs/<case>.layout.json`` alongside the source image and
OCR Page JSON, so each ``test<N>`` case is a self-contained triple
(``test<N>.png`` + ``test<N>.json`` + ``test<N>.layout.json``).

Usage:

    # Regenerate everything
    python tests/fixtures/layout_regression/regenerate_layouts.py

    # Regenerate one case
    python tests/fixtures/layout_regression/regenerate_layouts.py preface-with-drop-cap

    # Pick a different detector (e.g. for comparison)
    LAYOUT_DETECTOR=contour python tests/fixtures/layout_regression/regenerate_layouts.py
"""
# standalone CLI fixture script — print is progress reporting

from __future__ import annotations

import datetime
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT / "inputs"
# Layout JSON lands alongside the .png / .json so each test case is one
# self-contained directory of inputs.
OUTPUT_DIR = INPUT_DIR
# Per-run debug overlays — gitignored, regenerated on demand. Each
# invocation creates its own timestamped subfolder so a human can eyeball
# "did the model find the right boxes" across SHA pins or threshold
# tweaks without losing the previous overlay.
DEBUG_DIR = ROOT / "debug"


def _new_run_dir() -> Path:
    """Create a fresh ``debug/regen-<timestamp>/`` subfolder for this run.

    Mirrors the convention used by the reorganize regression tests
    (which produce ``debug/test-<timestamp>/``) so a human reading
    ``ls -t debug/`` can tell which producer wrote each folder.
    """
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    run = DEBUG_DIR / f"regen-{timestamp}"
    counter = 0
    while run.exists():
        counter += 1
        run = DEBUG_DIR / f"regen-{timestamp}.{counter}"
    run.mkdir(parents=True)
    return run


# Make the local package importable when run directly from a checkout
# without an installed editable build.
PACKAGE_ROOT = ROOT.parents[2]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))


def _draw_overlay(png_path: Path, layout, dest: Path) -> None:
    """Thin wrapper around :func:`pdomain_book_tools.layout.visualize.draw_layout_overlay`.

    Kept as a local name for backwards-compat with anyone shelling out to
    this script directly; new callers should import the public helper.
    """
    from pdomain_book_tools.layout.visualize import (
        draw_layout_overlay,
    )

    if draw_layout_overlay(png_path, layout, dest) is None:
        print(f"  (skipping overlay — could not read {png_path})")


def regenerate(case_name: str, detector_key: str, run_dir: Path) -> Path:
    from pdomain_book_tools.layout import get_detector

    png_path = INPUT_DIR / f"{case_name}.png"
    if not png_path.exists():
        raise SystemExit(f"missing fixture PNG: {png_path}")

    detector = get_detector(detector_key)
    layout = detector.detect(png_path)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{case_name}.layout.json"
    out_path.write_text(json.dumps(layout.to_dict(), indent=2) + "\n")

    overlay_path = run_dir / case_name / "layout-regions.png"
    _draw_overlay(png_path, layout, overlay_path)

    print(
        f"  {case_name}: {len(layout.regions)} regions "
        f"({layout.inference_ms} ms) → {out_path.relative_to(PACKAGE_ROOT)}"
    )
    print(f"      overlay → {overlay_path.relative_to(PACKAGE_ROOT)}")
    return out_path


def main(argv: list[str]) -> int:
    detector_key = os.environ.get("LAYOUT_DETECTOR", "pp-doclayout-plus-l")
    print(f"Detector: {detector_key}")

    run_dir = _new_run_dir()
    print(f"Overlays → {run_dir.relative_to(PACKAGE_ROOT)}/")

    if argv:
        cases = argv
    else:
        cases = sorted(p.stem for p in INPUT_DIR.glob("*.png"))
        if not cases:
            raise SystemExit(f"no PNGs in {INPUT_DIR}")

    for case in cases:
        regenerate(case, detector_key, run_dir)
    print(
        f"Done. {len(cases)} case(s) written to {OUTPUT_DIR.relative_to(PACKAGE_ROOT)}/"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
