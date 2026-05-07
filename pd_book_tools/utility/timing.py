import functools
import inspect
import logging
import time
import warnings


def func_log_execution_time(logger: logging.Logger, log_level=logging.DEBUG):
    """Decorator that logs the execution time of a function using the provided logger.

    R-22 / R-23: this is the canonical name. ``func_log_excution_time``
    (typo) and the ``logLevel`` keyword survive as deprecated aliases
    below for backward compatibility — both emit ``DeprecationWarning``
    on use and will be removed in a future major release.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # L-30: ``inspect.stack()`` walks the entire Python call stack
            # on every invocation — measured at hundreds of microseconds
            # per call on a typical OCR pipeline frame depth, which makes
            # the decorator measurably expensive even when the logger is
            # silenced. Skip the entire pre-call instrumentation block
            # when the logger will not emit at ``log_level`` so a disabled
            # ``DEBUG`` decorator becomes essentially free.
            log_enabled = logger.isEnabledFor(log_level)
            if log_enabled:
                caller = inspect.stack()[1].function  # Get caller function
                # L-28: route the call-site log line through the injected
                # ``logger`` rather than the root ``logging`` module so
                # the caller's per-module logger configuration (level,
                # handlers, propagation) is honoured.
                # L-29: log argument *count and types* rather than raw
                # values. Raw values for OCR pipelines mean megabytes of
                # NumPy / CuPy ndarray repr per call, plus an inadvertent
                # log of any sensitive material a caller hands the
                # wrapped function.
                arg_types = [type(a).__name__ for a in args]
                kwarg_summary = {k: type(v).__name__ for k, v in kwargs.items()}
                logger.log(
                    log_level,
                    f"Function {func.__name__} called from {caller} with "
                    f"{len(args)} positional args (types={arg_types}) and "
                    f"{len(kwargs)} kwargs (types={kwarg_summary})",
                )
            start_time = time.perf_counter()
            if log_enabled:
                logger.log(log_level, f"'{func.__name__}' started at {start_time}")
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            if log_enabled:
                execution_time = end_time - start_time
                logger.log(
                    log_level,
                    f"'{func.__name__}' ended at {end_time}. Executed in {execution_time:.6f} seconds",
                )
            return result

        return wrapper

    return decorator


def func_log_excution_time(logger: logging.Logger, logLevel=None, log_level=None):
    """Deprecated alias for :func:`func_log_execution_time` (R-22).

    Also accepts the deprecated ``logLevel`` camelCase keyword (R-23).
    Both spellings emit ``DeprecationWarning`` and will be removed in a
    future major release. Use ``func_log_execution_time(..., log_level=...)``.
    """
    warnings.warn(
        "func_log_excution_time is a deprecated alias for "
        "func_log_execution_time (R-22 — fixes 'excution' typo). "
        "Update imports; the alias will be removed in a future major release.",
        DeprecationWarning,
        stacklevel=2,
    )
    if logLevel is not None and log_level is not None:
        raise TypeError(
            "Pass either 'log_level' (canonical) or 'logLevel' (deprecated), not both."
        )
    if logLevel is not None:
        warnings.warn(
            "The 'logLevel' keyword is deprecated; use 'log_level' (R-23).",
            DeprecationWarning,
            stacklevel=2,
        )
        effective_level = logLevel
    elif log_level is not None:
        effective_level = log_level
    else:
        effective_level = logging.DEBUG
    return func_log_execution_time(logger, log_level=effective_level)
