"""
Retry utility for handling network errors and transient failures.
Provides decorators and functions to retry operations with exponential backoff.
"""

import time
import asyncio
import logging
from functools import wraps
from typing import Callable, Any, Tuple, Type
import traceback
import inspect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior"""
    # Network-related exceptions to retry
    NETWORK_EXCEPTIONS = (
        ConnectionError,
        TimeoutError,
        OSError,  # Includes socket errors, DNS errors
    )

    # HTTP/API related exceptions (will be caught as Exception and checked by message)
    TRANSIENT_ERROR_KEYWORDS = [
        'timeout',
        'timed out',
        'connection',
        'dns',
        'resolve',
        'ssl',
        'tls',
        '404',
        '429',  # Rate limit
        '500',  # Server error
        '502',  # Bad gateway
        '503',  # Service unavailable
        '504',  # Gateway timeout
        'curl:',
        'failed to perform',
        'max retries exceeded',
        'name or service not known',
        'nameresolutionerror',
    ]

    DEFAULT_MAX_RETRIES = 0
    DEFAULT_BASE_DELAY = 120  # 2 minutes
    DEFAULT_MAX_DELAY = 600   # 10 minutes


def is_transient_error(exception: Exception) -> bool:
    """
    Check if an exception is likely a transient network error that should be retried.

    Args:
        exception: The exception to check

    Returns:
        True if the error appears to be transient and worth retrying
    """
    # Check if it's a known network exception type
    if isinstance(exception, RetryConfig.NETWORK_EXCEPTIONS):
        return True

    # Check exception message for transient error keywords
    error_message = str(exception).lower()
    for keyword in RetryConfig.TRANSIENT_ERROR_KEYWORDS:
        if keyword in error_message:
            return True

    # Check exception type name
    exception_type = type(exception).__name__.lower()
    for keyword in RetryConfig.TRANSIENT_ERROR_KEYWORDS:
        if keyword in exception_type:
            return True

    return False


def retry_with_backoff(
    func: Callable,
    *args,
    max_retries: int = RetryConfig.DEFAULT_MAX_RETRIES,
    base_delay: int = RetryConfig.DEFAULT_BASE_DELAY,
    max_delay: int = RetryConfig.DEFAULT_MAX_DELAY,
    **kwargs
) -> Any:
    """
    Retry a function with exponential backoff on transient errors.

    Args:
        func: Function to retry
        *args: Positional arguments for func
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds (doubles each retry)
        max_delay: Maximum delay between retries in seconds
        **kwargs: Keyword arguments for func

    Returns:
        The result of func if successful

    Raises:
        The last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            # Check if this is a transient error worth retrying
            if not is_transient_error(e):
                logger.info(f"Non-transient error, not retrying: {e}")
                raise

            if attempt < max_retries - 1:
                # Calculate delay with exponential backoff
                delay = min(base_delay * (2 ** attempt), max_delay)

                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed with transient error: {e}\n"
                    f"Retrying in {delay} seconds..."
                )

                time.sleep(delay)
            else:
                logger.error(
                    f"All {max_retries} attempts failed. Last error: {e}\n"
                    f"Traceback:\n{traceback.format_exc()}"
                )

    # If we get here, all retries failed
    raise last_exception


async def retry_with_backoff_async(
    func: Callable,
    *args,
    max_retries: int = RetryConfig.DEFAULT_MAX_RETRIES,
    base_delay: int = RetryConfig.DEFAULT_BASE_DELAY,
    max_delay: int = RetryConfig.DEFAULT_MAX_DELAY,
    **kwargs
) -> Any:
    """
    Async version: Retry a function with exponential backoff on transient errors.

    Args:
        func: Async function to retry
        *args: Positional arguments for func
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds (doubles each retry)
        max_delay: Maximum delay between retries in seconds
        **kwargs: Keyword arguments for func

    Returns:
        The result of func if successful

    Raises:
        The last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            # Check if this is a transient error worth retrying
            if not is_transient_error(e):
                logger.info(f"Non-transient error, not retrying: {e}")
                raise

            if attempt < max_retries - 1:
                # Calculate delay with exponential backoff
                delay = min(base_delay * (2 ** attempt), max_delay)

                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed with transient error: {e}\n"
                    f"Retrying in {delay} seconds..."
                )

                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"All {max_retries} attempts failed. Last error: {e}\n"
                    f"Traceback:\n{traceback.format_exc()}"
                )

    # If we get here, all retries failed
    raise last_exception


def with_retry(
    max_retries: int = RetryConfig.DEFAULT_MAX_RETRIES,
    base_delay: int = RetryConfig.DEFAULT_BASE_DELAY,
    max_delay: int = RetryConfig.DEFAULT_MAX_DELAY
):
    """
    Decorator to add retry logic with exponential backoff to a function.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds (doubles each retry)
        max_delay: Maximum delay between retries in seconds

    Example:
        @with_retry(max_retries=3, base_delay=60)
        def fetch_data():
            return requests.get('https://example.com/api/data')
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return retry_with_backoff(
                func, *args,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                **kwargs
            )
        return wrapper
    return decorator


async def retry_telegram_operation(func: Callable, *args, **kwargs) -> Any:
    """
    Retry a Telegram API operation with appropriate settings.
    Uses shorter delays since Telegram usually recovers quickly.
    Supports both sync and async functions.

    Args:
        func: Function to retry (can be async or sync)
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        The result of func if successful
    """
    if inspect.iscoroutinefunction(func):
        return await retry_with_backoff_async(
            func, *args,
            max_retries=0,
            base_delay=30,  # 30 seconds for Telegram
            max_delay=180,  # 3 minutes max
            **kwargs
        )
    else:
        return retry_with_backoff(
            func, *args,
            max_retries=0,
            base_delay=30,  # 30 seconds for Telegram
            max_delay=180,  # 3 minutes max
            **kwargs
        )


def retry_data_fetch(func: Callable, *args, **kwargs) -> Any:
    """
    Retry a data fetch operation (yfinance, web scraping, etc.) with appropriate settings.
    Uses longer delays since these often involve DNS resolution issues.

    Args:
        func: Function to retry
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        The result of func if successful
    """
    return retry_with_backoff(
        func, *args,
        max_retries=0,
        base_delay=120,  # 2 minutes
        max_delay=600,   # 10 minutes max
        **kwargs
    )

