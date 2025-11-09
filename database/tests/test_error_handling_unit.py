"""Comprehensive unit tests for error_handling module"""

import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest

from database.src.error_handling import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    ConfigurationError,
    DatabaseConnectionError,
    DatabaseMCPError,
    DatabaseQueryError,
    DegradationConfig,
    ErrorCategory,
    ErrorContext,
    ErrorHandler,
    ErrorResponseFormatter,
    ErrorSeverity,
    GracefulDegradationManager,
    RateLimitExceededError,
    RecoveryAction,
    ResourceExhaustionError,
    RetryConfig,
    RetryManager,
    SecurityViolationError,
    ServiceState,
    ValidationError,
    handle_errors,
)


@pytest.mark.unit
class TestCustomExceptions:
    """Test custom exception classes"""

    def test_database_mcp_error_basic(self):
        """Test basic DatabaseMCPError creation"""
        error = DatabaseMCPError("Test error")
        assert error.message == "Test error"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.category == ErrorCategory.UNKNOWN
        assert error.error_code == "DatabaseMCPError"
        assert error.recoverable is False
        assert isinstance(error.context, dict)
        assert isinstance(error.timestamp, float)

    def test_database_mcp_error_with_context(self):
        """Test DatabaseMCPError with custom context"""
        context = {"user_id": "123", "operation": "query"}
        error = DatabaseMCPError(
            "Test error",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            error_code="TEST_ERROR",
            recoverable=True,
            context=context,
        )
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.DATABASE
        assert error.error_code == "TEST_ERROR"
        assert error.recoverable is True
        assert error.context == context

    def test_database_connection_error(self):
        """Test DatabaseConnectionError inherits correct defaults"""
        error = DatabaseConnectionError("Connection failed")
        assert error.message == "Connection failed"
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.DATABASE
        assert error.recoverable is True

    def test_database_query_error(self):
        """Test DatabaseQueryError inherits correct defaults"""
        error = DatabaseQueryError("Query failed")
        assert error.message == "Query failed"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.category == ErrorCategory.DATABASE
        assert error.recoverable is True

    def test_security_violation_error(self):
        """Test SecurityViolationError inherits correct defaults"""
        error = SecurityViolationError("Security breach")
        assert error.message == "Security breach"
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.category == ErrorCategory.SECURITY
        assert error.recoverable is False

    def test_validation_error(self):
        """Test ValidationError inherits correct defaults"""
        error = ValidationError("Invalid input")
        assert error.message == "Invalid input"
        assert error.severity == ErrorSeverity.LOW
        assert error.category == ErrorCategory.VALIDATION
        assert error.recoverable is False


