"""Tests for utility.timing module."""

from __future__ import annotations

import logging
import time
import warnings
from typing import TYPE_CHECKING, ParamSpec, TypeVar

import pytest

if TYPE_CHECKING:
    import inspect
    from collections.abc import Callable

from pdomain_book_tools.utility.timing import (
    func_log_excution_time as _deprecated_alias,
)
from pdomain_book_tools.utility.timing import (
    func_log_execution_time,
)

_P = ParamSpec("_P")
_R = TypeVar("_R")


def func_log_excution_time(
    logger: logging.Logger,
    logLevel: int | None = None,  # noqa: N803 -- mirrors the deprecated production kwarg
    log_level: int | None = None,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    """Test shim that calls the deprecated alias while suppressing the
    DeprecationWarning it emits — keeps the existing test bodies focused
    on behavior rather than warning hygiene. Tests of the deprecation
    behavior itself call ``_deprecated_alias`` directly below.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return _deprecated_alias(logger, logLevel=logLevel, log_level=log_level)


class TestFuncLogExecutionTime:
    """Test the func_log_excution_time decorator."""

    def test_returns_function_result(self) -> None:
        """Decorator should not change the wrapped function's return value."""
        logger = logging.getLogger("test_returns_function_result")

        @func_log_excution_time(logger)
        def add(a: int, b: int) -> int:
            return a + b

        assert add(2, 3) == 5

    def test_passes_args_and_kwargs(self) -> None:
        """Decorator should forward positional and keyword arguments."""
        logger = logging.getLogger("test_passes_args_and_kwargs")

        @func_log_excution_time(logger)
        def combine(a: str, b: str, sep: str = " ") -> str:
            return f"{a}{sep}{b}"

        assert combine("hello", "world", sep="-") == "hello-world"

    def test_logs_at_specified_level(self, caplog: pytest.LogCaptureFixture) -> None:
        """Decorator should log at the requested log level."""
        logger = logging.getLogger("test_logs_at_specified_level")
        logger.setLevel(logging.INFO)

        @func_log_excution_time(logger, logLevel=logging.INFO)
        def noop() -> str:
            return "ok"

        with caplog.at_level(logging.INFO, logger="test_logs_at_specified_level"):
            result = noop()

        assert result == "ok"
        # Expect at least the start and end log records
        messages = [r.getMessage() for r in caplog.records]
        assert any("started at" in m for m in messages)
        assert any("ended at" in m for m in messages)

    def test_default_log_level_debug(self, caplog: pytest.LogCaptureFixture) -> None:
        """Default level should be DEBUG and emit start/end records."""
        logger = logging.getLogger("test_default_log_level_debug")
        logger.setLevel(logging.DEBUG)

        @func_log_excution_time(logger)
        def quick() -> int:
            return 42

        with caplog.at_level(logging.DEBUG, logger="test_default_log_level_debug"):
            quick()

        messages = [r.getMessage() for r in caplog.records]
        assert any("started at" in m for m in messages)
        assert any("ended at" in m for m in messages)

    def test_preserves_function_metadata(self) -> None:
        """functools.wraps should preserve __name__ and docstring."""
        logger = logging.getLogger("test_preserves_function_metadata")

        @func_log_excution_time(logger)
        def documented() -> None:
            """A docstring."""
            return

        assert documented.__name__ == "documented"
        assert documented.__doc__ == "A docstring."

    def test_propagates_exception(self) -> None:
        """Exceptions raised inside the wrapped function must propagate."""
        logger = logging.getLogger("test_propagates_exception")

        @func_log_excution_time(logger)
        def raises() -> None:
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            raises()

    def test_call_site_log_uses_injected_logger(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """L-28 regression: the "Function X called from Y" line must be
        emitted on the *injected* logger, not the root ``logging`` module.

        Pre-fix the line was routed through ``logging.log(...)`` (root
        logger) so any caller-side per-module logger configuration was
        bypassed for this specific record. Asserts the record's
        ``name`` matches the injected logger and that the message is
        observable when only that logger is captured.
        """
        injected_name = "test_call_site_log_uses_injected_logger.injected"
        injected = logging.getLogger(injected_name)
        injected.setLevel(logging.DEBUG)

        @func_log_excution_time(injected)
        def noop() -> None:
            return None

        with caplog.at_level(logging.DEBUG, logger=injected_name):
            noop()

        called_records = [r for r in caplog.records if "called from" in r.getMessage()]
        assert called_records, "expected the 'called from' log line to be captured"
        # Every captured 'called from' record must be on the injected logger.
        for r in called_records:
            assert r.name == injected_name, (
                f"L-28: 'called from' record was emitted on {r.name!r}, "
                f"expected the injected logger {injected_name!r}"
            )

    def test_call_site_log_does_not_emit_raw_arg_values(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """L-29 regression: the call-site log must not include raw
        argument values. Pre-fix the wrapper formatted ``args`` and
        ``kwargs`` directly into the log message, producing megabytes
        of output for NumPy/CuPy arrays and risking inadvertent
        logging of sensitive values.

        Asserts that a unique sentinel string passed both positionally
        and via kwargs does NOT appear in any captured log message,
        while the count / type summary does.
        """
        logger = logging.getLogger("test_call_site_log_does_not_emit_raw_arg_values")
        logger.setLevel(logging.DEBUG)
        sentinel = "PDOMAIN_BOOK_TOOLS_L29_SECRET_VALUE_DO_NOT_LOG"

        @func_log_excution_time(logger)
        def takes_args(positional: str, *, kw: str) -> None:
            return None

        with caplog.at_level(
            logging.DEBUG, logger="test_call_site_log_does_not_emit_raw_arg_values"
        ):
            takes_args(sentinel, kw=sentinel)

        all_messages = "\n".join(r.getMessage() for r in caplog.records)
        assert sentinel not in all_messages, (
            "L-29: raw argument value leaked into the timing log"
        )
        # Positive assertion: the count/type summary IS emitted.
        assert "1 positional args" in all_messages
        assert "1 kwargs" in all_messages
        assert "str" in all_messages  # type name of the sentinel arg

    def test_inspect_stack_skipped_when_logger_disabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """L-30 regression: ``inspect.stack()`` is expensive (it walks the
        whole Python call stack) and must not run on every decorated
        invocation when the logger will not emit at ``logLevel``.

        Patches ``inspect.stack`` on the timing module to a sentinel that
        records call count, then invokes a DEBUG-decorated function with
        the injected logger pinned at WARNING (DEBUG is suppressed).
        Pre-fix the wrapper called ``inspect.stack`` unconditionally so
        the counter incremented; post-fix the call is gated by
        ``logger.isEnabledFor(logLevel)`` and the counter stays at 0.
        """
        from pdomain_book_tools.utility import timing as timing_mod

        call_count = {"n": 0}
        original_stack = timing_mod.inspect.stack

        def counting_stack(context: int = 1) -> list[inspect.FrameInfo]:
            call_count["n"] += 1
            return original_stack(context)

        monkeypatch.setattr(timing_mod.inspect, "stack", counting_stack)

        logger = logging.getLogger("test_inspect_stack_skipped_when_logger_disabled")
        logger.setLevel(logging.WARNING)  # DEBUG records will not be emitted

        @func_log_excution_time(logger, logLevel=logging.DEBUG)
        def noop() -> None:
            return None

        for _ in range(5):
            noop()

        assert call_count["n"] == 0, (
            f"L-30: inspect.stack was called {call_count['n']} times despite "
            "the logger being silenced at DEBUG"
        )

    def test_inspect_stack_runs_when_logger_enabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """L-30 sanity check: when the logger IS enabled at ``logLevel``,
        the gated ``inspect.stack`` call still happens (otherwise the
        ``called from {caller}`` log line would lose its caller info).
        """
        from pdomain_book_tools.utility import timing as timing_mod

        call_count = {"n": 0}
        original_stack = timing_mod.inspect.stack

        def counting_stack(context: int = 1) -> list[inspect.FrameInfo]:
            call_count["n"] += 1
            return original_stack(context)

        monkeypatch.setattr(timing_mod.inspect, "stack", counting_stack)

        logger = logging.getLogger("test_inspect_stack_runs_when_logger_enabled")
        logger.setLevel(logging.DEBUG)

        @func_log_excution_time(logger, logLevel=logging.DEBUG)
        def noop() -> None:
            return None

        noop()
        noop()
        assert call_count["n"] == 2

    def test_measures_execution_time(self, caplog: pytest.LogCaptureFixture) -> None:
        """The end log message should include a 6-decimal seconds value."""
        logger = logging.getLogger("test_measures_execution_time")
        logger.setLevel(logging.DEBUG)

        @func_log_excution_time(logger)
        def slow() -> str:
            time.sleep(0.005)
            return "done"

        with caplog.at_level(logging.DEBUG, logger="test_measures_execution_time"):
            slow()

        messages = [r.getMessage() for r in caplog.records]
        end_msg = next((m for m in messages if "Executed in" in m), None)
        assert end_msg is not None
        assert "seconds" in end_msg


class TestCanonicalNameAndDeprecation:
    """R-22 / R-23: canonical ``func_log_execution_time`` with snake_case
    ``log_level`` keyword; deprecated alias preserves backward compat."""

    def test_canonical_name_works(self) -> None:
        logger = logging.getLogger("test_canonical_name_works")

        @func_log_execution_time(logger, log_level=logging.DEBUG)
        def add(a: int, b: int) -> int:
            return a + b

        assert add(2, 3) == 5

    def test_canonical_default_log_level(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        logger = logging.getLogger("test_canonical_default_log_level")
        logger.setLevel(logging.DEBUG)

        @func_log_execution_time(logger)
        def quick() -> int:
            return 1

        with caplog.at_level(logging.DEBUG, logger="test_canonical_default_log_level"):
            quick()

        messages = [r.getMessage() for r in caplog.records]
        assert any("started at" in m for m in messages)
        assert any("ended at" in m for m in messages)

    def test_deprecated_alias_emits_warning(self) -> None:
        logger = logging.getLogger("test_deprecated_alias_emits_warning")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            @_deprecated_alias(logger)
            def noop() -> None:
                return None

            noop()

        depr = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert any("func_log_excution_time" in str(w.message) for w in depr), (
            "expected DeprecationWarning naming the typo'd alias"
        )

    def test_deprecated_logLevel_keyword_emits_warning(self) -> None:
        logger = logging.getLogger("test_deprecated_logLevel_kw")
        logger.setLevel(logging.INFO)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            @_deprecated_alias(logger, logLevel=logging.INFO)
            def noop() -> None:
                return None

            noop()

        depr = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert any("logLevel" in str(w.message) for w in depr)

    def test_deprecated_alias_rejects_both_keywords(self) -> None:
        logger = logging.getLogger("test_deprecated_alias_rejects_both_keywords")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            with pytest.raises(TypeError, match="not both"):
                _deprecated_alias(logger, logLevel=logging.INFO, log_level=logging.INFO)
