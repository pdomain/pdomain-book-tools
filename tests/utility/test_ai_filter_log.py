"""Unit tests for ``scripts/ai-filter-log.py``.

The script extracts failure-relevant sections from a captured ``make ci``
log. To avoid excessive memory/CPU on pathologically large CI logs it
caps the amount of input it accepts: oversized logs are read tail-first
up to a byte budget rather than slurped whole.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "ai-filter-log.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("ai_filter_log", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_read_log_returns_small_file_whole(tmp_path: Path):
    mod = _load_script_module()
    log = tmp_path / "small.log"
    log.write_text("line one\nline two\n", encoding="utf-8")
    assert mod.read_log(log) == "line one\nline two\n"


def test_read_log_caps_oversized_input(tmp_path: Path):
    mod = _load_script_module()
    cap = mod.MAX_INPUT_BYTES
    log = tmp_path / "huge.log"
    # Write more than the cap; the marker line at the very end must survive.
    filler = "x" * (cap + 1_000_000)
    log.write_text(filler + "\nFINAL FAILURE MARKER\n", encoding="utf-8")
    text = mod.read_log(log)
    # Capped: must not exceed the budget by more than a small margin.
    assert len(text.encode("utf-8")) <= cap
    # Tail-biased: the most recent (failure-relevant) content is retained.
    assert "FINAL FAILURE MARKER" in text


def test_max_input_bytes_is_bounded(tmp_path: Path):
    mod = _load_script_module()
    # A sane upper bound — large enough for real CI logs, small enough to
    # protect against multi-GB inputs.
    assert 1_000_000 <= mod.MAX_INPUT_BYTES <= 100_000_000
