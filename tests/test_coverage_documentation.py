"""Test that coverage thresholds are documented."""

from pathlib import Path


def test_readme_documents_coverage_thresholds():
    """Verify that README documents the coverage thresholds."""
    readme = Path("README.md").read_text()
    assert "80%" in readme, "README should mention the 80% hard threshold"
    assert "88%" in readme, "README should mention the 88% soft target"
    assert "coverage" in readme.lower(), "README should mention coverage testing"
