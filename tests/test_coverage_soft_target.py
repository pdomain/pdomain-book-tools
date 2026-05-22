"""Test that coverage report surfaces the 88% soft-target indicator."""

import importlib.util
import re
from pathlib import Path

_REPORTER = Path(__file__).parent.parent / "scripts/coverage_reporter.py"


def _load_reporter():
    spec = importlib.util.spec_from_file_location("coverage_reporter", _REPORTER)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_coverage_soft_target_script_exists():
    """Verify that the coverage reporter script exists."""
    assert _REPORTER.exists(), "Coverage reporter script should exist"
    content = _REPORTER.read_text()
    assert "SOFT_TARGET = 88" in content, "Script should define 88% soft target"


def test_reporter_reads_hard_threshold_from_pyproject():
    """The reporter must read the hard gate from pyproject's fail_under (#188).

    The number must never be hard-coded in the script — it has to match
    ``[tool.coverage.report] fail_under`` so the report cannot drift from
    the real CI gate.
    """
    module = _load_reporter()
    pyproject = (Path(__file__).parent.parent / "pyproject.toml").read_text()
    match = re.search(r"^\s*fail_under\s*=\s*(\d+)", pyproject, re.MULTILINE)
    assert match is not None, "pyproject.toml must declare fail_under"
    assert module.get_hard_threshold() == int(match.group(1))


def test_readme_hard_threshold_matches_gate():
    """README's stated hard threshold must match pyproject's fail_under (#188).

    The deep-review finding was that README.md claimed 80% while the real
    gate was 87%. Pin the README number to the actual gate.
    """
    root = Path(__file__).parent.parent
    pyproject = (root / "pyproject.toml").read_text()
    match = re.search(r"^\s*fail_under\s*=\s*(\d+)", pyproject, re.MULTILINE)
    assert match is not None, "pyproject.toml must declare fail_under"
    gate = match.group(1)
    readme = (root / "README.md").read_text()
    assert f"**Hard threshold:** {gate}%" in readme, (
        f"README hard threshold must state {gate}% to match the CI gate"
    )
