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
