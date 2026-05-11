"""Test that coverage threshold configuration is enforced."""

from pathlib import Path


def test_coverage_threshold_configured():
    """Verify that coverage fail_under threshold is set to 80%."""
    pyproject = Path("pyproject.toml").read_text()
    assert "fail_under = 80" in pyproject, "Coverage threshold should be set to 80%"
