"""
Intelligent retry mechanism for Azure API calls with exponential backoff
Handles transient failures gracefully while avoiding unnecessary delays
"""
import time
import random
from functools import wraps
from typing import Callable, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
from rich.console import Console
import logging

console = Console()


class RetryReason(str, Enum):
    """Reasons for retry attempts"""
    API_THROTTLING = "api_throttling"
    NETWORK_ERROR = "network_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    TIMEOUT = "timeout"
    TRANSIENT_ERROR = "transient_error"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    backoff_multiplier: float = 2.0  # Exponential backoff multiplier
    jitter: bool = True  # Add randomization to prevent thundering herd
    retryable_status_codes: Optional[List[int]] = None  # HTTP status codes that should trigger retry
    retryable_exceptions: Optional[List[type]] = None  # Exception types that should trigger retry
    
    def __post_init__(self):
        if self.retryable_status_codes is None:
            # Common transient HTTP status codes
            self.retryable_status_codes = [429, 500, 502, 503, 504, 408]
        
        if self.retryable_exceptions is None:
            # Common transient exception types
            self.retryable_exceptions = [
                ConnectionError,
                TimeoutError,
                # Azure specific exceptions will be added based on actual imports
            ]


@dataclass
class RetryAttempt:
    """Information about a retry attempt"""
    attempt_number: int
    delay_seconds: float
    reason: RetryReason
    error_message: str
    timestamp: float


class RetryableError(Exception):
    """Exception that indicates an operation should be retried"""
    
    def __init__(self, reason: RetryReason, original_error: Exception, retry_after: Optional[float] = None):
        self.reason = reason
        self.original_error = original_error
        self.retry_after = retry_after  # Hint from server about when to retry
        super().__init__(f"Retryable error ({reason.value}): {str(original_error)}")


class RetryStatistics:
    """Tracks retry statistics for monitoring and optimization"""
    
    def __init__(self):
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.total_retries = 0
        self.retry_attempts: List[RetryAttempt] = []
        self.average_delay = 0.0
        self.max_delay = 0.0
    
    def record_attempt(self, attempt: RetryAttempt):
        """Record a retry attempt"""
        self.retry_attempts.append(attempt)
        self.total_retries += 1
        self.max_delay = max(self.max_delay, attempt.delay_seconds)
        
        # Update average delay
        if self.retry_attempts:
            self.average_delay = sum(a.delay_seconds for a in self.retry_attempts) / len(self.retry_attempts)
    
    def record_call_result(self, success: bool):
        """Record the final result of a call"""
        self.total_calls += 1
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
    
    def get_success_rate(self) -> float:
        """Get the success rate as a percentage"""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100
    
    def display_stats(self):
        """Display retry statistics"""
        if self.total_calls == 0:
            console.print("[dim]No retry statistics available[/dim]")
            return
            
        console.print("\n[cyan]📊 Retry Statistics[/cyan]")
        console.print(f"Total API calls: {self.total_calls}")
        console.print(f"Success rate: {self.get_success_rate():.1f}%")
        console.print(f"Total retries: {self.total_retries}")
        console.print(f"Average retry delay: {self.average_delay:.2f}s")
        console.print(f"Max retry delay: {self.max_delay:.2f}s")
        
        # Retry reason breakdown
        if self.retry_attempts:
            reason_counts = {}
            for attempt in self.retry_attempts:
                reason_counts[attempt.reason] = reason_counts.get(attempt.reason, 0) + 1
            
            console.print("\nRetry reasons:")
            for reason, count in reason_counts.items():
                console.print(f"  {reason.value}: {count}")


# Global retry statistics instance
retry_stats = RetryStatistics()


