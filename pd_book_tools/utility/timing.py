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
            logging.log(
                logLevel,
                f"Function {func.__name__} called from {caller} with args: {args}, kwargs: {kwargs}",
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
