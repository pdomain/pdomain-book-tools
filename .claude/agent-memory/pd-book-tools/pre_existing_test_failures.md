# Pre-existing test failures on this dev container

These two failures are not caused by recent WIP changes — they reproduce
on a clean `master` and on a CPU-only / dev-container host.

## 1. `tests/gpu/test_cuda_functionality.py::TestGPUAvailability::test_skip_in_ci_example`

Decorated `@skipif_ci`, asserts `cuda_available`. So it skips in GitHub
Actions but is *expected* to fail on any local host that doesn't actually
have CUDA available (this dev container does not). Author intent was
"only run on a developer's GPU box."

To verify it's not your change: run `make test` on a clean checkout of
`master`. If you want a clean test run on a CPU-only host, target around
it: `uv run pytest -k "not test_skip_in_ci_example"` or similar.

## 2. `tests/ocr/test_reorganize_page_utils_grouping.py::test_reorganize_page_expected_text_outputs[frontispiece-madison-portrait]`

Flaky under `pytest-xdist` parallel execution (which `make test` uses).
Passes deterministically when run in isolation:

    uv run pytest "tests/ocr/test_reorganize_page_utils_grouping.py::test_reorganize_page_expected_text_outputs[frontispiece-madison-portrait]"

Likely a fixture/state ordering issue between workers. Worth a separate
investigation — but don't blame it on whatever else you're touching.
