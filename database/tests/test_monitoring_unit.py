"""Comprehensive unit tests for monitoring module"""
import time
from unittest.mock import MagicMock, patch

import pytest

from database.src.monitoring import (
    ErrorRecord,
    ErrorTracker,
    HealthCheckResult,
    HealthChecker,
    HealthStatus,
    Metric,
    MetricType,
    PerformanceTracker,
    ProductionMonitor,
    SystemResourceMonitor,
)


@pytest.mark.unit
class TestHealthCheckResult:
    """Test HealthCheckResult dataclass"""

    def test_health_check_result_creation(self):
        """Test basic HealthCheckResult creation"""
        result = HealthCheckResult(
            name="database_check",
            status=HealthStatus.HEALTHY,
            message="Database is responsive",
            details={"latency": 0.05},
            response_time=0.05,
        )

        assert result.name == "database_check"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Database is responsive"
        assert result.details == {"latency": 0.05}
        assert result.response_time == 0.05
        assert isinstance(result.timestamp, float)

    def test_health_check_result_defaults(self):
        """Test HealthCheckResult with default values"""
        result = HealthCheckResult(
            name="test_check",
            status=HealthStatus.DEGRADED,
            message="Service degraded",
        )

        assert result.details == {}
        assert result.response_time is None
        assert result.timestamp is not None


@pytest.mark.unit
class TestMetric:
    """Test Metric dataclass"""

    def test_metric_creation(self):
        """Test basic Metric creation"""
        metric = Metric(
            name="query_count",
            value=150.0,
            metric_type=MetricType.COUNTER,
            tags={"query_type": "SELECT", "client": "api"},
        )

        assert metric.name == "query_count"
        assert metric.value == 150.0
        assert metric.metric_type == MetricType.COUNTER
        assert metric.tags == {"query_type": "SELECT", "client": "api"}
        assert isinstance(metric.timestamp, float)

    def test_metric_defaults(self):
        """Test Metric with default values"""
        metric = Metric(
            name="latency",
            value=0.25,
            metric_type=MetricType.GAUGE,
        )

        assert metric.tags == {}
        assert metric.timestamp is not None


@pytest.mark.unit
class TestErrorRecord:
    """Test ErrorRecord dataclass"""

    def test_error_record_creation(self):
        """Test basic ErrorRecord creation"""
        timestamp = time.time()
        record = ErrorRecord(
            error_type="DatabaseError",
            error_message="Connection timeout",
            context={"host": "localhost", "port": 3306},
            timestamp=timestamp,
            severity="critical",
            count=5,
        )

        assert record.error_type == "DatabaseError"
        assert record.error_message == "Connection timeout"
        assert record.context == {"host": "localhost", "port": 3306}
        assert record.timestamp == timestamp
        assert record.severity == "critical"
        assert record.count == 5

    def test_error_record_defaults(self):
        """Test ErrorRecord with default values"""
        record = ErrorRecord(
            error_type="ValidationError",
            error_message="Invalid input",
            context={},
            timestamp=time.time(),
        )

        assert record.severity == "error"
        assert record.count == 1


