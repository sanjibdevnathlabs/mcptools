# Weather MCP - Local Development

Docker Compose setup for local development and testing of the Weather MCP.

## 🚀 Quick Start

### Start All Services

```bash
# From repo root
cd weather/deployment/local

# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Individual Services

```bash
# STDIO mode (interactive)
docker-compose up weather-stdio

# SSE mode (server on port 8084)
docker-compose up -d weather-sse
curl http://localhost:8084/health

# HTTP mode (server on port 8085)
docker-compose up -d weather-http
curl http://localhost:8085/health
```

## 🎯 Available Services

| Service | Transport | Port | Container Name |
|---------|-----------|------|----------------|
| `weather-stdio` | STDIO | - | `weather-stdio` |
| `weather-sse` | SSE | 8084 | `weather-sse` |
| `weather-http` | HTTP | 8085 | `weather-http` |

## 🔧 Development Workflow

### 1. Build Base Image First

```bash
# From repo root
docker build -f shared/docker/Dockerfile.base -t mcp-base:local-dev .
```

### 2. Start Weather Services

```bash
cd weather/deployment/local
docker-compose up -d
```

### 3. Test Weather API

```bash
# Get weather forecast for San Francisco
curl -X POST http://localhost:8084/tools/get_forecast \
  -H "Content-Type: application/json" \
  -d '{"city": "San Francisco"}'

# Get weather by coordinates
curl -X POST http://localhost:8084/tools/get_weather \
  -H "Content-Type: application/json" \
  -d '{"latitude": 37.7749, "longitude": -122.4194}'
```

### 4. View Logs

```bash
docker-compose logs -f weather-sse
docker-compose logs -f weather-http
```

### 5. Stop Services

```bash
docker-compose down
```

## 🧪 Testing

Run E2E tests against running services:

```bash
# From repo root
pytest tests/test_e2e_weather.py -v -k "sse"
pytest tests/test_e2e_weather.py -v -k "http"
```

## 🔄 Rebuild After Code Changes

```bash
# Rebuild all services
docker-compose build

# Or rebuild specific service
docker-compose build weather-sse

# Restart with new build
docker-compose up -d --force-recreate
```

## 📊 Environment Variables

Edit `docker-compose.yml` to customize:

```yaml
environment:
  - LOG_LEVEL=DEBUG           # Change to INFO, WARNING, ERROR
  - WEATHER_API_ENABLED=true  # Enable/disable Open-Meteo API
  - WEATHER_CACHE_TTL=3600    # Cache TTL in seconds (1 hour)
```

## 🌍 API Notes

This MCP uses the [Open-Meteo API](https://open-meteo.com/):
- ✅ **No API key required** - Completely free
- ✅ **Rate limits** - ~10k requests per day per IP
- ✅ **Global coverage** - Worldwide weather data
- ✅ **Real-time** - Up-to-date forecasts

## 🔗 Related

- [Weather Docker Image](../../docker/README.md)
- [Main Weather README](../../README.md)
- [E2E Tests](../../../tests/test_e2e_weather.py)

