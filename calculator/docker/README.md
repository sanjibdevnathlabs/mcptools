# Calculator MCP - Docker Image

Multi-transport MCP server for calculator operations packaged as a Docker image.

## 📦 Image Details

**Base Image**: `sanjibdevnath/mcp-base:latest`  
**Image Name**: `mcp-calculator:local` (development) | `sanjibdevnath/mcp-calculator:latest` (production)  
**Supported Transports**: SSE, Streamable-HTTP (stdio excluded from Docker)

## 🏗️ Image Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Docker Image Layers                         │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: Base Image (Python 3.13 + common dependencies)    │
│ Layer 2: Shared modules (config, logging)                  │
│ Layer 3: Calculator-specific code                          │
│ Layer 4: Test files (for in-container testing)             │
│ Layer 5: Configuration (ENTRYPOINT, ENV)                   │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Build Arguments

### BASE_TAG

Specifies which base image tag to use.

**Usage**:
```bash
# Use latest base image
docker build --build-arg BASE_TAG=latest -t mcp-calculator:latest .

# Use specific version
docker build --build-arg BASE_TAG=v1.0.0 -t mcp-calculator:v1.0.0 .

# Use local dev base
docker build --build-arg BASE_TAG=local-dev -t mcp-calculator:local .
```

**Default**: `latest`

## 🚀 Building the Image

### From Project Root

```bash
# Build with defaults
docker build -f calculator/docker/Dockerfile -t mcp-calculator:local .

# Build with specific base tag
docker build -f calculator/docker/Dockerfile \
  --build-arg BASE_TAG=v1.0.0 \
  -t mcp-calculator:v1.0.0 .

# Build without cache
docker build -f calculator/docker/Dockerfile \
  --no-cache \
  -t mcp-calculator:local .
```

### Using docker-compose

```bash
cd calculator/deployment/local
docker-compose build
```

### Using Makefile

```bash
# From project root
make docker-build-calculator

# Build all MCPs
make docker-build-all
```

## 🎯 Environment Variables

The image supports runtime configuration via environment variables:

### Required Variables

| Variable | Description | Default | Valid Values |
|----------|-------------|---------|--------------|
| `APP_ENV` | Environment name | `docker` | `dev`, `test`, `docker`, `prod` |
| `TRANSPORT_MODE` | Transport protocol | `sse` | `sse`, `streamable-http` |
| `FASTMCP_HOST` | Server bind address | `0.0.0.0` | Any valid IP/hostname |
| `FASTMCP_PORT` | Server port | `8080` | `1024-65535` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log format | `json` (from docker.toml) |
| `LOG_DESTINATION` | Log destination | `file` (forced in Docker) |
| `LOG_FILE_PATH` | Log file path | `logs/calculator.log` |

## 🏃 Running the Image

### SSE Transport

```bash
docker run -d \
  --name calculator-sse \
  -p 8080:8080 \
  -e TRANSPORT_MODE=sse \
  -e FASTMCP_PORT=8080 \
  -e LOG_LEVEL=DEBUG \
  mcp-calculator:local
```

### HTTP Transport

```bash
docker run -d \
  --name calculator-http \
  -p 8081:8081 \
  -e TRANSPORT_MODE=streamable-http \
  -e FASTMCP_PORT=8081 \
  -e LOG_LEVEL=DEBUG \
  mcp-calculator:local
```

### Custom Configuration

```bash
docker run -d \
  --name calculator-custom \
  -p 9000:9000 \
  -e APP_ENV=prod \
  -e TRANSPORT_MODE=sse \
  -e FASTMCP_HOST=0.0.0.0 \
  -e FASTMCP_PORT=9000 \
  -e LOG_LEVEL=WARNING \
  mcp-calculator:local
```

## 📁 Image Contents

### Copied Files

```
/app/
├── shared/                    # Shared modules
│   ├── config/                # Config loading
│   └── logging/               # Logging setup
├── calculator/                # Calculator MCP code
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py
│   ├── config/                # Calculator config
│   ├── environment/           # TOML configs
│   └── tests/                 # Unit tests
└── tests/                     # E2E tests
    ├── __init__.py
    ├── conftest.py
    └── test_e2e_calculator.py
```

### Exposed Ports

- `8080`: Default SSE transport
- `8081`: Default HTTP transport

**Note**: Actual port used depends on `FASTMCP_PORT` environment variable.

### Working Directory

`WORKDIR /app`

### Entry Point

```bash
ENTRYPOINT ["python", "-m", "calculator"]
```

## 🔍 Image Inspection

### View Image Labels

```bash
docker inspect mcp-calculator:local | jq '.[0].Config.Labels'
```

**Expected labels**:
```json
{
  "org.opencontainers.image.title": "Calculator MCP Server",
  "org.opencontainers.image.description": "MCP server for calculator operations",
  "org.opencontainers.image.vendor": "sanjibdevnath",
  "org.opencontainers.image.source": "https://github.com/sanjibdevnathlabs/mcptools",
  "mcp.name": "calculator",
  "mcp.version": "1.0.0",
  "mcp.transports": "sse,streamable-http"
}
```

### View Image Layers

```bash
docker history mcp-calculator:local
```