@pytest.mark.unit
class TestRetryManager:
    """Test RetryManager retry logic and exponential backoff"""

    def test_calculate_delay_basic(self):
        """Test basic delay calculation without jitter"""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)
        manager = RetryManager(config)

        # Attempt 1: 1.0 * 2^0 = 1.0
        assert manager.calculate_delay(1) == 1.0
        # Attempt 2: 1.0 * 2^1 = 2.0
        assert manager.calculate_delay(2) == 2.0
        # Attempt 3: 1.0 * 2^2 = 4.0
        assert manager.calculate_delay(3) == 4.0

    def test_calculate_delay_with_max_delay(self):
        """Test delay calculation respects max_delay"""
        config = RetryConfig(base_delay=1.0, max_delay=5.0, jitter=False)
        manager = RetryManager(config)

        # Should cap at max_delay
        assert manager.calculate_delay(10) == 5.0

    def test_calculate_delay_with_jitter(self):
        """Test delay calculation includes jitter"""
        config = RetryConfig(base_delay=10.0, jitter=True)
        manager = RetryManager(config)

        delay = manager.calculate_delay(1)
        # Should be within 10% jitter range of 10.0
        assert 9.0 <= delay <= 11.0

    def test_should_retry_within_max_attempts(self):
        """Test should_retry returns True for retryable exceptions within max attempts"""
        config = RetryConfig(max_attempts=3)
        manager = RetryManager(config)

        # ConnectionError is retryable
        assert manager.should_retry(ConnectionError("test"), attempt=1) is True
        assert manager.should_retry(ConnectionError("test"), attempt=2) is True

    def test_should_retry_exceeds_max_attempts(self):
        """Test should_retry returns False when max attempts exceeded"""
        config = RetryConfig(max_attempts=3)
        manager = RetryManager(config)

        assert manager.should_retry(ConnectionError("test"), attempt=3) is False
        assert manager.should_retry(ConnectionError("test"), attempt=4) is False

    def test_should_retry_non_retryable_exception(self):
        """Test should_retry returns False for non-retryable exceptions"""
        config = RetryConfig()
        manager = RetryManager(config)

        # ValueError is not in retryable_exceptions
        assert manager.should_retry(ValueError("test"), attempt=1) is False

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_first_attempt(self):
        """Test execute_with_retry succeeds on first attempt"""
        manager = RetryManager(RetryConfig(max_attempts=3))

        async def success_operation():
            return "success"

        result = await manager.execute_with_retry(success_operation, "test_op")
        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_after_failures(self):
        """Test execute_with_retry succeeds after initial failures"""
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        manager = RetryManager(config)

        call_count = 0

        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        result = await manager.execute_with_retry(flaky_operation, "flaky_op")
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_execute_with_retry_permanent_failure(self):
        """Test execute_with_retry fails on non-retryable exception"""
        manager = RetryManager(RetryConfig(max_attempts=3))

        async def non_retryable_operation():
            raise ValueError("Non-retryable")

        with pytest.raises(ValueError, match="Non-retryable"):
            await manager.execute_with_retry(non_retryable_operation, "bad_op")

    @pytest.mark.asyncio
    async def test_execute_with_retry_max_attempts_exceeded(self):
        """Test execute_with_retry fails after max attempts"""
        config = RetryConfig(max_attempts=2, base_delay=0.01)
        manager = RetryManager(config)

        async def always_fails():
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError, match="Always fails"):
            await manager.execute_with_retry(always_fails, "failing_op")


@pytest.mark.unit
class TestCircuitBreaker:
    """Test CircuitBreaker state transitions and protection logic"""

    def test_circuit_breaker_initial_state(self):
        """Test CircuitBreaker starts in CLOSED state"""
        cb = CircuitBreaker("test_cb")
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_success_keeps_closed(self):
        """Test CircuitBreaker stays CLOSED on successful operations"""
        cb = CircuitBreaker("test_cb")

        async def success_operation():
            return "success"

        result = await cb.call(success_operation)
        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_threshold(self):
        """Test CircuitBreaker opens after failure threshold"""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test_cb", config)

        async def failing_operation():
            raise ConnectionError("Failure")

        # Fail 3 times to reach threshold
        for _ in range(3):
            with pytest.raises(ConnectionError):
                await cb.call(failing_operation)

        assert cb.state == CircuitBreakerState.OPEN
        assert cb.failure_count == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_rejects_when_open(self):
        """Test CircuitBreaker rejects requests when OPEN"""
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=60.0)
        cb = CircuitBreaker("test_cb", config)

        async def failing_operation():
            raise ConnectionError("Failure")

        # First failure opens circuit
        with pytest.raises(ConnectionError):
            await cb.call(failing_operation)

        assert cb.state == CircuitBreakerState.OPEN

        # Subsequent calls should be rejected immediately
        with pytest.raises(DatabaseMCPError, match="Circuit breaker.*is OPEN"):
            await cb.call(failing_operation)

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_after_timeout(self):
        """Test CircuitBreaker transitions to HALF_OPEN after recovery timeout"""
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.1)
        cb = CircuitBreaker("test_cb", config)

        async def failing_operation():
            raise ConnectionError("Failure")

        # Open circuit
        with pytest.raises(ConnectionError):
            await cb.call(failing_operation)
        assert cb.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Next call should transition to HALF_OPEN
        async def success_operation():
            return "success"

        result = await cb.call(success_operation)
        assert result == "success"
        # After successful call in HALF_OPEN, need more successes to close

    @pytest.mark.asyncio
    async def test_circuit_breaker_closes_after_success_threshold(self):
        """Test CircuitBreaker closes after success threshold in HALF_OPEN"""
        config = CircuitBreakerConfig(
            failure_threshold=1, recovery_timeout=0.1, success_threshold=2
        )
        cb = CircuitBreaker("test_cb", config)

        async def failing_operation():
            raise ConnectionError("Failure")

        # Open circuit
        with pytest.raises(ConnectionError):
            await cb.call(failing_operation)
        assert cb.state == CircuitBreakerState.OPEN

        # Wait for recovery
        await asyncio.sleep(0.15)

        # Succeed twice to close circuit
        async def success_operation():
            return "success"

        await cb.call(success_operation)  # First success, still HALF_OPEN
        await cb.call(success_operation)  # Second success, should close

        assert cb.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_timeout(self):
        """Test CircuitBreaker enforces operation timeout"""
        config = CircuitBreakerConfig(timeout=0.1)
        cb = CircuitBreaker("test_cb", config)

        async def slow_operation():
            await asyncio.sleep(1.0)  # Exceed timeout
            return "too slow"

        with pytest.raises(asyncio.TimeoutError):
            await cb.call(slow_operation)

        # Should have recorded failure
        assert cb.failure_count == 1

    def test_circuit_breaker_get_state(self):
        """Test CircuitBreaker.get_state() returns current state"""
        cb = CircuitBreaker("test_cb")
        state = cb.get_state()

        assert state["name"] == "test_cb"
        assert state["state"] == "closed"
        assert state["failure_count"] == 0
        assert state["success_count"] == 0
        assert "last_failure_time" in state


