# Calculator MCP - Local Development

## 📦 Overview

Local development environment for Calculator MCP using Docker Compose. Runs both SSE and HTTP transports simultaneously for testing.

**Services:**
- `calculator-sse` - SSE transport on port 8080
- `calculator-http` - HTTP transport on port 8081

---

## 🚀 Quick Start

```bash
# From this directory
docker-compose up -d

# Or from repository root
make docker-compose-up-calculator

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

| Service | Port | Transport | Container Name | Health Check |
|---------|------|-----------|----------------|--------------|
| `calculator-sse` | 8080 | SSE | `calculator-sse` | ✅ TCP port check |
| `calculator-http` | 8081 | HTTP | `calculator-http` | ✅ TCP port check |

### Environment Variables

Both services use these environment variables:

```yaml
APP_ENV: docker                    # Loads environment/docker.toml
TRANSPORT_MODE: sse|streamable-http  # Transport protocol
FASTMCP_HOST: 0.0.0.0             # Bind to all interfaces
FASTMCP_PORT: 8080|8081           # Port number
LOG_LEVEL: DEBUG                   # Logging level
```

**Overriding Variables:**

Create a `.env` file in this directory:

```bash
# .env
LOG_LEVEL=INFO
TRANSPORT_MODE=sse
```

Or use environment variables:

```bash
LOG_LEVEL=INFO docker-compose up -d
```

---

## 🧪 Testing

### Using MCP Inspector

1. **Start services:**
   ```bash
   docker-compose up -d
   ```

2. **Test SSE transport:**
   - Open: http://localhost:8080/sse
   - Or use MCP Inspector: http://localhost:6274/

3. **Test HTTP transport:**
   - Open: http://localhost:8081/mcp
   - Or use MCP Inspector: http://localhost:6274/

### Using E2E Tests

```bash
# From repository root
pytest tests/test_e2e_calculator.py -v

# Test specific transport
pytest tests/test_e2e_calculator.py::TestCalculatorSSE -v
pytest tests/test_e2e_calculator.py::TestCalculatorHTTP -v
```

### Using cURL (HTTP transport)

```bash
# Initialize session
curl -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}'

# List tools
curl -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}'

# Call add tool
curl -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "add",
      "arguments": {"a": 5, "b": 3}
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
docker-compose logs -f calculator-sse
docker-compose logs -f calculator-http

# Last 50 lines
docker-compose logs --tail=50 calculator-sse
```

### Shell into Container

```bash
# SSE container
docker exec -it calculator-sse /bin/bash

# HTTP container
docker exec -it calculator-http /bin/bash

# Check config
docker exec calculator-sse python -c "
from calculator.config import config
print(f'Transport: {config.server.transport_mode}')
print(f'Port: {config.server.port}')
print(f'Log Level: {config.logger.level}')
"
```

### Check Health

```bash
# Check health status
docker-compose ps

# Manual health check
docker exec calculator-sse python -c "
import socket
s = socket.socket()
s.connect(('localhost', 8080))
s.close()
print('✅ Port 8080 is open')
"
```

### Network Inspection

```bash
# List networks
docker network ls | grep mcp

# Inspect network
docker network inspect mcp-local-network

# Check connectivity
docker exec calculator-sse ping -c 1 calculator-http
```

---

## 🛠️ Available Tools

The calculator MCP provides 4 basic tools:

1. **add** - Add two numbers
   ```json
   {"a": 5, "b": 3} → {"result": 8}
   ```

2. **subtract** - Subtract two numbers
   ```json
   {"a": 10, "b": 4} → {"result": 6}
   ```

3. **multiply** - Multiply two numbers
   ```json
   {"a": 6, "b": 7} → {"result": 42}
   ```

4. **divide** - Divide two numbers
   ```json
   {"a": 15, "b": 3} → {"result": 5.0}
   ```

---

## 📊 Port Mapping

| Host Port | Container Port | Service | Protocol |
|-----------|---------------|---------|----------|
| 8080 | 8080 | calculator-sse | SSE |
| 8081 | 8081 | calculator-http | HTTP |

**Avoiding Port Conflicts:**

If ports are already in use, modify `docker-compose.yml`:

```yaml
ports:
  - "9080:8080"  # Change host port to 9080
```

---

## 🧹 Cleanup

```bash
# Stop services
docker-compose down

# Remove volumes and networks
docker-compose down -v

# Remove images
docker-compose down --rmi local

# From repository root
make docker-compose-down-calculator
```

---

## 🔄 Rebuild After Code Changes

```bash
# Rebuild and restart
docker-compose up -d --build

# Or rebuild specific service
docker-compose up -d --build calculator-sse

# Force complete rebuild
docker-compose build --no-cache
docker-compose up -d
```

---

## 📁 File Structure

```
calculator/deployment/local/
├── docker-compose.yml   # Compose configuration
└── README.md           # This file

Related files:
├── ../../docker/
│   ├── Dockerfile      # Calculator image definition
│   └── .dockerignore   # Build exclusions
└── ../../environment/
    ├── default.toml    # Default config
    └── docker.toml     # Docker overrides
```

---

## ⚠️ Common Issues

### Issue: Port already in use

```
Error: bind: address already in use
```

**Solution:**
```bash
# Find process using port
lsof -i :8080

# Kill process or change port in docker-compose.yml
```

### Issue: Image not found

```
Error: image not found: sanjibdevnath/mcp-base:local-dev
```

**Solution:**
```bash
# Build base image first
cd ../../..
make docker-build-base
```

### Issue: Unhealthy container

```
Status: unhealthy
```

**Solution:**
```bash
# Check logs
docker-compose logs calculator-sse

# Verify port is listening
docker exec calculator-sse netstat -tlnp | grep 8080
```

---

## 🔗 Related Documentation

- [Docker Image Documentation](../../docker/README.md) - Image build details
- [Calculator MCP Overview](../../README.md) - Main documentation
- [GitOps Documentation](../../../docs/) - CI/CD setup
