# Usage Examples and Tutorials

This document provides comprehensive examples for using the Database MCP Server in different scenarios, from basic development setups to enterprise deployments.

## Quick Start Examples

### 1. Minimal Setup for Cursor/Copilot

**Most common use case - AI assistant integration:**

```bash
# Create .env file
echo "DATABASE_USER=root" > .env
echo "DATABASE_PASSWORD=your_password" >> .env

# Start the server
python -m database
```

**What you get:**
- ✅ 8 core tools (perfect for AI clients)  
- ✅ stdio transport (works with uvx)
- ✅ Connection to localhost:3306
- ✅ All security features enabled

**Use in Cursor/Copilot:**
- Add to your `mcp.json` configuration
- AI can execute SQL queries, explore schemas, optimize queries

### 2. MCP Inspector Testing

**For testing and debugging with MCP Inspector:**

```bash
# .env file
DATABASE_USER=root
DATABASE_PASSWORD=your_password
SERVER_TRANSPORT_MODE=streamable-http
SERVER_PORT=8080

# Start server
python -m database --transport streamable-http

# Open MCP Inspector
# Connect to: http://localhost:8080
```

### 3. CLI Testing Mode

**Test tools directly without external clients:**

```bash
# Interactive testing
python -m database --test-tools

# Test specific query
python -m database --test-query "SHOW DATABASES"

# List available tools and their descriptions
python -m database --test-tools
```

## Tool Mode Examples

### Lite Mode (Recommended for AI Clients)

```bash
# .env configuration
DATABASE_USER=root
DATABASE_PASSWORD=your_password
MCP_TOOL_MODE=lite

# Results in 8 focused tools:
# 1. execute_query - SQL execution
# 2. get_databases - Database discovery
# 3. get_tables - Table listing  
# 4. get_table_details - Table structure
# 5. explain_query - Query optimization
# 6. health_check - Connection status
# 7. connection_stats - Pool statistics
# 8. schema_info - Schema overview
```

### Full Mode (Enterprise/Power Users)

```bash
# .env configuration  
DATABASE_USER=admin_user
DATABASE_PASSWORD=admin_password
MCP_TOOL_MODE=full

# Results in 22 comprehensive tools:
# All lite mode tools plus:
# - create_schema_snapshot
# - export_schema
# - analyze_schema
# - table_info (legacy compatibility)
# - security_status
# - monitoring_status
# - performance_metrics
# - system_metrics
# - error_summary
# - export_metrics
# - error_handling_status
# - circuit_breaker_status
# - service_degradation_status
# - additional enterprise features
```

## Transport Mode Examples

### 1. Stdio Transport (Default)

**Perfect for Cursor, Copilot, and uvx clients:**

```bash
# .env file
DATABASE_USER=dev_user
DATABASE_PASSWORD=dev_password
# SERVER_TRANSPORT_MODE=stdio (default)

# Start server
python -m database

# Or use with uvx
uvx database-mcp
```

**MCP Client Configuration (mcp.json):**
```json
{
  "mcpServers": {
    "database": {
      "command": "uvx",
      "args": ["database-mcp"]
    }
  }
}
```

### 2. Streamable HTTP Transport

**Perfect for MCP Inspector and HTTP clients:**

```bash
# .env file
DATABASE_USER=test_user
DATABASE_PASSWORD=test_password
SERVER_TRANSPORT_MODE=streamable-http
SERVER_HOST=localhost
SERVER_PORT=8080

# Start server
python -m database --transport streamable-http
```

**HTTP Client Usage:**
```bash
# List tools
curl -X POST http://localhost:8080/tools/list

# Execute query
curl -X POST http://localhost:8080/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "execute_query",
    "arguments": {
      "sql": "SHOW DATABASES"
    }
  }'
```

### 3. SSE Transport

**For Server-Sent Events clients:**

```bash
# .env file  
DATABASE_USER=api_user
DATABASE_PASSWORD=api_password
SERVER_TRANSPORT_MODE=sse
SERVER_HOST=0.0.0.0
SERVER_PORT=8080

# Start server
python -m database --transport sse
```

