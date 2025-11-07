# Database MCP Server

A production-grade Model Context Protocol (MCP) server for MySQL database interactions with enterprise-level security, monitoring, and schema management capabilities.

## 🚀 Features

### Core Database Operations
- **Flexible Database Access**: Connect to any database on a MySQL host or specify a default database
- **Secure SQL Execution**: Execute queries with comprehensive parameter binding and validation
- **Connection Pooling**: Efficient `aiomysql` connection management with automatic retry
- **Multi-Transport Support**: Four transport modes - stdio, SSE, Streamable HTTP, and auto-detection
- **CLI Testing Mode**: Direct tool testing and query execution for development and debugging
- **Query Analysis**: Built-in `EXPLAIN` query analysis and performance insights

### 🛡️ Enterprise Security
- **Advanced SQL Injection Prevention**: Multi-layered protection with pattern analysis and AST parsing
- **Query Structure Analysis**: Deep inspection using `sqlparse` for dangerous constructs
- **Connection Security**: Rate limiting, authentication tracking, and suspicious behavior detection  
- **Security Audit Logging**: Comprehensive threat classification and response tracking
- **Risk Assessment**: Real-time query risk evaluation (low/medium/high/critical)

### 📊 Production Monitoring
- **Real-time Metrics**: Performance tracking, query statistics, and system resource monitoring
- **Health Checks**: Database connectivity, connection pool health, and service status monitoring
- **Error Tracking**: Comprehensive error aggregation, analysis, and trend detection
- **Metrics Export**: Prometheus and JSON format support for external monitoring systems

### 🔧 Error Handling & Recovery
- **Intelligent Retry Logic**: Exponential backoff with jitter for transient failures
- **Circuit Breaker Pattern**: Cascading failure prevention with automatic recovery detection
- **Graceful Degradation**: Service fallback with cached responses and readonly modes
- **Comprehensive Error Context**: Detailed error tracking with recovery attempt logging

### 🗃️ Schema Management
- **Advanced Introspection**: Complete database, table, column, index, and constraint discovery
- **Schema Analysis**: Automated health scoring, performance issue detection, and optimization recommendations
- **Change Detection**: SHA-256 hashing for schema versioning and diff generation
- **Export/Import**: JSON and SQL DDL formats with full metadata preservation

## 📦 Installation

### Prerequisites
- Python 3.11+ (3.10+ with `tomli` for TOML parsing)
- MySQL 5.7+ or MariaDB 10.3+
- Virtual environment (strongly recommended)

### Quick Setup

```bash
# Clone the repository
git clone <repository-url>
cd mcptools

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create development configuration
# Create database/environment/dev.toml with your credentials:
cat > database/environment/dev.toml <<EOF
[database]
host = "localhost"
user = "root"
password = "your_password"
database = ""  # Empty = connect to any database on the host

[server]
transport_mode = "stdio"
log_level = "INFO"

[mcp]
# Comma-separated allowed query types
allowed_query_types = "SHOW, DESCRIBE, SELECT"
EOF

# Run the server (uses config from environment/default.toml + dev.toml)
python -m database

# Or specify transport mode via CLI (overrides config)
python -m database --transport sse --port 8080
python -m database --transport streamable-http --port 8080

# For CLI testing and development
python -m database --test-tools
python -m database --test-query "SHOW DATABASES"
python -m database --config-check  # Validate configuration
```

### Dependencies

```bash
# Core dependencies (see requirements.txt)
aiomysql>=0.1.1          # Async MySQL client
fastmcp>=0.2.0           # MCP server framework  
uvicorn>=0.24.0          # ASGI server for SSE
starlette>=0.27.0        # Web framework for SSE transport
pydantic>=2.0.0          # Data validation and settings
python-dotenv>=1.0.0     # Environment variable loading
sqlparse>=0.4.0          # SQL parsing for security analysis
psutil>=5.9.0            # System resource monitoring
```

## 🗃️ Database Flexibility

The MCP server is designed to be **database-agnostic within a MySQL host**:

- **No Default Database**: Leave `DB_DATABASE` empty to connect to the MySQL server without selecting a specific database
- **Multi-Database Access**: Use `USE database_name` queries or fully qualified names like `database.table` to work with any database
- **Optional Default**: Set `DB_DATABASE` to specify a default database for convenience
- **Dynamic Switching**: Switch between databases during a session using standard SQL commands