@pytest.mark.unit
class TestPerformanceTracker:
    """Test PerformanceTracker for query and connection metrics"""

    def test_performance_tracker_initialization(self):
        """Test PerformanceTracker initializes correctly"""
        tracker = PerformanceTracker()

        assert len(tracker.query_times) == 0
        assert len(tracker.error_counts) == 0
        assert len(tracker.query_counts_by_type) == 0
        assert len(tracker.connection_events) == 0
        assert len(tracker.slow_queries) == 0
        assert tracker.peak_usage_tracker["max_concurrent_connections"] == 0
        assert tracker.peak_usage_tracker["max_query_time"] == 0.0

    def test_record_query_execution_success(self):
        """Test recording successful query execution"""
        tracker = PerformanceTracker()

        tracker.record_query_execution(
            query_type="SELECT",
            execution_time=0.05,
            success=True,
            client_id="client_1",
        )

        assert len(tracker.query_times) == 1
        assert tracker.query_counts_by_type["SELECT"] == 1
        assert tracker.error_counts["SELECT"] == 0

        query_record = tracker.query_times[0]
        assert query_record["execution_time"] == 0.05
        assert query_record["query_type"] == "SELECT"
        assert query_record["success"] is True
        assert query_record["client_id"] == "client_1"

    def test_record_query_execution_failure(self):
        """Test recording failed query execution"""
        tracker = PerformanceTracker()

        tracker.record_query_execution(
            query_type="INSERT",
            execution_time=0.02,
            success=False,
            client_id="client_2",
        )

        assert len(tracker.query_times) == 1
        assert tracker.query_counts_by_type["INSERT"] == 1
        assert tracker.error_counts["INSERT"] == 1  # Error recorded

    def test_record_slow_query(self):
        """Test recording slow queries above threshold"""
        tracker = PerformanceTracker()

        # Record slow query (>1.0 second default threshold)
        tracker.record_query_execution(
            query_type="SELECT",
            execution_time=2.5,
            success=True,
            client_id="slow_client",
            additional_context={"table": "large_table"},
        )

        assert len(tracker.slow_queries) == 1
        slow_query = tracker.slow_queries[0]
        assert slow_query["execution_time"] == 2.5
        assert slow_query["query_type"] == "SELECT"
        assert slow_query["client_id"] == "slow_client"
        assert slow_query["context"] == {"table": "large_table"}

    def test_record_peak_query_time(self):
        """Test tracking peak query time"""
        tracker = PerformanceTracker()

        tracker.record_query_execution("SELECT", 0.5, True)
        assert tracker.peak_usage_tracker["max_query_time"] == 0.5

        tracker.record_query_execution("SELECT", 1.5, True)
        assert tracker.peak_usage_tracker["max_query_time"] == 1.5

        # Lower time doesn't update peak
        tracker.record_query_execution("SELECT", 0.8, True)
        assert tracker.peak_usage_tracker["max_query_time"] == 1.5

    def test_record_connection_event(self):
        """Test recording connection events"""
        tracker = PerformanceTracker()

        tracker.record_connection_event(
            event_type="connect",
            client_id="client_1",
            details={"protocol": "stdio"},
        )

        assert len(tracker.connection_events) == 1
        event = tracker.connection_events[0]
        assert event["event_type"] == "connect"
        assert event["client_id"] == "client_1"
        assert event["details"] == {"protocol": "stdio"}
        assert "timestamp" in event

    def test_get_performance_metrics(self):
        """Test getting performance metrics summary"""
        tracker = PerformanceTracker()

        # Record some queries
        tracker.record_query_execution("SELECT", 0.05, True)
        tracker.record_query_execution("INSERT", 0.02, True)
        tracker.record_query_execution("SELECT", 2.0, True)  # Slow query
        tracker.record_query_execution("UPDATE", 0.03, False)  # Error

        metrics = tracker.get_performance_metrics()

        # Check top-level structure
        assert "query_performance" in metrics
        assert "peak_usage" in metrics
        assert "recent_connection_events" in metrics
        assert "slow_queries_sample" in metrics

        # Check query_performance nested dict
        perf = metrics["query_performance"]
        assert perf["total_queries"] == 4
        assert perf["query_counts_by_type"]["SELECT"] == 2
        assert perf["query_counts_by_type"]["INSERT"] == 1
        assert perf["error_counts"]["UPDATE"] == 1
        assert perf["slow_queries"] == 1
        assert "average_query_time" in perf
        assert "success_rate" in perf

    def test_deque_maxlen_enforcement(self):
        """Test that deques respect maxlen"""
        tracker = PerformanceTracker()

        # Add more than maxlen query times (maxlen=1000)
        for i in range(1100):
            tracker.record_query_execution("SELECT", 0.01, True)

        # Should only keep last 1000
        assert len(tracker.query_times) == 1000


