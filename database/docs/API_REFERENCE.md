# API Reference

Complete reference for all Database MCP Server tools, including parameters, response formats, and usage examples.

## Tool Mode Configuration

The Database MCP Server supports two tool modes to optimize the user experience:

| Mode | Tools | Use Case | Configuration |
|------|-------|----------|---------------|
| **lite** | 8 core tools | AI clients (Cursor/Copilot) | `MCP_TOOL_MODE=lite` |
| **full** | 22 tools | Enterprise/power users | `MCP_TOOL_MODE=full` |

**Recommendation:** Use `lite` mode for AI assistants to avoid overwhelming them with too many tools.

## Lite Mode Tools (8 Core Tools)

These 8 essential tools are available in both lite and full modes:

1. [`execute_query`](#execute_query) - Execute SQL queries
2. [`get_databases`](#get_databases) - Database discovery
3. [`get_tables`](#get_tables) - Table listing
4. [`get_table_details`](#get_table_details) - Table structure
5. [`explain_query`](#explain_query) - Query optimization
6. [`health_check`](#health_check) - Connection status
7. [`connection_stats`](#connection_stats) - Pool statistics
8. [`schema_info`](#schema_info) - Schema overview

## Full Mode Additional Tools (14 Enterprise Tools)

These additional tools are only available in full mode:

9. [`create_schema_snapshot`](#create_schema_snapshot) - Schema snapshots
10. [`export_schema`](#export_schema) - Schema export
11. [`analyze_schema`](#analyze_schema) - Schema analysis
12. [`table_info`](#table_info) - Legacy table info
13. [`security_status`](#security_status) - Security monitoring
14. [`monitoring_status`](#monitoring_status) - Production monitoring
15. [`performance_metrics`](#performance_metrics) - Performance data
16. [`system_metrics`](#system_metrics) - System resources
17. [`error_summary`](#error_summary) - Error tracking
18. [`export_metrics`](#export_metrics) - Metrics export
19. [`error_handling_status`](#error_handling_status) - Error system status
20. [`circuit_breaker_status`](#circuit_breaker_status) - Circuit breaker info
21. [`service_degradation_status`](#service_degradation_status) - Service status

## Common Response Format

All tools return responses in this standard format:

```json
{
  "success": true,
  "data": { ... },
  "error": "Error message (only if success: false)",
  "error_code": "ERROR_CODE (only if success: false)"
}
```

## Core Tools (Lite Mode)

### `execute_query`

Execute SQL queries with security validation and error handling.

**Parameters:**
- `sql` (string, required): SQL query to execute

**Example Usage:**
```json
{
  "name": "execute_query",
  "arguments": {
    "sql": "SELECT * FROM users WHERE active = 1 LIMIT 10"
  }
}
```

**Response:**
```json
{
  "success": true,
  "sql": "SELECT * FROM users WHERE active = 1 LIMIT 10",
  "data": [
    {"id": 1, "name": "John Doe", "email": "john@example.com", "active": 1},
    {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "active": 1}
  ],
  "row_count": 2
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Table 'nonexistent' doesn't exist",
  "sql": "SELECT * FROM nonexistent",
  "error_code": "QUERY_EXECUTION_ERROR"
}
```

### `get_databases`

Retrieve a list of all available databases with metadata.

**Parameters:** None

**Example Usage:**
```json
{
  "name": "get_databases",
  "arguments": {}
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "databases": [
      {
        "name": "app_production",
        "character_set": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "table_count": 15
      },
      {
        "name": "app_analytics",
        "character_set": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "table_count": 8
      }
    ],
    "total_databases": 2
  }
}
```

### `get_tables`

Get comprehensive table information for a database.

**Parameters:**
- `database_name` (string, optional): Specific database name
- `include_views` (boolean, optional): Include views in results (default: false)

**Example Usage:**
```json
{
  "name": "get_tables",
  "arguments": {
    "database_name": "app_production",
    "include_views": false
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "tables": [
      {
        "name": "users",
        "database_name": "app_production",
        "table_type": "BASE TABLE",
        "engine": "InnoDB",
        "table_rows": 1250,
        "data_length": 245760,
        "index_length": 98304,
        "table_comment": "User accounts",
        "create_time": "2024-01-15T10:30:00",
        "update_time": "2024-08-16T14:22:30"
      }
    ],
    "total_tables": 1,
    "database_filter": "app_production",
    "include_views": false
  }
}
```

### `get_table_details`

Get detailed information about a specific table including columns, indexes, and constraints.

**Parameters:**
- `table_name` (string, required): Name of the table
- `database_name` (string, optional): Database name (uses default if not specified)

**Example Usage:**
```json
{
  "name": "get_table_details",
  "arguments": {
    "table_name": "users",
    "database_name": "app_production"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "table_name": "users",
    "database_name": "app_production",
    "columns": [
      {
        "name": "id",
        "data_type": "int",
        "is_nullable": false,
        "default_value": null,
        "column_comment": "Primary key",
        "ordinal_position": 1,
        "character_maximum_length": null,
        "numeric_precision": 10,
        "numeric_scale": 0
      },
      {
        "name": "email",
        "data_type": "varchar",
        "is_nullable": false,
        "default_value": null,
        "column_comment": "User email address",
        "ordinal_position": 2,
        "character_maximum_length": 255,
        "numeric_precision": null,
        "numeric_scale": null
      }
    ],
    "indexes": [
      {
        "name": "PRIMARY",
        "columns": ["id"],
        "is_unique": true,
        "is_primary": true,
        "index_type": "BTREE",
        "index_comment": ""
      },
      {
        "name": "idx_email",
        "columns": ["email"],
        "is_unique": true,
        "is_primary": false,
        "index_type": "BTREE",
        "index_comment": "Unique email constraint"
      }
    ],
    "constraints": [
      {
        "name": "users_ibfk_1",
        "type": "FOREIGN KEY",
        "columns": ["department_id"],
        "referenced_table": "departments",
        "referenced_columns": ["id"]
      }
    ]
  }
}
```

### `explain_query`

Get query execution plan using EXPLAIN for optimization analysis.

**Parameters:**
- `sql` (string, required): SQL query to analyze
- `format_type` (string, optional): EXPLAIN format - "TRADITIONAL", "JSON", or "TREE" (default: "TRADITIONAL")

**Example Usage:**
```json
{
  "name": "explain_query",
  "arguments": {
    "sql": "SELECT u.name, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id",
    "format_type": "JSON"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "query_block": {
        "select_id": 1,
        "cost_info": {
          "query_cost": "450.25"
        },
        "grouping_operation": {
          "using_temporary_table": true,
          "using_filesort": false,
          "nested_loop": [
            {
              "table": {
                "table_name": "u",
                "access_type": "ALL",
                "rows_examined_per_scan": 1250,
                "rows_produced_per_join": 1250,
                "filtered": "100.00",
                "cost_info": {
                  "read_cost": "25.50",
                  "eval_cost": "125.00",
                  "prefix_cost": "150.50",
                  "data_read_per_join": "240K"
                }
              }
            }
          ]
        }
      }
    }
  ],
  "query": "SELECT u.name, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id",
  "format": "JSON"
}
```

### `health_check`

Perform comprehensive health check of the database connection and server.

**Parameters:** None

**Example Usage:**
```json
{
  "name": "health_check",
  "arguments": {}
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "overall_status": "healthy",
    "database_connection": "ok",
    "response_time_ms": 23,
    "timestamp": "2024-08-16T20:30:45Z",
    "details": {
      "pool_active": 3,
      "pool_size": 10,
      "pool_available": 7,
      "uptime_seconds": 7200,
      "version": "1.0.0"
    }
  }
}
```

### `connection_stats`

Get database connection pool statistics and performance metrics.

**Parameters:** None

**Example Usage:**
```json
{
  "name": "connection_stats",
  "arguments": {}
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "pool_size": 10,
    "active_connections": 3,
    "idle_connections": 7,
    "total_connections_created": 15,
    "connections_closed": 5,
    "connection_errors": 0,
    "average_connection_age_seconds": 1800,
    "peak_connections": 8,
    "pool_efficiency": 0.8
  }
}
```

### `schema_info`

Get comprehensive database schema information including databases, tables, and statistics.

**Parameters:**
- `database_name` (string, optional): Specific database name

**Example Usage:**
```json
{
  "name": "schema_info",
  "arguments": {
    "database_name": "app_production"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "database_name": "app_production",
    "table_count": 12,
    "view_count": 3,
    "total_rows": 125000,
    "total_size_mb": 245.6,
    "tables": [
      {
        "name": "users",
        "type": "BASE TABLE",
        "rows": 1250,
        "size_mb": 12.3
      },
      {
        "name": "orders",
        "type": "BASE TABLE", 
        "rows": 8500,
        "size_mb": 45.7
      }
    ]
  }
}
```

## Enterprise Tools (Full Mode Only)

### `create_schema_snapshot`

Create a comprehensive snapshot of database schemas for backup and versioning.

**Parameters:**
- `database_names` (array, optional): List of specific databases to snapshot

**Example Usage:**
```json
{
  "name": "create_schema_snapshot",
  "arguments": {
    "database_names": ["app_production", "app_analytics"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "snapshot_id": "snap_20240816_203045",
    "timestamp": "2024-08-16T20:30:45Z",
    "databases": [
      {
        "name": "app_production",
        "table_count": 12,
        "tables": [
          {
            "name": "users",
            "column_count": 8,
            "index_count": 3
          }
        ]
      }
    ],
    "total_databases": 2,
    "generation_time_ms": 1250
  }
}
```

### `export_schema`

Export database schema in various formats (JSON or SQL DDL).

**Parameters:**
- `database_names` (array, optional): List of databases to export
- `format_type` (string, optional): Export format - "json" or "sql" (default: "json")

**Example Usage:**
```json
{
  "name": "export_schema",
  "arguments": {
    "database_names": ["app_production"],
    "format_type": "sql"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "format": "sql",
    "exported_at": "2024-08-16T20:30:45Z",
    "schema_hash": "abc123def456",
    "content": "CREATE TABLE `users` (\n  `id` int NOT NULL AUTO_INCREMENT,\n  `email` varchar(255) NOT NULL,\n  PRIMARY KEY (`id`)\n) ENGINE=InnoDB;",
    "size_bytes": 2048,
    "database_count": 1,
    "table_count": 12
  }
}
```

### `analyze_schema`

Analyze database schema for performance issues, design problems, and recommendations.

**Parameters:**
- `database_names` (array, optional): List of databases to analyze

**Example Usage:**
```json
{
  "name": "analyze_schema",
  "arguments": {
    "database_names": ["app_production"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "analysis_timestamp": "2024-08-16T20:30:45Z",
    "databases_analyzed": ["app_production"],
    "overall_score": 85,
    "issues": [
      {
        "severity": "medium",
        "table": "orders",
        "issue": "Missing index on frequently queried column 'status'",
        "recommendation": "CREATE INDEX idx_orders_status ON orders(status)"
      },
      {
        "severity": "low",
        "table": "users",
        "issue": "Unused index detected",
        "recommendation": "Consider dropping index 'idx_unused' if not needed"
      }
    ],
    "statistics": {
      "total_tables": 12,
      "tables_with_issues": 2,
      "total_indexes": 28,
      "unused_indexes": 1
    }
  }
}
```

### `security_status`

Get comprehensive security status and statistics including threat detection and audit information.

**Parameters:** None

**Example Usage:**
```json
{
  "name": "security_status",
  "arguments": {}
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "security_level": "high",
    "threats_detected_24h": 0,
    "blocked_queries": 3,
    "audit_events": 150,
    "security_features": {
      "injection_detection": true,
      "dangerous_query_blocking": true,
      "audit_logging": true,
      "rate_limiting": true,
      "ip_whitelisting": false
    },
    "last_security_scan": "2024-08-16T20:00:00Z"
  }
}
```

### `monitoring_status`

Get comprehensive production monitoring status including health, performance, and operational metrics.

**Parameters:** None

**Example Usage:**
```json
{
  "name": "monitoring_status",
  "arguments": {}
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "monitoring_active": true,
    "uptime_seconds": 86400,
    "health_status": "healthy",
    "performance_grade": "A",
    "active_alerts": 0,
    "metrics_collected": 1440,
    "last_health_check": "2024-08-16T20:30:00Z",
    "service_availability": 99.95
  }
}
```

### `performance_metrics`

Get detailed performance metrics and statistics including query times, throughput, and resource usage.

**Parameters:** None

**Example Usage:**
```json
{
  "name": "performance_metrics",
  "arguments": {}
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query_performance": {
      "average_response_time_ms": 45.6,
      "p95_response_time_ms": 125.3,
      "p99_response_time_ms": 245.8,
      "queries_per_second": 12.5,
      "total_queries_24h": 10800
    },
    "resource_usage": {
      "cpu_usage_percent": 23.4,
      "memory_usage_mb": 256.8,
      "disk_io_ops_per_sec": 45.2
    },
    "cache_performance": {
      "hit_rate": 0.92,
      "cache_size_mb": 64.2,
      "evictions": 15
    }
  }
}
```

### `system_metrics`

Get system resource metrics including CPU, memory, disk, and network usage.

**Parameters:** None

**Example Usage:**
```json
{
  "name": "system_metrics",
  "arguments": {}
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "cpu": {
      "usage_percent": 23.4,
      "load_average": [0.45, 0.52, 0.48],
      "cores": 4
    },
    "memory": {
      "total_mb": 8192,
      "used_mb": 2048,
      "available_mb": 6144,
      "usage_percent": 25.0
    },
    "disk": {
      "total_gb": 100,
      "used_gb": 35,
      "available_gb": 65,
      "usage_percent": 35.0,
      "io_read_mb_per_sec": 12.5,
      "io_write_mb_per_sec": 8.3
    },
    "network": {
      "bytes_sent": 1250000,
      "bytes_received": 890000,
      "packets_sent": 1500,
      "packets_received": 1200
    }
  }
}
```

### `error_summary`

Get error tracking summary and statistics including error rates, types, and recent errors.

**Parameters:** None

**Example Usage:**
```json
{
  "name": "error_summary",
  "arguments": {}
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "error_rate_24h": 0.02,
    "total_errors_24h": 5,
    "error_types": {
      "connection_errors": 2,
      "query_errors": 2,
      "timeout_errors": 1
    },
    "recent_errors": [
      {
        "timestamp": "2024-08-16T19:45:00Z",
        "type": "QUERY_ERROR",
        "message": "Table 'temp_table' doesn't exist",
        "frequency": 1
      }
    ],
    "error_trend": "stable"
  }
}
```

## HTTP API Usage

When using the streamable-http transport, you can call tools via HTTP POST requests:

### List Available Tools

```bash
curl -X POST http://localhost:8080/tools/list \
  -H "Content-Type: application/json"
```

### Call a Tool

```bash
curl -X POST http://localhost:8080/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "execute_query",
    "arguments": {
      "sql": "SELECT COUNT(*) as user_count FROM users"
    }
  }'
```

### Authentication (if enabled)

```bash
curl -X POST http://localhost:8080/tools/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'username:password' | base64)" \
  -d '{
    "name": "get_databases",
    "arguments": {}
  }'
```

## Error Handling

All tools follow consistent error handling patterns:

### Common Error Codes

- `FEATURE_DISABLED`: Requested feature is disabled in configuration
- `QUERY_EXECUTION_ERROR`: SQL query execution failed
- `CONNECTION_ERROR`: Database connection failed
- `PERMISSION_DENIED`: Insufficient permissions for operation
- `RATE_LIMITED`: Rate limit exceeded
- `INVALID_FORMAT`: Invalid format specified
- `VALIDATION_ERROR`: Input validation failed

### Example Error Response

```json
{
  "success": false,
  "error": "Connection to database failed: Access denied for user 'test'@'localhost'",
  "error_code": "CONNECTION_ERROR",
  "details": {
    "host": "localhost",
    "user": "test",
    "timestamp": "2024-08-16T20:30:45Z"
  }
}
```

## Rate Limiting

When rate limiting is enabled (`MCP_ENABLE_RATE_LIMITING=true`), all tools are subject to rate limits:

- Default: 100 queries per minute
- Configurable via `MCP_MAX_QUERIES_PER_MINUTE`
- Rate limit exceeded returns `RATE_LIMITED` error code
- Rate limits are per-client (if client identification is available)

## Security Considerations

1. **SQL Injection Protection**: All queries are validated when security features are enabled
2. **Query Type Restrictions**: `MCP_ALLOWED_QUERY_TYPES` controls which query types are permitted
3. **Read-only Mode**: `MCP_READONLY_MODE=true` restricts to SELECT queries only
4. **Authentication**: HTTP transport supports basic authentication
5. **IP Whitelisting**: Restrict access by IP address ranges
6. **Audit Logging**: All tool usage can be logged for security auditing

## Tool Mode Recommendations

### For AI Assistants (Cursor/Copilot/Windsurf)
```bash
MCP_TOOL_MODE=lite
```
- 8 focused tools prevent AI confusion
- Covers all essential database operations
- Faster tool selection and execution
- Better user experience

### For Enterprise/Power Users
```bash
MCP_TOOL_MODE=full
```
- Complete set of 22 tools
- Advanced monitoring and analytics
- Schema management capabilities
- Production monitoring features

### For Security-Sensitive Environments
```bash
MCP_TOOL_MODE=lite
MCP_READONLY_MODE=true
MCP_ALLOWED_QUERY_TYPES=["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"]
```
- Minimal tool surface area
- Read-only database access
- Enhanced security monitoring

This API reference provides comprehensive documentation for all Database MCP Server tools. For additional information, see the [Configuration Guide](CONFIGURATION.md) and [Examples](EXAMPLES.md).
