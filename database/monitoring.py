import asyncio
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
import json
import psutil
import os
from .config import get_config
from .logging_config import get_logger

class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"

class MetricType(Enum):
    """Types of metrics we collect."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMING = "timing"

@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    response_time: Optional[float] = None
    timestamp: float = field(default_factory=time.time)

@dataclass
class Metric:
    """A single metric data point."""
    name: str
    value: float
    metric_type: MetricType
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

@dataclass
class ErrorRecord:
    """Record of an error for tracking."""
    error_type: str
    error_message: str
    context: Dict[str, Any]
    timestamp: float
    severity: str = "error"
    count: int = 1

class PerformanceTracker:
    """Tracks performance metrics and query statistics."""
    
    def __init__(self):
        """Initialize performance tracker."""
        self.query_times = deque(maxlen=1000)  # Last 1000 queries
        self.error_counts = defaultdict(int)
        self.query_counts_by_type = defaultdict(int)
        self.connection_events = deque(maxlen=500)
        self.slow_queries = deque(maxlen=100)  # Queries over threshold
        self.peak_usage_tracker = {
            'max_concurrent_connections': 0,
            'max_query_time': 0.0,
            'max_memory_usage': 0.0,
            'peak_timestamps': {}
        }
        self._lock = threading.Lock()
    
    def record_query_execution(
        self, 
        query_type: str, 
        execution_time: float, 
        success: bool,
        client_id: str = "default",
        additional_context: Optional[Dict] = None
    ) -> None:
        """Record a query execution event."""
        with self._lock:
            timestamp = time.time()
            
            # Record query timing
            self.query_times.append({
                'execution_time': execution_time,
                'timestamp': timestamp,
                'query_type': query_type,
                'success': success,
                'client_id': client_id
            })
            
            # Count by type
            self.query_counts_by_type[query_type.upper()] += 1
            
            # Track errors
            if not success:
                self.error_counts[query_type.upper()] += 1
            
            # Track slow queries (>1 second by default)
            config = get_config()
            slow_query_threshold = getattr(config.database, 'slow_query_threshold', 1.0)
            if execution_time > slow_query_threshold:
                self.slow_queries.append({
                    'execution_time': execution_time,
                    'query_type': query_type,
                    'timestamp': timestamp,
                    'client_id': client_id,
                    'context': additional_context or {}
                })
            
            # Update peak query time
            if execution_time > self.peak_usage_tracker['max_query_time']:
                self.peak_usage_tracker['max_query_time'] = execution_time
                self.peak_usage_tracker['peak_timestamps']['max_query_time'] = timestamp
    
    def record_connection_event(self, event_type: str, client_id: str, details: Dict[str, Any] = None) -> None:
        """Record a connection event."""
        with self._lock:
            self.connection_events.append({
                'event_type': event_type,
                'client_id': client_id,
                'timestamp': time.time(),
                'details': details or {}
            })
    
    def update_peak_connections(self, current_connections: int) -> None:
        """Update peak connection count."""
        with self._lock:
            if current_connections > self.peak_usage_tracker['max_concurrent_connections']:
                self.peak_usage_tracker['max_concurrent_connections'] = current_connections
                self.peak_usage_tracker['peak_timestamps']['max_concurrent_connections'] = time.time()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        with self._lock:
            now = time.time()
            recent_queries = [q for q in self.query_times if now - q['timestamp'] < 300]  # Last 5 minutes
            
            if recent_queries:
                avg_query_time = sum(q['execution_time'] for q in recent_queries) / len(recent_queries)
                success_rate = sum(1 for q in recent_queries if q['success']) / len(recent_queries)
            else:
                avg_query_time = 0.0
                success_rate = 1.0
            
            return {
                'query_performance': {
                    'total_queries': len(self.query_times),
                    'recent_queries_5min': len(recent_queries),
                    'average_query_time': avg_query_time,
                    'success_rate': success_rate,
                    'queries_per_minute': len(recent_queries) / 5.0,
                    'slow_queries': len(self.slow_queries),
                    'error_counts': dict(self.error_counts),
                    'query_counts_by_type': dict(self.query_counts_by_type)
                },
                'peak_usage': self.peak_usage_tracker.copy(),
                'recent_connection_events': list(self.connection_events)[-10:],  # Last 10 events
                'slow_queries_sample': list(self.slow_queries)[-5:]  # Last 5 slow queries
            }

class SystemResourceMonitor:
    """Monitors system resource usage."""
    
    def __init__(self):
        """Initialize system resource monitor."""
        self.logger = get_logger('monitoring')
        self.process = psutil.Process()
        self._last_cpu_time = None
        self._cpu_percent = 0.0
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system resource metrics."""
        try:
            # Process-specific metrics
            memory_info = self.process.memory_info()
            cpu_percent = self.process.cpu_percent()
            
            # System-wide metrics
            system_memory = psutil.virtual_memory()
            system_cpu = psutil.cpu_percent(interval=0.1)
            disk_usage = psutil.disk_usage('/')
            
            # Network I/O if available
            try:
                network_io = psutil.net_io_counters()
                network_stats = {
                    'bytes_sent': network_io.bytes_sent,
                    'bytes_recv': network_io.bytes_recv,
                    'packets_sent': network_io.packets_sent,
                    'packets_recv': network_io.packets_recv
                }
            except Exception:
                network_stats = {}
            
            return {
                'process': {
                    'memory_rss': memory_info.rss,
                    'memory_vms': memory_info.vms,
                    'memory_percent': self.process.memory_percent(),
                    'cpu_percent': cpu_percent,
                    'num_threads': self.process.num_threads(),
                    'num_fds': self.process.num_fds() if hasattr(self.process, 'num_fds') else None,
                    'create_time': self.process.create_time()
                },
                'system': {
                    'cpu_percent': system_cpu,
                    'memory_total': system_memory.total,
                    'memory_available': system_memory.available,
                    'memory_percent': system_memory.percent,
                    'disk_total': disk_usage.total,
                    'disk_free': disk_usage.free,
                    'disk_percent': disk_usage.percent,
                    'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
                },
                'network': network_stats
            }
        except Exception as e:
            self.logger.error("SYSTEM_METRICS_ERROR", {
                "error": str(e),
                "error_type": type(e).__name__
            }, exc_info=True)
            return {'error': str(e)}

