# Agent memory: pd-book-tools

- [Review docs in /loop bug-fix iterations are in scope](feedback_review_doc_strikethrough.md) — edit/commit docs/review/* as part of the loop; auto-fix markdownlint first; do not leave them as eternal staged-adds
- [Review docs can be stale; verify bug exists first](feedback_review_doc_can_be_stale.md) — grep current source before fixing; H-04 was already fixed in 2248366 long before the May 2026 review flagged it
- [Two pre-existing test failures known to flake on this machine, unrelated to any WIP](pre_existing_test_failures.md) — `tests/gpu/test_cuda_functionality.py::TestGPUAvailability::test_skip_in_ci_example` fails on non-CI hosts without a real GPU (it's `@skipif_ci` + asserts `cuda_available`); `test_reorganize_page_expected_text_outputs[frontispiece-madison-portrait]` is flaky under pytest-xdist parallel and passes when run in isolation. Don't attribute these to whatever you're currently changing — verify by running each in isolation.
