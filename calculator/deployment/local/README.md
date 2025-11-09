# Calculator MCP - Local Docker Deployment

Local development deployment using Docker Compose with separate containers for SSE and HTTP transports.

## 🏗️ Architecture

This deployment runs **two separate containers** from the same Docker image:

```
┌─────────────────────────────────────────────────────────┐
│                  Docker Network                          │
│                 (mcp-local-network)                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────┐   ┌──────────────────────┐   │
│  │  calculator-sse      │   │  calculator-http     │   │
│  │                      │   │                      │   │
│  │  Transport: SSE      │   │  Transport: HTTP     │   │
│  │  Port: 8080          │   │  Port: 8081          │   │
│  │  Logs: JSON to file  │   │  Logs: JSON to file  │   │
│  └──────────────────────┘   └──────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- curl (for health checks)

### Start All Services

```bash
# From project root
cd calculator/deployment/local
docker-compose up -d

# View logs
docker-compose logs -f

# Check service health
docker-compose ps
```

### Start Individual Services

```bash
# Start only SSE transport
docker-compose up -d calculator-sse

# Start only HTTP transport
docker-compose up -d calculator-http
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## 📊 Service Configuration

### calculator-sse (Port 8080)

**Purpose**: SSE (Server-Sent Events) transport for streaming responses

**Configuration**:
```yaml
environment:
  - APP_ENV=docker
  - TRANSPORT_MODE=sse
  - FASTMCP_HOST=0.0.0.0
  - FASTMCP_PORT=8080
  - LOG_LEVEL=DEBUG
```

**Health Check**: TCP connection to port 8080 (Python socket check)

**Test Connection**:
```bash
# Test if port is open and accepting connections
python -c "import socket; s=socket.socket(); s.connect(('localhost',8080)); s.close(); print('✅ Port 8080 is open')"
```

### calculator-http (Port 8081)

**Purpose**: Streamable HTTP transport for request-response

**Configuration**:
```yaml
environment:
  - APP_ENV=docker
  - TRANSPORT_MODE=streamable-http
  - FASTMCP_HOST=0.0.0.0
  - FASTMCP_PORT=8081
  - LOG_LEVEL=DEBUG
```

**Health Check**: TCP connection to port 8081 (Python socket check)

**Test Connection**:
```bash
# Test if port is open and accepting connections
python -c "import socket; s=socket.socket(); s.connect(('localhost',8081)); s.close(); print('✅ Port 8081 is open')"
```

## 🔧 Development Workflow

### Building the Image

```bash
# Build from project root
docker-compose build

# Build without cache
docker-compose build --no-cache

# Build specific service
docker-compose build calculator-sse
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f calculator-sse
docker-compose logs -f calculator-http

# Last 50 lines
docker-compose logs --tail=50 calculator-sse
```

### Accessing Container

```bash
# Execute command in running container
docker-compose exec calculator-sse /bin/bash

# Run one-off command
docker-compose run --rm calculator-sse python --version
```

### Testing Inside Container

```bash
# Run tests in SSE container
docker-compose exec calculator-sse pytest calculator/tests/ -v

# Run tests in HTTP container
docker-compose exec calculator-http pytest calculator/tests/ -v
```

## 🐛 Troubleshooting

### Service Won't Start

**Check logs**:
```bash
docker-compose logs calculator-sse
```

**Common issues**:
1. Port already in use
   ```bash
   # Check what's using the port
   lsof -i :8080
   lsof -i :8081
   ```

2. Image not built
   ```bash
   docker-compose build
   ```

3. Network issues
   ```bash
   docker network ls
   docker network inspect mcp-local-network
   ```

### Health Check Failing

**Check service status**:
```bash
docker-compose ps
```

**Verify port is listening**:
```bash
# From host
python -c "import socket; s=socket.socket(); s.connect(('localhost',8080)); s.close(); print('✅ Port 8080 is healthy')"

# From inside container
docker-compose exec calculator-sse python -c "import socket; s=socket.socket(); s.connect(('localhost',8080)); s.close(); print('✅ Port 8080 is healthy')"
```

### Logs Not Appearing

**Check log configuration**:
- Logs are written to files in Docker (not stdout when in docker environment)
- Check `environment/docker.toml` for log settings