class IntelligentRetry:
    """Intelligent retry handler with exponential backoff and jitter"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.logger = logging.getLogger(__name__)
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to add retry functionality to a function"""
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return self.execute_with_retry(func, *args, **kwargs)
        
        return wrapper
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        
        last_error = None
        
        for attempt in range(self.config.max_attempts):
            try:
                result = func(*args, **kwargs)
                retry_stats.record_call_result(True)
                
                if attempt > 0:
                    console.print(f"[green]✓[/green] Operation succeeded after {attempt} retry attempt(s)")
                
                return result
                
            except Exception as error:
                last_error = error
                
                # Check if this error should trigger a retry
                if attempt < self.config.max_attempts - 1:  # Not the last attempt
                    retry_reason = self._analyze_error(error)
                    
                    if retry_reason:
                        delay = self._calculate_delay(attempt, error, retry_reason)
                        
                        # Record retry attempt
                        retry_attempt = RetryAttempt(
                            attempt_number=attempt + 1,
                            delay_seconds=delay,
                            reason=retry_reason,
                            error_message=str(error),
                            timestamp=time.time()
                        )
                        retry_stats.record_attempt(retry_attempt)
                        
                        # Display retry information
                        self._display_retry_info(retry_attempt, self.config.max_attempts)
                        
                        # Wait before retry
                        time.sleep(delay)
                        continue
                
                # No retry or last attempt failed
                break
        
        # All attempts failed
        retry_stats.record_call_result(False)
        
        if last_error:
            console.print(f"[red]✗[/red] Operation failed after {self.config.max_attempts} attempts")
            raise last_error
    
    def _analyze_error(self, error: Exception) -> Optional[RetryReason]:
        """Analyze error to determine if it's retryable and why"""
        
        error_str = str(error).lower()
        
        # Check HTTP status codes if available
        if hasattr(error, 'status_code'):
            status_code = error.status_code
            
            if status_code == 429:
                return RetryReason.API_THROTTLING
            elif status_code in [500, 502, 503, 504]:
                return RetryReason.SERVICE_UNAVAILABLE
            elif status_code == 408:
                return RetryReason.TIMEOUT
            elif status_code in self.config.retryable_status_codes:
                return RetryReason.TRANSIENT_ERROR
        
        # Check exception type
        if self.config.retryable_exceptions and any(isinstance(error, exc_type) for exc_type in self.config.retryable_exceptions):
            return RetryReason.TRANSIENT_ERROR
        
        # Check error message patterns
        if any(keyword in error_str for keyword in ['timeout', 'timed out']):
            return RetryReason.TIMEOUT
        elif any(keyword in error_str for keyword in ['throttl', 'rate limit']):
            return RetryReason.API_THROTTLING
        elif any(keyword in error_str for keyword in ['connection', 'network']):
            return RetryReason.NETWORK_ERROR
        elif any(keyword in error_str for keyword in ['service unavailable', 'temporary', 'transient']):
            return RetryReason.SERVICE_UNAVAILABLE
        
        # Check Azure-specific error codes
        if hasattr(error, 'error') and hasattr(error.error, 'code'):
            error_code = error.error.code.lower()
            
            transient_codes = [
                'internalservererror',
                'serviceunavailable',
                'temporaryredirect',
                'toomanyrequest',
                'requesttimeout'
            ]
            
            if error_code in transient_codes:
                return RetryReason.TRANSIENT_ERROR
        
        return None  # Error is not retryable
    
    def _calculate_delay(self, attempt: int, error: Exception, reason: RetryReason) -> float:
        """Calculate delay for next retry attempt"""
        
        # Check if server provided a retry-after hint
        retry_after = self._extract_retry_after(error)
        if retry_after:
            return min(retry_after, self.config.max_delay)
        
        # Calculate exponential backoff delay
        delay = self.config.base_delay * (self.config.backoff_multiplier ** attempt)
        
        # Add jitter to prevent thundering herd
        if self.config.jitter:
            jitter_factor = 0.1  # 10% jitter
            jitter = delay * jitter_factor * (2 * random.random() - 1)  # -10% to +10%
            delay += jitter
        
        # Apply reason-specific adjustments
        if reason == RetryReason.API_THROTTLING:
            delay *= 2  # Longer delays for throttling
        elif reason == RetryReason.NETWORK_ERROR:
            delay *= 1.5  # Moderate delay for network issues
        
        # Ensure delay is within bounds
        return max(0.1, min(delay, self.config.max_delay))
    
    def _extract_retry_after(self, error: Exception) -> Optional[float]:
        """Extract retry-after hint from error response"""
        
        if hasattr(error, 'response') and hasattr(error.response, 'headers'):
            headers = error.response.headers
            
            # Check for Retry-After header
            retry_after = headers.get('Retry-After') or headers.get('retry-after')
            if retry_after:
                try:
                    return float(retry_after)
                except ValueError:
                    pass  # Invalid retry-after value
        
        return None
    
    def _display_retry_info(self, attempt: RetryAttempt, max_attempts: int):
        """Display information about the retry attempt"""
        
        reason_messages = {
            RetryReason.API_THROTTLING: "API rate limit exceeded",
            RetryReason.NETWORK_ERROR: "Network connectivity issue",
            RetryReason.SERVICE_UNAVAILABLE: "Azure service temporarily unavailable",
            RetryReason.TIMEOUT: "Request timed out",
            RetryReason.TRANSIENT_ERROR: "Transient error detected"
        }
        
        reason_msg = reason_messages.get(attempt.reason, "Unknown error")
        
        console.print(
            f"[yellow]⚠[/yellow] {reason_msg} - "
            f"Retrying in {attempt.delay_seconds:.1f}s "
            f"(attempt {attempt.attempt_number}/{max_attempts})"
        )


# Convenience decorators with different retry configurations
def azure_api_retry(max_attempts: int = 3, base_delay: float = 1.0):
    """Decorator for Azure API calls with standard retry configuration"""
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=60.0,
        retryable_status_codes=[429, 500, 502, 503, 504, 408]
    )
    return IntelligentRetry(config)


def network_retry(max_attempts: int = 5, base_delay: float = 0.5):
    """Decorator for network operations with aggressive retry"""
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=30.0,
        backoff_multiplier=1.5  # Less aggressive backoff for network issues
    )
    return IntelligentRetry(config)


def critical_operation_retry(max_attempts: int = 5, base_delay: float = 2.0):
    """Decorator for critical operations that must succeed"""
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=120.0,  # Allow longer delays for critical operations
        backoff_multiplier=2.0
    )
    return IntelligentRetry(config)


def get_retry_statistics() -> RetryStatistics:
    """Get global retry statistics"""
    return retry_stats


def reset_retry_statistics():
    """Reset global retry statistics"""
    global retry_stats
    retry_stats = RetryStatistics()


# Context manager for temporary retry configuration
class RetryContext:
    """Context manager for applying retry configuration to a block of code"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.retry_handler = IntelligentRetry(config)
    
    def __enter__(self):
        return self.retry_handler
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Could add cleanup logic here if needed
        pass


# Example usage patterns:
"""
# As a decorator
@azure_api_retry(max_attempts=3)
def get_virtual_machine(resource_group: str, vm_name: str):
    return compute_client.virtual_machines.get(resource_group, vm_name)

# As a context manager
with RetryContext(RetryConfig(max_attempts=5)) as retry_handler:
    result = retry_handler.execute_with_retry(some_azure_function, arg1, arg2)

# Manual retry
retry_handler = IntelligentRetry(RetryConfig(max_attempts=3))
result = retry_handler.execute_with_retry(azure_function, parameters)
"""