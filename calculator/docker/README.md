# Calculator MCP - Docker Image

## 📦 Overview

Docker image for the Calculator MCP server, providing basic arithmetic operations (add, subtract, multiply, divide) via MCP protocol.

**Base Image**: `sanjibdevnath/mcp-base:${BASE_TAG}`  
**Transports**: SSE, Streamable-HTTP  
**Exposed Ports**: 8080 (SSE), 8081 (HTTP)

---

## 🏗️ Build Instructions

### Using Makefile (Recommended)

```bash
# Build base image first (if not already built)
make docker-build-base

# Build calculator image
make docker-build-calculator
```

### Manual Build

```bash
# From repository root
docker build -f calculator/docker/Dockerfile \
  --build-arg BASE_TAG=local-dev \
  -t mcp-calculator:local .
```

---

## 🚀 Running the Container

### Quick Start

```bash
# SSE transport on port 8080
docker run -p 8080:8080 \
  -e TRANSPORT_MODE=sse \
  mcp-calculator:local

# HTTP transport on port 8081
docker run -p 8081:8081 \
  -e TRANSPORT_MODE=streamable-http \
  -e FASTMCP_PORT=8081 \
  mcp-calculator:local
```

### With Docker Compose (Recommended)

```bash
# See calculator/deployment/local/ for docker-compose setup
cd calculator/deployment/local
docker-compose up -d
```

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `docker` | Application environment (loads `environment/docker.toml`) |
| `TRANSPORT_MODE` | `sse` | Transport protocol: `sse` or `streamable-http` |
| `FASTMCP_HOST` | `0.0.0.0` | Server bind address |
| `FASTMCP_PORT` | `8080` | Server port (8080 for SSE, 8081 for HTTP) |
| `LOG_LEVEL` | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `LOG_FORMAT` | `json` | Log format: `text` or `json` (docker.toml sets to `json`) |
| `LOG_DESTINATION` | `stdout` | Log destination: `stdout`, `stderr`, `file`, `both` |

---

## 🏷️ Image Labels

```dockerfile
LABEL mcp.name="calculator"
LABEL mcp.version="1.0.0"
LABEL mcp.transports="sse,streamable-http"
```

Query labels:
```bash
docker inspect mcp-calculator:local | jq '.[0].Config.Labels'
```

---

## 📂 Image Contents

```
/app/
├── calculator/           # Calculator MCP code
│   ├── main.py
│   ├── config/
│   ├── environment/
│   └── tests/
├── shared/              # Shared modules (logging, config)
│   ├── config/
│   └── logging/
└── tests/               # E2E tests
    └── test_e2e_calculator.py
```

---

## 🔍 Debugging

```bash
# View logs
docker logs mcp-calculator-local -f

# Shell into container
docker exec -it mcp-calculator-local /bin/bash

# Check config
docker exec mcp-calculator-local python -c "from calculator.config import config; print(config.server.transport_mode)"

# Test tools
docker exec mcp-calculator-local python -m calculator --help
```

---

## 🧪 Testing

```bash
# Run E2E tests against container
pytest tests/test_e2e_calculator.py -v

# Test specific transport
pytest tests/test_e2e_calculator.py::TestCalculatorSSE -v
pytest tests/test_e2e_calculator.py::TestCalculatorHTTP -v
```

---

## 📊 Health Check

The image includes a TCP-based health check (configured in docker-compose):

```bash
# Manual health check
python -c "import socket; s=socket.socket(); s.connect(('localhost',8080)); s.close()"
```

---

## 🐳 Image Size

- **Base Image**: ~1GB (shared across all MCPs)
- **Calculator Layer**: ~5MB (calculator code only)
- **Total**: ~1GB (but base is cached and reused)

---

## 🔗 Related Documentation

- [Deployment Guide](../deployment/local/README.md) - Local development with docker-compose
- [Main README](../../README.md) - Calculator MCP overview
- [GitOps Documentation](../../../docs/) - CI/CD and infrastructure
