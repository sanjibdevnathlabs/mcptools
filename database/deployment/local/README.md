# Database MCP - Local Development

## 📦 Overview

Local development environment for Database MCP using Docker Compose. Includes MySQL 8.0 database and runs both SSE and HTTP transports simultaneously, with **automatic test execution**.

**Services:**
- `mysql` - MySQL 8.0 database on port 3306
- `database-sse` - SSE transport on port 8086
- `database-http` - HTTP transport on port 8087
- `database-test` - Automatic quality checks + tests (runs once, exits with status code)

---

## 🚀 Quick Start

```bash
# From this directory
docker-compose up -d

# Or from repository root
make docker-compose-up-database

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 📋 Prerequisites

1. **Docker** (20.10+) and **Docker Compose** (2.0+)
2. **Base image built**:
   ```bash
   cd ../../..  # Go to repo root
   make docker-build-base
   ```

---

## ⚙️ Configuration

### Docker Compose Services

| Service | Port | Transport | Container Name | Health Check | Depends On | Image |
|---------|------|-----------|----------------|--------------|------------|-------|
| `mysql` | 3306 | - | `mysql-mcp` | ✅ mysqladmin ping | - | `mysql:8.0` |
| `database-sse` | 8086 | SSE | `database-sse` | ✅ TCP port check | mysql | `mcp-database:local-sse` |
| `database-http` | 8087 | HTTP | `database-http` | ✅ TCP port check | mysql | `mcp-database:local-http` |
| `database-test` | - | N/A | `database-test` | N/A (exits after tests) | mysql | `mcp-database:test` |

**Test Service Behavior:**
- Runs automatically with `docker-compose up`
- Executes: black → ruff → mypy → pytest (191 tests)
- Exits with code 0 (success) or non-zero (failure)
- Status visible with: `docker ps -a --filter "name=database-test"`

### Environment Variables

#### MySQL Service

```yaml
MYSQL_ROOT_PASSWORD: testpassword   # Root password
MYSQL_DATABASE: mcp_db              # Default database
MYSQL_USER: mcp_user               # Additional user (optional)
MYSQL_PASSWORD: testpassword       # User password (optional)
```

#### Database MCP Services

```yaml
APP_ENV: docker                     # Loads environment/docker.toml
TRANSPORT_MODE: sse|streamable-http # Transport protocol
FASTMCP_HOST: 0.0.0.0              # Bind to all interfaces
FASTMCP_PORT: 8086|8087            # Port number
LOG_LEVEL: DEBUG                    # Logging level

# Database connection
DB_HOST: mysql                      # MySQL container hostname
DB_PORT: 3306                       # MySQL port
DB_USER: root                       # Database user
DB_PASSWORD: testpassword           # Database password
DB_DATABASE: mcp_db                 # Database name
```

**Overriding Variables:**

Create a `.env` file in this directory:

```bash
# .env
MYSQL_ROOT_PASSWORD=mypassword
DB_PASSWORD=mypassword
LOG_LEVEL=INFO
```

Or use environment variables:

```bash
MYSQL_ROOT_PASSWORD=mypassword docker-compose up -d
```

---

## 🧪 Testing

### Using MCP Inspector

1. **Start services:**
   ```bash
   docker-compose up -d
   
   # Wait for MySQL to be ready (check health)
   docker-compose ps
   ```

2. **Test SSE transport:**
   - Open MCP Inspector: http://localhost:6274/
   - URL: `http://localhost:8086/sse`
   - Test tools: `get_databases`, `execute_query`

3. **Test HTTP transport:**
   - Open MCP Inspector: http://localhost:6274/
   - URL: `http://localhost:8087/mcp`
   - Test tools: `get_databases`, `execute_query`

### Using E2E Tests

```bash
# From repository root
pytest tests/test_e2e_database.py -v

# Test specific transport
pytest tests/test_e2e_database.py::TestDatabaseSSE -v
pytest tests/test_e2e_database.py::TestDatabaseHTTP -v

# Test specific tools
pytest tests/test_e2e_database.py::TestDatabaseSSE::test_sse_execute_query -v
pytest tests/test_e2e_database.py::TestDatabaseSSE::test_sse_get_databases -v
```

### Using MySQL Client

```bash
# Connect to MySQL directly
docker exec -it mysql mysql -uroot -ptestpassword mcp_db

# Or from host (if mysql client installed)
mysql -h 127.0.0.1 -P 3306 -uroot -ptestpassword mcp_db
```

### Using cURL (HTTP transport)

```bash
# Initialize session
curl -X POST http://localhost:8087/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}'

# List databases
curl -X POST http://localhost:8087/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "get_databases",
      "arguments": {}
    }
  }'

# Execute query
curl -X POST http://localhost:8087/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "execute_query",
      "arguments": {
        "query": "SHOW TABLES",
        "database": "mcp_db"
      }
    }
  }'
```

---

## 🔍 Debugging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f mysql
docker-compose logs -f database-sse
docker-compose logs -f database-http

# Last 50 lines
docker-compose logs --tail=50 database-sse
```

### Shell into Containers

```bash
# MySQL container
docker exec -it mysql /bin/bash
docker exec -it mysql mysql -uroot -ptestpassword

# SSE container
docker exec -it database-sse /bin/bash

# HTTP container
docker exec -it database-http /bin/bash

