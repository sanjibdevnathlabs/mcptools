# Database MCP Docker Image

Docker image for the Database MCP server (MySQL/MariaDB operations).

## 🚀 Quick Start

### Pull from Docker Hub

```bash
# Latest version
docker pull sanjibdevnath/mcp-database:latest

# Specific version
docker pull sanjibdevnath/mcp-database:abc123def...
```

### Run Database MCP

```bash
# STDIO mode (requires MySQL connection details)
docker run -it \
  -e DATABASE_HOST=mysql.example.com \
  -e DATABASE_USER=root \
  -e DATABASE_PASSWORD=secret \
  -e DATABASE_NAME=mydb \
  sanjibdevnath/mcp-database:latest

# SSE mode
docker run -p 8081:8081 \
  -e DATABASE_HOST=mysql.example.com \
  -e DATABASE_USER=root \
  -e DATABASE_PASSWORD=secret \
  sanjibdevnath/mcp-database:latest \
  --transport sse --host 0.0.0.0 --port 8081
```

## 🔨 Building Locally

```bash
# From repo root
cd /path/to/mcptools

# Build base image first
docker build -f shared/docker/Dockerfile.base -t mcp-base:local-dev .

# Build database image
docker build -f database/docker/Dockerfile \
  --build-arg BASE_TAG=local-dev \
  -t mcp-database:local .

# Or use Make
make docker-build-database
```

## 🎯 Supported Transports

- **STDIO** - Standard input/output (default)
- **SSE** - Server-Sent Events (HTTP streaming)
- **HTTP** - Streamable HTTP

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TRANSPORT_MODE` | `stdio` | Transport protocol |
| `LOG_LEVEL` | `INFO` | Logging level |
| `FASTMCP_HOST` | `0.0.0.0` | Host to bind |
| `FASTMCP_PORT` | `8081` | Port to bind |
| `DATABASE_HOST` | `localhost` | MySQL host |
| `DATABASE_PORT` | `3306` | MySQL port |
| `DATABASE_USER` | `root` | MySQL user |
| `DATABASE_PASSWORD` | - | MySQL password (required) |
| `DATABASE_NAME` | `mcp_db` | Default database |

## 📊 Image Details

- **Base**: `sanjibdevnath/mcp-base:latest`
- **Size**: ~80-120MB (without base)
- **Exposed Ports**: 8081 (SSE/HTTP mode)
- **User**: `appuser` (non-root)
- **Requires**: MySQL/MariaDB 8.0+

## 🧪 Testing

```bash
# Run unit tests
docker run --rm mcp-database:local pytest database/tests/ -v

# Run integration tests (requires MySQL)
docker run --rm \
  --network host \
  -e DATABASE_HOST=127.0.0.1 \
  -e DATABASE_PASSWORD=test \
  mcp-database:local pytest database/tests/test_integration.py -v
```

## 🔗 Related

- [Database README](../README.md)
- [Shared Base Image](../../shared/docker/README.md)
- [Local Development with MySQL](../deployment/local/README.md)

