"""Test that coverage report surfaces the 88% soft-target indicator."""

from pathlib import Path


def test_coverage_soft_target_script_exists():
    """Verify that the coverage reporter script exists."""
    reporter = Path(__file__).parent.parent / "scripts/coverage_reporter.py"
    assert reporter.exists(), "Coverage reporter script should exist"
    content = reporter.read_text()
    assert "SOFT_TARGET = 88" in content, "Script should define 88% soft target"
    assert "HARD_THRESHOLD = 80" in content, "Script should define 80% hard threshold"
