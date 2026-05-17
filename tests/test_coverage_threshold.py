"""Test that coverage threshold configuration is enforced."""

from pathlib import Path


def test_coverage_threshold_configured():
    """Verify that coverage fail_under threshold is set (currently 87% post-branch migration)."""
    pyproject = (Path(__file__).parent.parent / "pyproject.toml").read_text()
    assert "fail_under = 87" in pyproject, (
        "Coverage threshold should be set to 87% (ratcheted from 80% when --cov-branch was added)"
    )
