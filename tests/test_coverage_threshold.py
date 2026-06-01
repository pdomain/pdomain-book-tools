"""Test that coverage threshold configuration is enforced."""

import configparser
import re
from pathlib import Path


def test_coverage_threshold_configured():
    """Verify that coverage fail_under threshold is set (currently 87% post-branch migration)."""
    pyproject = (Path(__file__).parent.parent / "pyproject.toml").read_text()
    assert "fail_under = 87" in pyproject, (
        "Coverage threshold should be set to 87% (ratcheted from 80% when --cov-branch was added)"
    )


def test_cpu_coverage_config_omits_optional_gpu_backend_and_keeps_gate():
    """CPU-only CI skips CuPy tests, so optional GPU backend files are omitted.

    The hard threshold remains aligned with the normal project coverage gate;
    only the measured source set changes when ``[gpu]`` dependencies are absent.
    """
    root = Path(__file__).parent.parent
    pyproject = root.joinpath("pyproject.toml").read_text()
    match = re.search(r"^\s*fail_under\s*=\s*(\d+)", pyproject, re.MULTILINE)
    assert match is not None, "pyproject.toml must declare fail_under"

    cpu_config_path = root / ".coveragerc.cpu"
    assert cpu_config_path.exists(), "CPU-only coverage config must exist"

    cpu_config = configparser.ConfigParser()
    cpu_config.read(cpu_config_path)
    assert cpu_config.get("report", "fail_under") == match.group(1)

    omit = cpu_config.get("run", "omit")
    assert "*/image_processing/cupy_processing/*" in omit
