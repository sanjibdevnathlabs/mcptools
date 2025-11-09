# Database MCP - Local Development

Docker Compose setup for local development and testing of the Database MCP with MySQL.

## 🚀 Quick Start

### Start All Services (including MySQL)

```bash
# From repo root
cd database/deployment/local

# Build and start all services
docker-compose up -d

# Wait for MySQL to be ready (watch logs)
docker-compose logs -f mysql

# Once MySQL is healthy, services will start automatically
docker-compose ps
```

### Individual Services

```bash
# MySQL only
docker-compose up -d mysql

# STDIO mode (interactive, requires MySQL)
docker-compose up database-stdio

# SSE mode (server on port 8082)
docker-compose up -d database-sse
curl http://localhost:8082/health

# HTTP mode (server on port 8083)
docker-compose up -d database-http
curl http://localhost:8083/health
```

## 🎯 Available Services

| Service | Transport | Port | Container Name |
|---------|-----------|------|----------------|
| `mysql` | - | 3306 | `mysql-mcp` |
| `database-stdio` | STDIO | - | `database-stdio` |
| `database-sse` | SSE | 8082 | `database-sse` |
| `database-http` | HTTP | 8083 | `database-http` |

## 🗄️ MySQL Configuration

**Credentials:**
- Host: `localhost` (or `mysql` from within Docker network)
- Port: `3306`
- Root Password: `testpassword`
- Database: `mcp_db`
- User: `mcp_user`
- Password: `mcp_password`

**Sample Data:**
- `users` table with 3 sample users
- `products` table with 3 sample products

## 🔧 Development Workflow

### 1. Build Base Image First

```bash
# From repo root
docker build -f shared/docker/Dockerfile.base -t mcp-base:local-dev .
```

### 2. Start MySQL and Database Services

```bash
cd database/deployment/local
docker-compose up -d
```

### 3. Connect to MySQL

```bash
# From host
mysql -h 127.0.0.1 -u root -ptestpassword mcp_db

# From container
docker-compose exec mysql mysql -u root -ptestpassword mcp_db
```

### 4. Test Database MCP

```bash
# Query via SSE endpoint
curl -X POST http://localhost:8082/tools/execute_query \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM users"}'

# Get schema information
curl -X POST http://localhost:8082/tools/get_schema \
  -H "Content-Type: application/json" \
  -d '{"database": "mcp_db"}'
```

### 5. View Logs

```bash
docker-compose logs -f mysql
docker-compose logs -f database-sse
docker-compose logs -f database-http
```

### 6. Stop Services

```bash
docker-compose down

# Remove volumes (deletes MySQL data)
docker-compose down -v
```

## 🧪 Testing

Run integration tests against running MySQL:

```bash
# From repo root (with MySQL running)
APP_ENV=test DATABASE_HOST=127.0.0.1 DATABASE_PASSWORD=testpassword \
  pytest database/tests/test_integration.py -v

# E2E tests
pytest tests/test_e2e_database.py -v
```

## 🔄 Rebuild After Code Changes

```bash
# Rebuild all services
docker-compose build

# Or rebuild specific service
docker-compose build database-sse

# Restart with new build
docker-compose up -d --force-recreate database-sse
```

## 📊 Useful Commands

```bash
# Check MySQL status
docker-compose exec mysql mysqladmin ping -u root -ptestpassword

# Reset database
docker-compose down -v
docker-compose up -d mysql

# View database schema
docker-compose exec mysql mysql -u root -ptestpassword -e "SHOW TABLES" mcp_db
```

## 🛠️ Custom Initialization

Edit `init.sql` to add your own tables and sample data:

```sql
-- Add your tables
CREATE TABLE IF NOT EXISTS my_table (...);

-- Add your data
INSERT INTO my_table VALUES (...);
```

Then rebuild:

```bash
docker-compose down -v
docker-compose up -d mysql
```

## 🔗 Related

- [Database Docker Image](../../docker/README.md)
- [Main Database README](../../README.md)
- [Integration Tests](../../tests/test_integration.py)
- [E2E Tests](../../../tests/test_e2e_database.py)

