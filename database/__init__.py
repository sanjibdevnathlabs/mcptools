"""
Database MCP Server

A production-grade Model Context Protocol (MCP) server for MySQL database interactions.
Supports both stdio and SSE transport modes with comprehensive security and monitoring.
"""

__version__ = "1.0.0"
__author__ = "Database MCP Team"

# Import main components for easier access
from .config import get_config, AppConfig
from .server import DatabaseMCPServer
from .database_manager import DatabaseManager
from .transport import run_transport, create_transport_manager
from .security import DatabaseSecurityManager, QuerySecurityAnalyzer, ConnectionSecurityManager
from .monitoring import ProductionMonitor, PerformanceTracker, SystemResourceMonitor, ErrorTracker, HealthChecker
from .error_handling import ErrorHandler, DatabaseMCPError, DatabaseConnectionError, SecurityViolationError, ValidationError
from .schema_manager import SchemaManager, SchemaAnalyzer, SchemaComparator, DatabaseInfo, TableInfo, ColumnInfo, IndexInfo, ConstraintInfo, SchemaSnapshot

__all__ = [
    "get_config", 
    "AppConfig",
    "DatabaseMCPServer",
    "DatabaseManager",
    "run_transport",
    "create_transport_manager",
    "DatabaseSecurityManager",
    "QuerySecurityAnalyzer", 
    "ConnectionSecurityManager",
    "ProductionMonitor",
    "PerformanceTracker",
    "SystemResourceMonitor",
    "ErrorTracker", 
    "HealthChecker",
    "ErrorHandler",
    "DatabaseMCPError",
    "DatabaseConnectionError",
    "SecurityViolationError",
    "ValidationError",
    "SchemaManager",
    "SchemaAnalyzer",
    "SchemaComparator",
    "DatabaseInfo",
    "TableInfo",
    "ColumnInfo", 
    "IndexInfo",
    "ConstraintInfo",
    "SchemaSnapshot",
]