**Examples:**
```sql
-- List all databases on the host
SHOW DATABASES;

-- Switch to a specific database
USE my_application_db;

-- Query a specific database without switching
SELECT * FROM inventory.products WHERE price > 100;

-- Work with multiple databases in one query
SELECT u.name, o.total 
FROM users.customers u 
JOIN orders.order_summary o ON u.id = o.customer_id;
```

This flexibility makes the MCP server ideal for:
- **Multi-tenant applications** with database-per-tenant architecture
- **Microservices** where each service has its own database
- **Data analysis** across multiple databases
- **Database administration** tasks requiring access to multiple schemas

## ⚙️ Configuration

### TOML-Based Configuration

The database server uses a hierarchical TOML configuration system with three layers:

1. **`database/environment/default.toml`** - Base configuration (committed to git)
2. **`database/environment/dev.toml`** - Development overrides (gitignored, create locally)
3. **`database/environment/prod.toml`** - Production overrides (committed to git)

### Configuration Files

**`database/environment/default.toml`** (Base configuration):

```toml
[app]
# Application configuration
name = "database-mcp-server"
version = "1.0.0"

[database]
# Database connection configuration
host = "localhost"
port = 3306
user = ""
password = ""
database = ""  # Empty = connect without default database
charset = "utf8mb4"
use_ssl = false

# Connection pool settings
pool_size = 10
pool_recycle = 3600
query_timeout = 30
max_query_length = 1048576  # 1MB
max_rows_limit = 1000

[server]
# Server configuration
host = "localhost"
port = 8080
transport_mode = "stdio"  # Options: stdio, sse, streamable-http
debug = false

# Logging configuration
log_level = "INFO"
log_file = "logs/database_mcp.log"
log_destination = "file"  # file, stderr, stdout, both (auto-set to file for stdio)
log_format = "json"  # json or text
log_include_timestamp = true
log_include_trace_id = true
log_max_file_size = "10MB"
log_backup_count = 5

[mcp]
# MCP server configuration
server_name = "database-mcp"
readonly_mode = false
tool_mode = true
enable_rate_limiting = true
max_queries_per_minute = 60

# Allowed query types (comma-separated string, case-insensitive)
# 
# FINE-GRAINED RULES:
# - "DROP" - allows any DROP operation (DATABASE, TABLE, INDEX, etc.)
# - "DROP TABLE" - allows ONLY DROP TABLE, blocks DROP DATABASE  
# - "DROP DATABASE" - allows ONLY DROP DATABASE, blocks DROP TABLE
# - "CREATE TABLE, ALTER TABLE, DROP TABLE" - table-level DDL only
#
# EXAMPLES:
# - Read-only: "SELECT, SHOW, DESCRIBE, EXPLAIN"
# - Safe writes: "SELECT, INSERT, UPDATE, SHOW, DESCRIBE"
# - Safe DDL: "SELECT, CREATE TABLE, ALTER TABLE, DROP TABLE"
# - Full access: "SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP"

allowed_query_types = "SELECT, SHOW, DESCRIBE, EXPLAIN, UPDATE, INSERT, DELETE, CREATE, ALTER, DROP"

[security]
# Security configuration
enable_sql_analysis = true
block_dangerous_queries = true
max_rows_returned = 10000
```

**`database/environment/dev.toml`** (Development overrides):

```toml
# Database MCP Server - Development Environment Overrides
# These settings override default.toml for development

[database]
# Smaller pool for dev
pool_size = 5

# Longer timeout for debugging
query_timeout = 60

# Dev database connection (no env vars needed for local development)
host = "localhost"
user = "root"
password = "root"
database = ""  # Empty = no default database, can connect to any

[server]
# Logging configuration
log_level = "ERROR"

# Transport mode for development
transport_mode = "stdio"  # or "sse" or "streamable-http"

[mcp]
# Override allowed_query_types for development (comma-separated string)
# 
# EXAMPLES - Uncomment to use:

# Example 1: Read-only (safe for dev testing)
# allowed_query_types = "SELECT, SHOW, DESCRIBE, EXPLAIN"

# Example 2: Safe writes (no DDL)
# allowed_query_types = "SELECT, INSERT, UPDATE, SHOW, DESCRIBE"

# Example 3: Fine-grained DDL (table operations only, blocks DROP DATABASE)
# allowed_query_types = "SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, ALTER TABLE, DROP TABLE"

# Example 4: Very restricted (schema inspection only)
allowed_query_types = "SHOW, DESCRIBE"

[security]
# More rows for development/testing
max_rows_returned = 10000
```

