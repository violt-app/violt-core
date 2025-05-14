"""
Violt Core - Retry Mechanism

This module implements retry logic for failed operations.
"""

from typing import TypeVar, Callable, Any, Optional, Type, Union, Tuple
import logging
import asyncio
from functools import wraps
import time

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryError(Exception):
    """Exception raised when all retry attempts fail."""

    def __init__(self, message: str, last_error: Optional[Exception] = None):
        super().__init__(message)
        self.last_error = last_error


class RetryHandler:
    """Handles retry logic for operations."""

    def __init__(
        self,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    ):
        self.max_retries = max_retries
        self.delay = delay
        self.backoff_factor = backoff_factor
        self.exceptions = exceptions if isinstance(exceptions, tuple) else (exceptions,)

    async def execute_with_retry(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """Execute a function with retry logic."""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            except self.exceptions as e:
                last_error = e
                if attempt == self.max_retries - 1:
                    break

                delay = self.delay * (self.backoff_factor**attempt)
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed: {e}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                await asyncio.sleep(delay)

        raise RetryError(
            f"Operation failed after {self.max_retries} attempts", last_error
        )


def with_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
):
    """Decorator for adding retry logic to functions."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        retry_handler = RetryHandler(
            max_retries=max_retries,
            delay=delay,
            backoff_factor=backoff_factor,
            exceptions=exceptions,
        )

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_handler.execute_with_retry(func, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            return retry_handler.execute_with_retry(func, *args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