@pytest.mark.unit
class TestErrorResponseFormatter:
    """Test ErrorResponseFormatter for consistent error formatting"""

    def test_format_database_mcp_error(self):
        """Test formatting DatabaseMCPError"""
        error = DatabaseMCPError(
            "Test error",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            error_code="TEST_ERROR",
            recoverable=True,
            context={"key": "value"},
        )

        response = ErrorResponseFormatter.format_error_response(error)

        assert response["success"] is False
        assert response["error"] == "Test error"
        assert response["error_code"] == "TEST_ERROR"
        assert response["severity"] == "high"
        assert response["category"] == "database"
        assert response["recoverable"] is True
        assert "timestamp" in response
        assert response["context"] == {"key": "value"}

    def test_format_generic_exception(self):
        """Test formatting generic Exception"""
        error = ValueError("Invalid value")

        response = ErrorResponseFormatter.format_error_response(error)

        assert response["success"] is False
        assert response["error"] == "Invalid value"
        assert response["error_code"] == "ValueError"  # Uses error.__class__.__name__
        assert response["severity"] == "medium"
        assert response["category"] == "unknown"
        assert response["recoverable"] is False
        assert response["timestamp"] is not None

    def test_format_with_error_context(self):
        """Test formatting with ErrorContext"""
        error = DatabaseQueryError("Query failed")
        error_context = ErrorContext(
            error_id="err_123",
            timestamp=time.time(),
            error_type="QueryError",
            error_message="Query failed",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.DATABASE,
            client_id="client_1",
            operation="select_users",
        )

        response = ErrorResponseFormatter.format_error_response(error, error_context)

        assert response["success"] is False
        # error_context fields are merged into response, not nested
        assert response["error_id"] == "err_123"
        assert response["client_id"] == "client_1"
        assert response["operation"] == "select_users"
        assert "recovery_attempted" in response
        assert "recovery_action" in response
        assert "recovery_success" in response

    def test_format_with_stack_trace(self):
        """Test formatting with stack trace included"""
        error = DatabaseConnectionError("Connection failed")

        try:
            raise error
        except Exception as e:
            response = ErrorResponseFormatter.format_error_response(
                e, include_stack_trace=True
            )

        assert response["success"] is False
        assert "stack_trace" in response
        assert response["stack_trace"] is not None


@pytest.mark.unit
class TestErrorContext:
    """Test ErrorContext dataclass"""

    def test_error_context_creation(self):
        """Test ErrorContext creation with all fields"""
        context = ErrorContext(
            error_id="err_123",
            timestamp=time.time(),
            error_type="TestError",
            error_message="Test message",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            client_id="client_1",
            operation="test_operation",
            context_data={"key": "value"},
            stack_trace="stack trace",
            recovery_attempted=True,
            recovery_action=RecoveryAction.RETRY,
            recovery_success=True,
        )

        assert context.error_id == "err_123"
        assert context.error_type == "TestError"
        assert context.error_message == "Test message"
        assert context.severity == ErrorSeverity.HIGH
        assert context.category == ErrorCategory.DATABASE
        assert context.client_id == "client_1"
        assert context.operation == "test_operation"
        assert context.context_data == {"key": "value"}
        assert context.recovery_attempted is True
        assert context.recovery_action == RecoveryAction.RETRY
        assert context.recovery_success is True

    def test_error_context_defaults(self):
        """Test ErrorContext with default values"""
        context = ErrorContext(
            error_id="err_456",
            timestamp=time.time(),
            error_type="TestError",
            error_message="Test",
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION,
        )

        assert context.client_id == "unknown"
        assert context.operation == "unknown"
        assert context.context_data == {}
        assert context.stack_trace is None
        assert context.recovery_attempted is False
        assert context.recovery_action is None
        assert context.recovery_success is False


