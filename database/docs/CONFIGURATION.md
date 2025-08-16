# Configuration Guide

This guide explains how to configure the Database MCP Server for different use cases, from minimal development setups to enterprise production deployments.

## Quick Start Configuration

### Minimal Setup (Recommended)

For most users, only 2 environment variables are required:

```bash
# .env file
DATABASE_USER=your_username
DATABASE_PASSWORD=your_password
```

This minimal configuration provides:
- ✅ Connection to `localhost:3306`
- ✅ `stdio` transport (perfect for Cursor/Copilot)
- ✅ `lite` mode with 8 core tools
- ✅ Secure connection pooling
- ✅ All security features enabled

### Tool Mode Configuration

🎯 **Control Tool Complexity for AI Clients**

```bash
# For AI clients (Cursor/Copilot/Windsurf) - RECOMMENDED
MCP_TOOL_MODE=lite

# For enterprise/power users
MCP_TOOL_MODE=full
```

**Tool Mode Comparison:**

| Mode | Tools | Use Case | Recommendation |
|------|-------|----------|----------------|
| `lite` | 8 core tools | AI clients, development | ✅ **Recommended** |
| `full` | 22 tools | Enterprise, power users | Advanced usage only |

**Lite Mode Tools:**
1. `execute_query` - SQL execution
2. `get_databases` - Database discovery
3. `get_tables` - Table listing
4. `get_table_details` - Table structure
5. `explain_query` - Query optimization
6. `health_check` - Connection status
7. `connection_stats` - Pool statistics
8. `schema_info` - Schema overview

## Transport Mode Configuration

Choose how clients connect to your MCP server:

### 1. Stdio Transport (Default)
**Perfect for Cursor/Copilot integration**

```bash
# Default - no configuration needed
SERVER_TRANSPORT_MODE=stdio
```

**Usage:**
```bash
python -m database
# or
uvx database-mcp
```

### 2. Streamable HTTP Transport
**Perfect for MCP Inspector and HTTP clients**

```bash
SERVER_TRANSPORT_MODE=streamable-http
SERVER_HOST=localhost
SERVER_PORT=8080
```

**Usage:**
```bash
python -m database --transport streamable-http
```

### 3. SSE Transport
**For Server-Sent Events clients**

```bash
SERVER_TRANSPORT_MODE=sse
SERVER_HOST=localhost
SERVER_PORT=8080
```

### 4. Auto Transport
**Automatic detection based on environment**

```bash
SERVER_TRANSPORT_MODE=auto
```

## Database Connection Configuration

### Basic Connection

```bash
# Required
DATABASE_USER=your_username
DATABASE_PASSWORD=your_password

# Optional (defaults shown)
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_DATABASE=              # Leave empty for any database access
DATABASE_CHARSET=utf8mb4
```

### SSL/TLS Configuration

**Recommended for production:**

```bash
DATABASE_USE_SSL=true
DATABASE_SSL_CA=/path/to/ca.pem
DATABASE_SSL_CERT=/path/to/client-cert.pem
DATABASE_SSL_KEY=/path/to/client-key.pem
DATABASE_VERIFY_SSL=true
```

### Connection Pool Tuning

```bash
# Default settings work for most use cases
DATABASE_POOL_MINSIZE=1          # Minimum connections
DATABASE_POOL_MAXSIZE=10         # Maximum connections
DATABASE_POOL_RECYCLE=3600       # Connection lifetime (seconds)

# Timeouts
DATABASE_CONNECT_TIMEOUT=10.0    # Connection timeout
DATABASE_READ_TIMEOUT=30.0       # Read timeout
DATABASE_WRITE_TIMEOUT=30.0      # Write timeout

# Query limits
DATABASE_MAX_QUERY_LENGTH=1048576   # 1MB query limit
DATABASE_QUERY_TIMEOUT=60.0         # Query timeout
DATABASE_MAX_ROWS_LIMIT=10000       # Row limit per query
```

## Security Configuration

### Basic Security (Default)

```bash
# Feature toggles (all enabled by default)
MCP_ENABLE_QUERY_EXECUTION=true
MCP_ENABLE_SCHEMA_INTROSPECTION=true
MCP_ENABLE_QUERY_EXPLAIN=true

# Safety settings
MCP_READONLY_MODE=false
MCP_ALLOWED_QUERY_TYPES=["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"]

# Rate limiting (enabled by default)
MCP_ENABLE_RATE_LIMITING=true
MCP_MAX_QUERIES_PER_MINUTE=100
```

### Enhanced Security

