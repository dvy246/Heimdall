import time
import random
from functools import wraps
import asyncio
from typing import Callable, Any
from src.config.logging_config import logger

def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
) -> Callable:
    """
    Decorator that retries a function with exponential backoff.

    This decorator automatically retries a function when it fails, with increasing
    delays between attempts. The delay follows an exponential backoff pattern,
    optionally with jitter to prevent thundering herd problems.

    Args:
        max_retries (int, optional): Maximum number of retries. Defaults to 3.
        initial_delay (float, optional): Initial delay in seconds before first retry. 
            Defaults to 1.0.
        exponential_base (float, optional): Base for exponential delay calculation. 
            Each retry delay = initial_delay * (exponential_base ^ attempt_number). 
            Defaults to 2.0.
        jitter (bool, optional): Whether to add random jitter (0-1 seconds) to delays 
            to prevent synchronized retries. Defaults to True.

    Returns:
        Callable: The decorated function with retry logic.

    Raises:
        Exception: The last exception encountered if all retries are exhausted.

    Example:
        >>> @retry_with_exponential_backoff(max_retries=5, initial_delay=0.5)
        >>> async def unreliable_api_call():
        >>>     # This will retry up to 5 times with delays: 0.5s, 1s, 2s, 4s, 8s
        >>>     response = await some_api_call()
        >>>     return response
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            """Async wrapper for coroutine functions."""
            last_exception = None
            logger.debug(f"Starting execution of {func.__name__}")
            for tries in range(max_retries + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if tries == max_retries:
                        raise e
                    delay = initial_delay * (exponential_base ** tries)
                    if jitter:
                        delay += random.random()
                    logger.warning(f"Attempt {tries + 1} failed for {func.__name__}, retrying in {delay:.2f}s: {str(e)}")
                    await asyncio.sleep(delay)
            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            """Synchronous wrapper for regular functions."""
            last_exception = None
            logger.debug(f"Starting execution of {func.__name__}")
            for tries in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if tries < max_retries:
                        delay = initial_delay * (exponential_base ** tries)
                        if jitter:
                            delay += random.random()
                        logger.warning(f"Attempt {tries + 1} failed for {func.__name__}, retrying in {delay:.2f}s: {str(e)}")
                        time.sleep(delay)
                    else:
                        raise e
            raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance.

    The circuit breaker pattern prevents cascading failures by monitoring
    function calls and "opening" the circuit when failures exceed a threshold.
    When open, calls fail fast without executing the wrapped function.
    After a recovery timeout, the circuit enters "half-open" state to test
    if the underlying service has recovered.

    States:
        - CLOSED: Normal operation, calls pass through
        - OPEN: Failing fast, calls immediately raise exception
        - HALF-OPEN: Testing recovery, single call allowed

    Attributes:
        failure_threshold (int): Number of failures before opening circuit
        recovery_timeout (int): Seconds to wait before testing recovery
        failure_count (int): Current count of consecutive failures
        last_failure_time (float): Timestamp of last failure
        state (str): Current circuit state ("closed", "open", "half-open")

    Example:
        >>> # Create circuit breaker with custom thresholds
        >>> db_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        >>> 
        >>> @db_breaker
        >>> async def database_query():
        >>>     # Database operation that might fail
        >>>     return await db.execute_query()
        >>>
        >>> # After 5 failures, circuit opens and calls fail fast
        >>> # After 60 seconds, circuit allows one test call
    """

    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 30):
        """
        Initialize a CircuitBreaker instance.

        Args:
            failure_threshold (int, optional): The number of consecutive failures 
                before opening the circuit. Defaults to 3.
            recovery_timeout (int, optional): The time in seconds to wait before 
                attempting to close the circuit. Defaults to 30.
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: float = 0
        self.state = "closed"

    def __call__(self, func: Callable):
        """
        Make the CircuitBreaker callable as a decorator.

        Args:
            func (Callable): The function to wrap with circuit breaker logic.

        Returns:
            Callable: The wrapped function with circuit breaker behavior.
        """
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            """Async wrapper with circuit breaker logic."""
            if self.state == "open":
                logger.warning(f"Circuit breaker OPENED for {func.__name__} after {self.failure_count} failures")

                current_time = time.time()
                if current_time - self.last_failure_time > self.recovery_timeout:
                    self.state = "half-open"
                    logger.info(f"Circuit breaker HALF-OPEN for {func.__name__}, testing recovery")
                else:
                    raise Exception("Circuit breaker is open")
            
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                if self.state == "half-open":
                    self.state = "closed"
                    self.failure_count = 0
                    logger.info(f"Circuit breaker CLOSED for {func.__name__}, recovery successful")
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self.state = "open"
                raise e

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            """Synchronous wrapper with circuit breaker logic."""
            if self.state == "open":
                current_time = time.time()
                if current_time - self.last_failure_time > self.recovery_timeout:
                    self.state = "half-open"
                else:
                    raise Exception("Circuit breaker is open")
            
            try:
                result = func(*args, **kwargs)
                if self.state == "half-open":
                    self.state = "closed"
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self.state = "open"
                raise e

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper


def fallback(fallback_func: Callable) -> Callable:
    """
    Decorator to provide fallback behavior for a function.

    This decorator catches exceptions from the wrapped function and executes
    a fallback function instead. The fallback function receives the same
    arguments as the original function.

    Args:
        fallback_func (Callable): The fallback function to execute when the 
            original function fails. Should accept the same arguments as the 
            decorated function.

    Returns:
        Callable: The decorated function with fallback behavior.

    Note:
        The decorator automatically handles both sync and async functions.
        If either the original function or fallback function is async,
        the wrapper will be async.

    Example:
        >>> def default_response():
        >>>     return {"status": "unavailable", "data": None}
        >>>
        >>> @fallback(default_response)
        >>> async def fetch_user_data(user_id: str):
        >>>     # Risky operation that might fail
        >>>     response = await api.get_user(user_id)
        >>>     return response
        >>>
        >>> # If fetch_user_data fails, default_response() is returned instead
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            """Async wrapper with fallback logic."""
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                if asyncio.iscoroutinefunction(fallback_func):
                    # In the except block
                    logger.warning(f"Function {func.__name__} failed, executing fallback: {str(e)}")
                    return await fallback_func(*args, **kwargs)
                else:
                    logger.warning(f"Function {func.__name__} failed, executing fallback: {str(e)}")
                    return fallback_func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            """Synchronous wrapper with fallback logic."""
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Function {func.__name__} failed, executing fallback: {str(e)}")
                return fallback_func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func) or asyncio.iscoroutinefunction(fallback_func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

    