import functools
import inspect
import logging
import time


def func_log_excution_time(logger: logging.Logger, logLevel=logging.DEBUG):
    """Decorator that logs the execution time of a function using the provided logger."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            caller = inspect.stack()[1].function  # Get caller function
            # L-28: route the call-site log line through the injected
            # ``logger`` rather than the root ``logging`` module so the
            # caller's per-module logger configuration (level, handlers,
            # propagation) is honoured.
            # L-29: log argument *count and types* rather than raw values.
            # Raw values for OCR pipelines mean megabytes of NumPy /
            # CuPy ndarray repr per call, plus an inadvertent log of any
            # sensitive material a caller hands the wrapped function.
            arg_types = [type(a).__name__ for a in args]
            kwarg_summary = {k: type(v).__name__ for k, v in kwargs.items()}
            logger.log(
                logLevel,
                f"Function {func.__name__} called from {caller} with "
                f"{len(args)} positional args (types={arg_types}) and "
                f"{len(kwargs)} kwargs (types={kwarg_summary})",
            )
            start_time = time.perf_counter()
            logger.log(logLevel, f"'{func.__name__}' started at {start_time}")
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            logger.log(
                logLevel,
                f"'{func.__name__}' ended at {end_time}. Executed in {execution_time:.6f} seconds",
            )
            return result

        return wrapper

    return decorator