```bash
# SQL injection protection
SECURITY_ENABLE_INJECTION_DETECTION=true
SECURITY_BLOCK_DANGEROUS_QUERIES=true
SECURITY_AUDIT_LOGGING=true

# Read-only mode
MCP_READONLY_MODE=true
MCP_ALLOWED_QUERY_TYPES=["SELECT", "SHOW", "DESCRIBE"]

# Stricter rate limiting
MCP_MAX_QUERIES_PER_MINUTE=50
```

### HTTP Authentication

**For HTTP transports only:**

```bash
SECURITY_ENABLE_AUTH=true
SECURITY_USERNAME=api_user
SECURITY_PASSWORD=secure_password
```

### IP Restrictions

```bash
SECURITY_ENABLE_IP_WHITELIST=true
SECURITY_ALLOWED_IPS=127.0.0.1,192.168.1.0/24
```

## Monitoring Configuration

### Basic Monitoring (Default)

```bash
MONITORING_ENABLE_METRICS=true
MONITORING_ENABLE_HEALTH_CHECKS=true
MONITORING_ENABLE_ERROR_TRACKING=true
```

### Advanced Monitoring

```bash
# Performance monitoring
MONITORING_METRICS_INTERVAL=60
MONITORING_TRACK_MEMORY_USAGE=true
MONITORING_TRACK_CPU_USAGE=true
MONITORING_TRACK_CONNECTION_POOL=true

# Error tracking
MONITORING_ERROR_RETENTION_DAYS=30
```

## Logging Configuration

### File Logging (Recommended)

```bash
LOG_ENABLE_FILE_LOGGING=true
LOG_DIRECTORY=./logs
LOG_MAX_FILE_SIZE=10MB
LOG_BACKUP_COUNT=5
```

### Log Levels

```bash
# Component-specific log levels
LOG_LEVEL_DATABASE=INFO
LOG_LEVEL_SECURITY=WARNING
LOG_LEVEL_MONITORING=INFO
LOG_LEVEL_MCP=INFO
SERVER_LOG_LEVEL=INFO
```

### Development Logging

```bash
SERVER_LOG_LEVEL=DEBUG
LOG_LEVEL_DATABASE=DEBUG
SERVER_DEBUG=true
```

## Configuration Examples by Use Case

### 1. Development (Cursor/Copilot)

**Perfect for local development with AI assistants:**

```bash
# .env file
DATABASE_USER=root
DATABASE_PASSWORD=dev_password

# Optional overrides
MCP_TOOL_MODE=lite
SERVER_TRANSPORT_MODE=stdio
SERVER_LOG_LEVEL=INFO
```

**Benefits:**
- ✅ Minimal configuration
- ✅ 8 focused tools for AI clients
- ✅ Fast local connections
- ✅ Comprehensive logging

### 2. Testing (MCP Inspector)

**For testing with MCP Inspector:**

```bash
# .env file  
DATABASE_USER=test_user
DATABASE_PASSWORD=test_password
SERVER_TRANSPORT_MODE=streamable-http
SERVER_PORT=8080
MCP_TOOL_MODE=full

# Optional testing features
SERVER_DEBUG=true
SERVER_LOG_LEVEL=DEBUG
```

### 3. Production HTTP Server

**Enterprise deployment with all features:**

```bash
# .env file
DATABASE_USER=prod_user
DATABASE_PASSWORD=secure_production_password
DATABASE_HOST=prod-mysql.company.com
DATABASE_USE_SSL=true
DATABASE_SSL_CA=/etc/ssl/ca.pem
DATABASE_SSL_CERT=/etc/ssl/client-cert.pem
DATABASE_SSL_KEY=/etc/ssl/client-key.pem

# Server configuration
SERVER_TRANSPORT_MODE=streamable-http
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
MCP_TOOL_MODE=full

# Security
SECURITY_ENABLE_AUTH=true
SECURITY_USERNAME=api_user
SECURITY_PASSWORD=api_secure_password
SECURITY_ENABLE_INJECTION_DETECTION=true
SECURITY_BLOCK_DANGEROUS_QUERIES=true

# Performance
DATABASE_POOL_MAXSIZE=20
MCP_MAX_QUERIES_PER_MINUTE=200

# Monitoring
MONITORING_ENABLE_METRICS=true
LOG_ENABLE_FILE_LOGGING=true
```

### 4. High Security Setup

**Maximum security for sensitive environments:**