### Environment Variable Interpolation

You can use environment variables in TOML files:

```toml
[database]
host = "${DB_HOST}"              # ${VAR} syntax
password = "$DB_PASSWORD"        # $VAR syntax
user = "${DB_USER:root}"         # With default value
```

### Configuration Access in Code

```python
from database.config import Config

# Initialize (loads and merges TOML files)
config = Config()

# Access configuration
print(config.database.host)
print(config.server.transport_mode)
print(config.mcp.get_allowed_query_types_list())  # Parses comma-separated string

# Get database connection string
print(config.get_database_dsn(mask_password=True))

# Get connection parameters for aiomysql
params = config.get_connection_params()
```

## 🔒 Security Features

### Query Validation Before Execution

The database server **validates all queries before sending them to MySQL**, providing a security layer that blocks dangerous operations:

**Key Features:**
- ✅ **Pre-execution validation**: Queries are analyzed before reaching the database
- ✅ **Fine-grained whitelisting**: Support for operation-specific rules (e.g., `DROP TABLE` allowed, `DROP DATABASE` blocked)
- ✅ **SQL injection detection**: Pattern-based detection of injection attempts
- ✅ **Risk assessment**: Queries are rated (low/medium/high/critical risk)
- ✅ **Threat logging**: All blocked queries are logged with threat details

**Configuration Example:**

```toml
[mcp]
# Only allow schema inspection (read-only)
allowed_query_types = "SHOW, DESCRIBE"

# Allow safe DDL (table operations only)
# allowed_query_types = "SELECT, CREATE TABLE, ALTER TABLE, DROP TABLE"

# Note: "DROP TABLE" allows ONLY table drops, "DROP DATABASE" is blocked
```

**Security Validation Flow:**

```
1. User sends query → 2. Security validation → 3. Execute if safe
                                ↓
                         Block if dangerous
                                ↓
                    Return SECURITY_VIOLATION error
```

**Example Blocked Query:**

```json
{
  "success": false,
  "error": "Query blocked by security validation",
  "error_code": "SECURITY_VIOLATION",
  "threats": [{
    "type": "dangerous_operation",
    "description": "High-risk keyword detected: DROP DATABASE",
    "severity": "high"
  }],
  "risk_level": "critical"
}
```

### Fine-Grained Query Control

The `allowed_query_types` configuration supports fine-grained control:

```toml
# Allow ANY drop operation
allowed_query_types = "SELECT, DROP"

# Allow ONLY table drops (database drops blocked)
allowed_query_types = "SELECT, DROP TABLE"

# Allow ONLY database drops (table drops blocked)
allowed_query_types = "SELECT, DROP DATABASE"

# Table-level DDL only
allowed_query_types = "SELECT, CREATE TABLE, ALTER TABLE, DROP TABLE"
```

## 🚦 Usage

### Starting the Server

#### Automatic Transport Detection (Recommended)
```bash
python -m database
# Automatically detects stdio (CLI) or SSE (HTTP) based on environment
```

#### Explicit Transport Mode
```bash
# Stdio transport (for uvx/CLI clients)
python -m database --transport stdio

# SSE transport (for Server-Sent Events clients)  
python -m database --transport sse --port 8080

# Streamable HTTP transport (for MCP Inspector and HTTP clients)
python -m database --transport streamable-http --port 8080

# Auto-detect transport based on environment
python -m database --transport auto
```

#### CLI Testing and Development
```bash
# Interactive tool testing mode
python -m database --test-tools

# Execute a specific query directly
python -m database --test-query "SHOW DATABASES"
python -m database --test-query "SELECT * FROM information_schema.tables LIMIT 5"

# Configuration validation
python -m database --config-check
```

#### Command Line Options
```bash
python -m database --help

Options:
  --transport {stdio,sse,streamable-http,auto}  Transport mode selection
  --test-tools                                  Enter CLI testing mode
  --test-query TEXT                            Execute specific SQL query
  --host TEXT                                  Server host (SSE/HTTP modes)
  --port INTEGER                               Server port (SSE/HTTP modes)  
  --debug                                      Enable debug mode
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}  Logging level
  --config-check                               Validate configuration and exit
  --config-reload                              Reload configuration from environment
  --version                                    Show version information
```