## Database Connection Examples

### 1. Local Development

```bash
# .env file - Minimal local setup
DATABASE_USER=root
DATABASE_PASSWORD=dev123

# Uses defaults:
# DATABASE_HOST=localhost
# DATABASE_PORT=3306
# DATABASE_DATABASE= (access any database)
```

### 2. Remote Database with SSL

```bash
# .env file - Production database
DATABASE_USER=prod_user
DATABASE_PASSWORD=secure_password
DATABASE_HOST=prod-mysql.company.com
DATABASE_PORT=3306

# SSL configuration
DATABASE_USE_SSL=true
DATABASE_SSL_CA=/etc/ssl/ca.pem
DATABASE_SSL_CERT=/etc/ssl/client-cert.pem
DATABASE_SSL_KEY=/etc/ssl/client-key.pem
DATABASE_VERIFY_SSL=true
```

### 3. Specific Database Connection

```bash
# .env file - Connect to specific database
DATABASE_USER=app_user
DATABASE_PASSWORD=app_password
DATABASE_HOST=app-db.internal
DATABASE_DATABASE=application_db
DATABASE_CHARSET=utf8mb4
```

### 4. Connection Pool Tuning

```bash
# .env file - High-traffic application
DATABASE_USER=api_user
DATABASE_PASSWORD=api_password
DATABASE_HOST=cluster-mysql.company.com

# Pool configuration
DATABASE_POOL_MINSIZE=5
DATABASE_POOL_MAXSIZE=25
DATABASE_POOL_RECYCLE=1800

# Timeout configuration
DATABASE_CONNECT_TIMEOUT=15.0
DATABASE_READ_TIMEOUT=60.0
DATABASE_WRITE_TIMEOUT=60.0
DATABASE_QUERY_TIMEOUT=120.0
```

## Security Configuration Examples

### 1. Read-Only Mode

```bash
# .env file - Safe read-only access
DATABASE_USER=readonly_user
DATABASE_PASSWORD=readonly_password

# Security settings
MCP_READONLY_MODE=true
MCP_ALLOWED_QUERY_TYPES=["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"]
MCP_TOOL_MODE=lite

# Rate limiting
MCP_ENABLE_RATE_LIMITING=true
MCP_MAX_QUERIES_PER_MINUTE=50
```

### 2. Enhanced Security

```bash
# .env file - High security environment
DATABASE_USER=secure_user
DATABASE_PASSWORD=complex_secure_password
DATABASE_USE_SSL=true

# Advanced security
SECURITY_ENABLE_INJECTION_DETECTION=true
SECURITY_BLOCK_DANGEROUS_QUERIES=true
SECURITY_AUDIT_LOGGING=true

# IP restrictions
SECURITY_ENABLE_IP_WHITELIST=true
SECURITY_ALLOWED_IPS=192.168.1.0/24,10.0.0.0/8

# HTTP authentication (for HTTP transports)
SECURITY_ENABLE_AUTH=true
SECURITY_USERNAME=api_admin
SECURITY_PASSWORD=admin_secure_password
```

### 3. Development Team Access

```bash
# .env file - Team development environment
DATABASE_USER=dev_team
DATABASE_PASSWORD=team_password
DATABASE_HOST=dev-mysql.company.com

# Flexible access
MCP_READONLY_MODE=false
MCP_ALLOWED_QUERY_TYPES=["SELECT", "INSERT", "UPDATE", "DELETE", "SHOW", "DESCRIBE", "EXPLAIN"]
MCP_TOOL_MODE=full

# Generous limits for development
MCP_MAX_QUERIES_PER_MINUTE=200
DATABASE_POOL_MAXSIZE=15
```

## Use Case Scenarios

### Scenario 1: AI Assistant Integration (Cursor/Copilot)

**Goal:** Integrate with Cursor or Copilot for AI-assisted database work

**Configuration:**
```bash
# .env file
DATABASE_USER=root
DATABASE_PASSWORD=your_password
MCP_TOOL_MODE=lite
```

