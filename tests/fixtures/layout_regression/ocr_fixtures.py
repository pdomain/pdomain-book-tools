"""Run DocTR OCR on every fixture image that lacks a paired ``.json``.

Tests load these JSONs (via :class:`Document.from_dict`) instead of running
DocTR — so the test suite stays fast and doesn't need GPU or network. Run
this script when:

  * a new fixture image is added to ``inputs/``
  * the OCR predictor / pinned model SHA changes

Outputs land in ``inputs/<case>.json`` alongside the source image. Existing
JSONs are skipped unless ``--force`` is passed.

Usage:

    # OCR everything missing a .json
    python tests/fixtures/layout_regression/ocr_fixtures.py

    # OCR one case (regenerate)
    python tests/fixtures/layout_regression/ocr_fixtures.py \
        chapter-head-credulities --force

    # OCR everything, regenerating existing JSONs too
    python tests/fixtures/layout_regression/ocr_fixtures.py --force
"""
# standalone CLI fixture script — print is progress reporting

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pdomain_book_tools.ocr.document import _DoctrPredictor

ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT / "inputs"

# Make the local pdomain_book_tools package importable when this script is run
# directly without an installed editable build.
PACKAGE_ROOT = ROOT.parents[2]  # tests/fixtures/layout_regression -> tests -> repo
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))


def _ocr_one(case: str, predictor: _DoctrPredictor) -> None:
    from pdomain_book_tools.ocr.document import Document

    png = INPUT_DIR / f"{case}.png"
    out = INPUT_DIR / f"{case}.json"
    if not png.exists():
        raise SystemExit(f"missing fixture PNG: {png}")
    t0 = time.perf_counter()
    doc, _rotation = Document.from_image_ocr_via_doctr(image=png, predictor=predictor)
    elapsed = time.perf_counter() - t0
    out.write_text(json.dumps(doc.to_dict(), indent=2), encoding="utf-8")
    print(f"  {case}: OCR in {elapsed:.1f}s -> {out.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "case",
        nargs="?",
        help="Specific case to OCR (default: all cases missing a .json)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if <case>.json already exists",
    )
    args = parser.parse_args()

    pngs = sorted(INPUT_DIR.glob("*.png"))
    if args.case:
        pngs = [p for p in pngs if p.stem == args.case]
        if not pngs:
            raise SystemExit(f"no fixture matching {args.case!r}")

    cases = [p.stem for p in pngs]
    if not args.force:
        cases = [c for c in cases if not (INPUT_DIR / f"{c}.json").exists()]

    if not cases:
        print("Nothing to do — every fixture already has a .json")
        return

    # Lazy import: don't pay the DocTR import cost when the user just wants
    # --help.
    from pdomain_book_tools.ocr.doctr_support import get_default_doctr_predictor

    print("Loading default DocTR predictor (cached after first run)...")
    t0 = time.perf_counter()
    predictor = get_default_doctr_predictor()
    print(f"  predictor ready in {time.perf_counter() - t0:.1f}s")

    print(f"OCRing {len(cases)} case(s)...")
    for case in cases:
        _ocr_one(case, predictor)


if __name__ == "__main__":
    main()