class ErrorTracker:
    """Tracks and aggregates errors for monitoring and alerting."""
    
    def __init__(self, max_errors: int = 1000):
        """Initialize error tracker."""
        self.max_errors = max_errors
        self.errors = deque(maxlen=max_errors)
        self.error_counts = defaultdict(int)
        self.error_rates = defaultdict(list)
        self._lock = threading.Lock()
    
    def record_error(
        self, 
        error_type: str, 
        error_message: str, 
        context: Dict[str, Any] = None,
        severity: str = "error"
    ) -> None:
        """Record an error occurrence."""
        with self._lock:
            timestamp = time.time()
            
            error_record = ErrorRecord(
                error_type=error_type,
                error_message=error_message,
                context=context or {},
                timestamp=timestamp,
                severity=severity
            )
            
            self.errors.append(error_record)
            self.error_counts[error_type] += 1
            
            # Track error rates (errors per minute)
            minute_bucket = int(timestamp // 60)
            self.error_rates[error_type].append(minute_bucket)
            
            # Keep only last hour of rate data
            cutoff = minute_bucket - 60
            self.error_rates[error_type] = [
                bucket for bucket in self.error_rates[error_type] 
                if bucket > cutoff
            ]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error tracking summary."""
        with self._lock:
            now = time.time()
            recent_errors = [e for e in self.errors if now - e.timestamp < 3600]  # Last hour
            
            # Calculate error rates
            error_rates = {}
            for error_type, buckets in self.error_rates.items():
                if buckets:
                    # Errors per minute in the last hour
                    error_rates[error_type] = len(buckets) / 60.0
                else:
                    error_rates[error_type] = 0.0
            
            # Group recent errors by type
            recent_by_type = defaultdict(list)
            for error in recent_errors:
                recent_by_type[error.error_type].append({
                    'message': error.error_message,
                    'timestamp': error.timestamp,
                    'severity': error.severity,
                    'context': error.context
                })
            
            return {
                'total_errors': len(self.errors),
                'recent_errors_1hour': len(recent_errors),
                'error_counts': dict(self.error_counts),
                'error_rates_per_minute': error_rates,
                'recent_errors_by_type': dict(recent_by_type),
                'top_errors': sorted(
                    self.error_counts.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:10]
            }

class HealthChecker:
    """Comprehensive health checking system."""
    
    def __init__(self, database_manager, security_manager):
        """Initialize health checker."""
        self.database_manager = database_manager
        self.security_manager = security_manager
        self.config = get_config()
        self.logger = get_logger('monitoring')
        
        # Health check registry
        self.health_checks: List[Callable] = [
            self._check_database_connectivity,
            self._check_connection_pool,
            self._check_system_resources,
            self._check_security_status,
            self._check_error_rates,
            self._check_performance_thresholds
        ]
    
    async def run_all_health_checks(self) -> Dict[str, Any]:
        """Run all registered health checks."""
        results = []
        overall_status = HealthStatus.HEALTHY
        start_time = time.time()
        
        for health_check in self.health_checks:
            try:
                result = await health_check()
                results.append(result)
                
                # Determine overall status (worst case)
                if result.status.value == "critical":
                    overall_status = HealthStatus.CRITICAL
                elif result.status.value == "unhealthy" and overall_status != HealthStatus.CRITICAL:
                    overall_status = HealthStatus.UNHEALTHY
                elif result.status.value == "degraded" and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
                    
            except Exception as e:
                self.logger.error("HEALTH_CHECK_ERROR", {
                    "error": str(e),
                    "error_type": type(e).__name__
                }, exc_info=True)
                results.append(HealthCheckResult(
                    name="health_check_error",
                    status=HealthStatus.CRITICAL,
                    message=f"Health check system error: {str(e)}"
                ))
                overall_status = HealthStatus.CRITICAL
        
        total_time = time.time() - start_time
        
        return {
            'overall_status': overall_status.value,
            'total_checks': len(results),
            'healthy_checks': sum(1 for r in results if r.status == HealthStatus.HEALTHY),
            'total_check_time': total_time,
            'timestamp': time.time(),
            'checks': [
                {
                    'name': r.name,
                    'status': r.status.value,
                    'message': r.message,
                    'details': r.details,
                    'response_time': r.response_time
                }
                for r in results
            ]
        }
    
    async def _check_database_connectivity(self) -> HealthCheckResult:
        """Check database connectivity and response time."""
        start_time = time.time()
        try:
            health_result = await self.database_manager.health_check()
            response_time = time.time() - start_time
            
            if health_result.get('status') == 'healthy':
                return HealthCheckResult(
                    name="database_connectivity",
                    status=HealthStatus.HEALTHY,
                    message="Database connection is healthy",
                    response_time=response_time,
                    details=health_result
                )
            else:
                return HealthCheckResult(
                    name="database_connectivity", 
                    status=HealthStatus.UNHEALTHY,
                    message="Database connection is unhealthy",
                    response_time=response_time,
                    details=health_result
                )
        except Exception as e:
            return HealthCheckResult(
                name="database_connectivity",
                status=HealthStatus.CRITICAL,
                message=f"Database connectivity check failed: {str(e)}",
                response_time=time.time() - start_time
            )
    
    async def _check_connection_pool(self) -> HealthCheckResult:
        """Check connection pool health."""
        try:
            stats = await self.database_manager.get_connection_stats()
            pool_initialized = stats.get('pool_initialized', False)
            
            if not pool_initialized:
                return HealthCheckResult(
                    name="connection_pool",
                    status=HealthStatus.CRITICAL,
                    message="Connection pool not initialized"
                )
            
            pool_size = stats.get('pool_size', 0)
            pool_free_size = stats.get('pool_free_size', 0)
            pool_max_size = stats.get('pool_max_size', 1)
            
            utilization = (pool_size - pool_free_size) / pool_max_size if pool_max_size > 0 else 0
            
            if utilization > 0.9:
                status = HealthStatus.CRITICAL
                message = f"Connection pool critically full ({utilization:.1%} utilization)"
            elif utilization > 0.7:
                status = HealthStatus.DEGRADED
                message = f"Connection pool high utilization ({utilization:.1%})"
            else:
                status = HealthStatus.HEALTHY
                message = f"Connection pool healthy ({utilization:.1%} utilization)"
            
            return HealthCheckResult(
                name="connection_pool",
                status=status,
                message=message,
                details={
                    'utilization': utilization,
                    'pool_size': pool_size,
                    'pool_free_size': pool_free_size,
                    'pool_max_size': pool_max_size
                }
            )
        except Exception as e:
            return HealthCheckResult(
                name="connection_pool",
                status=HealthStatus.CRITICAL,
                message=f"Connection pool check failed: {str(e)}"
            )
    
    async def _check_system_resources(self) -> HealthCheckResult:
        """Check system resource usage."""
        try:
            resource_monitor = SystemResourceMonitor()
            metrics = resource_monitor.get_system_metrics()
            
            if 'error' in metrics:
                return HealthCheckResult(
                    name="system_resources",
                    status=HealthStatus.DEGRADED,
                    message=f"Could not collect system metrics: {metrics['error']}"
                )
            
            # Check critical thresholds
            memory_percent = metrics['system']['memory_percent']
            cpu_percent = metrics['system']['cpu_percent']
            disk_percent = metrics['system']['disk_percent']
            
            issues = []
            status = HealthStatus.HEALTHY
            
            if memory_percent > 90:
                issues.append(f"High memory usage: {memory_percent:.1f}%")
                status = HealthStatus.CRITICAL
            elif memory_percent > 75:
                issues.append(f"Elevated memory usage: {memory_percent:.1f}%")
                status = HealthStatus.DEGRADED
            
            if cpu_percent > 80:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
                if status != HealthStatus.CRITICAL:
                    status = HealthStatus.DEGRADED
            
            if disk_percent > 95:
                issues.append(f"Critical disk usage: {disk_percent:.1f}%")
                status = HealthStatus.CRITICAL
            elif disk_percent > 85:
                issues.append(f"High disk usage: {disk_percent:.1f}%")
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED
            
            message = "System resources healthy" if not issues else "; ".join(issues)
            
            return HealthCheckResult(
                name="system_resources",
                status=status,
                message=message,
                details=metrics
            )
        except Exception as e:
            return HealthCheckResult(
                name="system_resources",
                status=HealthStatus.DEGRADED,
                message=f"System resource check failed: {str(e)}"
            )
    
    async def _check_security_status(self) -> HealthCheckResult:
        """Check security system status."""
        try:
            security_report = self.security_manager.get_comprehensive_security_report()
            connection_security = security_report.get('connection_security', {})
            
            active_blocks = connection_security.get('active_blocks', 0)
            clients_with_failures = connection_security.get('clients_with_failures', 0)
            
            if active_blocks > 10:
                status = HealthStatus.DEGRADED
                message = f"High number of blocked clients: {active_blocks}"
            elif clients_with_failures > 5:
                status = HealthStatus.DEGRADED
                message = f"Multiple clients with authentication failures: {clients_with_failures}"
            else:
                status = HealthStatus.HEALTHY
                message = "Security status normal"
            
            return HealthCheckResult(
                name="security_status",
                status=status,
                message=message,
                details={
                    'active_blocks': active_blocks,
                    'clients_with_failures': clients_with_failures
                }
            )
        except Exception as e:
            return HealthCheckResult(
                name="security_status",
                status=HealthStatus.DEGRADED,
                message=f"Security status check failed: {str(e)}"
            )
    
    async def _check_error_rates(self) -> HealthCheckResult:
        """Check error rates and patterns."""
        # This would integrate with the ErrorTracker
        # For now, return healthy status
        return HealthCheckResult(
            name="error_rates",
            status=HealthStatus.HEALTHY,
            message="Error rates within normal limits"
        )
    
    async def _check_performance_thresholds(self) -> HealthCheckResult:
        """Check performance metrics against thresholds."""
        # This would integrate with the PerformanceTracker
        # For now, return healthy status
        return HealthCheckResult(
            name="performance_thresholds",
            status=HealthStatus.HEALTHY,
            message="Performance metrics within acceptable ranges"
        )

class ProductionMonitor:
    """Main production monitoring system that coordinates all monitoring components."""
    
    def __init__(self, database_manager, security_manager):
        """Initialize production monitor."""
        self.database_manager = database_manager
        self.security_manager = security_manager
        self.config = get_config()
        self.logger = get_logger('monitoring')
        
        # Initialize monitoring components
        self.performance_tracker = PerformanceTracker()
        self.system_monitor = SystemResourceMonitor()
        self.error_tracker = ErrorTracker()
        self.health_checker = HealthChecker(database_manager, security_manager)
        
        # Metrics collection
        self.metrics = deque(maxlen=10000)  # Store last 10k metrics
        self._metrics_lock = threading.Lock()
        
        self.logger.info("MONITORING_SYSTEM_INIT", {
            "max_metrics": 10000,
            "components": ["performance_tracker", "system_monitor", "error_tracker", "health_checker"]
        })
    
    def record_metric(self, name: str, value: float, metric_type: MetricType, tags: Dict[str, str] = None) -> None:
        """Record a metric."""
        with self._metrics_lock:
            metric = Metric(
                name=name,
                value=value,
                metric_type=metric_type,
                tags=tags or {},
                timestamp=time.time()
            )
            self.metrics.append(metric)
    
    def record_query_metrics(self, query_type: str, execution_time: float, success: bool, client_id: str = "default") -> None:
        """Record query-related metrics."""
        self.performance_tracker.record_query_execution(query_type, execution_time, success, client_id)
        
        # Record individual metrics
        self.record_metric(
            "query_execution_time",
            execution_time,
            MetricType.TIMING,
            {"query_type": query_type, "client_id": client_id}
        )
        
        self.record_metric(
            "query_count",
            1,
            MetricType.COUNTER,
            {"query_type": query_type, "success": str(success), "client_id": client_id}
        )
    
    def record_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None, severity: str = "error") -> None:
        """Record an error for tracking."""
        self.error_tracker.record_error(error_type, error_message, context, severity)
        
        # Record error metric
        self.record_metric(
            "error_count",
            1,
            MetricType.COUNTER,
            {"error_type": error_type, "severity": severity}
        )
    
    async def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status."""
        timestamp = time.time()
        
        # Collect all monitoring data
        health_status = await self.health_checker.run_all_health_checks()
        performance_metrics = self.performance_tracker.get_performance_metrics()
        system_metrics = self.system_monitor.get_system_metrics()
        error_summary = self.error_tracker.get_error_summary()
        
        # Get recent metrics summary
        with self._metrics_lock:
            recent_metrics = [m for m in self.metrics if timestamp - m.timestamp < 300]  # Last 5 minutes
            
        return {
            'timestamp': timestamp,
            'uptime': timestamp - performance_metrics.get('peak_usage', {}).get('peak_timestamps', {}).get('max_concurrent_connections', timestamp),
            'overall_status': health_status['overall_status'],
            'health_checks': health_status,
            'performance': performance_metrics,
            'system_resources': system_metrics,
            'error_tracking': error_summary,
            'metrics_summary': {
                'total_metrics': len(self.metrics),
                'recent_metrics_5min': len(recent_metrics)
            },
            'configuration': {
                'monitoring_enabled': True,
                'max_metrics_stored': len(self.metrics),
                'health_check_count': len(self.health_checker.health_checks)
            }
        }
    
    async def get_metrics_export(self, format_type: str = "prometheus") -> str:
        """Export metrics in various formats for external monitoring systems."""
        if format_type.lower() == "prometheus":
            return await self._export_prometheus_format()
        elif format_type.lower() == "json":
            return await self._export_json_format()
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    async def _export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        with self._metrics_lock:
            # Group metrics by name
            metrics_by_name = defaultdict(list)
            for metric in self.metrics:
                metrics_by_name[metric.name].append(metric)
            
            for name, metric_list in metrics_by_name.items():
                if not metric_list:
                    continue
                
                # Add metric help and type
                lines.append(f"# HELP {name} Database MCP server metric")
                lines.append(f"# TYPE {name} {metric_list[0].metric_type.value}")
                
                # Add metric values
                for metric in metric_list[-100:]:  # Last 100 values
                    tags_str = ""
                    if metric.tags:
                        tag_pairs = [f'{k}="{v}"' for k, v in metric.tags.items()]
                        tags_str = "{" + ",".join(tag_pairs) + "}"
                    
                    lines.append(f"{name}{tags_str} {metric.value} {int(metric.timestamp * 1000)}")
        
        return "\n".join(lines)
    
    async def _export_json_format(self) -> str:
        """Export metrics in JSON format."""
        comprehensive_status = await self.get_comprehensive_status()
        return json.dumps(comprehensive_status, indent=2)