**Setup Steps:**
1. Create minimal `.env` file
2. Add to Cursor's `mcp.json`:
   ```json
   {
     "mcpServers": {
       "database": {
         "command": "uvx", 
         "args": ["database-mcp"]
       }
     }
   }
   ```
3. Start using AI commands like:
   - "Show me all databases"
   - "Describe the users table structure"
   - "Explain this query: SELECT * FROM orders WHERE date > '2024-01-01'"

**Benefits:**
- ✅ 8 focused tools won't overwhelm AI
- ✅ Fast local development
- ✅ Comprehensive SQL capabilities

### Scenario 2: Database Exploration and Analysis

**Goal:** Explore unfamiliar databases and analyze their structure

**Configuration:**
```bash
# .env file
DATABASE_USER=analyst_user
DATABASE_PASSWORD=analyst_password
DATABASE_HOST=analytics-db.company.com
MCP_TOOL_MODE=full
SERVER_TRANSPORT_MODE=streamable-http
SERVER_PORT=8080
```

**Workflow:**
1. Start server: `python -m database --transport streamable-http`
2. Open MCP Inspector at `http://localhost:8080`
3. Use tools in sequence:
   - `get_databases` - See all available databases
   - `get_tables` - List tables in each database
   - `get_table_details` - Examine table structures
   - `analyze_schema` - Get recommendations
   - `create_schema_snapshot` - Document current state

### Scenario 3: Production API Integration

**Goal:** Provide database access through HTTP API for applications

**Configuration:**
```bash
# .env file  
DATABASE_USER=api_user
DATABASE_PASSWORD=secure_api_password
DATABASE_HOST=prod-mysql.company.com
DATABASE_USE_SSL=true

# Server settings
SERVER_TRANSPORT_MODE=streamable-http
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
MCP_TOOL_MODE=full

# Security
SECURITY_ENABLE_AUTH=true
SECURITY_USERNAME=client_app
SECURITY_PASSWORD=client_secure_token
SECURITY_ENABLE_INJECTION_DETECTION=true

# Performance
DATABASE_POOL_MAXSIZE=30
MCP_MAX_QUERIES_PER_MINUTE=500

# Monitoring
MONITORING_ENABLE_METRICS=true
LOG_ENABLE_FILE_LOGGING=true
```

**Application Integration:**
```python
import requests

# Authenticate and execute query
response = requests.post(
    "http://api-server:8080/tools/call",
    headers={
        "Authorization": "Basic Y2xpZW50X2FwcDpjbGllbnRfc2VjdXJlX3Rva2Vu",
        "Content-Type": "application/json"
    },
    json={
        "name": "execute_query",
        "arguments": {
            "sql": "SELECT COUNT(*) FROM orders WHERE status = 'pending'"
        }
    }
)
data = response.json()
```

### Scenario 4: Development Team Database Management

**Goal:** Provide database access for development team with appropriate controls

**Configuration:**
```bash
# .env file
DATABASE_USER=dev_team_user  
DATABASE_PASSWORD=dev_team_password
DATABASE_HOST=dev-mysql.company.com

# Team-friendly settings
MCP_TOOL_MODE=full
MCP_READONLY_MODE=false
MCP_ALLOWED_QUERY_TYPES=["SELECT", "INSERT", "UPDATE", "DELETE", "SHOW", "DESCRIBE", "EXPLAIN", "CREATE", "DROP"]

# Reasonable limits
MCP_MAX_QUERIES_PER_MINUTE=150
DATABASE_POOL_MAXSIZE=20

# Audit and monitoring
SECURITY_AUDIT_LOGGING=true
MONITORING_ENABLE_METRICS=true
LOG_ENABLE_FILE_LOGGING=true
```

**Team Workflow:**
1. Each developer gets access to MCP tools
2. Can explore schemas, execute queries, analyze performance
3. All activity is logged for audit purposes
4. Connection pooling handles multiple concurrent users

### Scenario 5: Database Migration and Schema Analysis

**Goal:** Analyze database schemas before migration projects

