# Calculator MCP - Local Development (Single-Pod Architecture)

Production-ready Docker Compose setup for the Calculator MCP with unified transport management.

## 🏗️ Architecture

**Single Pod with Multiple Transports:**
```
┌─────────────────────────────────────┐
│     Calculator MCP (Single Pod)     │
│                                     │
│  Port 8080 → SSE Transport          │
│  Port 8081 → HTTP Transport         │
│  Port 9090 → Health + Metrics       │
└─────────────────────────────────────┘
```

## 🚀 Quick Start

### Start Calculator Service

```bash
# From repo root
cd calculator/deployment/local

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f calculator
```

Or use the Makefile:
```bash
# From repo root
make docker-compose-up-calculator
```

## 🎯 Available Endpoints

| Endpoint | Port | Purpose |
|----------|------|---------|
| **SSE Transport** | 8080 | `http://localhost:8080/sse` |
| **HTTP Transport** | 8081 | `http://localhost:8081/mcp` |
| **Health Check** | 9090 | `http://localhost:9090/health` |
| **Metrics** | 9090 | `http://localhost:9090/metrics` |

## 🔍 Health Check

The unified health endpoint reports the status of **both** transports:

```bash
curl http://localhost:9090/health
```

**Response:**
```json
{
    "healthy": true,
    "service": "calculator-mcp",
    "version": "1.0.0",
    "transports": {
        "sse": {"healthy": true},
        "http": {"healthy": true}
    }
}
```

- **200 OK**: All transports healthy
- **503 Service Unavailable**: One or more transports unhealthy

## 📊 Metrics

Prometheus-compatible metrics endpoint (placeholder for future implementation):

```bash
curl http://localhost:9090/metrics
```

Future format will include transport-level cardinality:
```prometheus
calculator_mcp_requests_total{transport="sse"} 150
calculator_mcp_requests_total{transport="http"} 300
```

## 🧪 Testing

### Test with MCP Inspector

1. Start MCP Inspector (if not already running)
2. Connect to SSE:
   - Transport: **SSE**
   - URL: `http://localhost:8080/sse`

3. Connect to HTTP:
   - Transport: **Streamable HTTP**
   - URL: `http://localhost:8081/mcp`

### Test with curl

**List Tools (HTTP):**
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
  curl -s -X POST http://localhost:8081/mcp/ \
  -H "Content-Type: application/json" -d @-
```

**Execute Tool:**
```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"add","arguments":{"a":10,"b":5}}}' | \
  curl -s -X POST http://localhost:8081/mcp/ \
  -H "Content-Type: application/json" -d @-
```

## 🛑 Stop Service

```bash
# Using docker-compose
cd calculator/deployment/local
docker-compose down

# Or using Makefile
make docker-compose-down-all
```

## 🐳 Docker Image

**Image:** `mcp-calculator:local`

**Exposed Ports:**
- 8080 (SSE)
- 8081 (HTTP)
- 9090 (Admin)

**Health Check:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:9090/health || exit 1
```

## 📦 Production Deployment

This architecture is production-ready for Kubernetes:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: calculator-mcp
spec:
  ports:
    - name: sse
      port: 8080
    - name: http
      port: 8081
    - name: admin
      port: 9090
  selector:
    app: calculator-mcp
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: calculator-mcp
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: calculator
        image: mcp-calculator:latest
        ports:
        - containerPort: 8080
          name: sse
        - containerPort: 8081
          name: http
        - containerPort: 9090
          name: admin
        livenessProbe:
          httpGet:
            path: /health
            port: 9090
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 9090
          initialDelaySeconds: 5
          periodSeconds: 10
```

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level |
| `FASTMCP_HOST` | `0.0.0.0` | Bind address |

## 📝 Available Tools

The calculator provides 13 mathematical operations:
- **add** - Add two numbers
- **subtract** - Subtract two numbers
- **multiply** - Multiply two numbers
- **divide** - Divide two numbers
- **power** - Power of two numbers
- **sqrt** - Square root
- **cbrt** - Cube root
- **factorial** - Factorial
- **log** - Natural logarithm
- **remainder** - Modulo operation
- **sin** - Sine
- **cos** - Cosine
- **tan** - Tangent

## 🎯 Benefits of Single-Pod Architecture

✅ **Efficiency**: Single pod = less resource overhead
✅ **Simplicity**: One deployment, one service definition
✅ **Unified Health**: Single health check for all transports
✅ **Standard Pattern**: Common in production (gRPC + HTTP)
✅ **Easy Scaling**: `kubectl scale` scales both transports together