@pytest.mark.unit
class TestAdditionalExceptions:
    """Test additional custom exception classes."""

    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Invalid config")
        assert error.message == "Invalid config"
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.CONFIGURATION
        assert error.recoverable is False

    def test_resource_exhaustion_error(self):
        """Test ResourceExhaustionError."""
        error = ResourceExhaustionError("Out of memory")
        assert error.message == "Out of memory"
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.SYSTEM
        assert error.recoverable is True

    def test_rate_limit_exceeded_error(self):
        """Test RateLimitExceededError."""
        error = RateLimitExceededError("Too many requests")
        assert error.message == "Too many requests"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.category == ErrorCategory.CLIENT
        assert error.recoverable is True


@pytest.mark.unit
class TestGracefulDegradationManager:
    """Unit tests for GracefulDegradationManager."""

    @pytest.fixture
    def mock_logger(self):
        """Mock the logger for GracefulDegradationManager."""
        with patch("database.src.error_handling.get_logger") as mock_get_logger:
            mock_logger_instance = MagicMock()
            mock_get_logger.return_value = mock_logger_instance
            yield mock_logger_instance

    @pytest.fixture
    def degradation_manager(self, mock_logger):
        """Fixture for GracefulDegradationManager."""
        config = DegradationConfig(
            max_degraded_duration=300.0,
            enable_cached_responses=True,
        )
        return GracefulDegradationManager(config)

    def test_initial_state(self, degradation_manager):
        """Test initial state of degradation manager."""
        state = degradation_manager.get_service_state("test_service")
        assert state == ServiceState.AVAILABLE

    def test_set_service_state_to_degraded(self, degradation_manager, mock_logger):
        """Test setting service state to degraded."""
        degradation_manager.set_service_state("test_service", ServiceState.DEGRADED)

        state = degradation_manager.get_service_state("test_service")
        assert state == ServiceState.DEGRADED

        # Should log degradation
        mock_logger.warning.assert_called_once()
        assert "SERVICE_DEGRADED" in str(mock_logger.warning.call_args)

    def test_set_service_state_to_unavailable(self, degradation_manager, mock_logger):
        """Test setting service state to unavailable."""
        degradation_manager.set_service_state("test_service", ServiceState.UNAVAILABLE)

        state = degradation_manager.get_service_state("test_service")
        assert state == ServiceState.UNAVAILABLE

        mock_logger.warning.assert_called_once()

    def test_set_service_state_to_available(self, degradation_manager, mock_logger):
        """Test recovering service to available state."""
        # First degrade
        degradation_manager.set_service_state("test_service", ServiceState.DEGRADED)
        mock_logger.warning.assert_called_once()

        # Then recover
        degradation_manager.set_service_state("test_service", ServiceState.AVAILABLE)
        state = degradation_manager.get_service_state("test_service")
        assert state == ServiceState.AVAILABLE

        # Should log recovery
        mock_logger.info.assert_called_once()
        assert "SERVICE_RECOVERED" in str(mock_logger.info.call_args)

    def test_should_use_fallback_unavailable(self, degradation_manager):
        """Test fallback decision for unavailable service."""
        degradation_manager.set_service_state("test_service", ServiceState.UNAVAILABLE)
        assert degradation_manager.should_use_fallback("test_service") is True

    def test_should_use_fallback_degraded_timeout(self, degradation_manager):
        """Test fallback decision for degraded service after timeout."""
        degradation_manager.set_service_state("test_service", ServiceState.DEGRADED)

        # Immediately should not use fallback
        assert degradation_manager.should_use_fallback("test_service") is False

        # Simulate time passing beyond max_degraded_duration
        with patch("time.time", return_value=time.time() + 400):
            assert degradation_manager.should_use_fallback("test_service") is True

    def test_should_use_fallback_available(self, degradation_manager):
        """Test fallback decision for available service."""
        assert degradation_manager.should_use_fallback("test_service") is False

    def test_cache_response(self, degradation_manager):
        """Test caching responses."""
        response = {"data": "test_data"}
        degradation_manager.cache_response("test_key", response)

        cached = degradation_manager.get_cached_response("test_key")
        assert cached is not None
        assert cached["data"] == "test_data"
        assert cached["_cached_response"] is True
        assert "_cached_at" in cached

    def test_get_cached_response_not_found(self, degradation_manager):
        """Test getting cached response that doesn't exist."""
        cached = degradation_manager.get_cached_response("nonexistent_key")
        assert cached is None

    def test_get_cached_response_expired(self, degradation_manager):
        """Test getting expired cached response."""
        response = {"data": "test_data"}
        degradation_manager.cache_response("test_key", response)

        # Simulate time passing beyond max_age
        with patch("time.time", return_value=time.time() + 400):
            cached = degradation_manager.get_cached_response("test_key", max_age=300.0)
            assert cached is None

    def test_caching_disabled(self, mock_logger):
        """Test that caching is disabled when config is set."""
        config = DegradationConfig(enable_cached_responses=False)
        manager = GracefulDegradationManager(config)

        response = {"data": "test"}
        manager.cache_response("test_key", response)

        cached = manager.get_cached_response("test_key")
        assert cached is None


