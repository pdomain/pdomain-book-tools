#!/usr/bin/env python3
"""Display coverage report with soft-target indicator.

The hard threshold (CI-failing gate) is the single source of truth in
``pyproject.toml`` under ``[tool.coverage.report] fail_under``. This
script reads it from there so the reported number can never drift from
the real gate (#188).
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SOFT_TARGET = 88
_DEFAULT_HARD_THRESHOLD = 87


def get_hard_threshold() -> int:
    """Read the hard coverage gate from ``[tool.coverage.report] fail_under``.

    Falls back to ``_DEFAULT_HARD_THRESHOLD`` if pyproject.toml is missing
    or does not declare ``fail_under``.
    """
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    if not pyproject.exists():
        return _DEFAULT_HARD_THRESHOLD
    match = re.search(
        r"^\s*fail_under\s*=\s*(\d+(?:\.\d+)?)",
        pyproject.read_text(),
        re.MULTILINE,
    )
    if match is None:
        return _DEFAULT_HARD_THRESHOLD
    return int(float(match.group(1)))


def get_coverage_percentage() -> float | None:
    """Extract total coverage percentage from coverage.xml."""
    coverage_xml = Path("coverage.xml")
    if not coverage_xml.exists():
        return None

    try:
        tree = ET.parse(coverage_xml)  # noqa: S314  # source is local CI-generated coverage.xml, not user input
        root = tree.getroot()
        lines_valid = int(root.get("lines-valid", 0))
        lines_covered = int(root.get("lines-covered", 0))
        if lines_valid > 0:
            return (lines_covered / lines_valid) * 100
    except Exception as e:  # noqa: BLE001  # final fallback: any parse failure returns None
        print(f"coverage_reporter: failed to parse coverage.xml: {e}", file=sys.stderr)
        return None

    return None


def main() -> None:
    """Print coverage report with soft-target indicator."""
    coverage_pct = get_coverage_percentage()
    hard_threshold = get_hard_threshold()

    print("\n" + "=" * 70)
    print("COVERAGE THRESHOLD REPORT")
    print("=" * 70)
    print(f"  Hard threshold (fail):   {hard_threshold}%")
    print(f"  Soft target (goal):      {SOFT_TARGET}%")
    if coverage_pct is not None:
        print(f"  Current coverage:        {coverage_pct:.1f}%")
        status = "✓" if coverage_pct >= SOFT_TARGET else "⚠"
        print(f"  {status} vs soft target:       {coverage_pct - SOFT_TARGET:+.1f}%")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
