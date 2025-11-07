"""
Database MCP Server

A production-grade Model Context Protocol (MCP) server for MySQL database interactions.
Supports both stdio and SSE transport modes with comprehensive security and monitoring.
"""

__version__ = "1.0.0"
__author__ = "Database MCP Team"

# Import main components for easier access
from database.config import (
    AppConfig,
    Config,
    DatabaseConfig,
    MCPConfig,
    SecurityConfig,
    ServerConfig,
)
from database.src.database_manager import DatabaseManager
from database.src.error_handling import (
    DatabaseConnectionError,
    DatabaseMCPError,
    ErrorHandler,
    SecurityViolationError,
    ValidationError,
)
from database.src.monitoring import (
    ErrorTracker,
    HealthChecker,
    PerformanceTracker,
    ProductionMonitor,
    SystemResourceMonitor,
)
from database.src.schema_manager import (
    ColumnInfo,
    ConstraintInfo,
    DatabaseInfo,
    IndexInfo,
    SchemaAnalyzer,
    SchemaComparator,
    SchemaManager,
    SchemaSnapshot,
    TableInfo,
)
from database.src.security import (
    ConnectionSecurityManager,
    DatabaseSecurityManager,
    QuerySecurityAnalyzer,
)
from database.src.server import DatabaseMCPServer
from database.src.transport import create_transport_manager, run_transport

__all__ = [
    "Config",
    "AppConfig",
    "DatabaseConfig",
    "ServerConfig",
    "MCPConfig",
    "SecurityConfig",
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