### Client Integration

#### MCP Client Configuration (mcp.json)

**Stdio Transport:**
```json
{
  "mcpServers": {
    "database": {
      "command": "uvx",
      "args": ["--from", "/path/to/mcptools", "python", "-m", "database", "--transport", "stdio"],
      "env": {
        "DB_HOST": "localhost",
        "DB_USER": "your_username", 
        "DB_PASSWORD": "your_password"
      }
    }
  }
}
```

**SSE Transport:**
```json
{
  "mcpServers": {
    "database": {
      "url": "http://localhost:8080/sse",
      "transport": "sse"
    }
  }
}
```

**Streamable HTTP Transport (for MCP Inspector):**
```json
{
  "mcpServers": {
    "database": {
      "url": "http://localhost:8080/mcp",
      "transport": "http"
    }
  }
}
```

#### MCP Inspector Integration

For testing and development with [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

1. **Start the server in streamable-http mode:**
   ```bash
   python -m database --transport streamable-http --port 8080
   ```

2. **Connect with MCP Inspector:**
   - **Transport Type**: HTTP (not SSE)
   - **URL**: `http://localhost:8080/mcp`
   - **Features**: Full tool listing, query execution, and real-time testing

3. **Available Tools in Inspector:**
   - `execute_query`: Execute SQL queries with security validation
   - `debug_test`: Simple debug tool for testing connectivity

**Example Queries to Test:**
```sql
-- List all databases
SHOW DATABASES;

-- Get table information
SHOW TABLES FROM information_schema LIMIT 5;

-- Query specific data
SELECT TABLE_NAME, TABLE_TYPE FROM information_schema.tables 
WHERE TABLE_SCHEMA = 'mysql' LIMIT 10;
```

#### HTTP Client Example

```python
import httpx
import json

# SSE endpoint for streaming MCP communication
sse_url = "http://localhost:8000/sse"

# Execute query via HTTP POST
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/messages",
        json={
            "command": "execute_query",
            "args": {
                "sql": "SELECT * FROM users LIMIT 10",
                "params": None,
                "max_rows": 10,
                "client_id": "my_app"
            }
        }
    )
    result = response.json()
```

## 📖 API Reference

### Core Commands

#### `execute_query`
Execute SQL queries with comprehensive security validation and error handling.

```python
# Parameters:
sql: str                    # SQL query string
params: List[Any] = None    # Optional query parameters  
max_rows: int = None        # Maximum rows to return
client_id: str = "default"  # Client identifier for tracking

# Returns:
{
  "success": bool,
  "data": [...],           # Query results
  "metadata": {
    "rows_returned": int,
    "execution_time": float,
    "query_type": str
  },
  "security_analysis": {
    "risk_level": str,
    "query_type": str,
    "threats_detected": int
  },
  "error_handling": {
    "retry_capable": bool,
    "circuit_breaker_protected": bool,
    "fallback_available": bool
  }
}
```

**Example:**
```python
await execute_query(
    sql="SELECT name, email FROM users WHERE status = %s AND created_at > %s",
    params=["active", "2024-01-01"], 
    max_rows=50,
    client_id="user_dashboard"
)
```

#### `explain_query`
Analyze query performance and execution plan.

```python
# Parameters:
sql: str                    # SQL query to analyze
params: List[Any] = None    # Optional query parameters

# Returns:
{
  "success": bool,
  "data": {
    "execution_plan": [...], 
    "performance_analysis": {
      "estimated_rows": int,
      "key_usage": str,
      "optimization_suggestions": [...]
    }
  }
}
```

### Schema Management Commands

#### `get_databases`
Get comprehensive database information.

```python
# Returns:
{
  "success": bool,
  "data": {
    "databases": [
      {
        "name": str,
        "character_set": str,
        "collation": str, 
        "table_count": int
      }
    ],
    "total_databases": int
  }
}
```

#### `get_table_details`
Get complete table structure including columns, indexes, and constraints.

```python
# Parameters:
table_name: str              # Table name to analyze
database_name: str = None    # Optional database name

# Returns:
{
  "success": bool,
  "data": {
    "table": {
      "name": str,
      "database_name": str,
      "table_type": str,
      "engine": str,
      "table_rows": int,
      "data_length": int,
      "table_comment": str
    },
    "columns": [...],        # Detailed column information
    "indexes": [...],        # Index definitions
    "constraints": [...],    # Constraint relationships
    "summary": {
      "total_columns": int,
      "total_indexes": int,
      "primary_key_columns": [str]
    }
  }
}
```

#### `create_schema_snapshot`
Create timestamped schema snapshot with change detection.

```python
# Parameters:
database_names: List[str] = None  # Optional database filter

# Returns:
{
  "success": bool,
  "data": {
    "snapshot": {
      "timestamp": str,      # ISO timestamp
      "schema_hash": str,    # SHA-256 hash for change detection
      "mysql_version": str,
      "database_count": int,
      "table_count": int,
      "databases": [str],
      "server_info": {...}
    }
  }
}
```

#### `analyze_schema`
Comprehensive schema analysis with health scoring and recommendations.

```python
# Parameters:  
database_names: List[str] = None  # Optional database filter

# Returns:
{
  "success": bool,
  "data": {
    "analysis_timestamp": str,
    "overall_score": int,    # 0-100 health score
    "overall_metrics": {
      "database_count": int,
      "table_count": int,
      "total_columns": int,
      "total_indexes": int
    },
    "database_recommendations": [...],
    "table_analyses": {
      "database.table": {
        "metrics": {...},
        "issues": [...],       # Performance/design issues
        "recommendations": [...], # Optimization suggestions
        "overall_score": int
      }
    }
  }
}
```

#### `export_schema`
Export complete schema in JSON or SQL DDL format.

```python
# Parameters:
database_names: List[str] = None  # Optional database filter
format_type: str = "json"         # "json" or "sql"

# Returns:
{
  "success": bool,
  "data": {
    "format": str,
    "exported_at": str,
    "schema_hash": str,
    "content": str,          # Exported schema content
    "size_bytes": int,
    "database_count": int,
    "table_count": int
  }
}
```

### Monitoring Commands

#### `monitoring_status`
Get comprehensive production monitoring overview.

```python
# Returns:
{
  "success": bool,
  "data": {
    "system_health": {...},
    "performance_summary": {...},
    "error_summary": {...},
    "database_health": {...},
    "security_status": {...}
  }
}
```

#### `performance_metrics`
Get detailed performance metrics and query statistics.

```python
# Returns:
{
  "success": bool,
  "data": {
    "query_metrics": {
      "total_queries": int,
      "average_execution_time": float,
      "queries_by_type": {...},
      "slow_queries": [...],
      "peak_concurrent_connections": int
    },
    "connection_metrics": {...},
    "resource_usage": {...}
  }
}
```

#### `export_metrics`
Export metrics in Prometheus or JSON format.

```python
# Parameters:
format_type: str = "json"  # "json" or "prometheus"

# Returns:
{
  "success": bool,
  "data": {
    "format": str,
    "exported_at": float,
    "content": str         # Formatted metrics data
  }
}
```

### Security Commands

#### `security_status`
Get comprehensive security report and threat analysis.

```python
# Returns:
{
  "success": bool,
  "data": {
    "query_security": {
      "total_queries_analyzed": int,
      "threats_detected": int,
      "blocked_queries": int,
      "risk_distribution": {...}
    },
    "connection_security": {
      "active_connections": int,
      "blocked_clients": int,
      "authentication_failures": int
    },
    "security_recommendations": [...]
  }
}
```

### Error Handling Commands

#### `error_handling_status`
Get comprehensive error handling system status.

```python
# Returns:
{
  "success": bool,
  "data": {
    "circuit_breakers": {...},    # Circuit breaker states
    "service_states": {...},      # Service health states  
    "degradation_times": {...},   # Service degradation durations
    "cached_responses": int,      # Number of cached responses
    "error_handling": {...}       # Error handling configuration
  }
}
```

#### `circuit_breaker_status`
Get circuit breaker status for services.

```python
# Parameters:
service_name: str = None    # Optional specific service filter

# Returns:
{
  "success": bool,
  "data": {
    "service_name": {
      "name": str,
      "state": str,           # "closed", "open", "half_open"
      "failure_count": int,
      "success_count": int,
      "last_failure_time": float
    }
  }
}
```

### Health & Diagnostics

#### `health_check`
Perform comprehensive database and system health check.

```python
# Returns:
{
  "success": bool,
  "data": {
    "database_connectivity": bool,
    "connection_pool_health": {...},
    "query_execution": bool,
    "overall_status": str    # "healthy", "degraded", "unhealthy"
  }
}
```

#### `connection_stats`
Get detailed connection pool statistics.

```python
# Returns:
{
  "success": bool,
  "data": {
    "pool_stats": {
      "size": int,
      "checked_in": int,
      "checked_out": int,
      "overflow": int,
      "invalid": int
    },
    "connection_metrics": {...},
    "recent_activity": [...]
  }
}
```

## 🔒 Security Best Practices

### Query Security
```python
# ✅ DO: Use parameterized queries
await execute_query(
    "SELECT * FROM users WHERE id = %s AND status = %s",
    params=[user_id, "active"]
)

# ❌ DON'T: Use string concatenation
sql = f"SELECT * FROM users WHERE id = {user_id}"  # Vulnerable to injection
```

### Connection Security
- Monitor `security_status` regularly for threat detection
- Review authentication failure patterns
- Use rate limiting to prevent abuse
- Enable readonly mode for untrusted clients

### Configuration Security
- Use strong database credentials
- Enable SSL/TLS for production deployments  
- Restrict network access to database server
- Regularly rotate credentials and certificates

## 📊 Monitoring & Observability

### Metrics Collection
The server automatically collects comprehensive metrics:
- Query execution times and frequencies
- Connection pool utilization
- System resource usage (CPU, memory, disk, network)
- Error rates and patterns
- Security threat detection

### Prometheus Integration
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'database-mcp'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### Grafana Dashboard
Monitor key metrics:
- Query performance and throughput
- Connection pool health
- Error rates and types
- Security threat levels
- System resource utilization

## 🐛 Troubleshooting

### Common Issues

#### Connection Failures
```bash
# Check database connectivity
mysql -h localhost -u username -p

# Verify environment variables
python -m database --config-check

# Test connection pool
python -c "
from database import DatabaseManager
import asyncio
async def test():
    db = DatabaseManager()
    await db.initialize_pool()
    print('Connection successful')
asyncio.run(test())
"
```

#### SSL/TLS Issues
```bash
# Verify SSL certificates
openssl x509 -in /path/to/cert.pem -text -noout

# Test SSL connection
mysql --ssl-ca=/path/to/ca.pem --ssl-cert=/path/to/cert.pem --ssl-key=/path/to/key.pem -h hostname -u username -p
```

#### Transport Issues
```bash
# Test stdio transport
echo '{"command": "health_check"}' | python -m database --transport stdio

# Test SSE transport
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"command": "health_check"}'
```

### Debug Mode
```bash
# Enable detailed logging
python -m database --debug --log-level DEBUG

# Check configuration
python -m database --config-check
```

### Performance Tuning
- Adjust connection pool settings based on load
- Monitor query execution times and optimize slow queries
- Use `explain_query` for performance analysis
- Configure appropriate timeouts for your use case

## 📈 Performance Optimization

### Connection Pool Tuning
```bash
# High-traffic scenarios
DB_POOL_MIN_SIZE=10
DB_POOL_MAX_SIZE=50
DB_POOL_RECYCLE=1800

# Low-traffic scenarios  
DB_POOL_MIN_SIZE=2
DB_POOL_MAX_SIZE=10
DB_POOL_RECYCLE=7200
```

### Query Optimization
- Use `EXPLAIN` analysis for slow queries
- Add indexes for frequently queried columns
- Limit result sets with appropriate `max_rows`
- Monitor schema analysis recommendations

### Resource Monitoring
```python
# Monitor system resources
await system_metrics()

# Track query performance
await performance_metrics()

# Analyze error patterns
await error_summary()
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code documentation
- **Configuration Issues**: Use `--config-check` flag for validation
- **Performance Issues**: Monitor with `performance_metrics` and `system_metrics`
- **Security Concerns**: Review `security_status` and audit logs
- **Error Debugging**: Enable debug mode and check error handling status

---

**Built with enterprise-grade security, monitoring, and reliability for production MySQL database operations via Model Context Protocol.**