### View Image Size

```bash
docker images mcp-calculator:local
```

## 🧪 Testing the Image

### Run Tests Inside Container

```bash
# Start container with bash
docker run --rm -it mcp-calculator:local /bin/bash

# Inside container
pytest calculator/tests/ -v
pytest tests/test_e2e_calculator.py -v
```

### Health Check

```bash
# Start container
docker run -d --name calc-test -p 8080:8080 mcp-calculator:local

# Check health
curl http://localhost:8080/health

# View logs
docker logs calc-test

# Cleanup
docker stop calc-test && docker rm calc-test
```

## 🎨 Customization

### Custom Base Image

```dockerfile
# Use custom base image
ARG BASE_TAG=custom
FROM myregistry/mcp-base:${BASE_TAG}
```

### Additional Dependencies

```dockerfile
# Add before COPY commands
RUN pip install additional-package==1.0.0
```

### Custom Entry Point

```dockerfile
# Override default entry point
ENTRYPOINT ["python", "-m", "calculator", "--custom-flag"]
```

## 📊 Image Optimization

### Multi-Stage Build (Already Implemented)

The base image uses multi-stage build to minimize size:
1. **Builder stage**: Install dependencies
2. **Runtime stage**: Copy only necessary files

### Size Reduction Tips

1. **Use slim base images**: `python:3.13-slim`
2. **Minimize layers**: Combine RUN commands
3. **Remove cache**: `pip install --no-cache-dir`
4. **Use .dockerignore**: Exclude unnecessary files

### .dockerignore

Create `.dockerignore` in project root:
```
# Python
__pycache__/
*.py[cod]
*.so
.Python
venv/
*.egg-info/

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
*.swp

# Git
.git/
.gitignore

# Documentation
*.md
docs/

# Logs
*.log
logs/
```

## 🔐 Security Best Practices

### 1. Non-Root User

**Currently runs as root** (inherited from base image). To add non-root user:

```dockerfile
# Add before ENTRYPOINT
RUN useradd -m -u 1000 calculator && \
    chown -R calculator:calculator /app

USER calculator
```

### 2. Minimal Permissions

```bash
# Run with read-only filesystem
docker run --read-only \
  --tmpfs /tmp \
  --tmpfs /app/logs \
  -p 8080:8080 \
  mcp-calculator:local
```

### 3. Resource Limits

```bash
docker run -d \
  --name calculator-sse \
  --memory=512m \
  --cpus=1 \
  -p 8080:8080 \
  mcp-calculator:local
```

## 🚢 Publishing the Image

### Tag for Registry

```bash
# Tag for Docker Hub
docker tag mcp-calculator:local sanjibdevnath/mcp-calculator:latest
docker tag mcp-calculator:local sanjibdevnath/mcp-calculator:v1.0.0

# Tag for private registry
docker tag mcp-calculator:local myregistry.com/mcp-calculator:latest
```

### Push to Registry

```bash
# Docker Hub
docker push sanjibdevnath/mcp-calculator:latest
docker push sanjibdevnath/mcp-calculator:v1.0.0

# Private registry
docker push myregistry.com/mcp-calculator:latest
```

## 🔄 Image Versioning

### Semantic Versioning

```bash
# Major release
docker tag mcp-calculator:local sanjibdevnath/mcp-calculator:2.0.0
docker tag mcp-calculator:local sanjibdevnath/mcp-calculator:2
docker tag mcp-calculator:local sanjibdevnath/mcp-calculator:latest

# Minor release
docker tag mcp-calculator:local sanjibdevnath/mcp-calculator:1.5.0
docker tag mcp-calculator:local sanjibdevnath/mcp-calculator:1.5

# Patch release
docker tag mcp-calculator:local sanjibdevnath/mcp-calculator:1.4.2
```

### Git SHA Tags

```bash
# Tag with git SHA
GIT_SHA=$(git rev-parse --short HEAD)
docker tag mcp-calculator:local sanjibdevnath/mcp-calculator:${GIT_SHA}
```

## 🐛 Troubleshooting

### Build Fails

**Check Docker version**:
```bash
docker --version
# Requires: Docker 20.10+
```

**Check build context**:
```bash
# Build from project root (not calculator/)
pwd  # Should be: /path/to/mcptools
docker build -f calculator/docker/Dockerfile -t mcp-calculator:local .
```

### Image Too Large

**Check size**:
```bash
docker images mcp-calculator:local
```

**Reduce size**:
1. Use multi-stage build
2. Remove unnecessary files
3. Combine RUN commands
4. Use `.dockerignore`

### Runtime Errors

**Check logs**:
```bash
docker logs <container-id>
```

**Exec into container**:
```bash
docker exec -it <container-id> /bin/bash
python -c "import calculator; print('OK')"
```

## 📚 Related Documentation

- **Base Image**: `shared/docker/README.md`
- **Local Deployment**: `deployment/local/README.md`
- **CI/CD**: `.github/workflows/docker.yml`
- **Testing**: `tests/README.md`

## 🆘 Support

**Issues**: https://github.com/sanjibdevnathlabs/mcptools/issues  
**Docker Hub**: https://hub.docker.com/r/sanjibdevnath/mcp-calculator
