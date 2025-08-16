# Environment Configuration

This document provides a comprehensive reference for all environment variables supported by the Database MCP Server.

## Quick Start (Minimal Configuration)

⚡ **Only 2 variables are required!** Create a `.env` file in the database directory:

```bash
# Database credentials - ONLY THESE ARE REQUIRED
DATABASE_USER=your_username
DATABASE_PASSWORD=your_password
```

That's it! All other settings have sensible defaults. The server will:
- Connect to `localhost:3306` 
- Use `stdio` transport (perfect for Cursor/Copilot)
- Enable `lite` mode with 8 core tools
- Use secure connection pooling

## Tool Mode Configuration

🎯 **NEW: Control Tool Complexity**

```bash
# Tool set configuration
MCP_TOOL_MODE=lite              # lite = 8 core tools (recommended for AI clients)
                                # full = 22 tools (enterprise/power users)
```

**Recommendation:** Use `lite` mode for Cursor/Copilot/Windsurf to avoid overwhelming the AI with too many tools.

## Complete Environment Variable Reference

### Database Connection (Required)

```bash
# Database credentials (REQUIRED)
DATABASE_USER=your_username      # MySQL/MariaDB username
DATABASE_PASSWORD=your_password  # MySQL/MariaDB password

# Connection details (optional - defaults shown)
DATABASE_HOST=localhost          # Database server host
DATABASE_PORT=3306              # Database server port  
DATABASE_DATABASE=              # Default database (leave empty for any database)
DATABASE_CHARSET=utf8mb4        # Character set for connections
```

### Connection Pool Configuration

```bash
# Pool sizing
DATABASE_POOL_MINSIZE=1         # Minimum connections to maintain
DATABASE_POOL_MAXSIZE=10        # Maximum connections allowed
DATABASE_POOL_RECYCLE=3600      # Pool connection recycle time (-1 for no recycle)

# Connection timeouts (seconds)
DATABASE_CONNECT_TIMEOUT=10.0   # Connection establishment timeout
DATABASE_READ_TIMEOUT=30.0      # Query read timeout
DATABASE_WRITE_TIMEOUT=30.0     # Query write timeout

# Query limits
DATABASE_MAX_QUERY_LENGTH=1048576  # Maximum query size (1MB)
DATABASE_QUERY_TIMEOUT=60.0        # Query execution timeout
DATABASE_MAX_ROWS_LIMIT=10000      # Maximum rows to return
```

### SSL/TLS Configuration

```bash
# SSL settings (recommended for production)
DATABASE_USE_SSL=false                    # Enable SSL/TLS encryption
DATABASE_SSL_CA=/path/to/ca.pem          # Certificate Authority file
DATABASE_SSL_CERT=/path/to/client-cert.pem  # Client certificate
DATABASE_SSL_KEY=/path/to/client-key.pem    # Client private key  
DATABASE_VERIFY_SSL=true                 # Verify SSL certificates
```

### Server Configuration

```bash
# Transport mode (how clients connect)
SERVER_TRANSPORT_MODE=stdio      # stdio (default), sse, streamable-http, auto
                                # stdio: For Cursor/Copilot via uvx command
                                # streamable-http: For MCP Inspector/HTTP clients
                                # sse: Server-Sent Events transport
                                # auto: Auto-detect based on environment

# HTTP server settings (only for sse/streamable-http modes)
SERVER_HOST=localhost           # Host to bind to (0.0.0.0 for all interfaces)
SERVER_PORT=8080               # Port for HTTP transports
SERVER_DEBUG=false             # Enable debug mode

# SSE-specific settings
SERVER_SSE_PATH=/sse           # SSE endpoint path
SERVER_SSE_MESSAGES_PATH=/messages  # SSE messages endpoint

# CORS settings
SERVER_ENABLE_CORS=true        # Enable CORS for HTTP transports
SERVER_ALLOWED_ORIGINS=["*"]   # Allowed origins (JSON array format)

# Health check
SERVER_ENABLE_HEALTH_CHECK=true    # Enable /health endpoint
SERVER_HEALTH_CHECK_PATH=/health   # Health check path
```

### MCP Server Settings

```bash
# Server identification
MCP_SERVER_NAME=database-mcp    # MCP server name
MCP_SERVER_VERSION=1.0.0        # MCP server version

# 🎯 Tool configuration (NEW)
MCP_TOOL_MODE=lite              # lite (8 tools) or full (22 tools)

# Feature toggles
MCP_ENABLE_QUERY_EXECUTION=true      # Allow SQL query execution
MCP_ENABLE_SCHEMA_INTROSPECTION=true # Allow schema browsing
MCP_ENABLE_QUERY_EXPLAIN=true       # Allow query EXPLAIN

# Safety settings
MCP_READONLY_MODE=false              # Read-only mode (SELECT only)
MCP_ALLOWED_QUERY_TYPES=["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"]  # Allowed queries (JSON array)

# Rate limiting
MCP_ENABLE_RATE_LIMITING=true       # Enable rate limiting
MCP_MAX_QUERIES_PER_MINUTE=100      # Queries per minute limit
```

### Security Settings