@pytest.mark.unit
class TestErrorTracker:
    """Test ErrorTracker for error aggregation"""

    def test_error_tracker_initialization(self):
        """Test ErrorTracker initializes correctly"""
        tracker = ErrorTracker(max_errors=100)

        assert tracker.max_errors == 100
        assert len(tracker.errors) == 0
        assert len(tracker.error_counts) == 0
        assert len(tracker.error_rates) == 0

    def test_record_error_basic(self):
        """Test recording basic error"""
        tracker = ErrorTracker()

        tracker.record_error(
            error_type="DatabaseError",
            error_message="Connection failed",
            context={"host": "localhost"},
            severity="critical",
        )

        assert len(tracker.errors) == 1
        assert tracker.error_counts["DatabaseError"] == 1

        error = tracker.errors[0]
        assert error.error_type == "DatabaseError"
        assert error.error_message == "Connection failed"
        assert error.context == {"host": "localhost"}
        assert error.severity == "critical"

    def test_record_multiple_errors_of_same_type(self):
        """Test recording multiple errors of same type increments count"""
        tracker = ErrorTracker()

        tracker.record_error("ValidationError", "Invalid email")
        tracker.record_error("ValidationError", "Invalid phone")
        tracker.record_error("ValidationError", "Invalid address")

        assert len(tracker.errors) == 3
        assert tracker.error_counts["ValidationError"] == 3

    def test_error_rate_tracking(self):
        """Test error rate tracking by minute"""
        tracker = ErrorTracker()

        # Record errors
        tracker.record_error("DatabaseError", "Connection timeout")
        tracker.record_error("DatabaseError", "Query timeout")

        # Error rates should be tracked
        assert "DatabaseError" in tracker.error_rates
        assert len(tracker.error_rates["DatabaseError"]) > 0

    def test_get_error_summary(self):
        """Test getting error summary"""
        tracker = ErrorTracker()

        # Record various errors
        tracker.record_error("DatabaseError", "Connection failed", severity="critical")
        tracker.record_error("ValidationError", "Invalid input", severity="warning")
        tracker.record_error("DatabaseError", "Query timeout", severity="error")

        summary = tracker.get_error_summary()

        # Check expected structure returned by get_error_summary
        assert "total_errors" in summary
        assert summary["total_errors"] == 3
        assert "recent_errors_1hour" in summary
        assert summary["recent_errors_1hour"] == 3
        assert "error_counts" in summary
        assert summary["error_counts"]["DatabaseError"] == 2
        assert summary["error_counts"]["ValidationError"] == 1
        assert "error_rates_per_minute" in summary
        assert "recent_errors_by_type" in summary
        assert "top_errors" in summary

    def test_maxlen_enforcement(self):
        """Test that error deque respects maxlen"""
        tracker = ErrorTracker(max_errors=10)

        # Record more than maxlen
        for i in range(15):
            tracker.record_error("TestError", f"Error {i}")

        # Should only keep last 10
        assert len(tracker.errors) == 10


@pytest.mark.unit
class TestSystemResourceMonitor:
    """Test SystemResourceMonitor for system metrics"""

    @patch("database.src.monitoring.psutil.Process")
    @patch("database.src.monitoring.psutil.virtual_memory")
    @patch("database.src.monitoring.psutil.cpu_percent")
    @patch("database.src.monitoring.psutil.disk_usage")
    def test_get_system_metrics_success(
        self,
        mock_disk_usage,
        mock_cpu_percent,
        mock_virtual_memory,
        mock_process_class,
    ):
        """Test getting system metrics successfully"""
        # Mock process
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=1000000, vms=2000000)
        mock_process.cpu_percent.return_value = 5.0
        mock_process.memory_percent.return_value = 2.5
        mock_process.num_threads.return_value = 10
        mock_process.create_time.return_value = time.time() - 3600
        mock_process.num_fds.return_value = 50
        mock_process_class.return_value = mock_process

        # Mock system metrics
        mock_virtual_memory.return_value = MagicMock(
            total=16000000000,
            available=8000000000,
            percent=50.0,
        )
        mock_cpu_percent.return_value = 25.0
        mock_disk_usage.return_value = MagicMock(
            total=500000000000,
            free=250000000000,
            percent=50.0,
        )

        monitor = SystemResourceMonitor()
        metrics = monitor.get_system_metrics()

        assert "process" in metrics
        assert metrics["process"]["memory_rss"] == 1000000
        assert metrics["process"]["cpu_percent"] == 5.0
        assert metrics["process"]["num_threads"] == 10
        assert "system" in metrics
        assert metrics["system"]["cpu_percent"] == 25.0
        assert metrics["system"]["memory_percent"] == 50.0
        assert "network" in metrics

    @patch("database.src.monitoring.psutil.Process")
    def test_get_system_metrics_error_handling(self, mock_process_class):
        """Test error handling in get_system_metrics"""
        # Make process.memory_info raise an exception
        mock_process = MagicMock()
        mock_process.memory_info.side_effect = Exception("Test error")
        mock_process_class.return_value = mock_process

        monitor = SystemResourceMonitor()
        metrics = monitor.get_system_metrics()

        assert "error" in metrics
        assert "Test error" in metrics["error"]