**Configuration:**
```bash
# .env file
DATABASE_USER=migration_analyst
DATABASE_PASSWORD=migration_password

# Full toolset for comprehensive analysis
MCP_TOOL_MODE=full
MCP_READONLY_MODE=true

# Focus on analysis tools
MCP_ALLOWED_QUERY_TYPES=["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"]
```

**Migration Workflow:**
1. `create_schema_snapshot` - Capture current state
2. `analyze_schema` - Identify issues and recommendations
3. `export_schema` - Generate SQL DDL for new environment
4. `get_table_details` - Document all table structures
5. `performance_metrics` - Baseline performance data

## Advanced Examples

### Custom Query Patterns

**Complex Analytics Queries:**
```sql
-- Use with execute_query tool
WITH monthly_sales AS (
  SELECT 
    DATE_FORMAT(order_date, '%Y-%m') as month,
    SUM(total_amount) as sales
  FROM orders 
  WHERE order_date >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
  GROUP BY DATE_FORMAT(order_date, '%Y-%m')
),
growth_calc AS (
  SELECT 
    month,
    sales,
    LAG(sales) OVER (ORDER BY month) as prev_month_sales,
    ((sales - LAG(sales) OVER (ORDER BY month)) / LAG(sales) OVER (ORDER BY month)) * 100 as growth_rate
  FROM monthly_sales
)
SELECT * FROM growth_calc WHERE growth_rate IS NOT NULL;
```

**Performance Analysis:**
```sql
-- Use with explain_query tool
EXPLAIN FORMAT=JSON
SELECT DISTINCT
  u.username,
  u.email,
  COUNT(o.id) as order_count,
  SUM(o.total_amount) as total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at >= '2024-01-01'
  AND u.status = 'active'
GROUP BY u.id, u.username, u.email
HAVING COUNT(o.id) > 5
ORDER BY total_spent DESC
LIMIT 100;
```

### Monitoring and Health Checks

**Health Check Automation:**
```bash
#!/bin/bash
# health-check.sh

# Check server health
python -m database --test-query "SELECT 1" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Database MCP Server is healthy"
else
    echo "❌ Database MCP Server health check failed"
    exit 1
fi

# Check connection pool
python -c "
import requests
response = requests.post('http://localhost:8080/tools/call', json={
    'name': 'connection_stats', 
    'arguments': {}
})
data = response.json()
if data.get('success') and data['data']['active_connections'] < 80:
    print('✅ Connection pool healthy')
else:
    print('⚠️ Connection pool may be stressed')
"
```

### Batch Operations

**Schema Documentation Generator:**
```python
#!/usr/bin/env python3
"""Generate comprehensive schema documentation"""

import requests
import json
from datetime import datetime

# MCP Server endpoint
MCP_URL = "http://localhost:8080/tools/call"

def call_tool(name, arguments=None):
    response = requests.post(MCP_URL, json={
        "name": name,
        "arguments": arguments or {}
    })
    return response.json()

def generate_documentation():
    print("# Database Schema Documentation")
    print(f"Generated: {datetime.now().isoformat()}")
    print()
    
    # Get all databases
    databases = call_tool("get_databases")
    for db in databases['data']['databases']:
        print(f"## Database: {db['name']}")
        print(f"- Character Set: {db['character_set']}")
        print(f"- Collation: {db['collation']}")
        print(f"- Tables: {db['table_count']}")
        print()
        
        # Get tables for this database
        tables = call_tool("get_tables", {"database_name": db['name']})
        for table in tables['data']['tables']:
            print(f"### Table: {table['name']}")
            print(f"- Engine: {table['engine']}")
            print(f"- Rows: {table['table_rows']:,}")
            print(f"- Size: {table['data_length']:,} bytes")
            print()
            
            # Get table details
            details = call_tool("get_table_details", {
                "table_name": table['name'],
                "database_name": db['name']
            })
            
            print("#### Columns:")
            for col in details['data']['columns']:
                nullable = "NULL" if col['is_nullable'] else "NOT NULL"
                default = f" DEFAULT {col['default_value']}" if col['default_value'] else ""
                print(f"- **{col['name']}** `{col['data_type']}` {nullable}{default}")
            print()

if __name__ == "__main__":
    generate_documentation()
```