```bash
# .env file
DATABASE_USER=readonly_user
DATABASE_PASSWORD=readonly_secure_password

# Security settings
MCP_READONLY_MODE=true
MCP_ALLOWED_QUERY_TYPES=["SELECT", "SHOW", "DESCRIBE"]
SECURITY_ENABLE_INJECTION_DETECTION=true
SECURITY_BLOCK_DANGEROUS_QUERIES=true
SECURITY_AUDIT_LOGGING=true

# IP restrictions
SECURITY_ENABLE_IP_WHITELIST=true
SECURITY_ALLOWED_IPS=192.168.1.0/24

# Rate limiting
MCP_ENABLE_RATE_LIMITING=true
MCP_MAX_QUERIES_PER_MINUTE=50

# Tool restriction
MCP_TOOL_MODE=lite
```

### 5. Development Team Setup

**For development teams with multiple databases:**

```bash
# .env file
DATABASE_USER=dev_team_user
DATABASE_PASSWORD=team_password
DATABASE_HOST=dev-mysql.company.com

# Flexible database access
DATABASE_DATABASE=              # Access any database

# Moderate security
MCP_TOOL_MODE=full
MCP_READONLY_MODE=false
MCP_ALLOWED_QUERY_TYPES=["SELECT", "INSERT", "UPDATE", "DELETE", "SHOW", "DESCRIBE", "EXPLAIN"]

# Team-friendly settings
MCP_MAX_QUERIES_PER_MINUTE=200
DATABASE_POOL_MAXSIZE=15
```

## Advanced Configuration

### Circuit Breaker Pattern

```bash
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60
```

### Query Caching

```bash
CACHE_ENABLED=true
CACHE_TTL=300
CACHE_MAX_SIZE=100
```

### Schema Management

```bash
SCHEMA_AUTO_DISCOVERY=true
SCHEMA_CACHE_ENABLED=true
SCHEMA_CACHE_TTL=3600
```

## Configuration Validation

### Testing Your Configuration

```bash
# Test basic connectivity
python -m database --test-tools

# Test specific transport mode
python -m database --transport streamable-http --test-tools

# Check configuration and logs
python -m database --transport stdio
```

### Health Checks

The server provides health check endpoints:

```bash
# For HTTP transports
curl http://localhost:8080/health

# Returns JSON with connection status, pool health, etc.
```

### CLI Testing Mode

```bash
# Interactive testing
python -m database --test-tools

# Test specific query
python -m database --test-query "SHOW DATABASES"
```

## Best Practices

### 1. Start Simple
- Begin with minimal configuration (just username/password)
- Add complexity only as needed
- Use `lite` mode for AI clients

### 2. Security
- Enable SSL/TLS in production
- Use read-only users when possible
- Enable rate limiting and audit logging
- Regularly rotate credentials

### 3. Performance
- Monitor connection pool usage
- Tune timeouts based on your queries
- Use caching for frequently accessed data
- Set appropriate query limits

### 4. Monitoring
- Enable file logging in production
- Set up health checks
- Monitor error rates and performance metrics
- Use structured logging for analysis

### 5. Environment Management
- Use separate configurations for dev/staging/production
- Never commit `.env` files to version control
- Use environment-specific credentials
- Document your configuration choices

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check database host and port
   DATABASE_HOST=localhost
   DATABASE_PORT=3306
   ```

2. **Access Denied**
   ```bash
   # Verify credentials
   DATABASE_USER=correct_username
   DATABASE_PASSWORD=correct_password
   ```

3. **Too Many Tools in AI Client**
   ```bash
   # Use lite mode
   MCP_TOOL_MODE=lite
   ```

4. **HTTP Transport Not Working**
   ```bash
   # Check transport mode and port
   SERVER_TRANSPORT_MODE=streamable-http
   SERVER_PORT=8080
   ```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
SERVER_DEBUG=true
SERVER_LOG_LEVEL=DEBUG
LOG_LEVEL_DATABASE=DEBUG
```

## Migration Guide

### From Older Versions

If upgrading from older versions, update these settings:

| Old Setting | New Setting | Notes |
|-------------|-------------|-------|
| `DB_*` | `DATABASE_*` | All database variables |
| `SERVER_TRANSPORT` | `SERVER_TRANSPORT_MODE` | Variable name change |
| No tool mode | `MCP_TOOL_MODE=lite` | New feature |

### Configuration File Migration

```bash
# Old .env format
DB_HOST=localhost
DB_USER=username
SERVER_TRANSPORT=auto

# New .env format  
DATABASE_HOST=localhost
DATABASE_USER=username
SERVER_TRANSPORT_MODE=stdio
MCP_TOOL_MODE=lite
```

The old format will continue to work but is deprecated.
