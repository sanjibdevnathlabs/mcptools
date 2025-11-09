# Weather MCP - Docker Image

## 📦 Overview

Docker image for the Weather MCP server, providing weather information, forecasts, and location-based weather data via MCP protocol using OpenWeatherMap API.

**Base Image**: `sanjibdevnath/mcp-base:${BASE_TAG}`  
**Transports**: SSE, Streamable-HTTP  
**Exposed Ports**: 8082 (SSE), 8083 (HTTP)  
**External Dependencies**: OpenWeatherMap API key

---

## 🏗️ Build Instructions

### Using Makefile (Recommended)

```bash
# Build base image first (if not already built)
make docker-build-base

# Build weather image
make docker-build-weather
```

### Manual Build

```bash
# From repository root
docker build -f weather/docker/Dockerfile \
  --build-arg BASE_TAG=local-dev \
  -t mcp-weather:local .
```

---

## 🚀 Running the Container

### With Docker Compose (Recommended)

```bash
cd weather/deployment/local
docker-compose up -d
```

This starts:
- `weather-sse`: SSE transport on port 8082
- `weather-http`: HTTP transport on port 8083

### Manual Run

```bash
# SSE transport
docker run -p 8082:8082 \
  -e TRANSPORT_MODE=sse \
  -e OPENWEATHER_API_KEY=your_api_key_here \
  mcp-weather:local

# HTTP transport
docker run -p 8083:8083 \
  -e TRANSPORT_MODE=streamable-http \
  -e FASTMCP_PORT=8083 \
  -e OPENWEATHER_API_KEY=your_api_key_here \
  mcp-weather:local
```

---

## ⚙️ Environment Variables

### Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `docker` | Application environment (loads `environment/docker.toml`) |
| `TRANSPORT_MODE` | `sse` | Transport protocol: `sse` or `streamable-http` |
| `FASTMCP_HOST` | `0.0.0.0` | Server bind address |
| `FASTMCP_PORT` | `8082` | Server port (8082 for SSE, 8083 for HTTP) |
| `LOG_LEVEL` | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `LOG_FORMAT` | `json` | Log format: `text` or `json` (docker.toml sets to `json`) |

### API Configuration

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `OPENWEATHER_API_KEY` | - | OpenWeatherMap API key | ✅ Yes |
| `OPENWEATHER_BASE_URL` | `https://api.openweathermap.org/data/2.5` | API base URL | No |
| `WEATHER_API_TIMEOUT` | `30` | API timeout (seconds) | No |
| `WEATHER_CACHE_TTL` | `300` | Cache TTL (seconds) | No |

**Getting an API Key:**
1. Sign up at [OpenWeatherMap](https://openweathermap.org/api)
2. Free tier: 1,000 calls/day, 60 calls/minute
3. Copy your API key from dashboard

---

## 🏷️ Image Labels

```dockerfile
LABEL mcp.name="weather"
LABEL mcp.version="1.0.0"
LABEL mcp.transports="sse,streamable-http"
```

Query labels:
```bash
docker inspect mcp-weather:local | jq '.[0].Config.Labels'
```

---

## 📂 Image Contents

```
/app/
├── weather/             # Weather MCP code
│   ├── main.py
│   ├── config/
│   ├── environment/
│   └── tests/
├── shared/             # Shared modules (logging, config)
│   ├── config/
│   └── logging/
└── tests/              # E2E tests
    └── test_e2e_weather.py
```

---

## 🔍 Debugging

```bash
# View logs
docker logs weather-sse -f

# Shell into container
docker exec -it weather-sse /bin/bash

# Check config
docker exec weather-sse python -c "
from weather.config import config
print(f'API Key: {config.api.openweather_api_key[:10]}...')
print(f'Base URL: {config.api.openweather_base_url}')
print(f'Transport: {config.server.transport_mode}')
"

# Test API connectivity
docker exec weather-sse python -c "
import requests
import os

api_key = os.getenv('OPENWEATHER_API_KEY')
url = f'https://api.openweathermap.org/data/2.5/weather?q=London&appid={api_key}'

response = requests.get(url, timeout=10)
print(f'Status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    print(f'City: {data[\"name\"]}')
    print(f'Temp: {data[\"main\"][\"temp\"]}K')
else:
    print(f'Error: {response.text}')
"
```

---

## 🧪 Testing

```bash
# Run E2E tests (requires valid API key)
export OPENWEATHER_API_KEY=your_key_here
pytest tests/test_e2e_weather.py -v

# Test specific transport
pytest tests/test_e2e_weather.py::TestWeatherSSE -v
pytest tests/test_e2e_weather.py::TestWeatherHTTP -v

# Test specific tools
pytest tests/test_e2e_weather.py::TestWeatherSSE::test_sse_get_forecast -v
pytest tests/test_e2e_weather.py::TestWeatherSSE::test_sse_get_current_weather -v
```

---

## 📊 Health Check

The image includes a TCP-based health check (configured in docker-compose):

```bash
# Manual health check
python -c "import socket; s=socket.socket(); s.connect(('localhost',8082)); s.close()"
```

---

## 🛠️ Available Tools

The weather MCP provides tools for:

**Current Weather:**
- `get_current_weather` - Get current weather for location
- `get_weather_by_coords` - Get weather by coordinates

**Forecasts:**
- `get_forecast` - Get weather forecast
- `get_hourly_forecast` - Get hourly forecast

**Historical & Analysis:**
- `get_weather_alerts` - Get weather alerts
- `get_air_quality` - Get air quality data

**Utilities:**
- `search_location` - Search for locations
- `get_weather_summary` - Get weather summary

---

## 🌍 API Rate Limits

**OpenWeatherMap Free Tier:**
- 1,000 calls/day
- 60 calls/minute
- Current weather data
- 5-day / 3-hour forecast

**Usage Tips:**
1. Implement caching (built-in: 5 minutes TTL)
2. Batch requests when possible
3. Monitor rate limit headers
4. Consider upgrading for production

---

## 🐳 Image Size

- **Base Image**: ~1GB (shared across all MCPs)
- **Weather Layer**: ~3MB (weather code only)
- **Total**: ~1GB (but base is cached and reused)

---

## ⚠️ Important Notes

1. **API Key Required**: Weather MCP will not start without a valid API key
2. **Rate Limiting**: Free tier has limits; implement caching
3. **Network**: Container needs internet access to reach OpenWeatherMap API
4. **Credentials**: Use environment variables, never hardcode API key

---

## 🔗 Related Documentation

- [Deployment Guide](../deployment/local/README.md) - Local development with docker-compose
- [Main README](../../README.md) - Weather MCP overview
- [OpenWeatherMap API Docs](https://openweathermap.org/api) - API documentation
- [GitOps Documentation](../../../docs/) - CI/CD and infrastructure