**Access log files**:
```bash
# Copy logs from container
docker cp calculator-sse:/app/logs/calculator.log ./calculator-sse.log
docker cp calculator-http:/app/logs/calculator.log ./calculator-http.log

# Tail log file inside container
docker-compose exec calculator-sse tail -f /app/logs/calculator.log
```

## 🔐 Environment Variables

### Required Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `APP_ENV` | Environment name | `docker` | `docker`, `dev`, `prod` |
| `TRANSPORT_MODE` | Transport protocol | `sse` | `sse`, `streamable-http` |
| `FASTMCP_HOST` | Server bind address | `0.0.0.0` | `0.0.0.0`, `127.0.0.1` |
| `FASTMCP_PORT` | Server port | `8080` | `8080`, `8081` |
| `LOG_LEVEL` | Logging level | `INFO` | `DEBUG`, `INFO`, `WARNING` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_FORMAT` | Log format | `json` (from docker.toml) |
| `LOG_DESTINATION` | Log destination | `file` (forced for docker) |
| `LOG_FILE_PATH` | Log file path | `logs/calculator.log` |

## 📁 Volume Mounts

### Development Mode

For development with live reload, mount source code:

```yaml
services:
  calculator-sse:
    volumes:
      - ../../..:/app  # Mount entire project
```

**Then**:
```bash
docker-compose up -d
docker-compose logs -f
# Edit code on host, changes reflect in container
```

## 🔄 Restart Policies

Both services use `restart: unless-stopped`:
- Automatically restart on failure
- Won't restart if manually stopped
- Restart on Docker daemon restart

**Change restart policy**:
```yaml
restart: always     # Always restart
restart: on-failure # Only on failure
restart: "no"       # Never restart
```

## 🌐 Network

**Network Name**: `mcp-local-network`
**Driver**: `bridge`

**Inspect network**:
```bash
docker network inspect mcp-local-network
```

**Connect external container**:
```yaml
services:
  external-service:
    networks:
      - mcp-local-network

networks:
  mcp-local-network:
    external: true
```

## 🧪 Testing the Deployment

### Basic Connectivity Test

```bash
# Test SSE port is listening
python -c "import socket; s=socket.socket(); s.connect(('localhost',8080)); s.close(); print('✅ SSE port 8080 is listening')"

# Test HTTP port is listening
python -c "import socket; s=socket.socket(); s.connect(('localhost',8081)); s.close(); print('✅ HTTP port 8081 is listening')"

# Check container health status
docker-compose ps
# Both services should show "healthy" in STATUS column
```

### MCP Protocol Test

**Using Playwright MCP client**:
```python
from mcp.client import Client

# Test SSE transport
async with Client(transport="sse", url="http://localhost:8080") as client:
    result = await client.call_tool("add", {"a": 5, "b": 3})
    print(result)  # 8

# Test HTTP transport
async with Client(transport="streamable-http", url="http://localhost:8081") as client:
    result = await client.call_tool("add", {"a": 5, "b": 3})
    print(result)  # 8
```

## 📝 Configuration Files

### Dockerfile

**Location**: `calculator/docker/Dockerfile`

**Key Settings**:
- Base image: `sanjibdevnath/mcp-base:latest`
- Exposed ports: `8080`, `8081`
- Entry point: `python -m calculator`
- Environment: `APP_ENV=docker`

### docker-compose.yml

**Location**: `calculator/deployment/local/docker-compose.yml`

**Services**:
- `calculator-sse`: SSE transport on port 8080
- `calculator-http`: HTTP transport on port 8081

### Environment Config

**Location**: `calculator/environment/docker.toml`

**Overrides**:
```toml
[app]
environment = "docker"

[logger]
format = "json"  # JSON logging for Docker
```

## 🎯 Next Steps

1. **Production Deployment**: See `../production/README.md` (if exists)
2. **Kubernetes Deployment**: See `../k8s/README.md` (if exists)
3. **CI/CD Integration**: See `.github/workflows/` in project root
4. **Monitoring Setup**: Add Prometheus metrics exporter

## 🆘 Support

**Issues**:
- GitHub Issues: https://github.com/sanjibdevnathlabs/mcptools/issues
- Logs: `docker-compose logs -f`
- Health: `docker-compose ps`

**Clean Slate Reset**:
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```
