import asyncio
import time
import traceback
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Type, Union, Tuple
import random
from functools import wraps
from .config import get_config
from .logging_config import get_logger

class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for better classification."""
    DATABASE = "database"
    SECURITY = "security"
    NETWORK = "network"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    CLIENT = "client"
    UNKNOWN = "unknown"

class RecoveryAction(Enum):
    """Types of recovery actions that can be taken."""
    RETRY = "retry"
    FAILOVER = "failover"
    DEGRADE = "degrade"
    CIRCUIT_BREAK = "circuit_break"
    ABORT = "abort"

@dataclass
class ErrorContext:
    """Contains detailed context about an error."""
    error_id: str
    timestamp: float
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    client_id: str = "unknown"
    operation: str = "unknown"
    context_data: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_action: Optional[RecoveryAction] = None
    recovery_success: bool = False

# Custom Exception Classes

class DatabaseMCPError(Exception):
    """Base exception class for all Database MCP errors."""
    
    def __init__(
        self, 
        message: str, 
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        error_code: Optional[str] = None,
        recoverable: bool = False,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.category = category
        self.error_code = error_code or self.__class__.__name__
        self.recoverable = recoverable
        self.context = context or {}
        self.timestamp = time.time()

class DatabaseConnectionError(DatabaseMCPError):
    """Raised when database connection issues occur."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            recoverable=True,
            **kwargs
        )

class DatabaseQueryError(DatabaseMCPError):
    """Raised when database query execution fails."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.DATABASE,
            recoverable=True,
            **kwargs
        )

class SecurityViolationError(DatabaseMCPError):
    """Raised when security violations are detected."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SECURITY,
            recoverable=False,
            **kwargs
        )

class ValidationError(DatabaseMCPError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION,
            recoverable=False,
            **kwargs
        )

class ConfigurationError(DatabaseMCPError):
    """Raised when configuration issues are detected."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.CONFIGURATION,
            recoverable=False,
            **kwargs
        )

class ResourceExhaustionError(DatabaseMCPError):
    """Raised when system resources are exhausted."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SYSTEM,
            recoverable=True,
            **kwargs
        )

class RateLimitExceededError(DatabaseMCPError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.CLIENT,
            recoverable=True,
            **kwargs
        )

# Retry Logic with Exponential Backoff

@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: Tuple[Type[Exception], ...] = (
        DatabaseConnectionError,
        DatabaseQueryError,
        ResourceExhaustionError,
        ConnectionError,
        asyncio.TimeoutError
    )

class RetryManager:
    """Manages retry logic with exponential backoff and jitter."""
    
    def __init__(self, config: RetryConfig = None):
        """Initialize retry manager."""
        self.config = config or RetryConfig()
        self.logger = get_logger('error_handling')
        
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt number."""
        delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            # Add jitter to avoid thundering herd
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if we should retry based on exception type and attempt count."""
        if attempt >= self.config.max_attempts:
            return False
        
        return isinstance(exception, self.config.retryable_exceptions)
    
    async def execute_with_retry(
        self, 
        operation: Callable,
        operation_name: str = "operation",
        context: Dict[str, Any] = None
    ) -> Any:
        """Execute an operation with retry logic."""
        context = context or {}
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                self.logger.debug("RETRY_ATTEMPT", {
                    "operation": operation_name,
                    "attempt": attempt,
                    "max_attempts": self.config.max_attempts
                })
                result = await operation()
                
                if attempt > 1:
                    self.logger.info("RETRY_SUCCESS", {
                        "operation": operation_name,
                        "attempt": attempt,
                        "max_attempts": self.config.max_attempts
                    })
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt):
                    self.logger.error("RETRY_FAILED_PERMANENT", {
                        "operation": operation_name,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "attempt": attempt
                    }, exc_info=True)
                    raise
                
                if attempt < self.config.max_attempts:
                    delay = self.calculate_delay(attempt)
                    self.logger.warning("RETRY_FAILED_RETRYING", {
                        "operation": operation_name,
                        "attempt": attempt,
                        "max_attempts": self.config.max_attempts,
                        "retry_delay": delay,
                        "error": str(e),
                        "error_type": type(e).__name__
                    })
                    await asyncio.sleep(delay)
                else:
                    self.logger.error("RETRY_FAILED_MAX_ATTEMPTS", {
                        "operation": operation_name,
                        "attempts": attempt,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }, exc_info=True)
        
        raise last_exception

