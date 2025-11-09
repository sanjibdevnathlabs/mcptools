# Weather MCP - Local Development

## 📦 Overview

Local development environment for Weather MCP using Docker Compose. Runs both SSE and HTTP transports simultaneously for testing weather information retrieval.

**Services:**
- `weather-sse` - SSE transport on port 8082
- `weather-http` - HTTP transport on port 8083

**External Dependency:** OpenWeatherMap API (free tier: 1,000 calls/day)

---

## 🚀 Quick Start

```bash
# Set your OpenWeatherMap API key
export OPENWEATHER_API_KEY=your_api_key_here

# From this directory
docker-compose up -d

# Or from repository root
OPENWEATHER_API_KEY=your_key make docker-compose-up-weather

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 📋 Prerequisites

1. **Docker** (20.10+) and **Docker Compose** (2.0+)
2. **OpenWeatherMap API Key** (required):
   - Sign up: https://openweathermap.org/api
   - Free tier: 1,000 calls/day, 60 calls/minute
   - Copy API key from dashboard
3. **Base image built**:
   ```bash
   cd ../../..  # Go to repo root
   make docker-build-base
   ```

---

## 🔑 Getting an API Key

1. Visit [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for a free account
3. Navigate to "API keys" in your dashboard
4. Copy your default API key (or create a new one)
5. Set as environment variable:
   ```bash
   export OPENWEATHER_API_KEY=your_api_key_here
   ```

**Free Tier Limits:**
- 1,000 API calls per day
- 60 API calls per minute
- Current weather data
- 5-day / 3-hour forecast
- Historical data (limited)

---

## ⚙️ Configuration

### Docker Compose Services

| Service | Port | Transport | Container Name | Health Check |
|---------|------|-----------|----------------|--------------|
| `weather-sse` | 8082 | SSE | `weather-sse` | ✅ TCP port check |
| `weather-http` | 8083 | HTTP | `weather-http` | ✅ TCP port check |

### Environment Variables

Both services use these environment variables:

```yaml
# Server configuration
APP_ENV: docker                     # Loads environment/docker.toml
TRANSPORT_MODE: sse|streamable-http # Transport protocol
FASTMCP_HOST: 0.0.0.0              # Bind to all interfaces
FASTMCP_PORT: 8082|8083            # Port number
LOG_LEVEL: DEBUG                    # Logging level

# API configuration
OPENWEATHER_API_KEY: (required)    # Your API key
```

**Overriding Variables:**

Create a `.env` file in this directory:

```bash
# .env
OPENWEATHER_API_KEY=your_api_key_here
LOG_LEVEL=INFO
TRANSPORT_MODE=sse
```

Or use environment variables:

```bash
OPENWEATHER_API_KEY=your_key LOG_LEVEL=INFO docker-compose up -d
```

---

## 🧪 Testing

### Using MCP Inspector

1. **Start services:**
   ```bash
   OPENWEATHER_API_KEY=your_key docker-compose up -d
   ```

2. **Test SSE transport:**
   - Open MCP Inspector: http://localhost:6274/
   - URL: `http://localhost:8082/sse`
   - Test tools: `get_current_weather`, `get_forecast`

3. **Test HTTP transport:**
   - Open MCP Inspector: http://localhost:6274/
   - URL: `http://localhost:8083/mcp`
   - Test tools: `get_current_weather`, `get_forecast`

### Using E2E Tests

```bash
# From repository root
export OPENWEATHER_API_KEY=your_key
pytest tests/test_e2e_weather.py -v

# Test specific transport
pytest tests/test_e2e_weather.py::TestWeatherSSE -v
pytest tests/test_e2e_weather.py::TestWeatherHTTP -v

# Test specific tools
pytest tests/test_e2e_weather.py::TestWeatherSSE::test_sse_get_current_weather -v
pytest tests/test_e2e_weather.py::TestWeatherSSE::test_sse_get_forecast -v
```

### Using cURL (HTTP transport)

```bash
# Initialize session
curl -X POST http://localhost:8083/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}'

# Get current weather
curl -X POST http://localhost:8083/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "get_current_weather",
      "arguments": {
        "location": "London",
        "units": "metric"
      }
    }
  }'

# Get forecast
curl -X POST http://localhost:8083/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "get_forecast",
      "arguments": {
        "location": "Paris",
        "days": 5,
        "units": "metric"
      }
    }
  }'
```

### Testing API Key

```bash
# Test API key directly
curl "https://api.openweathermap.org/data/2.5/weather?q=London&appid=YOUR_KEY"

# Or from container
docker exec weather-sse python -c "
import requests
import os

api_key = os.getenv('OPENWEATHER_API_KEY')
url = f'https://api.openweathermap.org/data/2.5/weather?q=London&appid={api_key}'

response = requests.get(url, timeout=10)
print(f'Status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    print(f'✅ API Key Valid')
    print(f'City: {data[\"name\"]}')
    print(f'Temp: {data[\"main\"][\"temp\"]}K')
else:
    print(f'❌ API Key Invalid: {response.text}')
"
```

---

## 🔍 Debugging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f weather-sse
docker-compose logs -f weather-http

# Last 50 lines
docker-compose logs --tail=50 weather-sse
```

### Shell into Containers

```bash
# SSE container
docker exec -it weather-sse /bin/bash

# HTTP container
docker exec -it weather-http /bin/bash

# Check config
docker exec weather-sse python -c "
from weather.config import config
print(f'Transport: {config.server.transport_mode}')
print(f'Port: {config.server.port}')
print(f'API Key: {config.api.openweather_api_key[:10]}...')
print(f'Base URL: {config.api.openweather_base_url}')
"
```

### Check Health

```bash
# Check health status
docker-compose ps