# Test database connection from MCP container
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
        print(f'✅ MySQL Version: {result[0]}')
    conn.close()

asyncio.run(test())
"
```

### Check Health

```bash
# Check all services health
docker-compose ps

# Manual MySQL health check
docker exec mysql mysqladmin ping -h localhost -uroot -ptestpassword

# Manual MCP health check
docker exec database-sse python -c "
import socket
s = socket.socket()
s.connect(('localhost', 8086))
s.close()
print('✅ Port 8086 is open')
"
```

### Network Inspection

```bash
# List networks
docker network ls | grep mcp

# Inspect network
docker network inspect mcp-local-network

# Check connectivity
docker exec database-sse ping -c 1 mysql
docker exec database-sse nc -zv mysql 3306
```

---

## 🛠️ Available Tools

The database MCP provides 21 tools organized by category:

### Query Operations (5 tools)
- `execute_query` - Execute SQL queries
- `get_databases` - List all databases
- `get_tables` - List tables in database
- `get_table_details` - Get table schema
- `explain_query` - Explain query execution plan

### Schema Management (5 tools)
- `schema_info` - Get schema information
- `create_schema_snapshot` - Create schema snapshot
- `export_schema` - Export schema
- `analyze_schema` - Analyze schema structure
- `table_info` - Get table details

### Monitoring (5 tools)
- `health_check` - Check database health
- `connection_stats` - Connection pool stats
- `performance_metrics` - Performance metrics
- `system_metrics` - System metrics
- `monitoring_status` - Monitoring status

### Error Handling (4 tools)
- `error_summary` - Error summary
- `error_handling_status` - Error handling status
- `circuit_breaker_status` - Circuit breaker status
- `service_degradation_status` - Service degradation status

### Export (2 tools)
- `export_metrics` - Export all metrics
- `security_status` - Security status

---

## 📊 Port Mapping

| Host Port | Container Port | Service | Protocol |
|-----------|---------------|---------|----------|
| 3306 | 3306 | mysql | MySQL |
| 8086 | 8086 | database-sse | SSE |
| 8087 | 8087 | database-http | HTTP |

**Avoiding Port Conflicts:**

If ports are already in use, modify `docker-compose.yml`:

```yaml
services:
  mysql:
    ports:
      - "3307:3306"  # Change host port to 3307
  
  database-sse:
    ports:
      - "9086:8086"  # Change host port to 9086
```

---

## 💾 Data Persistence

MySQL data is stored in a Docker volume:

```bash
# List volumes
docker volume ls | grep mysql

# Inspect volume
docker volume inspect database_local_mysql_data

# Backup data
docker exec mysql mysqldump -uroot -ptestpassword --all-databases > backup.sql

# Restore data
cat backup.sql | docker exec -i mysql mysql -uroot -ptestpassword

# Remove volume (WARNING: deletes all data)
docker-compose down -v
```

---

## 🧹 Cleanup

```bash
# Stop services (keeps data)
docker-compose down

# Remove volumes and data (WARNING: deletes database)
docker-compose down -v

# Remove images
docker-compose down --rmi local

# From repository root
make docker-compose-down-database
```

---

## 🔄 Rebuild After Code Changes

```bash
# Rebuild and restart MCP services only
docker-compose up -d --build database-sse database-http

# Force complete rebuild
docker-compose build --no-cache
docker-compose up -d
```

---

## 📁 File Structure

```
database/deployment/local/
├── docker-compose.yml   # Compose configuration
└── README.md           # This file

Related files:
├── ../../docker/
│   ├── Dockerfile      # Database image definition
│   └── .dockerignore   # Build exclusions
└── ../../environment/
    ├── default.toml    # Default config
    └── docker.toml     # Docker overrides
```

---

## ⚠️ Common Issues

### Issue: MySQL container keeps restarting

```
Error: MySQL container unhealthy
```

**Solution:**
```bash
# Check MySQL logs
docker-compose logs mysql

# Common causes:
# 1. Data corruption - remove volume and restart
docker-compose down -v
docker-compose up -d

# 2. Port conflict
lsof -i :3306
```

### Issue: Database MCP can't connect to MySQL

```
Error: Can't connect to MySQL server on 'mysql'
```

**Solution:**
```bash
# Wait for MySQL to be fully ready
docker-compose ps  # Check health status

# Manual connectivity test
docker exec database-sse nc -zv mysql 3306

# Check environment variables
docker exec database-sse env | grep DB_
```

### Issue: Authentication failed

```
Error: Authentication failed for user 'root'
```

**Solution:**
```bash
# Check password matches
docker exec mysql mysql -uroot -ptestpassword -e "SELECT 1"

# Verify environment variables match
docker-compose config | grep -A5 database-sse
```

### Issue: cryptography package error

```
Error: 'cryptography' package is required for sha256_password
```

**Solution:**
```bash
# Rebuild with updated base image (cryptography is now included)
cd ../../..
make docker-build-base
docker-compose up -d --build
```

---

## 🔗 Related Documentation

- [Docker Image Documentation](../../docker/README.md) - Image build details
- [Database MCP Overview](../../README.md) - Main documentation
- [MySQL Documentation](https://dev.mysql.com/doc/) - MySQL reference
- [GitOps Documentation](../../../docs/) - CI/CD setup
