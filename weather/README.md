# Weather MCP Server

A fast and lightweight Model Context Protocol (MCP) server for fetching weather data from OpenWeatherMap API for Indian locations.

## 🚀 Features

- **Current Weather**: Get real-time weather data for any Indian city
- **5-Day Forecast**: Fetch weather forecast with 3-hour intervals
- **Flexible Location**: Support for city name or latitude/longitude coordinates
- **TOML Configuration**: Modern configuration with environment variable support
- **Multi-Transport**: stdio, SSE, and streamable-http support
- **Error Handling**: Structured error messages and logging

## 📦 Installation

### Prerequisites
- Python 3.11+ (3.10+ with `tomli`)
- OpenWeatherMap API key (free tier available at https://openweathermap.org/api)
- Virtual environment (recommended)

### Quick Setup

```bash
# From project root
cd /path/to/mcptools

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Set API key
export OPENWEATHER_API_KEY="your_api_key_here"

# Run the server
python -m weather
```

## ⚙️ Configuration

### TOML Configuration Files

**`weather/environment/default.toml`** (Base configuration)
```toml
[app]
# Application configuration
name = "weather-mcp-server"

[server]
# Server configuration
transport_mode = "stdio"  # Options: stdio, sse, streamable-http

# Logging configuration
log_level = "INFO"

[api]
# OpenWeatherMap API configuration
openweather_api_key = "${OPENWEATHER_API_KEY}"  # From environment variable
base_url = "https://api.openweathermap.org/data/2.5"
timeout = 10
```

**`weather/environment/dev.toml`** (Development overrides - gitignored)
```toml
[server]
transport_mode = "stdio"  # or "sse" or "streamable-http" for testing
```

### Environment Variables

```bash
# Required
export OPENWEATHER_API_KEY="your_api_key_here"
```

## 🚦 Usage

### Starting the Server

```bash
# Default (uses stdio from default.toml)
python -m weather

# The transport mode is configured in TOML files
# Edit weather/environment/dev.toml to change transport
```

### Testing with MCP Inspector

**STDIO Mode:**
```bash
# In MCP Inspector:
Transport: STDIO
Command: /absolute/path/to/mcptools/venv/bin/python
Arguments: -m weather
Working Directory: /absolute/path/to/mcptools
```

**SSE Mode:**
```bash
# Set transport in dev.toml
# [server]
# transport_mode = "sse"

python -m weather

# In MCP Inspector:
Transport: SSE
URL: http://localhost:5000/sse
```

**HTTP Mode:**
```bash
# Set transport in dev.toml
# [server]
# transport_mode = "streamable-http"

python -m weather

# In MCP Inspector:
Transport: HTTP
URL: http://localhost:5000
```

## 📖 API Reference

### Available Tools

#### `get_weather`
Get current weather for an Indian location.

```python
# Parameters:
city: Optional[str] = None         # City name (e.g., "Mumbai", "Delhi")
latitude: Optional[float] = None   # Latitude coordinate
longitude: Optional[float] = None  # Longitude coordinate

# Returns:
str  # Weather information as formatted string

# Examples:
get_weather(city="Mumbai")
get_weather(city="New Delhi")
get_weather(latitude=19.0760, longitude=72.8777)  # Mumbai coordinates
```

#### `get_forecast`
Get 5-day weather forecast with 3-hour intervals.

```python
# Parameters:
city: Optional[str] = None         # City name
latitude: Optional[float] = None   # Latitude coordinate
longitude: Optional[float] = None  # Longitude coordinate

# Returns:
str  # Forecast information as formatted string

# Examples:
get_forecast(city="Bangalore")
get_forecast(latitude=12.9716, longitude=77.5946)  # Bangalore coordinates
```

### Response Format

**Current Weather:**
```
Weather in Mumbai, IN:
Temperature: 28.5°C
Feels like: 31.2°C
Condition: Clear sky
Humidity: 75%
Wind Speed: 3.5 m/s
```

**Forecast:**
```
5-day forecast for Delhi, IN:

2024-01-15 12:00:00
  Temp: 18.3°C
  Condition: Cloudy
  Humidity: 65%

2024-01-15 15:00:00
  Temp: 22.1°C
  Condition: Clear
  Humidity: 55%

...
```

## 🔧 Development

### Configuration Structure

```python
from weather.config import Config

# Initialize config
config = Config()

# Access configuration
print(config.app.name)                    # "weather-mcp-server"
print(config.server.transport_mode)       # "stdio"
print(config.api.openweather_api_key)     # Your API key
print(config.api.base_url)                # OpenWeatherMap API URL
```

### Adding New Features

1. Add configuration to `config/` classes
2. Update `environment/default.toml` with new settings
3. Implement feature in `main.py`
4. Test with MCP Inspector

## 🐛 Troubleshooting

### API Key Issues

```bash
# Verify API key is set
echo $OPENWEATHER_API_KEY

# Test API key manually
curl "https://api.openweathermap.org/data/2.5/weather?q=Mumbai&appid=YOUR_API_KEY"
```

### Connection Issues

```bash
# Check if server is running
# For SSE/HTTP modes, verify the port is available
lsof -i :5000
```

### Invalid City Name

- Use proper city names: "Mumbai", "New Delhi", "Bangalore"
- For multi-word cities, use spaces or underscores
- Alternatively, use latitude/longitude coordinates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes in the `weather/` directory
4. Test with MCP Inspector
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**Built with FastMCP for lightweight weather data access via Model Context Protocol.**