# Manual health check
docker exec weather-sse python -c "
import socket
s = socket.socket()
s.connect(('localhost', 8082))
s.close()
print('✅ Port 8082 is open')
"
```

### Network Inspection

```bash
# List networks
docker network ls | grep mcp

# Inspect network
docker network inspect mcp-local-network

# Check internet connectivity
docker exec weather-sse ping -c 1 api.openweathermap.org
docker exec weather-sse curl -I https://api.openweathermap.org
```

---

## 🛠️ Available Tools

The weather MCP provides tools for weather information:

### Current Weather
- `get_current_weather` - Get current weather for location
- `get_weather_by_coords` - Get weather by coordinates (lat/lon)

### Forecasts
- `get_forecast` - Get 5-day / 3-hour weather forecast
- `get_hourly_forecast` - Get hourly forecast

### Historical & Analysis
- `get_weather_alerts` - Get weather alerts and warnings
- `get_air_quality` - Get air quality index (AQI)

### Utilities
- `search_location` - Search for locations by name
- `get_weather_summary` - Get comprehensive weather summary

**Example Tool Usage:**

```python
# Get current weather
get_current_weather(location="New York", units="metric")
# Returns: temperature, humidity, pressure, wind, etc.

# Get forecast
get_forecast(location="Tokyo", days=5, units="metric")
# Returns: 5-day forecast with 3-hour intervals

# Get weather by coordinates
get_weather_by_coords(lat=51.5074, lon=-0.1278, units="metric")
# Returns: Weather for London (latitude/longitude)
```

---

## 📊 Port Mapping

| Host Port | Container Port | Service | Protocol |
|-----------|---------------|---------|----------|
| 8082 | 8082 | weather-sse | SSE |
| 8083 | 8083 | weather-http | HTTP |

**Avoiding Port Conflicts:**

If ports are already in use, modify `docker-compose.yml`:

```yaml
weather-sse:
  ports:
    - "9082:8082"  # Change host port to 9082

weather-http:
  ports:
    - "9083:8083"  # Change host port to 9083
```

---

## 🧹 Cleanup

```bash
# Stop services
docker-compose down

# Remove networks
docker-compose down -v

# Remove images
docker-compose down --rmi local

# From repository root
make docker-compose-down-weather
```

---

## 🔄 Rebuild After Code Changes

```bash
# Rebuild and restart
docker-compose up -d --build

# Or rebuild specific service
docker-compose up -d --build weather-sse

# Force complete rebuild
docker-compose build --no-cache
docker-compose up -d
```

---

## 📁 File Structure

```
weather/deployment/local/
├── docker-compose.yml   # Compose configuration
└── README.md           # This file

Related files:
├── ../../docker/
│   ├── Dockerfile      # Weather image definition
│   └── .dockerignore   # Build exclusions
└── ../../environment/
    ├── default.toml    # Default config
    └── docker.toml     # Docker overrides
```

---

## ⚠️ Common Issues

### Issue: Missing API key

```
Error: OPENWEATHER_API_KEY environment variable not set
```

**Solution:**
```bash
# Set API key before starting
export OPENWEATHER_API_KEY=your_key_here
docker-compose up -d

# Or use .env file
echo "OPENWEATHER_API_KEY=your_key" > .env
docker-compose up -d
```

### Issue: Invalid API key

```
Error: Invalid API key. Please see https://openweathermap.org/faq
```

**Solution:**
```bash
# Verify API key is correct
curl "https://api.openweathermap.org/data/2.5/weather?q=London&appid=YOUR_KEY"

# Common causes:
# 1. API key not activated yet (wait ~1 hour after signup)
# 2. Typo in API key
# 3. Account suspended
```

### Issue: Rate limit exceeded

```
Error: 429 Too Many Requests
```

**Solution:**
```bash
# Free tier: 60 calls/minute, 1000 calls/day
# Wait 1 minute or upgrade plan

# Check current usage:
# Visit: https://home.openweathermap.org/statistics
```

### Issue: No internet connectivity

```
Error: Failed to connect to api.openweathermap.org
```

**Solution:**
```bash
# Test internet from container
docker exec weather-sse ping -c 3 8.8.8.8
docker exec weather-sse curl -I https://api.openweathermap.org

# Check DNS resolution
docker exec weather-sse nslookup api.openweathermap.org

# Check firewall/proxy settings
```

---

## 🌍 API Rate Limits & Best Practices

### Free Tier Limits
- **60 calls per minute**
- **1,000 calls per day**
- **Current weather data**
- **5-day / 3-hour forecast**

### Best Practices
1. **Implement caching** (built-in: 5 minutes)
2. **Batch requests** when possible
3. **Monitor rate limits** via API headers
4. **Use appropriate units** (metric, imperial, standard)
5. **Consider upgrading** for production use

### Monitoring Usage
```bash
# Check rate limit headers in response
curl -I "https://api.openweathermap.org/data/2.5/weather?q=London&appid=YOUR_KEY"

# Look for:
# X-RateLimit-Limit: 60
# X-RateLimit-Remaining: 59
```

---

## 🔗 Related Documentation

- [Docker Image Documentation](../../docker/README.md) - Image build details
- [Weather MCP Overview](../../README.md) - Main documentation
- [OpenWeatherMap API Docs](https://openweathermap.org/api) - API reference
- [GitOps Documentation](../../../docs/) - CI/CD setup
