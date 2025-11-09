# Database MCP - Docker Image

## 📦 Overview

Docker image for the Database MCP server, providing MySQL/MariaDB database operations via MCP protocol. Includes connection pooling, query execution, schema analysis, and monitoring tools.

**Base Image**: `sanjibdevnath/mcp-base:${BASE_TAG}`  
**Transports**: SSE, Streamable-HTTP  
**Exposed Ports**: 8086 (SSE), 8087 (HTTP)  
**External Dependencies**: MySQL 8.0+ or MariaDB 10.5+

---

## 🏗️ Build Instructions

### Using Makefile (Recommended)

```bash
# Build base image first (if not already built)
make docker-build-base

# Build database image
make docker-build-database
```

### Manual Build

```bash
# From repository root
docker build -f database/docker/Dockerfile \
  --build-arg BASE_TAG=local-dev \
  -t mcp-database:local .
```

---

## 🚀 Running the Container

### With Docker Compose (Recommended)

```bash
# Includes MySQL service automatically
cd database/deployment/local
docker-compose up -d
```

This starts:
- `database-sse`: SSE transport on port 8086
- `database-http`: HTTP transport on port 8087
- `mysql`: MySQL 8.0 on port 3306

### Manual Run (Requires External MySQL)

```bash
# SSE transport
docker run -p 8086:8086 \
  -e TRANSPORT_MODE=sse \
  -e DB_HOST=host.docker.internal \
  -e DB_PORT=3306 \
  -e DB_USER=root \
  -e DB_PASSWORD=your_password \
  -e DB_DATABASE=mcp_db \
  mcp-database:local

# HTTP transport
docker run -p 8087:8087 \
  -e TRANSPORT_MODE=streamable-http \
  -e FASTMCP_PORT=8087 \
  -e DB_HOST=host.docker.internal \
  -e DB_PORT=3306 \
  -e DB_USER=root \
  -e DB_PASSWORD=your_password \
  -e DB_DATABASE=mcp_db \
  mcp-database:local
```

---

## ⚙️ Environment Variables

### Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `docker` | Application environment (loads `environment/docker.toml`) |
| `TRANSPORT_MODE` | `sse` | Transport protocol: `sse` or `streamable-http` |
| `FASTMCP_HOST` | `0.0.0.0` | Server bind address |
| `FASTMCP_PORT` | `8086` | Server port (8086 for SSE, 8087 for HTTP) |
| `LOG_LEVEL` | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `LOG_FORMAT` | `json` | Log format: `text` or `json` (docker.toml sets to `json`) |

### Database Configuration

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `DB_HOST` | `mysql` | MySQL host | ✅ Yes |
| `DB_PORT` | `3306` | MySQL port | ✅ Yes |
| `DB_USER` | `mcp_user` | Database user | ✅ Yes |
| `DB_PASSWORD` | - | Database password | ✅ Yes |
| `DB_DATABASE` | `mcp_db` | Database name | ✅ Yes |
| `DB_POOL_SIZE` | `10` | Connection pool size | No |
| `DB_POOL_TIMEOUT` | `30` | Pool timeout (seconds) | No |

**Note**: MySQL 8.0 requires the `cryptography` package for authentication (included in base image).

---

## 🏷️ Image Labels

```dockerfile
LABEL mcp.name="database"
LABEL mcp.version="1.0.0"
LABEL mcp.transports="sse,streamable-http"
```

Query labels:
```bash
docker inspect mcp-database:local | jq '.[0].Config.Labels'
```

---

## 📂 Image Contents

```
/app/
├── database/            # Database MCP code
│   ├── main.py
│   ├── config/
│   ├── environment/
│   ├── src/            # Core database logic
│   │   ├── server.py
│   │   ├── database_manager.py
│   │   ├── query_executor.py
│   │   └── schema_analyzer.py
│   └── tests/
├── shared/             # Shared modules (logging, config)
│   ├── config/
│   └── logging/
└── tests/              # E2E tests
    └── test_e2e_database.py
```

---

## 🔍 Debugging

```bash
# View logs
docker logs database-sse -f

# Shell into container
docker exec -it database-sse /bin/bash

# Test database connection
docker exec database-sse python -c "
from database.config import config
print(f'DB Host: {config.database.host}')
print(f'DB Port: {config.database.port}')
print(f'DB User: {config.database.user}')
print(f'DB Name: {config.database.database}')
"

# Test MySQL connectivity
docker exec database-sse python -c "
import aiomysql
import asyncio

async def test():
    conn = await aiomysql.connect(
        host='mysql',
        port=3306,
        user='root',
        password='testpassword',
        db='mcp_db'
    )
    async with conn.cursor() as cur:
        await cur.execute('SELECT VERSION()')
        result = await cur.fetchone()
        print(f'MySQL Version: {result[0]}')
    conn.close()

asyncio.run(test())
"
```

---

## 🧪 Testing

```bash
# Run E2E tests (requires MySQL running)
pytest tests/test_e2e_database.py -v

# Test specific transport
pytest tests/test_e2e_database.py::TestDatabaseSSE -v
pytest tests/test_e2e_database.py::TestDatabaseHTTP -v

# Test specific tools
pytest tests/test_e2e_database.py::TestDatabaseSSE::test_sse_get_databases -v
pytest tests/test_e2e_database.py::TestDatabaseSSE::test_sse_execute_query -v
```

---

## 📊 Health Check

The image includes a TCP-based health check (configured in docker-compose):

```bash
# Manual health check
python -c "import socket; s=socket.socket(); s.connect(('localhost',8086)); s.close()"
```

---

## 🛠️ Available Tools

The database MCP provides 21 tools:

**Query Operations:**
- `execute_query` - Execute SQL queries
- `get_databases` - List all databases
- `get_tables` - List tables in database
- `get_table_details` - Get table schema
- `explain_query` - Explain query execution plan

**Schema Management:**
- `schema_info` - Get schema information
- `create_schema_snapshot` - Create schema snapshot
- `export_schema` - Export schema
- `analyze_schema` - Analyze schema structure
- `table_info` - Get table details

**Monitoring:**
- `health_check` - Check database health
- `connection_stats` - Connection pool stats
- `performance_metrics` - Performance metrics
- `system_metrics` - System metrics
- `monitoring_status` - Monitoring status

**Error Handling:**
- `error_summary` - Error summary
- `error_handling_status` - Error handling status
- `circuit_breaker_status` - Circuit breaker status
- `service_degradation_status` - Service degradation status

**Export:**
- `export_metrics` - Export all metrics
- `security_status` - Security status

---

## 🐳 Image Size

- **Base Image**: ~1GB (shared across all MCPs)
- **Database Layer**: ~10MB (database code + dependencies)
- **Total**: ~1GB (but base is cached and reused)

---

## ⚠️ Important Notes

1. **MySQL Authentication**: Requires `cryptography` package (included in base image)
2. **Connection Pooling**: Uses lazy initialization (pool created on first use)
3. **Network**: Container must be able to reach MySQL host
4. **Credentials**: Use environment variables, never hardcode

---

## 🔗 Related Documentation

- [Deployment Guide](../deployment/local/README.md) - Local development with docker-compose
- [Main README](../../README.md) - Database MCP overview
- [GitOps Documentation](../../../docs/) - CI/CD and infrastructure
