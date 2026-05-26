"""Verify the CI-detection helper and ``skipif_ci`` marker behavior.

These tests do **not** require a GPU. They cover:

1. ``_is_ci_environment()`` — direct unit tests using ``monkeypatch`` to
   set/clear the env vars it inspects.
2. ``skipif_ci`` — an integration test using pytest's ``pytester`` fixture
   that spawns an inner pytest run with ``CI=true`` and asserts that a
   ``@skipif_ci``-decorated test is reported as skipped.
"""

from __future__ import annotations

import textwrap

import pytest

from tests.conftest import _is_ci_environment

# Enable the bundled ``pytester`` plugin for the inner-pytest tests below.
pytest_plugins = ["pytester"]

# Every env var the helper considers a CI indicator.
CI_VARS = (
    "CI",
    "GITHUB_ACTIONS",
    "GITLAB_CI",
    "JENKINS_URL",
    "BUILDKITE",
    "CIRCLECI",
    "TRAVIS",
)


def _clear_ci_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in CI_VARS:
        monkeypatch.delenv(var, raising=False)


class TestIsCiEnvironment:
    def test_returns_false_when_all_ci_vars_unset(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_ci_env(monkeypatch)
        assert _is_ci_environment() is False

    def test_returns_true_when_ci_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_ci_env(monkeypatch)
        monkeypatch.setenv("CI", "true")
        assert _is_ci_environment() is True

    @pytest.mark.parametrize("var", CI_VARS)
    def test_returns_true_for_each_indicator(
        self, monkeypatch: pytest.MonkeyPatch, var: str
    ) -> None:
        _clear_ci_env(monkeypatch)
        monkeypatch.setenv(var, "1")
        assert _is_ci_environment() is True, f"expected True when {var} is set"

    def test_empty_string_treated_as_unset(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # ``os.getenv`` returns "" for an explicitly-empty var, which is falsy.
        _clear_ci_env(monkeypatch)
        monkeypatch.setenv("CI", "")
        assert _is_ci_environment() is False


# Minimal conftest mirroring the production helper + marker so the inner
# pytest doesn't need to import the full pdomain_book_tools test suite.
_INNER_CONFTEST = textwrap.dedent(
    """
    import os
    import pytest

    def _is_ci_environment():
        ci_indicators = [
            "CI", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_URL",
            "BUILDKITE", "CIRCLECI", "TRAVIS",
        ]
        return any(os.getenv(i) for i in ci_indicators)

    skipif_ci = pytest.mark.skipif(
        _is_ci_environment(), reason="Skipping GPU tests in CI environment"
    )
    """
)


class TestSkipifCiMarker:
    """Spawn an inner pytest run to verify ``skipif_ci`` actually skips."""

    def test_skipif_ci_skips_under_ci_env(
        self, pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pytester.makeconftest(_INNER_CONFTEST)
        pytester.makepyfile(
            """
            from conftest import skipif_ci

            @skipif_ci
            def test_should_be_skipped_in_ci():
                assert True
            """
        )

        _clear_ci_env(monkeypatch)
        monkeypatch.setenv("CI", "true")

        result = pytester.runpytest_subprocess("-v")
        result.assert_outcomes(skipped=1)

    def test_skipif_ci_runs_when_ci_unset(
        self, pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pytester.makeconftest(_INNER_CONFTEST)
        pytester.makepyfile(
            """
            from conftest import skipif_ci

            @skipif_ci
            def test_should_run_when_not_in_ci():
                assert True
            """
        )

        _clear_ci_env(monkeypatch)

        result = pytester.runpytest_subprocess("-v")
        result.assert_outcomes(passed=1)