@pytest.mark.unit
class TestErrorHandler:
    """Unit tests for ErrorHandler."""

    @pytest.fixture
    def mock_config(self):
        """Mock Config for ErrorHandler."""
        with patch("database.src.error_handling.Config") as MockConfig:  # noqa: N806
            mock_instance = MockConfig.return_value
            mock_instance.server.debug = False
            yield mock_instance

    @pytest.fixture
    def mock_logger(self):
        """Mock logger for ErrorHandler."""
        with patch("database.src.error_handling.get_logger") as mock_get_logger:
            mock_logger_instance = MagicMock()
            mock_get_logger.return_value = mock_logger_instance
            yield mock_logger_instance

    @pytest.fixture
    def error_handler(self, mock_config, mock_logger):
        """Fixture for ErrorHandler."""
        return ErrorHandler()

    def test_get_circuit_breaker_creates_new(self, error_handler):
        """Test that get_circuit_breaker creates a new circuit breaker."""
        cb = error_handler.get_circuit_breaker("test_service")
        assert cb is not None
        assert cb.name == "test_service"

    def test_get_circuit_breaker_returns_existing(self, error_handler):
        """Test that get_circuit_breaker returns existing circuit breaker."""
        cb1 = error_handler.get_circuit_breaker("test_service")
        cb2 = error_handler.get_circuit_breaker("test_service")
        assert cb1 is cb2

    @pytest.mark.asyncio
    async def test_handle_operation_success(self, error_handler):
        """Test handle_operation context manager with successful operation."""
        async with error_handler.handle_operation("test_op", client_id="client_1"):
            result = "success"

        assert result == "success"

    @pytest.mark.asyncio
    async def test_handle_operation_error(self, error_handler, mock_logger):
        """Test handle_operation context manager with error."""
        with pytest.raises(DatabaseQueryError):
            async with error_handler.handle_operation(
                "test_op", client_id="client_1", service_name="test_service"
            ):
                raise DatabaseQueryError("Query failed")

        # Should log the error
        mock_logger.error.assert_called_once()
        assert "OPERATION_FAILED" in str(mock_logger.error.call_args)

    @pytest.mark.asyncio
    async def test_execute_with_recovery_success(self, error_handler):
        """Test execute_with_recovery with successful operation."""

        async def successful_op():
            return {"data": "success"}

        result = await error_handler.execute_with_recovery(
            successful_op, "test_op", enable_retry=False, enable_circuit_breaker=False
        )

        assert result == {"data": "success"}

    @pytest.mark.asyncio
    async def test_execute_with_recovery_with_retry(self, error_handler):
        """Test execute_with_recovery with retry enabled."""
        call_count = {"count": 0}

        async def flaky_op():
            call_count["count"] += 1
            if call_count["count"] < 2:
                raise DatabaseConnectionError("Connection failed")
            return {"data": "success"}

        result = await error_handler.execute_with_recovery(
            flaky_op, "test_op", enable_retry=True, enable_circuit_breaker=False
        )

        assert result == {"data": "success"}
        assert call_count["count"] == 2

    @pytest.mark.asyncio
    async def test_execute_with_recovery_with_circuit_breaker(self, error_handler):
        """Test execute_with_recovery with circuit breaker enabled."""

        async def successful_op():
            return {"data": "success"}

        result = await error_handler.execute_with_recovery(
            successful_op,
            "test_op",
            enable_retry=False,
            enable_circuit_breaker=True,
            service_name="test_service",
        )

        assert result == {"data": "success"}
        # Circuit breaker should be created
        assert "test_service" in error_handler.circuit_breakers

    @pytest.mark.asyncio
    async def test_execute_with_recovery_with_fallback(self, error_handler):
        """Test execute_with_recovery with fallback operation."""

        async def failing_op():
            raise DatabaseConnectionError("Primary failed")

        async def fallback_op():
            return {"data": "fallback_data"}

        # Set service to degraded so fallback is used
        error_handler.degradation_manager.set_service_state(
            "test_service", ServiceState.DEGRADED
        )

        # Simulate time passing beyond max_degraded_duration
        with patch("time.time", return_value=time.time() + 400):
            result = await error_handler.execute_with_recovery(
                failing_op,
                "test_op",
                enable_retry=False,
                enable_circuit_breaker=False,
                service_name="test_service",
                fallback_operation=fallback_op,
            )

        assert result["data"] == "fallback_data"
        assert result["_fallback_used"] is True

    @pytest.mark.asyncio
    async def test_execute_with_recovery_fallback_also_fails(
        self, error_handler, mock_logger
    ):
        """Test execute_with_recovery when both primary and fallback fail."""

        async def failing_op():
            raise DatabaseConnectionError("Primary failed")

        async def failing_fallback_op():
            raise DatabaseQueryError("Fallback failed")

        error_handler.degradation_manager.set_service_state(
            "test_service", ServiceState.DEGRADED
        )

        with patch("time.time", return_value=time.time() + 400):
            with pytest.raises(DatabaseConnectionError):
                await error_handler.execute_with_recovery(
                    failing_op,
                    "test_op",
                    enable_retry=False,
                    enable_circuit_breaker=False,
                    service_name="test_service",
                    fallback_operation=failing_fallback_op,
                )

        # Should log fallback failure
        assert any(
            "FALLBACK_OPERATION_FAILED" in str(call)
            for call in mock_logger.error.call_args_list
        )


