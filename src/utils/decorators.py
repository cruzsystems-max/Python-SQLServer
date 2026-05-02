"""
Utility decorators for database operations.

Provides decorators for retry logic, logging, and other common patterns.
"""

import time
import functools
from typing import Callable, Type, Tuple
from ..core.logger import get_logger


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator to retry a function on failure.

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts (seconds)
        backoff: Multiplier for delay after each attempt
        exceptions: Tuple of exceptions to catch

    Example:
        >>> @retry(max_attempts=3, delay=1.0, backoff=2.0)
        ... def flaky_database_call():
        ...     # This will retry up to 3 times with exponential backoff
        ...     return db.execute_query(...)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}), "
                        f"retrying in {current_delay:.1f}s: {e}"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator


def log_execution(func: Callable) -> Callable:
    """
    Decorator to log function execution.

    Logs function name, arguments, execution time, and result/exception.

    Example:
        >>> @log_execution
        ... def get_customer(customer_id: int):
        ...     return db.query(...)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)

        # Log function call
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)

        logger.debug(f"Calling {func.__name__}({signature})")

        # Execute and time
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time

            logger.debug(
                f"{func.__name__} completed in {elapsed:.3f}s, result: {result!r}"
            )

            return result

        except Exception as e:
            elapsed = time.time() - start_time

            logger.error(
                f"{func.__name__} failed after {elapsed:.3f}s: {e}",
                exc_info=True
            )

            raise

    return wrapper


def measure_time(func: Callable) -> Callable:
    """
    Decorator to measure and log execution time.

    Example:
        >>> @measure_time
        ... def slow_query():
        ...     return db.execute_complex_query(...)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)

        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time

        logger.info(f"{func.__name__} took {elapsed:.3f}s")

        return result

    return wrapper
