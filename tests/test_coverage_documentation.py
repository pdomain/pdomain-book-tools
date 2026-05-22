"""Test that coverage thresholds are documented."""

import re
from pathlib import Path


def test_readme_documents_coverage_thresholds():
    """Verify that README documents the coverage thresholds.

    The hard threshold stated in README must match the real CI gate
    (``[tool.coverage.report] fail_under`` in pyproject.toml) so the docs
    cannot drift from the gate (#188).
    """
    root = Path(__file__).parent.parent
    readme = root.joinpath("README.md").read_text()
    pyproject = root.joinpath("pyproject.toml").read_text()
    match = re.search(r"^\s*fail_under\s*=\s*(\d+)", pyproject, re.MULTILINE)
    assert match is not None, "pyproject.toml must declare fail_under"
    gate = match.group(1)
    assert f"{gate}%" in readme, (
        f"README should mention the {gate}% hard threshold (the CI gate)"
    )
    assert "88%" in readme, "README should mention the 88% soft target"
    assert "coverage" in readme.lower(), "README should mention coverage testing"
