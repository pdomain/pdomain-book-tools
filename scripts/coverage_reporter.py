#!/usr/bin/env python3
"""Display coverage report with soft-target indicator."""

import xml.etree.ElementTree as ET
from pathlib import Path

SOFT_TARGET = 88
HARD_THRESHOLD = 80


def get_coverage_percentage() -> float | None:
    """Extract total coverage percentage from coverage.xml."""
    coverage_xml = Path("coverage.xml")
    if not coverage_xml.exists():
        return None

    try:
        tree = ET.parse(coverage_xml)
        root = tree.getroot()
        lines_valid = int(root.get("lines-valid", 0))
        lines_covered = int(root.get("lines-covered", 0))
        if lines_valid > 0:
            return (lines_covered / lines_valid) * 100
    except Exception:
        pass

    return None


def main() -> None:
    """Print coverage report with soft-target indicator."""
    coverage_pct = get_coverage_percentage()

    print("\n" + "=" * 70)
    print("COVERAGE THRESHOLD REPORT")
    print("=" * 70)
    print(f"  Hard threshold (fail):   {HARD_THRESHOLD}%")
    print(f"  Soft target (goal):      {SOFT_TARGET}%")
    if coverage_pct is not None:
        print(f"  Current coverage:        {coverage_pct:.1f}%")
        status = "✓" if coverage_pct >= SOFT_TARGET else "⚠"
        print(f"  {status} vs soft target:       {coverage_pct - SOFT_TARGET:+.1f}%")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