## Troubleshooting Examples

### Connection Issues

**Test Database Connectivity:**
```bash
# Test with minimal configuration
echo "DATABASE_USER=root" > test.env
echo "DATABASE_PASSWORD=test123" >> test.env

# Load test environment and check
DATABASE_USER=root DATABASE_PASSWORD=test123 python -m database --test-query "SELECT 1"
```

**Debug SSL Issues:**
```bash
# Test SSL connection manually
mysql --ssl-ca=/path/to/ca.pem \
      --ssl-cert=/path/to/client-cert.pem \
      --ssl-key=/path/to/client-key.pem \
      -h your-host -u your-user -p

# If manual connection works, check MCP SSL config
DATABASE_USE_SSL=true \
DATABASE_SSL_CA=/path/to/ca.pem \
DATABASE_SSL_CERT=/path/to/client-cert.pem \
DATABASE_SSL_KEY=/path/to/client-key.pem \
python -m database --test-tools
```

### Performance Issues

**Analyze Slow Queries:**
```bash
# Enable query profiling
DEV_ENABLE_QUERY_PROFILING=true python -m database --test-query "
SELECT u.*, COUNT(o.id) as order_count 
FROM users u 
LEFT JOIN orders o ON u.id = o.user_id 
GROUP BY u.id 
ORDER BY order_count DESC 
LIMIT 10
"

# Use explain_query tool for analysis
python -m database --test-query "EXPLAIN FORMAT=JSON SELECT ..."
```

**Connection Pool Monitoring:**
```bash
# Monitor connection usage
watch -n 5 'python -c "
import requests
r = requests.post(\"http://localhost:8080/tools/call\", json={\"name\": \"connection_stats\"})
data = r.json()
print(f\"Active: {data[\"data\"][\"active_connections\"]}\")
print(f\"Pool size: {data[\"data\"][\"pool_size\"]}\")
"'
```

### Tool Registration Issues

**Verify Tool Registration:**
```bash
# Check tool count by mode
echo "Testing lite mode (should show 8 tools):"
MCP_TOOL_MODE=lite python -m database --test-tools | grep "Available tools:" 

echo "Testing full mode (should show 22 tools):"
MCP_TOOL_MODE=full python -m database --test-tools | grep "Available tools:"
```

## Integration Examples

### Jupyter Notebook Integration

```python
# notebook_helper.py
import requests
import pandas as pd

class DatabaseMCP:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
    
    def query(self, sql):
        response = requests.post(
            f"{self.base_url}/tools/call",
            json={"name": "execute_query", "arguments": {"sql": sql}}
        )
        data = response.json()
        if data.get('success'):
            return pd.DataFrame(data['data'])
        else:
            raise Exception(f"Query failed: {data.get('error')}")
    
    def get_tables(self, database=None):
        response = requests.post(
            f"{self.base_url}/tools/call", 
            json={"name": "get_tables", "arguments": {"database_name": database}}
        )
        return response.json()

# Usage in Jupyter
db = DatabaseMCP()
sales_data = db.query("SELECT * FROM sales WHERE date >= '2024-01-01'")
sales_data.head()
```

### Docker Compose Example

```yaml
# docker-compose.yml
version: '3.8'
services:
  database-mcp:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_USER=app_user
      - DATABASE_PASSWORD=app_password
      - DATABASE_HOST=mysql
      - SERVER_TRANSPORT_MODE=streamable-http
      - MCP_TOOL_MODE=full
    depends_on:
      - mysql
    
  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=root_password
      - MYSQL_DATABASE=app_db
      - MYSQL_USER=app_user  
      - MYSQL_PASSWORD=app_password
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

These examples should provide comprehensive guidance for using the Database MCP Server in various scenarios. For additional help, see the [Configuration Guide](CONFIGURATION.md) and [Environment Variables Reference](ENVIRONMENT.md).