# Circuit Breaker Pattern

class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: float = 60.0      # Seconds before trying half-open
    success_threshold: int = 2          # Successes needed to close
    timeout: float = 30.0               # Operation timeout

class CircuitBreaker:
    """Circuit breaker for protecting against cascading failures."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        """Initialize circuit breaker."""
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.logger = get_logger('error_handling')
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self._lock = asyncio.Lock()
    
    async def call(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation through circuit breaker."""
        async with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if time.time() - self.last_failure_time < self.config.recovery_timeout:
                    raise DatabaseMCPError(
                        f"Circuit breaker {self.name} is OPEN",
                        severity=ErrorSeverity.HIGH,
                        category=ErrorCategory.SYSTEM,
                        error_code="CIRCUIT_BREAKER_OPEN"
                    )
                else:
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.success_count = 0
                    self.logger.info("CIRCUIT_BREAKER_HALF_OPEN", {
                        "circuit_breaker": self.name,
                        "state": "HALF_OPEN",
                        "failure_count": self.failure_count,
                        "recovery_timeout": self.config.recovery_timeout
                    })
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                operation(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            await self._record_success()
            return result
            
        except Exception as e:
            await self._record_failure()
            raise
    
    async def _record_success(self):
        """Record a successful operation."""
        async with self._lock:
            self.failure_count = 0
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitBreakerState.CLOSED
                    self.logger.info("CIRCUIT_BREAKER_CLOSED", {
                        "circuit_breaker": self.name,
                        "state": "CLOSED",
                        "success_count": self.success_count,
                        "success_threshold": self.config.success_threshold
                    })
    
    async def _record_failure(self):
        """Record a failed operation."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.config.failure_threshold:
                if self.state != CircuitBreakerState.OPEN:
                    self.state = CircuitBreakerState.OPEN
                    self.logger.warning("CIRCUIT_BREAKER_OPEN", {
                        "circuit_breaker": self.name,
                        "state": "OPEN", 
                        "failure_count": self.failure_count,
                        "failure_threshold": self.config.failure_threshold
                    })
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time
        }

# Error Response Formatter

class ErrorResponseFormatter:
    """Formats error responses consistently."""
    
    @staticmethod
    def format_error_response(
        error: Exception,
        error_context: Optional[ErrorContext] = None,
        include_stack_trace: bool = False
    ) -> Dict[str, Any]:
        """Format an error into a standardized response."""
        
        if isinstance(error, DatabaseMCPError):
            response = {
                "success": False,
                "error": error.message,
                "error_code": error.error_code,
                "severity": error.severity.value,
                "category": error.category.value,
                "recoverable": error.recoverable,
                "timestamp": error.timestamp,
                "context": error.context
            }
        else:
            response = {
                "success": False,
                "error": str(error),
                "error_code": error.__class__.__name__,
                "severity": ErrorSeverity.MEDIUM.value,
                "category": ErrorCategory.UNKNOWN.value,
                "recoverable": False,
                "timestamp": time.time(),
                "context": {}
            }
        
        if error_context:
            response.update({
                "error_id": error_context.error_id,
                "client_id": error_context.client_id,
                "operation": error_context.operation,
                "recovery_attempted": error_context.recovery_attempted,
                "recovery_action": error_context.recovery_action.value if error_context.recovery_action else None,
                "recovery_success": error_context.recovery_success
            })
        
        if include_stack_trace:
            response["stack_trace"] = traceback.format_exc()
        
        return response

# Graceful Degradation Manager

class ServiceState(Enum):
    """Service availability states."""
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"

@dataclass
class DegradationConfig:
    """Configuration for graceful degradation."""
    enable_readonly_fallback: bool = True
    enable_cached_responses: bool = True
    max_degraded_duration: float = 300.0  # 5 minutes
    health_check_interval: float = 30.0   # 30 seconds

class GracefulDegradationManager:
    """Manages graceful degradation of services."""
    
    def __init__(self, config: DegradationConfig = None):
        """Initialize degradation manager."""
        self.config = config or DegradationConfig()
        self.logger = get_logger('error_handling')
        self.service_states: Dict[str, ServiceState] = {}
        self.degradation_start_times: Dict[str, float] = {}
        self.cached_responses: Dict[str, Dict[str, Any]] = {}
        
    def get_service_state(self, service_name: str) -> ServiceState:
        """Get current state of a service."""
        return self.service_states.get(service_name, ServiceState.AVAILABLE)
    
    def set_service_state(self, service_name: str, state: ServiceState) -> None:
        """Set service state and track degradation time."""
        old_state = self.service_states.get(service_name, ServiceState.AVAILABLE)
        self.service_states[service_name] = state
        
        if state in [ServiceState.DEGRADED, ServiceState.UNAVAILABLE] and old_state == ServiceState.AVAILABLE:
            self.degradation_start_times[service_name] = time.time()
            self.logger.warning("SERVICE_DEGRADED", {
                "service": service_name,
                "state": state.value,
                "previous_state": old_state.value,
                "degradation_start": self.degradation_start_times[service_name]
            })
        elif state == ServiceState.AVAILABLE and old_state != ServiceState.AVAILABLE:
            self.degradation_start_times.pop(service_name, None)
            self.logger.info("SERVICE_RECOVERED", {
                "service": service_name,
                "state": state.value,
                "previous_state": old_state.value
            })
    
    def should_use_fallback(self, service_name: str) -> bool:
        """Check if we should use fallback for a service."""
        state = self.get_service_state(service_name)
        
        if state == ServiceState.UNAVAILABLE:
            return True
        
        if state == ServiceState.DEGRADED:
            start_time = self.degradation_start_times.get(service_name, 0)
            if time.time() - start_time > self.config.max_degraded_duration:
                return True
        
        return False
    
    def cache_response(self, cache_key: str, response: Dict[str, Any]) -> None:
        """Cache a successful response for fallback use."""
        if self.config.enable_cached_responses:
            self.cached_responses[cache_key] = {
                "response": response,
                "cached_at": time.time()
            }
    
    def get_cached_response(self, cache_key: str, max_age: float = 300.0) -> Optional[Dict[str, Any]]:
        """Get a cached response if available and not too old."""
        if not self.config.enable_cached_responses:
            return None
        
        cached_data = self.cached_responses.get(cache_key)
        if not cached_data:
            return None
        
        if time.time() - cached_data["cached_at"] > max_age:
            self.cached_responses.pop(cache_key, None)
            return None
        
        response = cached_data["response"].copy()
        response["_cached_response"] = True
        response["_cached_at"] = cached_data["cached_at"]
        return response

# Main Error Handler

class ErrorHandler:
    """Main error handling coordinator."""
    
    def __init__(self):
        """Initialize error handler."""
        self.config = get_config()
        self.logger = get_logger('error_handling')
        self.retry_manager = RetryManager()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.degradation_manager = GracefulDegradationManager()
        self.error_formatter = ErrorResponseFormatter()
        
        # Create circuit breakers for critical services
        self.circuit_breakers["database"] = CircuitBreaker(
            "database",
            CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30.0)
        )
        
    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get or create a circuit breaker for a service."""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name)
        return self.circuit_breakers[name]
    
    @asynccontextmanager
    async def handle_operation(
        self,
        operation_name: str,
        client_id: str = "unknown",
        enable_retry: bool = True,
        enable_circuit_breaker: bool = True,
        service_name: Optional[str] = None
    ):
        """Context manager for comprehensive error handling."""
        error_context = None
        start_time = time.time()
        
        try:
            yield self
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Create error context
            error_context = ErrorContext(
                error_id=f"err_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
                timestamp=time.time(),
                error_type=e.__class__.__name__,
                error_message=str(e),
                severity=getattr(e, 'severity', ErrorSeverity.MEDIUM),
                category=getattr(e, 'category', ErrorCategory.UNKNOWN),
                client_id=client_id,
                operation=operation_name,
                context_data={
                    "execution_time": execution_time,
                    "service_name": service_name
                },
                stack_trace=traceback.format_exc()
            )
            
            self.logger.error("OPERATION_FAILED", {
                "operation": operation_name,
                "client_id": client_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "error_id": error_context.error_id,
                "error_category": error_context.category.value,
                "error_severity": error_context.severity.value,
                "execution_time": execution_time
            }, exc_info=True)
            
            # Update service state if applicable
            if service_name and isinstance(e, (DatabaseConnectionError, ResourceExhaustionError)):
                self.degradation_manager.set_service_state(service_name, ServiceState.DEGRADED)
            
            raise
    
    async def execute_with_recovery(
        self,
        operation: Callable,
        operation_name: str,
        client_id: str = "unknown",
        enable_retry: bool = True,
        enable_circuit_breaker: bool = True,
        service_name: Optional[str] = None,
        fallback_operation: Optional[Callable] = None
    ) -> Any:
        """Execute an operation with full error handling and recovery."""
        
        async def _wrapped_operation():
            if enable_circuit_breaker and service_name:
                circuit_breaker = self.get_circuit_breaker(service_name)
                return await circuit_breaker.call(operation)
            else:
                return await operation()
        
        try:
            if enable_retry:
                return await self.retry_manager.execute_with_retry(
                    _wrapped_operation,
                    operation_name,
                    context={"client_id": client_id, "service_name": service_name}
                )
            else:
                return await _wrapped_operation()
                
        except Exception as e:
            # Try fallback if available and service is degraded
            if fallback_operation and service_name:
                if self.degradation_manager.should_use_fallback(service_name):
                    self.logger.info("FALLBACK_OPERATION_USED", {
                        "operation": operation_name,
                        "service": service_name,
                        "reason": "service_degradation"
                    })
                    try:
                        result = await fallback_operation()
                        result["_fallback_used"] = True
                        return result
                    except Exception as fallback_error:
                        self.logger.error("FALLBACK_OPERATION_FAILED", {
                            "operation": operation_name,
                            "service": service_name,
                            "fallback_error": str(fallback_error),
                            "fallback_error_type": type(fallback_error).__name__
                        }, exc_info=True)
            
            raise
    
    def format_error_response(
        self,
        error: Exception,
        error_context: Optional[ErrorContext] = None,
        include_debug_info: bool = None
    ) -> Dict[str, Any]:
        """Format error response with appropriate level of detail."""
        if include_debug_info is None:
            include_debug_info = self.config.server.debug
        
        return self.error_formatter.format_error_response(
            error,
            error_context,
            include_stack_trace=include_debug_info
        )
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health including error handling status."""
        return {
            "circuit_breakers": {
                name: breaker.get_state()
                for name, breaker in self.circuit_breakers.items()
            },
            "service_states": {
                service: state.value
                for service, state in self.degradation_manager.service_states.items()
            },
            "degradation_times": {
                service: time.time() - start_time
                for service, start_time in self.degradation_manager.degradation_start_times.items()
            },
            "cached_responses": len(self.degradation_manager.cached_responses),
            "error_handling": {
                "retry_enabled": True,
                "circuit_breaker_enabled": True,
                "graceful_degradation_enabled": True
            }
        }

# Decorator for easy error handling

def handle_errors(
    operation_name: str = None,
    enable_retry: bool = True,
    enable_circuit_breaker: bool = True,
    service_name: str = None
):
    """Decorator for automatic error handling."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get error handler (assume it's available in the instance)
            if hasattr(args[0], 'error_handler'):
                error_handler = args[0].error_handler
            else:
                error_handler = ErrorHandler()
            
            op_name = operation_name or func.__name__
            
            return await error_handler.execute_with_recovery(
                lambda: func(*args, **kwargs),
                op_name,
                enable_retry=enable_retry,
                enable_circuit_breaker=enable_circuit_breaker,
                service_name=service_name
            )
        return wrapper
    return decorator
