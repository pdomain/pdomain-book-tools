"""Dump the current `Page.reorganize_page` output for a fixture case.

Use when bootstrapping a new ``expected_text/baseline/<case>.reorganize.txt``:

    python tests/fixtures/layout_regression/dump_reorganize_output.py preface-with-drop-cap

Prints the reorganize pipeline's textual output to stdout. Pipe / redirect
into ``expected_text/baseline/<case>.reorganize.txt`` once you've eyeballed
the result against the source PNG and confirmed it's what you expect.

Inputs read from ``tests/fixtures/layout_regression/inputs/<case>.{json,png}``.
This is intentionally a thin script — it does not write files, lint, or run
tests; it only invokes the reorganize pipeline and prints the output.
"""
# standalone CLI script — print is the output mechanism

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT / "inputs"

# Make the local pdomain_book_tools package importable when this script is run
# directly (e.g. from the repo root) without an installed editable build.
PACKAGE_ROOT = ROOT.parents[2]  # tests/fixtures/layout_regression -> tests -> repo
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))


def dump_case(case_name: str) -> str:
    json_path = INPUT_DIR / f"{case_name}.json"
    png_path = INPUT_DIR / f"{case_name}.png"
    if not json_path.exists():
        raise SystemExit(f"missing fixture JSON: {json_path}")
    if not png_path.exists():
        raise SystemExit(f"missing fixture PNG: {png_path}")

    import cv2

    from pdomain_book_tools.ocr.document import Document

    doc = Document.from_dict(json.loads(json_path.read_text(encoding="utf-8")))
    page = doc.pages[0]
    page.name = case_name
    image = cv2.imread(str(png_path))
    if image is None:
        raise SystemExit(f"failed to load fixture image: {png_path}")
    page.cv2_numpy_page_image = image
    page.refine_bounding_boxes()
    # Opt into the legacy word-dropping paths so freshly-dumped baselines
    # match the regression test's expectation (it also passes
    # ``drop_layout_words=True``). The new default preserves all words; if
    # you want a baseline with footnotes/figure-noise included, drop the
    # kwarg.
    page.reorganize_page(drop_layout_words=True)
    return (page.text or "").rstrip() + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: dump_reorganize_output.py <case_name>", file=sys.stderr)
        return 2
    sys.stdout.write(dump_case(argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
