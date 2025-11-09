# Weather MCP Docker Image

Docker image for the Weather MCP server (Open-Meteo API integration).

## 🚀 Quick Start

### Pull from Docker Hub

```bash
# Latest version
docker pull sanjibdevnath/mcp-weather:latest

# Specific version
docker pull sanjibdevnath/mcp-weather:abc123def...
```

### Run Weather MCP

```bash
# STDIO mode (default)
docker run -it sanjibdevnath/mcp-weather:latest

# SSE mode
docker run -p 8082:8082 sanjibdevnath/mcp-weather:latest \
  --transport sse --host 0.0.0.0 --port 8082

# HTTP mode
docker run -p 8082:8082 sanjibdevnath/mcp-weather:latest \
  --transport http --host 0.0.0.0 --port 8082
```

## 🔨 Building Locally

```bash
# From repo root
cd /path/to/mcptools

# Build base image first
docker build -f shared/docker/Dockerfile.base -t mcp-base:local-dev .

# Build weather image
docker build -f weather/docker/Dockerfile \
  --build-arg BASE_TAG=local-dev \
  -t mcp-weather:local .

# Or use Make
make docker-build-weather
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
| `FASTMCP_PORT` | `8082` | Port to bind |
| `WEATHER_API_ENABLED` | `true` | Enable Open-Meteo API |
| `WEATHER_CACHE_TTL` | `3600` | Cache TTL in seconds |

## 📊 Image Details

- **Base**: `sanjibdevnath/mcp-base:latest`
- **Size**: ~50-80MB (without base)
- **Exposed Ports**: 8082 (SSE/HTTP mode)
- **User**: `appuser` (non-root)
- **Requires**: Internet connection (Open-Meteo API)

## 🧪 Testing

```bash
# Run tests inside container
docker run --rm mcp-weather:local pytest weather/tests/ -v

# Run E2E tests
docker run --rm mcp-weather:local pytest tests/test_e2e_weather.py -v
```

## 🌍 API Integration

This MCP uses the [Open-Meteo API](https://open-meteo.com/) which is:
- ✅ **Free** - No API key required
- ✅ **Fast** - Low latency responses
- ✅ **Accurate** - High-quality weather data
- ✅ **Global** - Worldwide coverage

## 🔗 Related

- [Weather README](../README.md)
- [Shared Base Image](../../shared/docker/README.md)
- [Local Development](../deployment/local/README.md)

