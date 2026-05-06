"""Tests for utility.timing module."""

import logging
import time

import pytest

from pd_book_tools.utility.timing import func_log_excution_time


class TestFuncLogExecutionTime:
    """Test the func_log_excution_time decorator."""

    def test_returns_function_result(self):
        """Decorator should not change the wrapped function's return value."""
        logger = logging.getLogger("test_returns_function_result")

        @func_log_excution_time(logger)
        def add(a, b):
            return a + b

        assert add(2, 3) == 5

    def test_passes_args_and_kwargs(self):
        """Decorator should forward positional and keyword arguments."""
        logger = logging.getLogger("test_passes_args_and_kwargs")

        @func_log_excution_time(logger)
        def combine(a, b, sep=" "):
            return f"{a}{sep}{b}"

        assert combine("hello", "world", sep="-") == "hello-world"

    def test_logs_at_specified_level(self, caplog):
        """Decorator should log at the requested log level."""
        logger = logging.getLogger("test_logs_at_specified_level")
        logger.setLevel(logging.INFO)

        @func_log_excution_time(logger, logLevel=logging.INFO)
        def noop():
            return "ok"

        with caplog.at_level(logging.INFO, logger="test_logs_at_specified_level"):
            result = noop()

        assert result == "ok"
        # Expect at least the start and end log records
        messages = [r.getMessage() for r in caplog.records]
        assert any("started at" in m for m in messages)
        assert any("ended at" in m for m in messages)

    def test_default_log_level_debug(self, caplog):
        """Default level should be DEBUG and emit start/end records."""
        logger = logging.getLogger("test_default_log_level_debug")
        logger.setLevel(logging.DEBUG)

        @func_log_excution_time(logger)
        def quick():
            return 42

        with caplog.at_level(logging.DEBUG, logger="test_default_log_level_debug"):
            quick()

        messages = [r.getMessage() for r in caplog.records]
        assert any("started at" in m for m in messages)
        assert any("ended at" in m for m in messages)

    def test_preserves_function_metadata(self):
        """functools.wraps should preserve __name__ and docstring."""
        logger = logging.getLogger("test_preserves_function_metadata")

        @func_log_excution_time(logger)
        def documented():
            """A docstring."""
            return None

        assert documented.__name__ == "documented"
        assert documented.__doc__ == "A docstring."

    def test_propagates_exception(self):
        """Exceptions raised inside the wrapped function must propagate."""
        logger = logging.getLogger("test_propagates_exception")

        @func_log_excution_time(logger)
        def raises():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            raises()

    def test_call_site_log_uses_injected_logger(self, caplog):
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
        def noop():
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

    def test_call_site_log_does_not_emit_raw_arg_values(self, caplog):
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
        sentinel = "PD_BOOK_TOOLS_L29_SECRET_VALUE_DO_NOT_LOG"

        @func_log_excution_time(logger)
        def takes_args(positional, *, kw):
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

    def test_measures_execution_time(self, caplog):
        """The end log message should include a 6-decimal seconds value."""
        logger = logging.getLogger("test_measures_execution_time")
        logger.setLevel(logging.DEBUG)

        @func_log_excution_time(logger)
        def slow():
            time.sleep(0.005)
            return "done"

        with caplog.at_level(logging.DEBUG, logger="test_measures_execution_time"):
            slow()

        messages = [r.getMessage() for r in caplog.records]
        end_msg = next((m for m in messages if "Executed in" in m), None)
        assert end_msg is not None
        assert "seconds" in end_msg
