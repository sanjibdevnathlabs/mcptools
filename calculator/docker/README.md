# Calculator MCP Docker Image

Production-ready Docker image for the Calculator MCP server with multi-transport support.

## 🏗️ Architecture

Single container running **three concurrent servers**:
- **Port 8080**: SSE Transport (`/sse`)
- **Port 8081**: HTTP Transport (`/mcp`)
- **Port 9090**: Health & Metrics (`/health`, `/metrics`)

## 🐳 Building

### Using Makefile (Recommended)

```bash
# Build base image first
make docker-build-base

# Build calculator image
make docker-build-calculator
```

### Using Docker Directly

```bash
# Build with local-dev tag
docker build \
  -f calculator/docker/Dockerfile \
  --build-arg BASE_TAG=local-dev \
  -t mcp-calculator:local \
  .
```

## 🚀 Running

### Docker Run

```bash
docker run -d \
  --name calculator \
  -p 8080:8080 \
  -p 8081:8081 \
  -p 9090:9090 \
  -e LOG_LEVEL=DEBUG \
  mcp-calculator:local
```

### Docker Compose (Recommended)

See `calculator/deployment/local/docker-compose.yml`

## 📦 Image Details

**Base Image:** `sanjibdevnath/mcp-base:latest`
- Python 3.13-slim
- Common dependencies pre-installed

**Size:** ~200MB (shared base layer)

**Labels:**
```
mcp.name=calculator
mcp.version=1.0.0
mcp.transports=stdio,sse,http
```

## 🔍 Health Check

Built-in Docker health check via admin port:

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:9090/health || exit 1
```

## 🌐 Ports

| Port | Protocol | Endpoint |
|------|----------|----------|
| 8080 | SSE | `/sse` |
| 8081 | HTTP | `/mcp` |
| 9090 | HTTP | `/health`, `/metrics` |

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_NAME` | `calculator` | Service name |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `FASTMCP_HOST` | `0.0.0.0` | Bind address |

## 📊 Multi-Stage Build

The Dockerfile uses a multi-stage build pattern:

1. **Base Stage**: Inherits from `mcp-base` with Python 3.13 and shared dependencies
2. **Application Stage**: Copies only calculator-specific code

**Benefits:**
- Smaller final image (shared base layer)
- Faster builds (cached base layer)
- Consistent environment across all MCPs

## 🎯 Production Use

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: calculator-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: calculator-mcp
  template:
    metadata:
      labels:
        app: calculator-mcp
    spec:
      containers:
      - name: calculator
        image: mcp-calculator:latest
        ports:
        - containerPort: 8080
          name: sse
          protocol: TCP
        - containerPort: 8081
          name: http
          protocol: TCP
        - containerPort: 9090
          name: admin
          protocol: TCP
        env:
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 9090
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 9090
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 3
```

### Service Definition

```yaml
apiVersion: v1
kind: Service
metadata:
  name: calculator-mcp
spec:
  type: ClusterIP
  ports:
  - name: sse
    port: 8080
    targetPort: 8080
  - name: http
    port: 8081
    targetPort: 8081
  - name: admin
    port: 9090
    targetPort: 9090
  selector:
    app: calculator-mcp
```

## 🔐 Security

- Runs as non-root user (`appuser`, UID 1000)
- No secrets in image
- Minimal attack surface (slim base)
- Health checks prevent unhealthy pods from receiving traffic

## 📈 Monitoring

### Prometheus ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: calculator-mcp
spec:
  selector:
    matchLabels:
      app: calculator-mcp
  endpoints:
  - port: admin
    path: /metrics
    interval: 30s
```

## 🧪 Testing

```bash
# Start container
docker run -d -p 9090:9090 -p 8080:8080 -p 8081:8081 mcp-calculator:local

# Test health
curl http://localhost:9090/health

# Test metrics
curl http://localhost:9090/metrics

# Test SSE (via MCP Inspector)
# URL: http://localhost:8080/sse

# Test HTTP
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
  curl -s -X POST http://localhost:8081/mcp/ \
  -H "Content-Type: application/json" -d @-
```

## 🔗 Related

- **Base Image**: `shared/docker/README.md`
- **Local Development**: `calculator/deployment/local/README.md`
- **Calculator Source**: `calculator/main.py`