@pytest.mark.unit
class TestHandleErrorsDecorator:
    """Unit tests for handle_errors decorator."""

    @pytest.fixture
    def mock_logger(self):
        """Mock logger."""
        with patch("database.src.error_handling.get_logger") as mock_get_logger:
            mock_logger_instance = MagicMock()
            mock_get_logger.return_value = mock_logger_instance
            yield mock_logger_instance

    @pytest.fixture
    def mock_config(self):
        """Mock Config."""
        with patch("database.src.error_handling.Config") as MockConfig:  # noqa: N806
            mock_instance = MockConfig.return_value
            mock_instance.server.debug = False
            yield mock_instance

    @pytest.mark.asyncio
    async def test_decorator_success(self, mock_logger, mock_config):
        """Test decorator with successful operation."""

        class TestClass:
            error_handler = ErrorHandler()

        @handle_errors(enable_retry=False, enable_circuit_breaker=False)
        async def test_method(self):
            return "success"

        instance = TestClass()
        result = await test_method(instance)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_decorator_with_error(self, mock_logger, mock_config):
        """Test decorator with error."""

        class TestClass:
            error_handler = ErrorHandler()

        @handle_errors(enable_retry=False, enable_circuit_breaker=False)
        async def test_method(self):
            raise DatabaseQueryError("Query failed")

        instance = TestClass()

        with pytest.raises(DatabaseQueryError):
            await test_method(instance)

    @pytest.mark.asyncio
    async def test_decorator_without_error_handler(self, mock_logger, mock_config):
        """Test decorator when instance doesn't have error_handler."""

        class TestClass:
            pass  # No error_handler attribute

        @handle_errors(enable_retry=False, enable_circuit_breaker=False)
        async def test_method(self):
            return "success"

        instance = TestClass()
        result = await test_method(instance)
        assert result == "success"
