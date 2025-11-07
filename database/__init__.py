"""
Database MCP Server

A production-grade Model Context Protocol (MCP) server for MySQL database interactions.
Supports both stdio and SSE transport modes with comprehensive security and monitoring.
"""

__version__ = "1.0.0"
__author__ = "Database MCP Team"

# Import main components for easier access
from database.config import Config, AppConfig, DatabaseConfig, ServerConfig, MCPConfig, SecurityConfig
from database.src.server import DatabaseMCPServer
from database.src.database_manager import DatabaseManager
from database.src.transport import run_transport, create_transport_manager
from database.src.security import DatabaseSecurityManager, QuerySecurityAnalyzer, ConnectionSecurityManager
from database.src.monitoring import ProductionMonitor, PerformanceTracker, SystemResourceMonitor, ErrorTracker, HealthChecker
from database.src.error_handling import ErrorHandler, DatabaseMCPError, DatabaseConnectionError, SecurityViolationError, ValidationError
from database.src.schema_manager import SchemaManager, SchemaAnalyzer, SchemaComparator, DatabaseInfo, TableInfo, ColumnInfo, IndexInfo, ConstraintInfo, SchemaSnapshot

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
