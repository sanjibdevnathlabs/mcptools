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
- Python 3.8+
- MySQL 5.7+ or MariaDB 10.3+
- Virtual environment (recommended)

### Quick Setup

```bash
# Clone the repository
git clone <repository-url>
cd mcptools/database

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r ../requirements.txt

# Create environment configuration (see docs/ENVIRONMENT.md for complete reference)
# Copy the example configuration and edit with your credentials
cp docs/env.example .env
# Edit .env with your actual database credentials:
#   DATABASE_HOST=localhost
#   DATABASE_PORT=3306  
#   DATABASE_USER=your_username
#   DATABASE_PASSWORD=your_password
# DATABASE_DATABASE is optional - leave empty to access any database on the host

# Run the server (stdio transport by default)
python -m database

# Or specify transport mode
python -m database --transport sse --port 8080
python -m database --transport streamable-http --port 8080

# For CLI testing and development
python -m database --test-tools
python -m database --test-query "SHOW DATABASES"
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

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database Connection (Required)
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_CHARSET=utf8mb4

# Connection Pool Settings
DB_POOL_MIN_SIZE=5
DB_POOL_MAX_SIZE=20
DB_POOL_RECYCLE=3600
DB_CONNECT_TIMEOUT=10
DB_QUERY_TIMEOUT=30

# SSL Configuration (Optional)
DB_SSL_ENABLE=false
DB_SSL_CA_FILE=/path/to/ca.pem
DB_SSL_CERT_FILE=/path/to/client-cert.pem
DB_SSL_KEY_FILE=/path/to/client-key.pem

# Server Configuration
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
SERVER_DEBUG=false
SERVER_LOG_LEVEL=INFO
SERVER_TRANSPORT=auto  # auto, stdio, sse

# Security Settings
MCP_READONLY_MODE=false
MCP_ENABLE_RATE_LIMITING=true
MCP_MAX_QUERIES_PER_MINUTE=100
MCP_MAX_QUERY_LENGTH=50000
MCP_ALLOWED_QUERY_TYPES=SELECT,INSERT,UPDATE,DELETE,SHOW,DESCRIBE,EXPLAIN

# Monitoring & Logging
SERVER_ENABLE_HEALTH_CHECKS=true
SERVER_ENABLE_METRICS=true
SERVER_METRICS_RETENTION_HOURS=24
SERVER_LOG_SQL_QUERIES=true

# Schema Introspection
MCP_ENABLE_SCHEMA_INTROSPECTION=true
MCP_ENABLE_QUERY_ANALYSIS=true
```

### Advanced Configuration Options

```python
# database/config.py provides extensive customization:
# - SSL/TLS configuration with certificate validation
# - Connection pool tuning and health checks
# - Rate limiting and security policies
# - Monitoring and metrics collection settings
# - Cross-validation rules and dependency checks
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
