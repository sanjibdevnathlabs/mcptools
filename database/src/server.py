import asyncio
import logging
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional
from mcp.server import FastMCP, Server
from mcp.server.fastmcp.prompts import base
from database.config import Config
from .database_manager import DatabaseManager
from .security import DatabaseSecurityManager
from .monitoring import ProductionMonitor, MetricType
from .error_handling import ErrorHandler, DatabaseMCPError, DatabaseConnectionError, SecurityViolationError, ValidationError
from .schema_manager import SchemaManager
from .logging_config import get_logger

# Temporary fallback logger for tool functions that don't have access to self.logger
logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple rate limiter for query execution."""
    
    def __init__(self, max_queries: int, window_minutes: int = 1):
        """Initialize rate limiter."""
        self.max_queries = max_queries
        self.window_seconds = window_minutes * 60
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_id: str = "default") -> bool:
        """Check if request is allowed for the client."""
        now = time.time()
        client_requests = self.requests[client_id]
        
        # Remove old requests outside the window
        cutoff = now - self.window_seconds
        self.requests[client_id] = [req_time for req_time in client_requests if req_time > cutoff]
        
        # Check if under limit
        if len(self.requests[client_id]) < self.max_queries:
            self.requests[client_id].append(now)
            return True
        
        return False
    
    def get_reset_time(self, client_id: str = "default") -> float:
        """Get time until rate limit resets for client."""
        if not self.requests[client_id]:
            return 0.0
        
        oldest_request = min(self.requests[client_id])
        return max(0.0, (oldest_request + self.window_seconds) - time.time())



class DatabaseMCPServer:
    """Main MCP server for database operations."""
    
    def __init__(self):
        """Initialize the database MCP server."""
        self.config = Config()
        self.logger = get_logger('server')
        self.database_manager = DatabaseManager()
        self.security_manager = DatabaseSecurityManager()
        self.production_monitor = ProductionMonitor(self.database_manager, self.security_manager)
        self.error_handler = ErrorHandler()
        self.schema_manager = SchemaManager(self.database_manager)
        self.rate_limiter = RateLimiter(
            self.config.mcp.max_queries_per_minute
        ) if self.config.mcp.enable_rate_limiting else None
        
        # Create FastMCP instance
        self.mcp = FastMCP(self.config.mcp.server_name)
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up MCP handlers for prompts, commands, and events."""
        
        # Tools are registered based on MCP_TOOL_MODE in the initialization section
        @self.mcp.prompt()
        def get_initial_prompts() -> List[base.Message]:
            """Provide initial prompts for the MCP server."""
            readonly_notice = " (READ-ONLY MODE)" if self.config.mcp.readonly_mode else ""
            allowed_queries = self.config.mcp.allowed_query_types
            
            return [
                base.UserMessage(f"""
You are a helpful database assistant that can execute MySQL queries{readonly_notice}.

Available capabilities:
- Execute SQL queries: {allowed_queries}
- Schema introspection: View database structure, tables, and columns
- Query analysis: Get execution plans with EXPLAIN
- Connection monitoring: Check database health and performance
- Security monitoring: Get security status and audit information

Enhanced Security Features:
🛡️  Advanced SQL injection detection with pattern analysis
🔍 Query structure parsing and threat identification  
📊 Connection-level rate limiting and anomaly detection
🚨 Security audit logging with threat classification
⚖️  Risk assessment for all queries (low/medium/high/critical)
🔒 Client blocking for suspicious behavior patterns
📈 Comprehensive security reporting and recommendations

Enterprise Error Handling & Recovery:
🔄 Automatic retry logic with exponential backoff and jitter
⚡ Circuit breaker pattern for cascading failure prevention
🎯 Graceful degradation with intelligent fallback mechanisms
💾 Response caching for offline/degraded service scenarios
🔧 Service health tracking with automatic recovery detection
📊 Comprehensive error classification and context preservation
🚀 Fault tolerance with multiple recovery strategies

Query Limits & Controls:
- Rate limiting: {self.config.mcp.max_queries_per_minute} queries/minute
- Row limit: Maximum {self.config.database.max_rows_limit} rows per query
- Query timeout: {self.config.database.query_timeout} seconds
- Max query length: {self.config.database.max_query_length} characters

Available Commands:
- execute_query: Run SQL queries with comprehensive security validation
- explain_query: Analyze query performance
- health_check: Check database connectivity and health
- connection_stats: Get connection pool statistics
- security_status: Get detailed security report and recommendations

Database Schema Management Commands:
- get_databases: Get comprehensive list of all databases with metadata
- get_tables: Get detailed table information with optional database filtering and view inclusion
- get_table_details: Get complete table structure including columns, indexes, constraints, and relationships
- create_schema_snapshot: Create timestamped schema snapshots with hash for change detection
- export_schema: Export complete schema in JSON or SQL DDL format with full metadata preservation
- analyze_schema: Analyze schema for performance issues, design problems, and optimization recommendations
- schema_info: Legacy compatibility for basic database schema information
- table_info: Legacy compatibility for basic table information

Production Monitoring Commands:
- monitoring_status: Get comprehensive production monitoring overview
- performance_metrics: Get detailed performance metrics and query statistics  
- system_metrics: Get system resource usage (CPU, memory, disk, network)
- error_summary: Get error tracking and analysis data
- export_metrics: Export metrics in JSON or Prometheus format

Error Handling & Recovery Commands:
- error_handling_status: Get comprehensive error handling system status
- circuit_breaker_status: Get circuit breaker status for services (with optional service filter)
- service_degradation_status: Get service degradation and fallback status

Security Best Practices:
✅ Always use parameterized queries to prevent SQL injection
✅ Monitor security_status regularly for threats and recommendations
✅ Review audit logs for suspicious patterns
✅ Use explain_query to optimize performance and reduce resource usage

Remember: This server has enterprise-grade security monitoring. All queries are analyzed for threats and logged for audit purposes. Be responsible with database access!
""")
            ]
        
        # Register tools
        try:
            self.logger.info("TOOL_REGISTER_START", {"tool_name": "execute_query"})
            @self.mcp.tool()
            async def execute_query(sql: str) -> Dict[str, Any]:
                """Execute a SQL query and return results"""
                try:
                    # SECURITY: Validate query before execution
                    security_result = self.security_manager.validate_query_security(sql)
                    
                    if not security_result.get("safe", False):
                        self.logger.warning("QUERY_SECURITY_BLOCKED", {
                            "sql": sql[:100] + ('...' if len(sql) > 100 else ''),
                            "threats": security_result.get("threats_detected", []),
                            "risk_level": security_result.get("risk_level", "unknown")
                        })
                        return {
                            "success": False,
                            "error": "Query blocked by security validation",
                            "sql": sql,
                            "error_code": "SECURITY_VIOLATION",
                            "threats": security_result.get("threats_detected", []),
                            "risk_level": security_result.get("risk_level", "unknown")
                        }
                    
                    # Execute query after security validation passed
                    result = await self.database_manager.execute_query(sql)
                    
                    return {
                        "success": True,
                        "sql": sql,
                        "data": result,
                        "row_count": len(result) if isinstance(result, list) else 1
                    }
                    
                except Exception as e:
                    self.logger.error("QUERY_EXECUTION_ERROR", {
                        "sql": sql[:100] + ('...' if len(sql) > 100 else ''),
                        "error": str(e),
                        "error_type": type(e).__name__
                    }, exc_info=True)
                    return {
                        "success": False,
                        "error": str(e),
                        "sql": sql,
                        "error_code": "QUERY_EXECUTION_ERROR"
                    }
        except Exception as e:
            self.logger.error("TOOL_REGISTER_FAILED", {
                "tool_name": "execute_query",
                "error": str(e),
                "error_type": type(e).__name__
            }, exc_info=True)
            raise
        
        # Register tools based on mode
        if self.config.mcp.tool_mode == "lite":
            self.logger.info("TOOLS_REGISTER_LITE", {"mode": "lite", "tool_count": 8})
            self._register_core_tools()
            self.logger.info("TOOLS_REGISTER_SUCCESS", {"mode": "lite", "tool_count": 8})
        elif self.config.mcp.tool_mode == "full":
            self.logger.info("TOOLS_REGISTER_FULL", {"mode": "full", "tool_count": 22})
            self._register_core_tools()
            self._register_enterprise_tools()
            self.logger.info("TOOLS_REGISTER_SUCCESS", {"mode": "full", "tool_count": 22})
        
    async def startup(self):
        """Initialize database connection pool on startup."""
        self.logger.info("SERVER_STARTUP_BEGIN", {
            "server_name": self.config.mcp.server_name,
            "tool_mode": self.config.mcp.tool_mode,
            "transport_mode": self.config.server.transport_mode
        })
        try:
            await self.database_manager.initialize_pool()
            self.logger.info("SERVER_STARTUP_SUCCESS", {
                "server_name": self.config.mcp.server_name
            })
        except Exception as e:
            self.logger.error("SERVER_STARTUP_FAILED", {
                "error": str(e),
                "error_type": type(e).__name__,
                "server_name": self.config.mcp.server_name
            }, exc_info=True)
            raise
    
    async def shutdown(self):
        """Clean up database connections on shutdown."""
        self.logger.info("SERVER_SHUTDOWN_BEGIN", {
            "server_name": self.config.mcp.server_name
        })
        try:
            await self.database_manager.close_pool()
            self.logger.info("SERVER_SHUTDOWN_SUCCESS", {
                "server_name": self.config.mcp.server_name
            })
        except Exception as e:
            self.logger.error("SERVER_SHUTDOWN_ERROR", {
                "error": str(e),
                "error_type": type(e).__name__,
                "server_name": self.config.mcp.server_name
            }, exc_info=True)
    
    def _register_core_tools(self):
        """Register core MCP tools (lite mode - 8 essential tools)."""
        
        @self.mcp.tool()
        async def execute_query(sql: str) -> Dict[str, Any]:
            """
            Execute a SQL query on the database.
            
            Args:
                sql: The SQL query to execute
            
            Returns:
                Query results or error information
            """
            if not self.config.mcp.enable_query_execution:
                return {
                    "success": False,
                    "error": "Query execution is disabled",
                    "error_code": "FEATURE_DISABLED"
                }
            
            try:
                result = await self.database_manager.execute_query(sql)
                return {
                    "success": True,
                    "sql": sql,
                    "data": result,
                    "row_count": len(result) if isinstance(result, list) else 1
                }
            except Exception as e:
                logger.error(f"Error executing query '{sql}': {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "sql": sql,
                    "error_code": "QUERY_EXECUTION_ERROR"
                }
        
        @self.mcp.tool()
        async def get_databases() -> Dict[str, Any]:
            """
            Get list of all databases with comprehensive information.
            
            Returns:
                List of databases with metadata
            """
            if not self.config.mcp.enable_schema_introspection:
                return {
                    "success": False,
                    "error": "Schema introspection is disabled",
                    "error_code": "FEATURE_DISABLED"
                }
            
            try:
                databases = await self.schema_manager.get_databases()
                return {
                    "success": True,
                    "data": {
                        "databases": [
                            {
                                "name": db.name,
                                "character_set": db.character_set,
                                "collation": db.collation,
                                "table_count": db.table_count
                            } for db in databases
                        ],
                        "total_databases": len(databases)
                    }
                }
            except Exception as e:
                error_response = self.error_handler.format_error_response(e)
                return error_response
        
        @self.mcp.tool()
        async def get_tables(
            database_name: Optional[str] = None,
            include_views: bool = False
        ) -> Dict[str, Any]:
            """
            Get comprehensive table information.
            
            Args:
                database_name: Optional specific database name
                include_views: Whether to include views in results
            
            Returns:
                Table information with metadata
            """
            if not self.config.mcp.enable_schema_introspection:
                return {
                    "success": False,
                    "error": "Schema introspection is disabled",
                    "error_code": "FEATURE_DISABLED"
                }
            
            try:
                tables = await self.schema_manager.get_tables(database_name, include_views)
                return {
                    "success": True,
                    "data": {
                        "tables": [
                            {
                                "name": table.name,
                                "database_name": table.database_name,
                                "table_type": table.table_type,
                                "engine": table.engine,
                                "table_rows": table.table_rows,
                                "data_length": table.data_length,
                                "index_length": table.index_length,
                                "table_comment": table.table_comment,
                                "create_time": table.create_time.isoformat() if table.create_time else None,
                                "update_time": table.update_time.isoformat() if table.update_time else None
                            } for table in tables
                        ],
                        "total_tables": len(tables),
                        "database_filter": database_name,
                        "include_views": include_views
                    }
                }
            except Exception as e:
                error_response = self.error_handler.format_error_response(e)
                return error_response
        
        @self.mcp.tool()
        async def get_table_details(
            table_name: str,
            database_name: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Get detailed information about a specific table including columns, indexes, and constraints.
            
            Args:
                table_name: Name of the table
                database_name: Optional database name (uses default if not specified)
            
            Returns:
                Detailed table information
            """
            if not self.config.mcp.enable_schema_introspection:
                return {
                    "success": False,
                    "error": "Schema introspection is disabled",
                    "error_code": "FEATURE_DISABLED"
                }
            
            try:
                table_details = await self.schema_manager.get_table_details(table_name, database_name)
                return {
                    "success": True,
                    "data": {
                        "table_name": table_details.table_name,
                        "database_name": table_details.database_name,
                        "columns": [
                            {
                                "name": col.name,
                                "data_type": col.data_type,
                                "is_nullable": col.is_nullable,
                                "default_value": col.default_value,
                                "column_comment": col.column_comment,
                                "ordinal_position": col.ordinal_position,
                                "character_maximum_length": col.character_maximum_length,
                                "numeric_precision": col.numeric_precision,
                                "numeric_scale": col.numeric_scale
                            } for col in table_details.columns
                        ],
                        "indexes": [
                            {
                                "name": idx.name,
                                "columns": idx.columns,
                                "is_unique": idx.is_unique,
                                "is_primary": idx.is_primary,
                                "index_type": idx.index_type,
                                "index_comment": idx.index_comment
                            } for idx in table_details.indexes
                        ],
                        "constraints": [
                            {
                                "name": constraint.name,
                                "type": constraint.constraint_type,
                                "columns": constraint.columns,
                                "referenced_table": constraint.referenced_table,
                                "referenced_columns": constraint.referenced_columns
                            } for constraint in table_details.constraints
                        ]
                    }
                }
            except Exception as e:
                error_response = self.error_handler.format_error_response(e)
                return error_response
        
        @self.mcp.tool()
        async def explain_query(
            sql: str,
            format_type: str = "TRADITIONAL"
        ) -> Dict[str, Any]:
            """
            Get query execution plan using EXPLAIN.
            
            Args:
                sql: The SQL query to explain
                format_type: EXPLAIN format (TRADITIONAL, JSON, TREE)
            
            Returns:
                Query execution plan information
            """
            if not self.config.mcp.enable_query_explain:
                return {
                    "success": False,
                    "error": "Query EXPLAIN is disabled",
                    "error_code": "FEATURE_DISABLED"
                }
            
            try:
                result = await self.database_manager.explain_query(sql, format_type)
                return {
                    "success": True,
                    "data": result,
                    "query": sql,
                    "format": format_type
                }
            except Exception as e:
                error_response = self.error_handler.format_error_response(e)
                return error_response
        
        @self.mcp.tool()
        async def health_check() -> Dict[str, Any]:
            """
            Perform comprehensive health check of the database connection and server.
            
            Returns:
                Health status information
            """
            try:
                health_status = await self.production_monitor.get_health_status()
                return {
                    "success": True,
                    "data": {
                        "overall_status": health_status.overall_status,
                        "database_connection": health_status.database_connection,
                        "response_time_ms": health_status.response_time_ms,
                        "timestamp": health_status.timestamp.isoformat(),
                        "details": health_status.details
                    }
                }
            except Exception as e:
                logger.error(f"Error during health check: {e}")
                return {
                    "success": False,
                    "error": f"Health check failed: {str(e)}",
                    "error_code": "HEALTH_CHECK_ERROR"
                }
        
        @self.mcp.tool()
        async def connection_stats() -> Dict[str, Any]:
            """
            Get database connection pool statistics.
            
            Returns:
                Connection pool statistics
            """
            try:
                stats = await self.database_manager.get_connection_stats()
                return {
                    "success": True,
                    "data": stats
                }
            except Exception as e:
                logger.error(f"Error getting connection stats: {e}")
                return {
                    "success": False,
                    "error": f"Failed to get connection stats: {str(e)}",
                    "error_code": "CONNECTION_STATS_ERROR"
                }
        
        @self.mcp.tool()
        async def schema_info(database_name: Optional[str] = None) -> Dict[str, Any]:
            """
            Get comprehensive database schema information.
            
            Args:
                database_name: Optional specific database name
            
            Returns:
                Schema information including databases, tables, and basic statistics
            """
            if not self.config.mcp.enable_schema_introspection:
                return {
                    "success": False,
                    "error": "Schema introspection is disabled",
                    "error_code": "FEATURE_DISABLED"
                }
            
            try:
                schema_info = await self.schema_manager.get_schema_info(database_name)
                return {
                    "success": True,
                    "data": schema_info
                }
            except Exception as e:
                error_response = self.error_handler.format_error_response(e)
                return error_response
    
    def _register_enterprise_tools(self):
        """Register enterprise MCP tools (full mode only - 14 additional tools)."""
        
        @self.mcp.tool()
        async def create_schema_snapshot(database_names: Optional[List[str]] = None) -> Dict[str, Any]:
            """Create comprehensive schema snapshot."""
            if not self.config.mcp.enable_schema_introspection:
                return {
                    "success": False,
                    "error": "Schema introspection is disabled",
                    "error_code": "FEATURE_DISABLED"
                }
            
            try:
                snapshot = await self.schema_manager.create_schema_snapshot(database_names)
                return {
                    "success": True,
                    "data": {
                        "snapshot_id": snapshot.id,
                        "timestamp": snapshot.timestamp.isoformat(),
                        "databases": [
                            {
                                "name": db.name,
                                "table_count": len(db.tables),
                                "tables": [
                                    {
                                        "name": table.name,
                                        "column_count": len(table.columns),
                                        "index_count": len(table.indexes)
                                    } for table in db.tables
                                ]
                            } for db in snapshot.databases
                        ],
                        "total_databases": len(snapshot.databases),
                        "generation_time_ms": snapshot.generation_time_ms
                    }
                }
            except Exception as e:
                error_response = self.error_handler.format_error_response(e)
                return error_response
        
        @self.mcp.tool()
        async def export_schema(
            database_names: Optional[List[str]] = None,
            format_type: str = "json"
        ) -> Dict[str, Any]:
            """Export database schema in various formats."""
            if not self.config.mcp.enable_schema_introspection:
                return {
                    "success": False,
                    "error": "Schema introspection is disabled",
                    "error_code": "FEATURE_DISABLED"
                }
            
            try:
                if format_type.lower() not in ['json', 'sql']:
                    return {
                        "success": False,
                        "error": f"Unsupported format: {format_type}. Use 'json' or 'sql'",
                        "error_code": "INVALID_FORMAT"
                    }
                
                snapshot = await self.schema_manager.create_schema_snapshot(database_names)
                exported_data = self.schema_manager.export_schema_snapshot(snapshot, format_type)
                
                return {
                    "success": True,
                    "data": {
                        "format": format_type,
                        "exported_at": snapshot.timestamp.isoformat(),
                        "schema_hash": snapshot.schema_hash,
                        "content": exported_data,
                        "size_bytes": len(exported_data.encode('utf-8')),
                        "database_count": len(snapshot.databases),
                        "table_count": len(snapshot.tables)
                    }
                }
            except Exception as e:
                error_response = self.error_handler.format_error_response(e)
                return error_response
        
        @self.mcp.tool()
        async def analyze_schema(database_names: Optional[List[str]] = None) -> Dict[str, Any]:
            """Analyze database schema for issues and recommendations."""
            if not self.config.mcp.enable_schema_introspection:
                return {
                    "success": False,
                    "error": "Schema introspection is disabled",
                    "error_code": "FEATURE_DISABLED"
                }
            
            try:
                analysis = await self.schema_manager.analyze_schema(database_names)
                return {
                    "success": True,
                    "data": analysis
                }
            except Exception as e:
                error_response = self.error_handler.format_error_response(e)
                return error_response
        
        @self.mcp.tool()
        async def table_info(
            table_name: str, 
            database_name: Optional[str] = None
        ) -> Dict[str, Any]:
            """Get detailed table information (legacy compatibility)."""
            # Redirect to core get_table_details for compatibility
            return await get_table_details(table_name, database_name)
        
        @self.mcp.tool()
        async def security_status() -> Dict[str, Any]:
            """Get comprehensive security status and statistics."""
            return {
                "success": True,
                "data": self.security_manager.get_comprehensive_security_report()
            }
        
        @self.mcp.tool()
        async def monitoring_status() -> Dict[str, Any]:
            """Get comprehensive production monitoring status."""
            try:
                status = await self.production_monitor.get_comprehensive_status()
                return {
                    "success": True,
                    "data": status
                }
            except Exception as e:
                logger.error(f"Error getting monitoring status: {e}")
                return {
                    "success": False,
                    "error": f"Failed to get monitoring status: {str(e)}",
                    "error_code": "MONITORING_ERROR"
                }
        
        @self.mcp.tool()
        async def performance_metrics() -> Dict[str, Any]:
            """Get detailed performance metrics and statistics."""
            try:
                metrics = self.production_monitor.performance_tracker.get_performance_metrics()
                return {
                    "success": True,
                    "data": metrics
                }
            except Exception as e:
                logger.error(f"Error getting performance metrics: {e}")
                return {
                    "success": False,
                    "error": f"Failed to get performance metrics: {str(e)}",
                    "error_code": "METRICS_ERROR"
                }
        
        @self.mcp.tool()
        async def system_metrics() -> Dict[str, Any]:
            """Get system resource metrics."""
            try:
                metrics = self.production_monitor.system_monitor.get_system_metrics()
                return {
                    "success": True,
                    "data": metrics
                }
            except Exception as e:
                logger.error(f"Error getting system metrics: {e}")
                return {
                    "success": False,
                    "error": f"Failed to get system metrics: {str(e)}",
                    "error_code": "SYSTEM_METRICS_ERROR"
                }
        
        @self.mcp.tool()
        async def error_summary() -> Dict[str, Any]:
            """Get error tracking summary and statistics."""
            try:
                summary = self.production_monitor.error_tracker.get_error_summary()
                return {
                    "success": True,
                    "data": summary
                }
            except Exception as e:
                logger.error(f"Error getting error summary: {e}")
                return {
                    "success": False,
                    "error": f"Failed to get error summary: {str(e)}",
                    "error_code": "ERROR_SUMMARY_ERROR"
                }
        
        @self.mcp.tool()
        async def export_metrics(format_type: str = "json") -> Dict[str, Any]:
            """Export metrics in various formats for external monitoring systems."""
            try:
                if format_type.lower() not in ['json', 'prometheus']:
                    return {
                        "success": False,
                        "error": f"Unsupported format: {format_type}. Use 'json' or 'prometheus'",
                        "error_code": "INVALID_FORMAT"
                    }
                
                exported_data = await self.production_monitor.get_metrics_export(format_type)
                return {
                    "success": True,
                    "data": {
                        "format": format_type,
                        "exported_at": time.time(),
                        "content": exported_data
                    }
                }
            except Exception as e:
                logger.error(f"Error exporting metrics: {e}")
                return {
                    "success": False,
                    "error": f"Failed to export metrics: {str(e)}",
                    "error_code": "EXPORT_ERROR"
                }
        
        @self.mcp.tool()
        async def error_handling_status() -> Dict[str, Any]:
            """Get comprehensive error handling system status."""
            try:
                status = self.error_handler.get_system_health()
                return {
                    "success": True,
                    "data": status
                }
            except Exception as e:
                logger.error(f"Error getting error handling status: {e}")
                return {
                    "success": False,
                    "error": f"Failed to get error handling status: {str(e)}",
                    "error_code": "ERROR_HANDLING_STATUS_ERROR"
                }
        
        @self.mcp.tool()
        async def circuit_breaker_status(service_name: Optional[str] = None) -> Dict[str, Any]:
            """Get circuit breaker status for specific service or all services."""
            try:
                if service_name:
                    if service_name in self.error_handler.circuit_breakers:
                        breaker_info = self.error_handler.circuit_breakers[service_name].get_state()
                        return {
                            "success": True,
                            "data": breaker_info
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Circuit breaker for service '{service_name}' not found",
                            "error_code": "CIRCUIT_BREAKER_NOT_FOUND"
                        }
                else:
                    all_breakers = {
                        name: breaker.get_state()
                        for name, breaker in self.error_handler.circuit_breakers.items()
                    }
                    return {
                        "success": True,
                        "data": all_breakers
                    }
            except Exception as e:
                logger.error(f"Error getting circuit breaker status: {e}")
                return {
                    "success": False,
                    "error": f"Failed to get circuit breaker status: {str(e)}",
                    "error_code": "CIRCUIT_BREAKER_STATUS_ERROR"
                }
        
        @self.mcp.tool()
        async def service_degradation_status() -> Dict[str, Any]:
            """Get service degradation and fallback status."""
            try:
                degradation_info = {
                    "service_states": {
                        service: state.value
                        for service, state in self.error_handler.degradation_manager.service_states.items()
                    },
                    "degradation_times": {
                        service: time.time() - start_time
                        for service, start_time in self.error_handler.degradation_manager.degradation_start_times.items()
                    },
                    "cached_responses": len(self.error_handler.degradation_manager.cached_responses),
                    "fallback_configuration": {
                        "readonly_fallback_enabled": self.error_handler.degradation_manager.config.enable_readonly_fallback,
                        "cached_responses_enabled": self.error_handler.degradation_manager.config.enable_cached_responses,
                        "max_degraded_duration": self.error_handler.degradation_manager.config.max_degraded_duration
                    }
                }
                
                return {
                    "success": True,
                    "data": degradation_info
                }
            except Exception as e:
                logger.error(f"Error getting service degradation status: {e}")
                return {
                    "success": False,
                    "error": f"Failed to get service degradation status: {str(e)}",
                    "error_code": "DEGRADATION_STATUS_ERROR"
                }
    
    def get_server(self) -> Server:
        """Get the underlying MCP server instance."""
        return self.mcp._mcp_server  # noqa: SLF001
    
    def get_fastmcp(self):
        """Get the FastMCP instance."""
        return self.mcp
