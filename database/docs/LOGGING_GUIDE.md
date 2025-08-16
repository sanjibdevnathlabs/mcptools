# 📊 Database MCP - Advanced Logging System

## Overview

The Database MCP now features a production-grade logging system with:

- **JSON structured logging** for better parsing and analysis
- **Trace code based messages** for consistent debugging 
- **Configurable output destinations** (file, stdout, stderr, both)
- **Automatic trace ID generation** for request tracking
- **Single file logging** with rotation (no more multiple files)
- **K8s/Fluentbit ready** for container deployments

## Quick Setup

### Basic Configuration (Default)
```bash
# Only these lines in your .env - everything else uses sensible defaults
DATABASE_USER=your_username
DATABASE_PASSWORD=your_password
```

### Advanced Logging Configuration
```bash
# Logging format and destination
SERVER_LOG_FORMAT=json                    # json or text
SERVER_LOG_DESTINATION=file              # file, stdout, stderr, both
SERVER_LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL

# File settings (when using file destination)
SERVER_LOG_FILE_PATH=./logs/database_mcp.log
SERVER_LOG_MAX_FILE_SIZE=100MB
SERVER_LOG_BACKUP_COUNT=5

# Advanced features
SERVER_LOG_INCLUDE_TRACE_ID=true         # Include trace IDs
SERVER_LOG_INCLUDE_TIMESTAMP=true        # Include timestamps
```

## Trace Code Format

All log messages use **trace codes** for consistent identification:

```python
logger.info("TRACE_CODE", {"key": "value"})
logger.error("ERROR_CODE", {"error": "details"}, exc_info=True)
```

### Common Trace Codes

| Code | Level | Description |
|------|-------|-------------|
| `SERVER_STARTING` | INFO | Server initialization |
| `DATABASE_CONNECT` | INFO | Database connection established |
| `QUERY_EXECUTE` | INFO | SQL query execution |
| `QUERY_ERROR` | ERROR | SQL query failed |
| `AUTH_FAILURE` | ERROR | Authentication failure |
| `RATE_LIMIT_HIT` | WARNING | Rate limit exceeded |

## JSON Log Format

### Successful Operation
```json
{
  "trace_code": "QUERY_EXECUTE",
  "trace_id": "a1b2c3d4", 
  "logger_name": "database.server",
  "level": "INFO",
  "timestamp": "2025-08-17T00:13:15.738Z",
  "sql": "SELECT * FROM users WHERE id = ?",
  "duration_ms": 45,
  "rows_returned": 1
}
```

### Error with Context
```json
{
  "trace_code": "DATABASE_ERROR",
  "trace_id": "a1b2c3d4",
  "logger_name": "database.manager", 
  "level": "ERROR",
  "timestamp": "2025-08-17T00:13:15.738Z",
  "error": "Table 'test.nonexistent' doesn't exist",
  "error_type": "ProgrammingError",
  "sql": "SELECT * FROM nonexistent",
  "exception": "Traceback (most recent call last)..."
}
```

## Deployment Scenarios

### 1. Development (Text Format)
```bash
SERVER_LOG_FORMAT=text
SERVER_LOG_DESTINATION=stdout
SERVER_LOG_LEVEL=DEBUG
```

### 2. Production (JSON + File)
```bash
SERVER_LOG_FORMAT=json
SERVER_LOG_DESTINATION=file
SERVER_LOG_LEVEL=INFO
SERVER_LOG_FILE_PATH=/var/log/database_mcp.log
```

### 3. Kubernetes (Stdout for Fluentbit)
```bash
SERVER_LOG_FORMAT=json
SERVER_LOG_DESTINATION=stdout
SERVER_LOG_LEVEL=INFO
```

### 4. Hybrid (Console + File)
```bash
SERVER_LOG_FORMAT=json
SERVER_LOG_DESTINATION=both
SERVER_LOG_LEVEL=INFO
```

## Log Analysis Examples

### Finding All Errors
```bash
# Using jq to filter JSON logs
cat logs/database_mcp.log | jq 'select(.level == "ERROR")'
```

### Tracking a Request
```bash
# Follow a specific trace ID
cat logs/database_mcp.log | jq 'select(.trace_id == "a1b2c3d4")'
```

### Query Performance Analysis
```bash
# Find slow queries (>1000ms)
cat logs/database_mcp.log | jq 'select(.trace_code == "QUERY_EXECUTE" and .duration_ms > 1000)'
```

## Integration with Log Aggregation

### Fluentbit Configuration
```ini
[INPUT]
    Name tail
    Path /var/log/database_mcp.log
    Parser json
    Tag database.mcp

[OUTPUT]
    Name elasticsearch
    Match database.*
    Host elasticsearch.default.svc.cluster.local
    Port 9200
    Index database-mcp
```

### Filebeat Configuration
```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/database_mcp.log
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "database-mcp-%{+yyyy.MM.dd}"
```

## Code Usage Examples

### Basic Logging
```python
from logging_config import get_logger, generate_trace_id

logger = get_logger('server')
trace_id = generate_trace_id()

logger.info("OPERATION_START", {
    "operation": "user_query",
    "user_id": "user123"
})
```

### Error Handling
```python
try:
    result = await database.execute(sql)
    logger.info("QUERY_SUCCESS", {
        "sql": sql,
        "rows": len(result),
        "duration_ms": duration
    })
except Exception as e:
    logger.error("QUERY_FAILED", {
        "sql": sql,
        "error": str(e),
        "error_type": type(e).__name__
    }, exc_info=True)
```

### Performance Monitoring
```python
import time

start_time = time.time()
try:
    result = await expensive_operation()
    duration = (time.time() - start_time) * 1000
    
    logger.info("OPERATION_COMPLETE", {
        "operation": "expensive_task",
        "duration_ms": duration,
        "success": True
    })
except Exception as e:
    duration = (time.time() - start_time) * 1000
    logger.error("OPERATION_FAILED", {
        "operation": "expensive_task", 
        "duration_ms": duration,
        "error": str(e)
    }, exc_info=True)
```

## Migration from Old System

The new system is **backwards compatible**. Old `logger.info("message")` calls still work but will be formatted as:

```json
{
  "message": "old style message",
  "level": "INFO",
  "logger_name": "database.server",
  "timestamp": "2025-08-17T00:13:15.738Z",
  "trace_id": "auto-generated"
}
```

## Benefits

1. **🔍 Better Debugging**: Trace codes make finding specific events instant
2. **📊 Analytics Ready**: JSON format works with ELK, Grafana, etc.
3. **🚀 Production Ready**: Structured logging scales with your infrastructure
4. **🔗 Request Tracking**: Trace IDs connect related log entries
5. **🛠️ DevOps Friendly**: Single file, configurable destinations
6. **☁️ Cloud Native**: Works seamlessly with K8s logging pipelines

## Testing the System

```bash
# Test with different formats
python -m database --test-tools

# View JSON logs
tail -f logs/database_mcp.log | jq '.'

# View text logs  
SERVER_LOG_FORMAT=text python -m database --test-tools
```
