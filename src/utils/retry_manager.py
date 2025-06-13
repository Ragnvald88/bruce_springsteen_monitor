"""Retry manager with exponential backoff."""

import asyncio
import logging
from typing import Optional, Callable, Any, TypeVar, Coroutine
from functools import wraps
import random

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryManager:
    """Manages retry logic with exponential backoff."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            # Add random jitter to prevent thundering herd
            delay = delay * (0.5 + random.random() * 0.5)
            
        return delay
        
    async def retry_async(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args,
        on_retry: Optional[Callable[[int, Exception], None]] = None,
        **kwargs
    ) -> T:
        """
        Retry an async function with exponential backoff.
        
        Args:
            func: Async function to retry
            on_retry: Optional callback for retry events
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(f"All {self.max_retries} retries exhausted for {func.__name__}")
                    raise
                    
                delay = self.calculate_delay(attempt)
                logger.warning(
                    f"Retry {attempt + 1}/{self.max_retries} for {func.__name__} "
                    f"after {delay:.1f}s delay. Error: {str(e)}"
                )
                
                if on_retry:
                    on_retry(attempt + 1, e)
                    
                await asyncio.sleep(delay)
                
        raise last_exception


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for adding retry logic to async functions.
    
    Usage:
        @with_retry(max_retries=5, base_delay=2.0)
        async def fetch_data():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry_manager = RetryManager(
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay
            )
            
            return await retry_manager.retry_async(func, *args, **kwargs)
            
        return wrapper
    return decorator


class CircuitBreaker:
    """Circuit breaker pattern for preventing cascading failures."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if self.last_failure_time and \
               (asyncio.get_event_loop().time() - self.last_failure_time) > self.recovery_timeout:
                self.state = "half-open"
            else:
                raise Exception(f"Circuit breaker is open for {func.__name__}")
                
        try:
            result = await func(*args, **kwargs)
            
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
                logger.info(f"Circuit breaker recovered for {func.__name__}")
                
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = asyncio.get_event_loop().time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(
                    f"Circuit breaker opened for {func.__name__} "
                    f"after {self.failure_count} failures"
                )
                
            raise


# Global retry manager instance
retry_manager = RetryManager()