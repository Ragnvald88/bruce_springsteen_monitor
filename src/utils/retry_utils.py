"""
StealthMaster AI Retry Utilities v3.0
Smart retry logic with exponential backoff and circuit breaker pattern
"""

import asyncio
import functools
import logging
import time
from typing import Optional, Callable, Any, TypeVar, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitBreaker:
    """
    Circuit breaker pattern implementation to prevent cascading failures
    """
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
        
    def call(self, func: Callable) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half-open'
            else:
                raise Exception(f"Circuit breaker is OPEN (failures: {self.failure_count})")
        
        try:
            result = func()
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
            
    async def async_call(self, func: Callable) -> Any:
        """Execute async function with circuit breaker protection"""
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half-open'
            else:
                raise Exception(f"Circuit breaker is OPEN (failures: {self.failure_count})")
        
        try:
            result = await func()
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
            
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit"""
        return (self.last_failure_time and 
                time.time() - self.last_failure_time >= self.recovery_timeout)
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = 'closed'
        
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


def exponential_backoff(attempt: int, 
                       base_delay: float = 1.0, 
                       max_delay: float = 60.0,
                       jitter: bool = True) -> float:
    """
    Calculate exponential backoff delay with optional jitter
    
    Args:
        attempt: Current attempt number (0-based)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Add random jitter to prevent thundering herd
        
    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (2 ** attempt), max_delay)
    
    if jitter:
        import random
        delay = delay * (0.5 + random.random() * 0.5)
        
    return delay


def retry(max_attempts: int = 3,
          exceptions: Union[type, tuple] = Exception,
          base_delay: float = 1.0,
          max_delay: float = 60.0,
          exponential: bool = True,
          circuit_breaker: Optional[CircuitBreaker] = None):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_attempts: Maximum number of attempts
        exceptions: Exception types to catch and retry
        base_delay: Base delay between retries
        max_delay: Maximum delay between retries
        exponential: Use exponential backoff
        circuit_breaker: Optional circuit breaker instance
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    if circuit_breaker:
                        return await circuit_breaker.async_call(
                            lambda: func(*args, **kwargs)
                        )
                    else:
                        return await func(*args, **kwargs)
                        
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        if exponential:
                            delay = exponential_backoff(attempt, base_delay, max_delay)
                        else:
                            delay = base_delay
                            
                        logger.warning(
                            f"Retry {attempt + 1}/{max_attempts} for {func.__name__} "
                            f"after {type(e).__name__}: {str(e)[:100]}. "
                            f"Waiting {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )
                        
            raise last_exception
            
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    if circuit_breaker:
                        return circuit_breaker.call(
                            lambda: func(*args, **kwargs)
                        )
                    else:
                        return func(*args, **kwargs)
                        
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        if exponential:
                            delay = exponential_backoff(attempt, base_delay, max_delay)
                        else:
                            delay = base_delay
                            
                        logger.warning(
                            f"Retry {attempt + 1}/{max_attempts} for {func.__name__} "
                            f"after {type(e).__name__}: {str(e)[:100]}. "
                            f"Waiting {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )
                        
            raise last_exception
            
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator


class RetryContext:
    """Context manager for retry logic with statistics"""
    
    def __init__(self, 
                 name: str,
                 max_attempts: int = 3,
                 exceptions: Union[type, tuple] = Exception,
                 base_delay: float = 1.0):
        self.name = name
        self.max_attempts = max_attempts
        self.exceptions = exceptions
        self.base_delay = base_delay
        
        self.attempts = 0
        self.start_time = None
        self.success = False
        
    async def __aenter__(self):
        self.start_time = time.time()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.success = True
            duration = time.time() - self.start_time
            logger.info(f"✅ {self.name} succeeded after {self.attempts + 1} attempts ({duration:.2f}s)")
        elif isinstance(exc_val, self.exceptions) and self.attempts < self.max_attempts - 1:
            self.attempts += 1
            delay = exponential_backoff(self.attempts - 1, self.base_delay)
            logger.warning(f"⚠️  {self.name} failed (attempt {self.attempts}), retrying in {delay:.1f}s...")
            await asyncio.sleep(delay)
            return True  # Suppress exception to allow retry
        else:
            duration = time.time() - self.start_time
            logger.error(f"❌ {self.name} failed after {self.attempts + 1} attempts ({duration:.2f}s)")
            
        return False


# Pre-configured decorators for common use cases
retry_on_network_error = retry(
    max_attempts=3,
    exceptions=(ConnectionError, TimeoutError, OSError),
    base_delay=2.0,
    max_delay=30.0
)

retry_on_block = retry(
    max_attempts=5,
    exceptions=(Exception,),  # Should be BlockedError when imported
    base_delay=5.0,
    max_delay=60.0
)

retry_critical = retry(
    max_attempts=10,
    exceptions=Exception,
    base_delay=1.0,
    max_delay=120.0,
    circuit_breaker=CircuitBreaker(failure_threshold=5, recovery_timeout=300)
)