```bash
# SQL injection protection
SECURITY_ENABLE_INJECTION_DETECTION=true  # Detect malicious queries
SECURITY_BLOCK_DANGEROUS_QUERIES=true     # Block dangerous operations
SECURITY_AUDIT_LOGGING=true               # Security audit logging

# Access control
SECURITY_ENABLE_IP_WHITELIST=false        # IP address restrictions
SECURITY_ALLOWED_IPS=127.0.0.1,192.168.1.0/24  # Allowed IPs/CIDRs

# Authentication (for HTTP transports)
SECURITY_ENABLE_AUTH=false                # Basic authentication
SECURITY_USERNAME=admin                   # HTTP auth username
SECURITY_PASSWORD=secure_password         # HTTP auth password
```

### Monitoring and Metrics

```bash
# Performance monitoring
MONITORING_ENABLE_METRICS=true           # Collect performance metrics
MONITORING_METRICS_INTERVAL=60           # Collection interval (seconds)
MONITORING_ENABLE_HEALTH_CHECKS=true     # Health monitoring

# Error tracking
MONITORING_ENABLE_ERROR_TRACKING=true    # Error aggregation
MONITORING_ERROR_RETENTION_DAYS=30       # Error log retention

# Resource monitoring  
MONITORING_TRACK_MEMORY_USAGE=true       # Memory usage tracking
MONITORING_TRACK_CPU_USAGE=true          # CPU usage tracking
MONITORING_TRACK_CONNECTION_POOL=true    # Connection pool health
```

### Logging Configuration

```bash
# File logging
LOG_ENABLE_FILE_LOGGING=true     # Enable file-based logging
LOG_DIRECTORY=./logs             # Log file directory
LOG_MAX_FILE_SIZE=10MB           # Maximum log file size
LOG_BACKUP_COUNT=5               # Backup files to keep

# Log levels per component
LOG_LEVEL_DATABASE=INFO          # Database operations
LOG_LEVEL_SECURITY=WARNING       # Security events  
LOG_LEVEL_MONITORING=INFO        # Monitoring events
LOG_LEVEL_MCP=INFO               # MCP protocol
SERVER_LOG_LEVEL=INFO            # Overall server logging
```

### Advanced Configuration

```bash
# Circuit breaker pattern
CIRCUIT_BREAKER_ENABLED=true             # Circuit breaker protection
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5      # Failures before opening
CIRCUIT_BREAKER_TIMEOUT=60               # Open timeout (seconds)

# Query caching
CACHE_ENABLED=false                       # Query result caching
CACHE_TTL=300                            # Cache TTL (seconds)
CACHE_MAX_SIZE=100                       # Max cached queries

# Schema management
SCHEMA_AUTO_DISCOVERY=true               # Auto schema discovery
SCHEMA_CACHE_ENABLED=true                # Cache schema metadata
SCHEMA_CACHE_TTL=3600                    # Schema cache TTL
```

### Development and Testing

```bash
# Development features
DEV_ENABLE_QUERY_EXPLAIN=true           # Query EXPLAIN debugging
DEV_ENABLE_QUERY_PROFILING=false        # Query profiling
DEV_MOCK_DATA_ENABLED=false             # Mock data for testing

# Testing configuration
TEST_DATABASE_PREFIX=test_               # Test database prefix
TEST_ENABLE_FIXTURES=false              # Test data fixtures
```

## Configuration Examples

### 1. Minimal Setup (Cursor/Copilot)
```bash
DATABASE_USER=root
DATABASE_PASSWORD=your_password
# Uses all defaults: stdio transport, lite mode, localhost:3306
```

### 2. MCP Inspector Testing
```bash
DATABASE_USER=root  
DATABASE_PASSWORD=your_password
SERVER_TRANSPORT_MODE=streamable-http
SERVER_PORT=8080
```

### 3. Production HTTP Server
```bash
DATABASE_USER=prod_user
DATABASE_PASSWORD=secure_password
DATABASE_HOST=prod-mysql.company.com
DATABASE_USE_SSL=true
SERVER_TRANSPORT_MODE=streamable-http
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
MCP_TOOL_MODE=full
SECURITY_ENABLE_AUTH=true
SECURITY_USERNAME=api_user
SECURITY_PASSWORD=api_secure_password
```

### 4. High Security Setup
```bash
DATABASE_USER=readonly_user
DATABASE_PASSWORD=readonly_password
MCP_READONLY_MODE=true
MCP_ALLOWED_QUERY_TYPES=["SELECT", "SHOW", "DESCRIBE"]
SECURITY_ENABLE_INJECTION_DETECTION=true
SECURITY_BLOCK_DANGEROUS_QUERIES=true
MCP_ENABLE_RATE_LIMITING=true
MCP_MAX_QUERIES_PER_MINUTE=50
```

## Best Practices

1. **Start Minimal**: Only set `DATABASE_USER` and `DATABASE_PASSWORD`
2. **Use Lite Mode**: Keep `MCP_TOOL_MODE=lite` for AI clients
3. **Enable SSL**: Use `DATABASE_USE_SSL=true` in production
4. **Secure Credentials**: Use environment variables, not hardcoded values
5. **Monitor Resources**: Enable monitoring for production deployments
6. **Rate Limiting**: Enable rate limiting to prevent abuse
7. **Audit Logging**: Enable security audit logging for compliance

## Migration from Old Configuration

If upgrading from older versions, update these prefixes:

| Old Prefix | New Prefix | Example |
|------------|------------|---------|
| `DB_*` | `DATABASE_*` | `DB_HOST` → `DATABASE_HOST` |
| `SERVER_TRANSPORT` | `SERVER_TRANSPORT_MODE` | Update variable name |

The old configuration will continue to work but is deprecated.
